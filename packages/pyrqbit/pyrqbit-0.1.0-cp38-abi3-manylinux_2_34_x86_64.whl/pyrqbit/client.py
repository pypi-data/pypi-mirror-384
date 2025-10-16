"""
High-level, developer-friendly wrapper for pyrqbit.

This module provides a Pythonic interface with context managers,
progress callbacks, and convenient methods for common operations.
"""

import time
from typing import Optional, List, Callable, Dict, Any, Union
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass

from .pyrqbit import Session as _Session, TorrentHandle as _TorrentHandle


@dataclass
class DownloadProgress:
    """Progress information for a download."""
    torrent_id: int
    info_hash: str
    total_bytes: int
    downloaded_bytes: int
    uploaded_bytes: int
    download_speed: float  # MB/s
    upload_speed: float  # MB/s
    progress_percent: float
    state: str
    connected_peers: int
    seen_peers: int
    elapsed_time: float

    @property
    def is_complete(self) -> bool:
        """Check if download is complete."""
        return self.progress_percent >= 100.0

    @property
    def eta_seconds(self) -> Optional[float]:
        """Estimate time remaining in seconds."""
        if self.download_speed <= 0 or self.is_complete:
            return None
        remaining_mb = (self.total_bytes - self.downloaded_bytes) / (1024 * 1024)
        return remaining_mb / self.download_speed

    def __str__(self) -> str:
        """Human-readable progress string."""
        mb_down = self.downloaded_bytes / (1024 * 1024)
        mb_total = self.total_bytes / (1024 * 1024)
        eta = self.eta_seconds
        eta_str = f"{int(eta)}s" if eta else "∞"

        return (
            f"Progress: {self.progress_percent:.1f}% "
            f"({mb_down:.1f}/{mb_total:.1f} MB) | "
            f"Speed: {self.download_speed:.2f} MB/s | "
            f"Peers: {self.connected_peers} | "
            f"ETA: {eta_str}"
        )


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
    ):
        """
        Initialize the torrent client.

        Args:
            output_folder: Where to save downloaded files
            listen_port: Port for incoming connections (None to disable)
            disable_dht: Disable DHT
            disable_trackers: Disable tracker communication
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self._session = _Session(
            str(self.output_folder),
            listen_port=listen_port,
            disable_dht=disable_dht,
            disable_trackers=disable_trackers,
        )
        self._active_downloads: Dict[int, _TorrentHandle] = {}

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up session."""
        self.close()

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
    ) -> _TorrentHandle:
        """
        Download a torrent with progress tracking.

        Args:
            source: Magnet link, .torrent file path, or HTTP(S) URL
            output_folder: Custom output folder (overrides default)
            include_files: List of file indices to download
            include_pattern: Regex pattern for file selection (e.g., r'\\.mp4$')
            paused: Start in paused state
            overwrite: Overwrite existing files
            progress_callback: Function called with DownloadProgress
            progress_interval: Seconds between progress callbacks
            wait_for_completion: Block until download finishes
            timeout: Maximum wait time in seconds (None = no timeout)

        Returns:
            TorrentHandle for the download

        Example:
            >>> def on_progress(p: DownloadProgress):
            ...     print(f"{p.progress_percent:.1f}% - {p.download_speed:.2f} MB/s")
            >>>
            >>> with TorrentClient() as client:
            ...     client.download(
            ...         "magnet:?xt=urn:btih:...",
            ...         include_pattern=r'\\.mp4$',
            ...         progress_callback=on_progress
            ...     )
        """
        # Resolve output folder
        out_folder = str(Path(output_folder)) if output_folder else None

        # Add the torrent
        handle = self._session.add_torrent(
            source=source,
            output_folder=out_folder,
            only_files=include_files,
            only_files_regex=include_pattern,
            paused=paused,
            overwrite=overwrite,
        )

        self._active_downloads[handle.id] = handle

        # Track progress if callback provided or waiting
        if progress_callback or wait_for_completion:
            self._track_progress(
                handle,
                progress_callback=progress_callback,
                progress_interval=progress_interval,
                wait=wait_for_completion,
                timeout=timeout,
            )

        return handle

    def _track_progress(
        self,
        handle: _TorrentHandle,
        progress_callback: Optional[Callable[[DownloadProgress], None]],
        progress_interval: float,
        wait: bool,
        timeout: Optional[float],
    ):
        """Track download progress with callbacks."""
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            stats = handle.stats()

            progress = DownloadProgress(
                torrent_id=handle.id,
                info_hash=handle.info_hash,
                total_bytes=stats['total_bytes'],
                downloaded_bytes=stats['downloaded_bytes'],
                uploaded_bytes=stats['uploaded_bytes'],
                download_speed=stats['download_speed'],
                upload_speed=stats['upload_speed'],
                progress_percent=stats['progress_percent'],
                state=stats['state'],
                connected_peers=stats['connected_peers'],
                seen_peers=stats['seen_peers'],
                elapsed_time=elapsed,
            )

            # Call progress callback
            if progress_callback:
                progress_callback(progress)

            # Check completion
            if progress.is_complete:
                break

            # Check timeout
            if timeout and elapsed >= timeout:
                raise TimeoutError(
                    f"Download did not complete within {timeout} seconds"
                )

            # Stop if not waiting
            if not wait:
                break

            time.sleep(progress_interval)

    def list_files(self, torrent_id: int) -> List[Dict[str, Any]]:
        """
        List files in a torrent.

        Args:
            torrent_id: The torrent ID

        Returns:
            List of file info dictionaries

        Example:
            >>> files = client.list_files(0)
            >>> for f in files:
            ...     print(f"{f['index']}: {f['path']} ({f['size']} bytes)")
        """
        handle = self._active_downloads.get(torrent_id)
        if not handle:
            handle = self._session.get_torrent(torrent_id)
            if not handle:
                raise ValueError(f"Torrent {torrent_id} not found")

        return handle.list_files()

    def select_files(self, torrent_id: int, file_indices: List[int]):
        """
        Update which files to download.

        Args:
            torrent_id: The torrent ID
            file_indices: List of file indices to download

        Example:
            >>> # List files first
            >>> files = client.list_files(0)
            >>> # Download only the first two files
            >>> client.select_files(0, [0, 1])
        """
        handle = self._active_downloads.get(torrent_id)
        if not handle:
            handle = self._session.get_torrent(torrent_id)
            if not handle:
                raise ValueError(f"Torrent {torrent_id} not found")

        handle.update_only_files(file_indices)

    def pause(self, torrent_id: int):
        """Pause a torrent download."""
        handle = self._active_downloads.get(torrent_id)
        if not handle:
            handle = self._session.get_torrent(torrent_id)
            if not handle:
                raise ValueError(f"Torrent {torrent_id} not found")
        handle.pause()

    def list_torrents(self) -> List[Dict[str, Any]]:
        """
        List all managed torrents.

        Returns:
            List of torrent info dictionaries

        Example:
            >>> torrents = client.list_torrents()
            >>> for t in torrents:
            ...     print(f"{t['id']}: {t['info_hash']}")
        """
        torrents = self._session.list_torrents()
        return [
            {"id": tid, "info_hash": info_hash}
            for tid, info_hash in torrents
        ]

    def remove(self, torrent_id: int, delete_files: bool = False):
        """
        Remove a torrent from the session.

        Args:
            torrent_id: The torrent ID
            delete_files: Also delete downloaded files

        Example:
            >>> # Remove but keep files
            >>> client.remove(0, delete_files=False)
            >>> # Remove and delete everything
            >>> client.remove(1, delete_files=True)
        """
        self._session.delete_torrent(torrent_id, delete_files)
        self._active_downloads.pop(torrent_id, None)

    def get_stats(self, torrent_id: int) -> Dict[str, Any]:
        """Get statistics for a torrent."""
        handle = self._active_downloads.get(torrent_id)
        if not handle:
            handle = self._session.get_torrent(torrent_id)
            if not handle:
                raise ValueError(f"Torrent {torrent_id} not found")
        return handle.stats()

    def close(self):
        """Stop the session and clean up."""
        if self._session:
            self._session.stop()
            self._session = None


