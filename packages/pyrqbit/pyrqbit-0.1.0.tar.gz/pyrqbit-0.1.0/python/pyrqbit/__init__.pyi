"""Python bindings for librqbit - a feature-rich BitTorrent client library"""

from typing import Optional, List, Tuple, Dict, Any, Callable, Union
from pathlib import Path
from dataclasses import dataclass

# Low-level API (Rust bindings)

class Session:
    """A torrent session managing multiple torrents"""

    def __init__(
        self,
        output_folder: str,
        listen_port: Optional[int] = None,
        disable_dht: bool = False,
        disable_trackers: bool = False,
    ) -> None: ...

    def add_torrent(
        self,
        source: str,
        output_folder: Optional[str] = None,
        only_files: Optional[List[int]] = None,
        only_files_regex: Optional[str] = None,
        paused: Optional[bool] = None,
        overwrite: Optional[bool] = None,
    ) -> "TorrentHandle": ...

    def get_torrent(self, torrent_id: int) -> Optional["TorrentHandle"]: ...
    def list_torrents(self) -> List[Tuple[int, str]]: ...
    def delete_torrent(self, torrent_id: int, delete_files: bool = False) -> None: ...
    def stop(self) -> None: ...

class TorrentHandle:
    """Handle to a managed torrent"""

    @property
    def id(self) -> int: ...
    @property
    def info_hash(self) -> str: ...
    @property
    def is_paused(self) -> bool: ...
    @property
    def is_live(self) -> bool: ...

    def stats(self) -> Dict[str, Any]: ...
    def pause(self) -> None: ...
    def list_files(self) -> List[Dict[str, Any]]: ...
    def update_only_files(self, file_indices: List[int]) -> None: ...
    def wait_until_completed(self, timeout_secs: Optional[int] = None) -> bool: ...

# High-level API

@dataclass
class DownloadProgress:
    """Progress information for a download."""
    torrent_id: int
    info_hash: str
    total_bytes: int
    downloaded_bytes: int
    uploaded_bytes: int
    download_speed: float
    upload_speed: float
    progress_percent: float
    state: str
    connected_peers: int
    seen_peers: int
    elapsed_time: float

    @property
    def is_complete(self) -> bool: ...
    @property
    def eta_seconds(self) -> Optional[float]: ...
    def __str__(self) -> str: ...

class TorrentClient:
    """
    High-level torrent download client with progress tracking.

    Example:
        >>> with TorrentClient("./downloads") as client:
        ...     client.download("magnet:?xt=urn:btih:...",
        ...                     progress_callback=lambda p: print(p))
    """

    def __init__(
        self,
        output_folder: Union[str, Path] = "./downloads",
        listen_port: Optional[int] = 6881,
        disable_dht: bool = False,
        disable_trackers: bool = False,
    ) -> None: ...

    def __enter__(self) -> "TorrentClient": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def download(
        self,
        source: str,
        output_folder: Optional[Union[str, Path]] = None,
        include_files: Optional[List[int]] = None,
        include_pattern: Optional[str] = None,
        paused: bool = False,
        overwrite: bool = True,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        progress_interval: float = 1.0,
        wait_for_completion: bool = True,
        timeout: Optional[float] = None,
    ) -> TorrentHandle: ...

    def list_files(self, torrent_id: int) -> List[Dict[str, Any]]: ...
    def select_files(self, torrent_id: int, file_indices: List[int]) -> None: ...
    def pause(self, torrent_id: int) -> None: ...
    def list_torrents(self) -> List[Dict[str, Any]]: ...
    def remove(self, torrent_id: int, delete_files: bool = False) -> None: ...
    def get_stats(self, torrent_id: int) -> Dict[str, Any]: ...
    def close(self) -> None: ...

def download_torrent(
    source: str,
    output_folder: Union[str, Path] = "./downloads",
    include_files: Optional[List[int]] = None,
    include_pattern: Optional[str] = None,
    progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    **kwargs
) -> TorrentHandle:
    """
    Context manager for one-off torrent downloads.

    Example:
        >>> with download_torrent("magnet:?...", progress_callback=print):
        ...     print("Downloading...")
    """
    ...

def quick_download(
    source: str,
    output_folder: Union[str, Path] = "./downloads",
    include_pattern: Optional[str] = None,
    show_progress: bool = True,
) -> None:
    """
    Quick download with automatic progress display.

    Example:
        >>> quick_download("magnet:?xt=urn:btih:...")
        >>> quick_download("file.torrent", include_pattern=r'\\.mp4$')
    """
    ...
