import logging
import platform
import re
import tempfile
from abc import ABC, abstractmethod
from asyncio import BoundedSemaphore, TaskGroup
from pathlib import Path, PurePath
from typing import Sequence

from aiofile import async_open
from asynctaskpool import AsyncTaskPool

import libqcanvas.database.tables as db
from libqcanvas.database import QCanvasDatabase
from libqcanvas.net.resources.extracting.extractors import Extractors
from libqcanvas.net.resources.extracting.link_extractor import LinkExtractor
from libqcanvas.net.resources.scanning.resource_scanner import ResourceScanner
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import ContextManagerReporter

_logger = logging.getLogger(__name__)
_temp_download_dir = Path(tempfile.gettempdir()) / "qcanvas"


class ResourceManager(ABC):
    def __init__(
        self,
        database: QCanvasDatabase,
        download_dest: Path,
        extractors: Extractors = Extractors(),
        max_concurrent_downloads: int = 8,
    ):
        super().__init__()
        self._download_pool = AsyncTaskPool[None]()
        self._db = database
        self._extractors = extractors
        self._scanner = ResourceScanner(extractors)
        self._download_dest = download_dest
        self._download_limiter = BoundedSemaphore(max_concurrent_downloads)

    def add_existing_resources(self, existing_resources: Sequence[db.Resource]):
        self._scanner.add_existing_resources(existing_resources)

    def is_video(self, resource: db.Resource) -> bool:
        # todo using the extractor to tell if its a video is kinda lacklustre
        return self._extractors.extractor_for_resource(resource).is_video_extractor

    async def batch_download(
        self,
        resources: list[db.Resource],
    ) -> None:
        downloads: list[tuple[LinkExtractor, db.Resource]] = []
        deferred_downloads: list[tuple[LinkExtractor, db.Resource]] = []

        for resource in resources:
            extractor = self._extractors.extractor_for_resource(resource)

            # Defer large downloads to do them 1 at a time
            if extractor.is_video_extractor:
                deferred_downloads.append((extractor, resource))
            else:
                downloads.append((extractor, resource))

        async with TaskGroup() as tg:
            for extractor, resource in downloads:
                tg.create_task(
                    self._start_download(extractor, resource, suppress_exceptions=True)
                )

        # Do large downloads one at a time. Parallelizing them is unlikely to speed anything up.
        for extractor, resource in deferred_downloads:
            await self._start_download(extractor, resource, suppress_exceptions=True)

    async def download(self, resource: db.Resource) -> None:
        if resource.download_state != db.ResourceDownloadState.DOWNLOADED:
            extractor = self._extractors.extractor_for_resource(resource)
            await self._start_download(extractor, resource)

    async def _start_download(
        self,
        extractor: LinkExtractor,
        resource: db.Resource,
        suppress_exceptions: bool = False,
    ) -> None:
        await self._download_pool.submit(
            resource.id,
            self._download_task(
                extractor, resource, suppress_exceptions=suppress_exceptions
            ),
        )

    async def _download_task(
        self,
        extractor: LinkExtractor,
        resource: db.Resource,
        *,
        suppress_exceptions: bool = False,
    ) -> None:
        download_destination = self.resource_download_location(resource)

        if download_destination.exists():
            _logger.info(
                f"Resource {resource.file_name} seems to already be downloaded, skipping download"
            )

            await self._finished_download(
                resource, final_file_size=download_destination.stat().st_size
            )
            return
        else:
            download_destination.parent.mkdir(parents=True, exist_ok=True)

        async with self._download_limiter:
            try:
                # Use a temporary destination to download the file to, then once it's done, move it to the proper location.
                # This way, if something goes wrong we won't have garbage files in the download directory.
                temp_destination = self._prepare_temp_download_dest(resource)

                with register_reporter(
                    ContextManagerReporter("Download", resource.file_name, 0)
                ) as prog:  # type: ContextManagerReporter
                    async for progress in extractor.download(
                        resource,
                        destination=temp_destination,
                    ):
                        prog.progress(progress.downloaded_bytes, progress.total_bytes)
                        self.on_download_progress(
                            resource=resource,
                            current=progress.downloaded_bytes,
                            total=progress.total_bytes,
                        )

                    # Copy the temp file to the proper location
                    await _async_copy(src=temp_destination, dest=download_destination)
            except Exception as e:
                await self._db.record_resource_download_failed(resource, message=str(e))
                self.on_download_failed(resource)

                if not suppress_exceptions:
                    raise RuntimeError() from e
                else:
                    _logger.warning("Download failed", exc_info=e)
            else:
                # Get the file size so we can update the DB record to be accurate
                file_size = download_destination.stat().st_size

                await self._finished_download(resource, final_file_size=file_size)
            finally:
                # Delete the temp file if it was created
                temp_destination.unlink(missing_ok=True)

    async def _finished_download(
        self, resource: db.Resource, final_file_size: int
    ) -> None:
        await self._db.record_resource_downloaded(resource, final_file_size)
        self.on_download_finished(resource)

    def _prepare_temp_download_dest(self, resource: db.Resource) -> Path:
        _temp_download_dir.mkdir(parents=True, exist_ok=True)
        temp_destination = _temp_download_dir / self.resource_download_file_name(
            resource
        )
        return temp_destination

    def resource_download_location(self, resource: db.Resource) -> Path:
        return (
            self._download_dest
            / self.course_folder_name(resource.course)
            / self.resource_download_file_name(resource)
        )

    def resource_download_file_name(self, resource: db.Resource) -> str:
        file_name, file_suffix = ResourceManager._split_resource_name(resource)
        file_suffix = f" [{resource.id}]{file_suffix}"
        # Ensure the filename is not too long, most filesystems permit up to 255 chars
        file_name = file_name[: 255 - len(file_suffix)]

        return self._replace_illegal_chars(file_name + file_suffix)

    def course_folder_name(self, course: db.Course) -> str:
        return self._replace_illegal_chars(course.name)

    @staticmethod
    def _split_resource_name(resource: db.Resource) -> tuple[str, str]:
        file = PurePath(resource.file_name)
        return file.stem, file.suffix

    @staticmethod
    def _replace_illegal_chars(file_name: str) -> str:
        if platform.system() == "Windows":
            return re.sub(r"[<>:\"/\\|?*]", "_", file_name)
        else:
            return file_name.replace("/", "_")

    @property
    def scanner(self) -> ResourceScanner:
        return self._scanner

    @property
    def extractors(self) -> Extractors:
        return self._extractors

    @property
    def downloads_folder(self) -> Path:
        return self._download_dest

    @abstractmethod
    def on_download_progress(
        self, resource: db.Resource, current: int, total: int
    ) -> None: ...

    @abstractmethod
    def on_download_failed(self, resource: db.Resource) -> None: ...

    @abstractmethod
    def on_download_finished(self, resource: db.Resource) -> None: ...


async def _async_copy(*, src: Path, dest: Path) -> None:
    async with async_open(src, "rb") as src_file, async_open(dest, "wb") as dest_file:
        async for chunk in src_file.iter_chunked(65535):
            await dest_file.write(chunk)
