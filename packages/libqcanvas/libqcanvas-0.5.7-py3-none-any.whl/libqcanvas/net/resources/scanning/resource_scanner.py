import logging
from typing import NamedTuple, Optional, Sequence

import bs4
from asynctaskpool import AsyncTaskPool
from asynctaskpool.task_failed_exception import TaskFailedError
from bs4 import Tag

import libqcanvas.database.tables as db
from libqcanvas.net.constants import SYNC_GOAL
from libqcanvas.net.resources.extracting.extractors import Extractors
from libqcanvas.net.resources.extracting.no_extractor_error import NoExtractorError
from libqcanvas.net.resources.scanning.extracted_resources import ExtractedResources
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import CompoundTaskReporter
from libqcanvas.util import CollectingTaskGroup, is_link_invisible

_logger = logging.getLogger(__name__)


class _HiddenResource(NamedTuple):
    """
    A HiddenResource is a resource that, due to stupid shit that canvas does, may be in the HTML of a course page but
    are completely invisible, due to containing no text. I suspect these are created from something weird the canvas
    RCE (rich content editor) is doing when people edit links/pages.

    See Also
    --------
    libqcanvas.util.canvas_data_sanitiser.is_link_invisible
    """

    resource: db.Resource
    is_hidden: bool


class ResourceScanner:
    """
    A ResourceScanner uses Extractors to extract resources from course content
    """

    def __init__(self, extractors: Extractors):
        self._lazy_resource_cache = AsyncTaskPool[db.Resource]()
        self._extractor_collection = extractors

    def add_existing_resources(self, existing_resources: Sequence[db.Resource]):
        resources_mapped_by_id = {
            resource.id: resource for resource in existing_resources
        }
        self._lazy_resource_cache.update_results(resources_mapped_by_id)

    async def scan_content_for_resources(
        self, content_items: Sequence[db.AnyContentItem]
    ) -> list[ExtractedResources]:
        _logger.info("Scanning %i content items for resources", len(content_items))

        if len(content_items) == 0:
            return []

        with register_reporter(
            CompoundTaskReporter(SYNC_GOAL, "Scan for resources", len(content_items))
        ) as prog:
            async with CollectingTaskGroup[ExtractedResources]() as tg:
                for content_item in content_items:
                    prog.attach(
                        tg.create_task(self._extract_content_resources(content_item))
                    )

        return tg.results

    async def _extract_content_resources(
        self, content: db.AnyContentItem
    ) -> ExtractedResources:
        async with CollectingTaskGroup[_HiddenResource | None]() as tg:
            for tag in self._extract_tags_from_page(content):
                tg.create_task(
                    self._extract_resource(
                        tag=tag, course_id=content.course_id, content_id=content.id
                    )
                )

        invisible_resources = []
        visible_resources = []

        for resource, is_invisible in filter(None, tg.results):
            if is_invisible:
                invisible_resources.append(resource)
            else:
                visible_resources.append(resource)

        _logger.debug(
            "Found %i resources (%i invisible) on %s %s (id='%s')",
            len(invisible_resources) + len(visible_resources),
            len(invisible_resources),
            type(content).__name__,
            content.name,
            content.id,
        )

        return ExtractedResources(
            content=content,
            resources=visible_resources,
            invisible_resources=invisible_resources,
        )

    async def _extract_resource(
        self, tag: Tag, course_id: str, content_id: str
    ) -> Optional[_HiddenResource]:
        file_id = None

        try:
            extractor = self._extractor_collection.extractor_for_tag(tag)
            file_id = extractor.resource_id_from_tag(tag)

            result = await self._lazy_resource_cache.submit(
                task_id=file_id,
                future=extractor.resource_from_tag(
                    tag, course_id=course_id, resource_id=file_id
                ),
            )

            return _HiddenResource(resource=result, is_hidden=is_link_invisible(tag))
        except TaskFailedError as e:
            _logger.warning(
                "Extraction failed for file_id=%s on page id=%s",
                file_id or "(no id)",
                content_id,
                exc_info=e,
            )
        except NoExtractorError:
            pass
        except Exception as e:
            _logger.warning("Could not extract resource", exc_info=e)
            pass

    def _extract_tags_from_page(self, page: db.AnyContentItem) -> list[Tag]:
        if page.body is None:
            return []

        doc = bs4.BeautifulSoup(page.body, "html.parser")
        return doc.find_all(self._extractor_collection.tag_whitelist)
