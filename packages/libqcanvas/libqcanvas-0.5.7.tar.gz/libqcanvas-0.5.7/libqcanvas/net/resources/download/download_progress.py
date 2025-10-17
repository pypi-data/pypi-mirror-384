from typing import NamedTuple


class DownloadProgress(NamedTuple):
    downloaded_bytes: int
    total_bytes: int
