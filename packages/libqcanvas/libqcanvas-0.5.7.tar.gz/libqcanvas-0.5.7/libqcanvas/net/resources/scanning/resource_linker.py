import logging
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

import libqcanvas.database.tables as db
from libqcanvas.database import resource_links
from libqcanvas.net.resources.scanning.extracted_resources import ExtractedResources
from libqcanvas.net.sync.canvas_sync_observer import CanvasSyncObservable

_logger = logging.getLogger(__name__)


class ResourceLinker(CanvasSyncObservable):
    def __init__(self, session: AsyncSession):
        super().__init__()
        self._session = session

    async def link_resources(self, extracted_resource_links: list[ExtractedResources]):
        if len(extracted_resource_links) == 0:
            return

        await self._mark_content_links_as_dead(extracted_resource_links)
        await self._link_new_resources_and_restore_active_links(
            extracted_resource_links
        )

    async def _mark_content_links_as_dead(
        self, extracted_resource_links: list[ExtractedResources]
    ):
        await resource_links.bulk_change_embedded_link_states(
            self._session,
            [link.content for link in extracted_resource_links],
            link_state="residual",
        )

    async def _link_new_resources_and_restore_active_links(
        self, extracted_resource_links: list[ExtractedResources]
    ):
        for link in extracted_resource_links:
            existing_resource_links = await resource_links.get_associated_resource_ids(
                self._session, link.content, link_type="embedded"
            )
            newly_linked_resources: list[str] = []

            await self._create_links_for_resources(
                existing_resource_links=existing_resource_links,
                extracted_resource_links=link,
                newly_linked_resources=newly_linked_resources,
            )

            await self._create_links_for_invisible_resources(
                existing_resource_links=existing_resource_links,
                extracted_resource_links=link,
                newly_linked_resources=newly_linked_resources,
            )

    async def _create_links_for_resources(
        self,
        existing_resource_links: Sequence[str],
        extracted_resource_links: ExtractedResources,
        newly_linked_resources: list[str],
    ):
        for extracted_resource in extracted_resource_links.resources:
            if extracted_resource.id in existing_resource_links:
                # If a resource is still linked on this page, reactivate the link
                await resource_links.change_embedded_link_state(
                    session=self._session,
                    content_item=extracted_resource_links.content,
                    resource=extracted_resource,
                    link_state="active",
                )
            # Prevent adding duplicate links (duplicate links have been observed on some pages)
            elif extracted_resource.id not in newly_linked_resources:
                await resource_links.create_resource_link(
                    self._session,
                    content_item=extracted_resource_links.content,
                    resource=extracted_resource,
                )
                newly_linked_resources.append(extracted_resource.id)

                await self._add_resource_to_db_if_new(extracted_resource)

    async def _create_links_for_invisible_resources(
        self,
        existing_resource_links: Sequence[str],
        extracted_resource_links: ExtractedResources,
        newly_linked_resources: list[str],
    ):
        for resource in extracted_resource_links.invisible_resources:
            if (
                resource.id in existing_resource_links
                or resource.id in newly_linked_resources
            ):
                # If the resource was already on the page, or it has just been added, don't add it again
                continue

            await resource_links.create_resource_link(
                self._session,
                content_item=extracted_resource_links.content,
                resource=resource,
                link_state="residual",
            )
            newly_linked_resources.append(resource.id)
            await self._add_resource_to_db_if_new(resource)

    async def _add_resource_to_db_if_new(self, resource: db.Resource):
        does_not_exist = (await self._session.get(db.Resource, resource.id)) is None

        if does_not_exist:
            _logger.debug("New resource %s (id=%s)", resource.file_name, resource.id)
            self._session.add(resource)
            self.notify_observers_for_updated_item(resource)
