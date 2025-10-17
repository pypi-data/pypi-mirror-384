from bs4 import Tag

import libqcanvas.database.tables as db
from libqcanvas.net.resources.extracting.link_extractor import LinkExtractor
from libqcanvas.net.resources.extracting.no_extractor_error import NoExtractorError
from libqcanvas.util import flatten


class Extractors:
    def __init__(self, *args: LinkExtractor):
        self._extractors = list(args)
        self._tag_whitelist = set(
            flatten([extractor.tag_whitelist for extractor in self._extractors])
        )

    def add(self, extractor: LinkExtractor):
        self._extractors.append(extractor)
        self._tag_whitelist.update(extractor.tag_whitelist)

    def extend(self, extractors: list[LinkExtractor]):
        self._extractors.extend(extractors)
        self._tag_whitelist.update(
            flatten([extractor.tag_whitelist for extractor in extractors])
        )

    def extractor_for_tag(self, tag: Tag) -> LinkExtractor:
        for extractor in self._extractors:
            if extractor.accepts_tag(tag):
                return extractor

        raise NoExtractorError()

    def extractor_for_resource(self, resource: db.Resource) -> LinkExtractor:
        split = str(resource.id).split(LinkExtractor.RESOURCE_ID_SEPARATOR, 2)
        extractor_name = split[0]

        for extractor in self._extractors:
            if extractor.extractor_id == extractor_name:
                return extractor

        raise NoExtractorError()

    @property
    def tag_whitelist(self) -> set[str]:
        return self._tag_whitelist
