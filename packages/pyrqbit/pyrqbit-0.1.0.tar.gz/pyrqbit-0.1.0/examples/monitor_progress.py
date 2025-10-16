#!/usr/bin/env python3
"""
Advanced progress monitoring example using pyrqbit.

This example shows how to:
- Display detailed torrent statistics
- Show real-time progress with a nice UI
- Monitor multiple torrents simultaneously
- Handle torrent lifecycle events
"""

import pyrqbit
import time
import sys
from datetime import datetime, timedelta


def format_bytes(bytes_value):
    """Format bytes into human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_speed(mbps):
    """Format speed in MB/s."""
    if mbps < 1.0:
        return f"{mbps * 1024:.2f} KB/s"
    return f"{mbps:.2f} MB/s"


def estimate_time_remaining(downloaded, total, speed_mbps):
    """Estimate time remaining based on current speed."""
    if speed_mbps <= 0 or downloaded >= total:
        return "Unknown"

    remaining_mb = (total - downloaded) / (1024 * 1024)
    seconds = remaining_mb / speed_mbps

    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def display_torrent_info(torrent):
    """Display detailed information about a torrent."""
    print(f"\n{'='*70}")
    print(f"Torrent ID: {torrent.id}")
    print(f"Info Hash: {torrent.info_hash}")
    print(f"Status: {'Paused' if torrent.is_paused else 'Active'}")
    print(f"{'='*70}\n")


def display_file_list(torrent):
    """Display the file list for a torrent."""
    files = torrent.list_files()
    print("Files:")
    for file_info in files:
        status = "✓" if file_info['included'] else "✗"
        size = format_bytes(file_info['size'])
        print(f"  [{status}] {file_info['index']:3d}: {file_info['path']} ({size})")
    print()


def monitor_single_torrent(session, torrent_source, show_files=False):
    """Monitor a single torrent with detailed statistics."""
    print(f"Adding torrent: {torrent_source[:60]}...")

    torrent = session.add_torrent(
        torrent_source,
        paused=False,
        overwrite=True,
    )

    display_torrent_info(torrent)

    if show_files:
        display_file_list(torrent)

    print("Monitoring progress (Ctrl+C to stop)...\n")

    start_time = time.time()
    last_downloaded = 0

    try:
        while True:
            stats = torrent.stats()

            # Calculate metrics
            progress = stats['progress_percent']
            downloaded = stats['downloaded_bytes']
            total = stats['total_bytes']
            upload_speed = stats['upload_speed']
            download_speed = stats['download_speed']
            connected_peers = stats['connected_peers']
            seen_peers = stats['seen_peers']
            state = stats['state']
            uploaded = stats['uploaded_bytes']

            # Calculate average speed
            elapsed = time.time() - start_time
            avg_speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0

            # Estimate time remaining
            eta = estimate_time_remaining(downloaded, total, download_speed)

            # Create progress bar
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            # Clear previous output
            print(f"\033[2J\033[H", end='')

            # Display statistics
            print(f"{'='*70}")
            print(f"Torrent: {torrent.info_hash}")
            print(f"{'='*70}")
            print(f"\nProgress: [{bar}] {progress:.1f}%")
            print(f"\nSize:      {format_bytes(downloaded)} / {format_bytes(total)}")
            print(f"Download:  {format_speed(download_speed)} (avg: {format_speed(avg_speed)})")
            print(f"Upload:    {format_speed(upload_speed)}")
            print(f"Uploaded:  {format_bytes(uploaded)}")
            print(f"\nPeers:     {connected_peers} connected, {seen_peers} known")
            print(f"State:     {state}")
            print(f"ETA:       {eta}")
            print(f"Runtime:   {timedelta(seconds=int(elapsed))}")

            # Calculate ratio
            if downloaded > 0:
                ratio = uploaded / downloaded
                print(f"Ratio:     {ratio:.3f}")

            print(f"\n{'='*70}")
            print("Press Ctrl+C to stop monitoring")

            if progress >= 100.0:
                print("\n✓ Download complete!")
                break

            last_downloaded = downloaded
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")


def monitor_multiple_torrents(session, torrent_sources):
    """Monitor multiple torrents simultaneously."""
    torrents = []

    print("Adding torrents...")
    for source in torrent_sources:
        try:
            torrent = session.add_torrent(source, paused=False, overwrite=True)
            torrents.append(torrent)
            print(f"  ✓ Added: {torrent.info_hash[:16]}...")
        except Exception as e:
            print(f"  ✗ Failed to add {source[:40]}...: {e}")

    if not torrents:
        print("No torrents to monitor")
        return

    print(f"\nMonitoring {len(torrents)} torrent(s)...\n")

    try:
        while True:
            print(f"\033[2J\033[H", end='')  # Clear screen
            print(f"{'='*70}")
            print(f"Monitoring {len(torrents)} Torrents - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*70}\n")

            all_complete = True

            for i, torrent in enumerate(torrents, 1):
                stats = torrent.stats()
                progress = stats['progress_percent']
                speed = stats['download_speed']
                peers = stats['connected_peers']
                state = stats['state']

                bar_length = 30
                filled = int(bar_length * progress / 100)
                bar = '█' * filled + '░' * (bar_length - filled)

                print(f"Torrent {i}: {torrent.info_hash[:16]}...")
                print(f"  [{bar}] {progress:.1f}% | {format_speed(speed)} | {peers} peers | {state}")

                if progress < 100.0:
                    all_complete = False

            print(f"\n{'='*70}")
            print("Press Ctrl+C to stop monitoring")

            if all_complete:
                print("\n✓ All downloads complete!")
                break

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")


def main():
    if len(sys.argv) < 2:
        print("Usage: python monitor_progress.py <torrent1> [torrent2] [torrent3] ...")
        print("\nOptions:")
        print("  Add --show-files to display file list")
        print("\nExamples:")
        print("  python monitor_progress.py 'magnet:?...'")
        print("  python monitor_progress.py file.torrent --show-files")
        print("  python monitor_progress.py torrent1.torrent torrent2.torrent")
        sys.exit(1)

    show_files = '--show-files' in sys.argv
    torrent_sources = [arg for arg in sys.argv[1:] if not arg.startswith('--')]

    download_folder = "./downloads"

    print(f"Creating session with output folder: {download_folder}")
    session = pyrqbit.Session(
        output_folder=download_folder,
        listen_port=6881,
    )

    try:
        if len(torrent_sources) == 1:
            monitor_single_torrent(session, torrent_sources[0], show_files)
        else:
            monitor_multiple_torrents(session, torrent_sources)

    finally:
        print("\nStopping session...")
        session.stop()
        print("Done!")


if __name__ == "__main__":
    main()
