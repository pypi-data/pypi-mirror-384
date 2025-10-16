# pyrqbit

Python bindings for [librqbit](https://github.com/ikatson/rqbit) - a feature-rich BitTorrent client library written in Rust.

## Installation

### Install from PyPI (recommended)

We provide pre-built wheels for the latest versions of Python:

```bash
pip install pyrqbit
```

### Build from Source

Prerequisites:

- Python 3.10 or higher
- Rust toolchain (for building from source)
- Git (for cloning with submodules)

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/fakerybakery/pyrqbit.git
cd pyrqbit

# Install maturin (Rust-Python build tool)
pip install maturin

# Build and install in development mode
maturin develop --release

# Or build a wheel for distribution
maturin build --release
pip install target/wheels/pyrqbit-*.whl
```

## Quick Start

pyrqbit provides two APIs: a **high-level API** (recommended) and a **low-level API** (for advanced use).

### High-Level API (Recommended)

Pythonic interface with context managers and progress callbacks:

```python
from pyrqbit import TorrentClient

# Context manager automatically handles cleanup
with TorrentClient("./downloads") as client:
    # Download with progress callback
    client.download(
        "magnet:?xt=urn:btih:...",
        progress_callback=lambda p: print(f"{p.progress_percent:.1f}% - {p.download_speed:.2f} MB/s"),
    )
```

Even simpler - one-liner download:

```python
from pyrqbit import quick_download

# Automatically shows progress and cleans up
quick_download("magnet:?xt=urn:btih:...")
```

Download only specific files:

```python
from pyrqbit import TorrentClient

with TorrentClient("./downloads") as client:
    # Download only MP4 files
    client.download(
        "magnet:?xt=urn:btih:...",
        include_pattern=r'\.mp4$',
        progress_callback=lambda p: print(p),
    )
```

### Low-Level API

Direct bindings to librqbit for fine-grained control:

```python
import pyrqbit
import time

# Create a session
session = pyrqbit.Session(
    output_folder="/path/to/downloads",
    listen_port=6881,
)

# Add a torrent
torrent = session.add_torrent(
    "magnet:?xt=urn:btih:...",
    paused=False,
    overwrite=True
)

# Monitor progress manually
while True:
    stats = torrent.stats()
    print(f"Progress: {stats['progress_percent']:.1f}%")
    print(f"Speed: {stats['download_speed']:.2f} MB/s")

    if stats['progress_percent'] >= 100.0:
        break

    time.sleep(1)

session.stop()
```

### Selective File Download

```python
import pyrqbit

session = pyrqbit.Session("/path/to/downloads")

# Download only video files using regex
torrent = session.add_torrent(
    "magnet:?xt=urn:btih:...",
    only_files_regex=r"\.(mp4|mkv|avi)$"
)

# Or download specific files by index
torrent = session.add_torrent(
    "/path/to/file.torrent",
    only_files=[0, 2, 5]  # Download files 0, 2, and 5
)

# List all files in the torrent
for file_info in torrent.list_files():
    print(f"{file_info['index']}: {file_info['path']} ({file_info['size']} bytes)")
    print(f"  Included: {file_info['included']}")

# Update file selection after adding
torrent.update_only_files([1, 3, 4])
```

### Advanced Usage

```python
import pyrqbit

# Create session with custom options
session = pyrqbit.Session(
    output_folder="/downloads",
    listen_port=6881,
    disable_dht=False,
    disable_trackers=False
)

# Add torrent from local file
torrent = session.add_torrent(
    "/path/to/file.torrent",
    output_folder="/custom/output",  # Override default
    overwrite=True
)

# Pause and resume
torrent.pause()
print(f"Paused: {torrent.is_paused}")

# Wait for completion with timeout
if torrent.wait_until_completed(timeout_secs=3600):
    print("Download finished!")
else:
    print("Timeout reached")

# Get torrent info
print(f"Torrent ID: {torrent.id}")
print(f"Info Hash: {torrent.info_hash}")

# List all torrents
for torrent_id, info_hash in session.list_torrents():
    print(f"{torrent_id}: {info_hash}")

# Delete torrent (keep files)
session.delete_torrent(torrent.id, delete_files=False)

# Stop session
session.stop()
```

## API Reference

### Session

```python
class Session:
    def __init__(
        self,
        output_folder: str,
        listen_port: Optional[int] = None,
        disable_dht: bool = False,
        disable_trackers: bool = False,
    )
```

Create a new torrent session.

**Methods:**

- `add_torrent(source, output_folder=None, only_files=None, only_files_regex=None, paused=None, overwrite=None) -> TorrentHandle`
- `get_torrent(torrent_id: int) -> Optional[TorrentHandle]`
- `list_torrents() -> List[Tuple[int, str]]`
- `delete_torrent(torrent_id: int, delete_files: bool = False)`
- `stop()`

### TorrentHandle

**Properties:**

- `id: int` - Torrent ID
- `info_hash: str` - Info hash as hex string
- `is_paused: bool` - Whether torrent is paused
- `is_live: bool` - Whether torrent is active

**Methods:**

- `stats() -> Dict` - Get torrent statistics
- `pause()` - Pause the torrent
- `list_files() -> List[Dict]` - List files in torrent
- `update_only_files(file_indices: List[int])` - Update file selection
- `wait_until_completed(timeout_secs: Optional[int] = None) -> bool` - Wait for completion

## Supported Torrent Sources

- **Magnet links**: `magnet:?xt=urn:btih:...`
- **HTTP(S) URLs**: Direct links to .torrent files
- **Info hashes**: 40-character hex strings
- **Local files**: Path to .torrent files

## Examples

See the `examples/` directory for more detailed examples:

- `examples/basic_download.py` - Simple torrent download
- `examples/selective_download.py` - Download specific files
- `examples/monitor_progress.py` - Real-time progress monitoring

## Building and Development

### Setup Development Environment

```bash
# Clone with submodules
git clone --recursive https://github.com/fakerybakery/pyrqbit.git
cd pyrqbit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install maturin pytest

# Build in development mode
maturin develop
```

### Running Tests

```bash
pytest tests/
```

### Building Release

```bash
# Build release wheel
maturin build --release

# The wheel will be in target/wheels/
ls target/wheels/
```

## License

Like rqbit, pyrqbit is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## Credits

This project wraps [rqbit](https://github.com/ikatson/rqbit) by Igor Katson.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request