@contextmanager
def download_torrent(
    source: str,
    output_folder: Union[str, Path] = "./downloads",
    include_files: Optional[List[int]] = None,
    include_pattern: Optional[str] = None,
    progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    **kwargs
):
    """
    Context manager for one-off torrent downloads.

    Args:
        source: Magnet link, .torrent file, or URL
        output_folder: Where to save files
        include_files: File indices to download
        include_pattern: Regex pattern for file selection
        progress_callback: Progress callback function
        **kwargs: Additional arguments for TorrentClient

    Example:
        >>> with download_torrent("magnet:?...", progress_callback=print):
        ...     print("Downloading...")
        ... # Download completes and cleans up automatically
    """
    client = TorrentClient(output_folder, **kwargs)
    try:
        handle = client.download(
            source,
            include_files=include_files,
            include_pattern=include_pattern,
            progress_callback=progress_callback,
            wait_for_completion=True,
        )
        yield handle
    finally:
        client.close()


# Convenience function
def quick_download(
    source: str,
    output_folder: Union[str, Path] = "./downloads",
    include_pattern: Optional[str] = None,
    show_progress: bool = True,
) -> None:
    """
    Quick download with automatic progress display.

    Args:
        source: Magnet link, .torrent file, or URL
        output_folder: Where to save files
        include_pattern: Regex pattern for file selection
        show_progress: Show progress bar

    Example:
        >>> # Download all files
        >>> quick_download("magnet:?xt=urn:btih:...")
        >>>
        >>> # Download only video files
        >>> quick_download("file.torrent", include_pattern=r'\\.mp4$')
    """
    def progress_printer(p: DownloadProgress):
        # Create progress bar
        bar_length = 50
        filled = int(bar_length * p.progress_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)

        print(f"\r[{bar}] {p}", end='', flush=True)

    callback = progress_printer if show_progress else None

    with download_torrent(
        source,
        output_folder=output_folder,
        include_pattern=include_pattern,
        progress_callback=callback,
    ):
        if show_progress:
            print()  # New line after completion
