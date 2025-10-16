#!/usr/bin/env python3
"""
Basic torrent download example using pyrqbit.

This example shows how to:
- Create a session
- Add a torrent
- Monitor download progress
- Wait for completion
"""

import pyrqbit
import time
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python basic_download.py <magnet_link_or_torrent_file>")
        sys.exit(1)

    torrent_source = sys.argv[1]
    download_folder = "./downloads"

    print(f"Creating session with output folder: {download_folder}")
    session = pyrqbit.Session(
        output_folder=download_folder,
        listen_port=6881,
    )

    print(f"Adding torrent: {torrent_source[:60]}...")
    torrent = session.add_torrent(
        torrent_source,
        paused=False,
        overwrite=True,
    )

    print(f"Torrent added! ID: {torrent.id}, Info Hash: {torrent.info_hash}")
    print(f"Starting download...\n")

    # Monitor progress
    try:
        while True:
            stats = torrent.stats()

            progress = stats['progress_percent']
            downloaded = stats['downloaded_bytes'] / (1024 * 1024)  # MB
            total = stats['total_bytes'] / (1024 * 1024)  # MB
            speed = stats['download_speed']
            peers = stats['connected_peers']
            state = stats['state']

            # Create progress bar
            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = '=' * filled + '-' * (bar_length - filled)

            print(f"\r[{bar}] {progress:.1f}% | "
                  f"{downloaded:.1f}/{total:.1f} MB | "
                  f"{speed:.2f} MB/s | "
                  f"Peers: {peers} | "
                  f"State: {state}", end='', flush=True)

            if progress >= 100.0:
                print("\n\nDownload complete!")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        torrent.pause()
        print("Torrent paused")

    finally:
        session.stop()
        print("Session stopped")


if __name__ == "__main__":
    main()
