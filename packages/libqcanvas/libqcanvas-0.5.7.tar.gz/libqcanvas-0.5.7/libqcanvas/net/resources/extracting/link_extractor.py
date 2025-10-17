import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional, final

import httpx
from aiofile import async_open
from bs4 import Tag

import libqcanvas.database.tables as db
from libqcanvas.net.resources.download.download_progress import DownloadProgress

# Use a single client for the generic downloader, making a lot of clients is not a great idea
_generic_download_client = httpx.AsyncClient(http2=True)

_logger = logging.getLogger(__name__)


class LinkExtractor(ABC):
    """
    Resource ids are formatted using this:
    <extractor name>{RESOURCE_ID_SEPARATOR}<resource id>
    E.g. canvas$12341234
    """

    RESOURCE_ID_SEPARATOR = "$"

    def __init__(
        self,
        tag_whitelist: list[str],
        is_video_extractor: bool = False,
    ):
        if not hasattr(self, "extractor_id"):
            raise AttributeError(
                f"{type(self).__name__} is missing extractor_id (did you forget to define it?)"
            )

        # Convince pycharm that extractor_id is a real thing
        self.extractor_id: str = getattr(self, "extractor_id")
        self._tag_whitelist = tag_whitelist
        self._is_video_extractor = is_video_extractor

    @final
    def accepts_tag(self, tag: Tag) -> bool:
        if tag.name not in self.tag_whitelist:
            return False
        else:
            return self._is_tag_valid(tag)

    @abstractmethod
    def _is_tag_valid(self, tag: Tag) -> bool: ...

    @final
    def resource_id_from_tag(self, tag: Tag) -> str:
        return f"{self.extractor_id}{self.RESOURCE_ID_SEPARATOR}{self._tag_id(tag)}"

    @abstractmethod
    def _tag_id(self, tag: Tag) -> str: ...

    @final
    async def resource_from_tag(
        self, tag: Tag, course_id: str, resource_id: str
    ) -> db.Resource:
        resource = await self._extract_resource(tag)
        resource.id = resource_id
        resource.course_id = course_id
        resource.discovery_date = datetime.now().astimezone()

        return resource

    @abstractmethod
    async def _extract_resource(self, tag: Tag) -> db.Resource: ...

    async def download(
        self, resource: db.Resource, destination: Path
    ) -> AsyncIterator[DownloadProgress]:
        _logger.info("Using generic downloader for %s", resource.id)

        yield DownloadProgress(0, 0)

        finished = False

        async with _generic_download_client.stream(
            url=resource.url, method="get", follow_redirects=True
        ) as response:  # type: httpx.Response
            async for progress in self._download_stream_response(
                destination, response, resource.file_size
            ):
                yield progress

                if progress.downloaded_bytes >= progress.total_bytes:
                    finished = True

        if not finished:
            # Make sure we emit a download finished value
            yield DownloadProgress(1, 1)

    @staticmethod
    async def _download_stream_response(
        destination: Path, response: httpx.Response, file_size: Optional[int]
    ) -> AsyncIterator[DownloadProgress]:
        response.raise_for_status()

        if "content-length" in response.headers:
            content_length = int(response.headers["content-length"])
        elif file_size is not None:
            content_length = file_size
        else:
            _logger.warning(
                "Content length was missing from response and file size is unknown"
            )
            _logger.debug("Headers were %s", ", ".join(response.headers.keys()))
            _logger.debug(
                "content-type: %s", response.headers.get("content-type", "MISSING!")
            )

            # Use 1 as default to prevent division by 0 errors
            content_length = 1

        async with async_open(destination, "wb") as out:
            async for chunk in response.aiter_bytes():
                await out.write(chunk)

                downloaded_bytes = int(response.num_bytes_downloaded)
                # Use max to increase total bytes if downloaded_bytes exceeds the (sometimes unreliable) reported file size
                total_bytes = max(
                    content_length,
                    downloaded_bytes,
                )

                yield DownloadProgress(
                    total_bytes=total_bytes,
                    downloaded_bytes=downloaded_bytes,
                )

    @property
    def tag_whitelist(self) -> list[str]:
        return self._tag_whitelist

    @property
    def is_video_extractor(self) -> bool:
        return self._is_video_extractor
