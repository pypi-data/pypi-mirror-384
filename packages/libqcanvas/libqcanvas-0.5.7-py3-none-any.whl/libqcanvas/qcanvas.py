import logging
from asyncio import BoundedSemaphore
from pathlib import Path
from typing import Optional, Type

from libqcanvas_clients.canvas import CanvasClient, CanvasClientConfig
from libqcanvas_clients.panopto import (
    FakePanoptoClient,
    PanoptoClient,
    PanoptoClientConfig,
)

import libqcanvas.database.tables as db
from libqcanvas.database import QCanvasDatabase
from libqcanvas.database.data_monolith import DataMonolith
from libqcanvas.net.resources.download.resource_manager import ResourceManager
from libqcanvas.net.resources.extracting import (
    CanvasFileExtractor,
    CanvasMediaObjectExtractor,
    EmbeddedPanoptoExtractor,
)
from libqcanvas.net.resources.extracting.extractors import Extractors
from libqcanvas.net.resources.extracting.link_extractor import LinkExtractor
from libqcanvas.net.sync.sync_receipt import SyncReceipt
from libqcanvas.net.sync.synchronization_client import SynchronizationClient
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import AtomicTaskReporter

_logger = logging.getLogger(__name__)


class QCanvas[U: ResourceManager]:
    def __init__(
        self,
        canvas_config: CanvasClientConfig,
        panopto_config: Optional[PanoptoClientConfig],
        storage_path: Path,
        resource_manager_class: Type[U],
    ):
        storage_path.mkdir(parents=True, exist_ok=True)

        self._data_cache = None
        self._cache_semaphore = BoundedSemaphore()
        self.canvas_client = CanvasClient(client_config=canvas_config)

        if panopto_config is None:
            self.panopto_client = FakePanoptoClient()
        else:
            self.panopto_client = PanoptoClient(
                client_config=panopto_config, canvas_client=self.canvas_client
            )

        self.database = QCanvasDatabase(storage_path / "qcanvas.v2.db")
        self.resource_manager: U = self._create_resource_manager(
            manager=resource_manager_class,
            database=self.database,
            download_dest=storage_path / "downloads",
            extractors=Extractors(*self._create_extractors()),
        )
        self._synchronization_client = SynchronizationClient(
            database=self.database,
            canvas_client=self.canvas_client,
            panopto_client=self.panopto_client,
            resource_scanner=self.resource_manager.scanner,
            sync_meta_store_location=storage_path / "sync_meta.json",
        )
        self._init_called = False

    def _create_extractors(self) -> list[LinkExtractor]:
        result = [
            CanvasFileExtractor(self.canvas_client),
            CanvasMediaObjectExtractor(self.canvas_client),
        ]

        if not isinstance(self.panopto_client, FakePanoptoClient):
            result.append(
                EmbeddedPanoptoExtractor(self.canvas_client, self.panopto_client)
            )

        return result

    @staticmethod
    def _create_resource_manager(
        manager: Type[U],
        database: QCanvasDatabase,
        download_dest: Path,
        extractors: Extractors,
    ) -> ResourceManager:
        return manager(
            database=database, download_dest=download_dest, extractors=extractors
        )

    async def init(self) -> None:
        await self.database.init()
        self.resource_manager.add_existing_resources(
            await self.database.get_existing_resources()
        )

        self._init_called = True

    async def synchronise_canvas(self, quick_sync: bool = False) -> SyncReceipt:
        assert self._init_called
        _logger.info("Synchronising")

        receipt = await self._synchronization_client.synchronise_canvas(
            include_old_courses=quick_sync
        )
        await self._reload_data()
        return receipt

    async def _reload_data(self) -> None:
        self._data_cache = None
        await self.load()

    async def download(self, resource: db.Resource) -> None:
        assert self._init_called
        _logger.info(
            "Downloading %s (course_id=%s)", resource.file_name, resource.course_id
        )

        await self.resource_manager.download(resource)

    async def load(self) -> DataMonolith:
        assert self._init_called

        async with self._cache_semaphore:
            if self._data_cache is None:
                _logger.info("Loading all data from database")

                # Reading the entire DB can take a few seconds (especially when in portable mode on a shitty usb stick)
                with register_reporter(AtomicTaskReporter("Load", "Read database")):
                    self._data_cache = await self.database.get_data()

            return self._data_cache
