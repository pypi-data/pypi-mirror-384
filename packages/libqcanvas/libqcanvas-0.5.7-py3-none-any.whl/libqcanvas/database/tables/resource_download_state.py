from enum import Enum


class ResourceDownloadState(Enum):
    NOT_DOWNLOADED = 0
    DOWNLOADED = 1
    FAILED = 2

    @staticmethod
    def human_readable(value: "ResourceDownloadState"):
        match value:
            case ResourceDownloadState.NOT_DOWNLOADED:
                return "Not downloaded"
            case ResourceDownloadState.DOWNLOADED:
                return "Downloaded"
            case ResourceDownloadState.FAILED:
                return "Failed"

        raise ValueError(value)
