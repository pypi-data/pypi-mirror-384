from pathlib import Path
from typing import AsyncIterator, NamedTuple

from bs4 import Tag
from httpx import URL
from libqcanvas_clients.canvas import CanvasClient

import libqcanvas.database.tables as db
from libqcanvas.net.resources.download.download_progress import DownloadProgress
from libqcanvas.net.resources.extracting.link_extractor import LinkExtractor


class _CanvasResourceInfo(NamedTuple):
    file_id: str
    course_id: str


class CanvasFileExtractor(LinkExtractor):
    extractor_id = "canvas"

    def __init__(self, canvas_client: CanvasClient):
        super().__init__(tag_whitelist=["a", "img"])
        self._canvas_client = canvas_client

    def _is_tag_valid(self, tag: Tag) -> bool:
        if "data-api-returntype" not in tag.attrs:
            return False
        elif tag.attrs["data-api-returntype"] != "File":
            return False

        return True

    async def download(
        self, resource: db.Resource, destination: Path
    ) -> AsyncIterator[DownloadProgress]:
        yield DownloadProgress(0, 0)

        response = await self._canvas_client.get_file_download_stream(resource.url)

        try:
            async for progress in self._download_stream_response(
                destination, response, resource.file_size
            ):
                yield progress
        finally:
            await response.aclose()

    async def _extract_resource(self, tag: Tag) -> db.Resource:
        file_id, course_id = self._course_and_file_id_from_tag(tag)
        file = await self._canvas_client.get_file(file_id=file_id, course_id=course_id)

        return db.Resource(
            url=file.url,
            file_name=file.display_name,
            file_size=file.size,
        )

    def _tag_id(self, tag: Tag) -> str:
        return self._course_and_file_id_from_tag(tag).file_id

    def _course_and_file_id_from_tag(self, tag: Tag) -> _CanvasResourceInfo:
        # https://canvas_instance/api/v1/courses/123/files/456...
        # ---------- Extract these parts:        ^^^  and  ^^^

        parts = self._tag_api_endpoint(tag).path.rsplit("/", 3)
        return _CanvasResourceInfo(file_id=parts[-1], course_id=parts[-3])

    @staticmethod
    def _tag_api_endpoint(tag: Tag) -> URL:
        return URL(tag.attrs["data-api-endpoint"])
