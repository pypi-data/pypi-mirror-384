#!/usr/bin/env python3
"""
Examples demonstrating the high-level pyrqbit API.

This shows the developer-friendly interface with context managers,
progress callbacks, and convenient methods.
"""

import sys
from pyrqbit import TorrentClient, DownloadProgress, download_torrent, quick_download


def example_1_context_manager():
    """Example 1: Using TorrentClient with context manager."""
    print("="*70)
    print("Example 1: Context Manager with Progress Callback")
    print("="*70)

    def on_progress(progress: DownloadProgress):
        """Custom progress callback."""
        print(f"\r{progress}", end='', flush=True)

    # Automatic cleanup when exiting context
    with TorrentClient("./downloads") as client:
        client.download(
            "magnet:?xt=urn:btih:...",  # Replace with actual magnet link
            progress_callback=on_progress,
            wait_for_completion=True,
        )
    print("\n\nDownload complete!")


def example_2_selective_download():
    """Example 2: Download only specific files."""
    print("="*70)
    print("Example 2: Selective File Download")
    print("="*70)

    with TorrentClient("./downloads") as client:
        # Add torrent in paused state to inspect files
        handle = client.download(
            "magnet:?xt=urn:btih:...",
            paused=True,
            wait_for_completion=False,
        )

        # List all files
        files = client.list_files(handle.id)
        print("\nFiles in torrent:")
        for f in files:
            print(f"  [{f['index']}] {f['path']} ({f['size']} bytes)")

        # Select specific files
        print("\nDownloading files 0 and 2 only...")
        client.select_files(handle.id, [0, 2])

        # Now unpause and download
        # (In real code, you'd unpause via handle or session)


def example_3_pattern_matching():
    """Example 3: Download files matching a pattern."""
    print("="*70)
    print("Example 3: Pattern Matching")
    print("="*70)

    with TorrentClient("./downloads") as client:
        # Download only MP4 files
        client.download(
            "magnet:?xt=urn:btih:...",
            include_pattern=r'\.mp4$',
            progress_callback=lambda p: print(f"{p.progress_percent:.1f}%"),
        )


def example_4_one_off_download():
    """Example 4: One-off download with context manager."""
    print("="*70)
    print("Example 4: One-Off Download")
    print("="*70)

    # Automatically creates client and cleans up
    with download_torrent(
        "magnet:?xt=urn:btih:...",
        output_folder="./my_downloads",
        include_pattern=r'\.(mkv|mp4)$',
    ) as handle:
        print(f"Downloading torrent: {handle.info_hash}")
        # Download happens automatically


def example_5_quick_download():
    """Example 5: Quick download with auto progress."""
    print("="*70)
    print("Example 5: Quick Download")
    print("="*70)

    # Simplest possible API - just download and show progress
    quick_download(
        "magnet:?xt=urn:btih:...",
        output_folder="./downloads",
        show_progress=True,
    )


def example_6_custom_progress():
    """Example 6: Custom progress handling."""
    print("="*70)
    print("Example 6: Custom Progress Display")
    print("="*70)

    def fancy_progress(p: DownloadProgress):
        """Fancy progress display with ETA."""
        # Clear line
        print("\033[2K", end='')

        # Progress bar
        bar_length = 30
        filled = int(bar_length * p.progress_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)

        # Format sizes
        mb_down = p.downloaded_bytes / (1024 * 1024)
        mb_total = p.total_bytes / (1024 * 1024)

        # ETA
        eta = p.eta_seconds
        if eta:
            eta_str = f"{int(eta//60)}m {int(eta%60)}s"
        else:
            eta_str = "calculating..."

        print(
            f"\r[{bar}] {p.progress_percent:5.1f}% | "
            f"{mb_down:7.1f}/{mb_total:7.1f} MB | "
            f"{p.download_speed:5.2f} MB/s | "
            f"↑{p.upload_speed:4.2f} MB/s | "
            f"Peers: {p.connected_peers:3d} | "
            f"ETA: {eta_str}",
            end='',
            flush=True
        )

    with TorrentClient() as client:
        client.download(
            "magnet:?xt=urn:btih:...",
            progress_callback=fancy_progress,
        )
    print()


def example_7_multiple_downloads():
    """Example 7: Managing multiple downloads."""
    print("="*70)
    print("Example 7: Multiple Downloads")
    print("="*70)

    with TorrentClient("./downloads") as client:
        # Start multiple downloads without waiting
        handles = []
        for magnet in ["magnet:?...", "magnet:?...", "magnet:?..."]:
            handle = client.download(
                magnet,
                wait_for_completion=False,
            )
            handles.append(handle)

        print(f"Started {len(handles)} downloads")

        # Monitor all downloads
        while True:
            all_complete = True
            for h in handles:
                stats = client.get_stats(h.id)
                progress = stats['progress_percent']
                print(f"  {h.info_hash[:8]}... {progress:.1f}%")

                if progress < 100.0:
                    all_complete = False

            if all_complete:
                break

            print("\n" + "="*50)
            import time
            time.sleep(2)


def example_8_with_timeout():
    """Example 8: Download with timeout."""
    print("="*70)
    print("Example 8: Download with Timeout")
    print("="*70)

    with TorrentClient() as client:
        try:
            client.download(
                "magnet:?xt=urn:btih:...",
                timeout=300,  # 5 minutes max
                progress_callback=lambda p: print(f"{p.progress_percent:.1f}%"),
            )
            print("Download completed within timeout!")
        except TimeoutError:
            print("Download timed out after 5 minutes")


def main():
    """Run examples based on command line argument."""
    if len(sys.argv) < 2:
        print("Usage: python high_level_api.py <example_number>")
        print("\nAvailable examples:")
        print("  1: Context Manager with Progress Callback")
        print("  2: Selective File Download")
        print("  3: Pattern Matching")
        print("  4: One-Off Download")
        print("  5: Quick Download")
        print("  6: Custom Progress Display")
        print("  7: Multiple Downloads")
        print("  8: Download with Timeout")
        print("\nOr run all: python high_level_api.py all")
        sys.exit(1)

    example = sys.argv[1]

    examples = {
        '1': example_1_context_manager,
        '2': example_2_selective_download,
        '3': example_3_pattern_matching,
        '4': example_4_one_off_download,
        '5': example_5_quick_download,
        '6': example_6_custom_progress,
        '7': example_7_multiple_downloads,
        '8': example_8_with_timeout,
    }

    if example == 'all':
        for func in examples.values():
            func()
            print("\n")
    elif example in examples:
        examples[example]()
    else:
        print(f"Unknown example: {example}")
        sys.exit(1)


if __name__ == "__main__":
    # For quick testing without args
    print("High-Level pyrqbit API Examples")
    print("\nSimple usage:")
    print("-" * 70)
    print("""
from pyrqbit import quick_download

# Download a torrent with auto progress display
quick_download("magnet:?xt=urn:btih:YOUR_HASH_HERE")
    """)
    print("\nAdvanced usage:")
    print("-" * 70)
    print("""
from pyrqbit import TorrentClient

with TorrentClient("./downloads") as client:
    client.download(
        "magnet:?xt=urn:btih:YOUR_HASH_HERE",
        include_pattern=r'\\.mp4$',  # Only MP4 files
        progress_callback=lambda p: print(p),
    )
    """)
    print("\n" + "="*70)
    print("Run with an example number to see specific examples")
    print("Example: python high_level_api.py 1")
