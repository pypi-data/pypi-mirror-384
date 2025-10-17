import asyncio
from pathlib import Path
from typing import AsyncIterator, Callable

import asynchronize
import yt_dlp
from httpx import URL
from libqcanvas_clients.panopto import PanoptoClient
from yt_dlp import DownloadError

from libqcanvas.net.resources.download.download_progress import DownloadProgress


async def download_video(
    video_id: str, client: PanoptoClient, destination: Path
) -> AsyncIterator[DownloadProgress]:
    max_retries = 3
    retries = 0

    while retries < max_retries:
        retries += 1

        callback = asynchronize.AsyncCallback()
        download_task = asyncio.create_task(
            asyncio.to_thread(
                _download_helper,
                headers={"cookie": cookies_for_download(client)},
                url=client.get_viewer_url(video_id),
                destination=destination,
                step_callback=callback.step_callback,
                done_callback=callback.finished_callback,
            )
        )

        yield DownloadProgress(0, 0)
        finished = False

        async for message in callback:
            if _is_progress_message(message):
                progress = _unwrap_args(message)

                current = int(progress["downloaded_bytes"])
                total = int(progress["total_bytes"])

                if current != total or not finished:
                    if current >= total:
                        finished = True

                    yield DownloadProgress(
                        downloaded_bytes=current,
                        # yt-dlp frequently reports progress > 100% - the task reporter listening to this download will not accept this,
                        # so ensure that current <= total always holds
                        total_bytes=max(total, current),
                    )
        try:
            await download_task

            # Ensure we indicate we are finished
            if not finished:
                yield DownloadProgress(downloaded_bytes=1, total_bytes=1)

            return
        except DownloadError as e:
            if _is_logged_out_error(e):
                await client.force_authenticate()
                continue
            else:
                raise RuntimeError() from e
        except Exception as e:
            raise RuntimeError() from e

    if retries == max_retries:
        raise RuntimeError(
            f"Gave up trying to download panopto video after {max_retries} attempts"
        )


def _is_progress_message(message: asynchronize.Args) -> bool:
    if len(message.args) >= 1 and isinstance(message.args[0], dict):
        data = _unwrap_args(message)

        return "total_bytes" in data and "downloaded_bytes" in data

    return False


def _unwrap_args(args: asynchronize.Args) -> dict:
    return args.args[0]


def _is_logged_out_error(e: DownloadError):
    return "This video is only available for registered users" in e.msg


def _download_helper(
    url: URL,
    headers: dict[str, str],
    destination: Path,
    done_callback: Callable,
    step_callback: Callable,
):
    try:
        with yt_dlp.YoutubeDL(
            dict(
                progress_hooks=[step_callback],
                http_headers=headers,
                outtmpl=str(destination.absolute()),
            )
        ) as ytdl:
            ytdl.download(str(url))
    finally:
        done_callback()


def cookies_for_download(client: PanoptoClient) -> str:
    return ";".join(
        [f"{cookie.name}={cookie.value}" for cookie in client.cookies_for_download]
    )
