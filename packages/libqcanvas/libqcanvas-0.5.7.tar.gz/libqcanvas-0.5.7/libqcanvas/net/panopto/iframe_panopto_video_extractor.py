import json
import logging
import re
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup, Tag
from httpx import URL, HTTPStatusError, Response
from libqcanvas_clients.canvas import CanvasClient
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from libqcanvas.net.panopto.iframe_panopto_video_info import IFramePanoptoVideoInfo
from libqcanvas.util import extract_form_inputs


class IFramePanoptoVideoExtractor:
    _logger = logging.getLogger(__name__)
    _info_json_pattern = re.compile(
        r"new PanoptoTS\.Embed\.EmbeddedViewer\((.+)\);[\r\n]"
    )

    def __init__(self, canvas_client: CanvasClient):
        self._canvas_client = canvas_client

    @retry(
        wait=wait_exponential(exp_base=1.2, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type(HTTPStatusError),
        stop=stop_after_attempt(8),
    )
    async def retrieve_embedded_video_info(
        self, embedded_url: str | URL
    ) -> IFramePanoptoVideoInfo:
        # Panopto videos can be embedded on in 2 or 3 ways for some reason. One of those ways is through an "LTI"
        # (learning tool integration) and the way it works normally (on the browser) is that it makes several requests
        # which return pages with a form on them that is autosubmitted through javascript. This happens twice, as you
        # can see below.
        response = await self._make_request(embedded_url)
        response = await self._execute_next_form_action_from_response(response)
        response = await self._execute_next_form_action_from_response(response)

        response.raise_for_status()

        # self._logger.debug("Found video info at %s", response.url)

        return IFramePanoptoVideoInfo(**self._extract_info_json(response.text))

    async def _execute_next_form_action_from_response(
        self, response: Response
    ) -> Response:
        doc = BeautifulSoup(response.text, features="html.parser")
        return await self._execute_html_form_action(doc.find("form"))

    async def _execute_html_form_action(self, form_element: Tag) -> Response:
        attrs = form_element.attrs

        return await self._make_request(
            method=attrs["method"],
            url=attrs["action"],
            data=extract_form_inputs(form_element),
        )

    async def _make_request(
        self, url: str | URL, method: str = "GET", data: Optional[dict] = None
    ) -> Response:
        response = await self._canvas_client.make_generic_request(
            httpx.Request(url=url, method=method, data=data), follow_redirects=True
        )

        return response.raise_for_status()

    def _extract_info_json(self, response_text: str) -> dict[str, Any]:
        matches = self._info_json_pattern.findall(response_text)
        if len(matches) != 1:
            raise ValueError(
                f"Expected to have exactly 1 info json match, got {len(matches)}"
            )

        return json.loads(matches[0])
