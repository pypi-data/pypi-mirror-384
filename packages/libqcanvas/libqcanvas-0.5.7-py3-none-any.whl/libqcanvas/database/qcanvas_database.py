import logging
from pathlib import Path
from typing import Sequence

import sqlalchemy
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectin_polymorphic

import libqcanvas.database.tables as db
from libqcanvas.database.data_monolith import DataMonolith
from libqcanvas.database.tables.canvas_database_types import Base

_logger = logging.getLogger(__name__)


class QCanvasDatabase:
    def __init__(self, database_file: Path):
        self._database_file = database_file
        self._engine = create_async_engine(f"sqlite+aiosqlite:///{database_file}")
        self._session_maker = async_sessionmaker(self._engine, expire_on_commit=False)

    @staticmethod
    async def create(database_file: Path) -> "QCanvasDatabase":
        _database = QCanvasDatabase(database_file)
        await _database.init()
        return _database

    async def upgrade(self) -> None:
        if not self._database_file.exists():
            _logger.info("Database does not exist, not upgrading")
            return

        _logger.info("Preparing for database upgrade")

        config = self._get_alembic_config()
        script_dir = ScriptDirectory.from_config(config)

        async with self._engine.begin() as conn:

            def get_current_revision(connection: Connection) -> str:
                migration_context = MigrationContext.configure(connection=connection)
                return migration_context.get_current_revision()

            head = script_dir.get_revision("head").revision
            current_revision = await conn.run_sync(get_current_revision)

            _logger.debug("current head = %s, head = %s", current_revision, head)

            if current_revision == head:
                _logger.info("Upgrade not required")
                return
            else:
                # ScriptDirectory is 2hard4me... just use the command wrapper instead
                _logger.info("Upgrading database to %s", head)

                def run_upgrade(
                    connection: sqlalchemy.Connection, config: Config
                ) -> None:
                    config.attributes["connection"] = connection

                    command.upgrade(config, "head")

                await conn.run_sync(run_upgrade, config)

    async def init(self):
        is_first_run = not self._database_file.exists()

        if is_first_run:
            _logger.info("First run detected")

            async with self._engine.begin() as conn:

                def run_stamp(
                    connection: sqlalchemy.Connection, config: Config
                ) -> None:
                    config.attributes["connection"] = connection

                    command.stamp(config, "head")

                await conn.run_sync(Base.metadata.create_all)
                await conn.run_sync(run_stamp, self._get_alembic_config())
        else:
            _logger.info("Database already exists")

    @staticmethod
    def _get_alembic_config() -> Config:
        module_dir = Path(__file__).resolve().parents[1]
        alembic_dir = module_dir / "alembic"

        config = Config()
        config.set_main_option("script_location", str(alembic_dir.absolute()))

        return config

    def session(self):
        # Return type is missing intentionally.
        # Don't try and make this a context manager (which would normally be better) because pycharm still can't
        # determine the type correctly. Blech.
        return self._session_maker.begin()

    async def get_existing_course_ids(self) -> Sequence[str]:
        async with self._session_maker.begin() as session:
            return (await session.scalars(select(db.Course.id))).all()

    async def get_existing_resources(self) -> Sequence[db.Resource]:
        async with self._session_maker.begin() as session:
            stmt = select(db.Resource)
            return (await session.scalars(stmt)).all()

    async def get_resource(self, id: str) -> db.Resource:
        async with self._session_maker.begin() as session:
            stmt = (
                select(db.Resource)
                .where(db.Resource.id == id)
                .options(selectin_polymorphic(db.Resource, [db.PanoptoResource]))
            )
            return (await session.scalars(stmt)).one()

    async def record_resource_downloaded(
        self, resource: db.Resource, final_file_size: int
    ):
        await self._update_resource_download_state(
            resource,
            state=db.ResourceDownloadState.DOWNLOADED,
            final_file_size=final_file_size,
        )

    async def record_resource_download_failed(
        self, resource: db.Resource, message: str
    ):
        await self._update_resource_download_state(
            resource, message=message, state=db.ResourceDownloadState.FAILED
        )

    async def _update_resource_download_state(
        self,
        resource: db.Resource,
        *,
        state: db.ResourceDownloadState,
        final_file_size: int | None = None,
        message: str | None = None,
    ):
        async with self._session_maker.begin() as session:
            resource.download_state = state
            resource.download_error_message = message
            resource.file_size = final_file_size

            await session.execute(
                update(db.Resource),
                [
                    {
                        db.Resource.id.key: resource.id,
                        db.Resource.download_state.key: resource.download_state,
                        db.Resource.download_error_message.key: resource.download_error_message,
                        db.Resource.file_size.key: final_file_size,
                    }
                ],
            )

    async def get_data(self) -> DataMonolith:
        async with self.session() as session:
            return await DataMonolith.create(session)
