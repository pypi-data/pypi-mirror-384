"""Python bindings for librqbit - a feature-rich BitTorrent client library"""

from .pyrqbit import Session, TorrentHandle
from .client import (
    TorrentClient,
    DownloadProgress,
    download_torrent,
    quick_download,
)

__version__ = "0.1.0"
__all__ = [
    # Low-level API
    "Session",
    "TorrentHandle",
    # High-level API
    "TorrentClient",
    "DownloadProgress",
    "download_torrent",
    "quick_download",
]
