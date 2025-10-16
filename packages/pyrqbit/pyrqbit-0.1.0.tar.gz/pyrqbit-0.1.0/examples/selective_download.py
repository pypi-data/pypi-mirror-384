#!/usr/bin/env python3
"""
Selective file download example using pyrqbit.

This example shows how to:
- List files in a torrent
- Download only specific files using indices
- Download files matching a regex pattern
- Update file selection after adding
"""

import pyrqbit
import sys
import time


def download_by_indices(session, torrent_source):
    """Download specific files by their indices."""
    print("\n=== Download by Indices ===")

    # First, add in list-only mode to see files (not implemented in basic version)
    # For now, we'll add and then list
    torrent = session.add_torrent(
        torrent_source,
        paused=True,  # Start paused
    )

    print(f"\nFiles in torrent {torrent.info_hash}:")
    files = torrent.list_files()

    for file_info in files:
        idx = file_info['index']
        path = file_info['path']
        size = file_info['size'] / (1024 * 1024)  # MB
        included = file_info['included']
        status = "✓" if included else "✗"
        print(f"  [{status}] {idx}: {path} ({size:.2f} MB)")

    # Ask user which files to download
    print("\nEnter file indices to download (comma-separated, e.g., 0,2,5):")
    print("Or press Enter to download all files:")
    user_input = input("> ").strip()

    if user_input:
        try:
            indices = [int(x.strip()) for x in user_input.split(',')]
            print(f"\nUpdating to download only files: {indices}")
            torrent.update_only_files(indices)
        except ValueError:
            print("Invalid input, downloading all files")

    # Resume download
    print("Starting download...")
    # Note: In the current implementation, we'd need to add unpause functionality
    # For now, the torrent is paused and user can manually manage it

    return torrent


def download_by_regex(session, torrent_source, pattern):
    """Download files matching a regex pattern."""
    print(f"\n=== Download by Regex: {pattern} ===")

    torrent = session.add_torrent(
        torrent_source,
        only_files_regex=pattern,
        paused=False,
    )

    print(f"\nFiles that will be downloaded:")
    files = torrent.list_files()

    for file_info in files:
        if file_info['included']:
            idx = file_info['index']
            path = file_info['path']
            size = file_info['size'] / (1024 * 1024)  # MB
            print(f"  ✓ {idx}: {path} ({size:.2f} MB)")

    return torrent


def main():
    if len(sys.argv) < 2:
        print("Usage: python selective_download.py <magnet_link_or_torrent_file> [regex_pattern]")
        print("\nExamples:")
        print("  python selective_download.py file.torrent")
        print("  python selective_download.py 'magnet:?...' '\\.mp4$'")
        print("  python selective_download.py file.torrent '\\.mkv$|\\.mp4$'")
        sys.exit(1)

    torrent_source = sys.argv[1]
    regex_pattern = sys.argv[2] if len(sys.argv) > 2 else None

    download_folder = "./downloads"

    print(f"Creating session with output folder: {download_folder}")
    session = pyrqbit.Session(
        output_folder=download_folder,
        listen_port=6881,
    )

    try:
        if regex_pattern:
            # Download using regex pattern
            torrent = download_by_regex(session, torrent_source, regex_pattern)
        else:
            # Download by selecting indices interactively
            torrent = download_by_indices(session, torrent_source)

        print(f"\nTorrent ID: {torrent.id}")
        print(f"Info Hash: {torrent.info_hash}")
        print(f"Paused: {torrent.is_paused}")

        # Monitor progress
        if not torrent.is_paused:
            print("\nMonitoring progress (Ctrl+C to stop)...")
            while True:
                stats = torrent.stats()
                progress = stats['progress_percent']
                speed = stats['download_speed']
                peers = stats['connected_peers']

                print(f"\rProgress: {progress:.1f}% | "
                      f"Speed: {speed:.2f} MB/s | "
                      f"Peers: {peers}", end='', flush=True)

                if progress >= 100.0:
                    print("\n\nDownload complete!")
                    break

                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        session.stop()
        print("Session stopped")


if __name__ == "__main__":
    main()
