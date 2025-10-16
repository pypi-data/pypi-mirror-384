use pyo3::prelude::*;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;
use tokio::runtime::Runtime;

use librqbit::{Session as RqbitSession, AddTorrent, AddTorrentOptions as RqbitAddTorrentOptions, AddTorrentResponse, ManagedTorrent, ListenerOptions, ListenerMode};
use std::net::SocketAddr;

type ManagedTorrentHandle = std::sync::Arc<ManagedTorrent>;

/// Python wrapper for librqbit Session
#[pyclass]
struct Session {
    session: Arc<RqbitSession>,
    runtime: Arc<Runtime>,
}

#[pymethods]
impl Session {
    /// Create a new torrent session
    ///
    /// Args:
    ///     output_folder: Default folder where torrents will be downloaded
    ///     listen_port: Optional port to listen for incoming connections (default: None)
    ///     disable_dht: Disable DHT (default: False)
    ///     disable_trackers: Disable trackers (default: False)
    ///
    /// Returns:
    ///     A new Session instance
    #[new]
    #[pyo3(signature = (output_folder, listen_port=None, disable_dht=false, disable_trackers=false))]
    fn new(
        output_folder: String,
        listen_port: Option<u16>,
        disable_dht: bool,
        disable_trackers: bool,
    ) -> PyResult<Self> {
        let runtime = Arc::new(
            tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?
        );

        let session = runtime.block_on(async {
            let mut opts = librqbit::SessionOptions {
                disable_dht,
                disable_trackers,
                ..Default::default()
            };

            if let Some(port) = listen_port {
                opts.listen = Some(ListenerOptions {
                    mode: ListenerMode::TcpAndUtp,
                    listen_addr: SocketAddr::from(([0, 0, 0, 0], port)),
                    enable_upnp_port_forwarding: true,
                    utp_opts: None,
                });
            }

            RqbitSession::new_with_opts(PathBuf::from(output_folder), opts).await
        }).map_err(|e| PyRuntimeError::new_err(format!("Failed to create session: {}", e)))?;

        Ok(Self {
            session,
            runtime,
        })
    }

    /// Add a torrent by URL, magnet link, or file path
    ///
    /// Args:
    ///     source: Magnet link, HTTP(S) URL, info hash, or local file path
    ///     output_folder: Optional custom output folder for this torrent
    ///     only_files: Optional list of file indices to download (0-indexed)
    ///     only_files_regex: Optional regex pattern to filter files by name
    ///     paused: Start torrent in paused state (default: False)
    ///     overwrite: Allow overwriting existing files (default: False)
    ///
    /// Returns:
    ///     TorrentHandle object for managing the torrent
    #[pyo3(signature = (source, output_folder=None, only_files=None, only_files_regex=None, paused=None, overwrite=None))]
    fn add_torrent(
        &self,
        source: String,
        output_folder: Option<String>,
        only_files: Option<Vec<usize>>,
        only_files_regex: Option<String>,
        paused: Option<bool>,
        overwrite: Option<bool>,
    ) -> PyResult<TorrentHandle> {
        // Validate mutually exclusive options
        if only_files.is_some() && only_files_regex.is_some() {
            return Err(PyValueError::new_err(
                "only_files and only_files_regex are mutually exclusive"
            ));
        }

        let add_torrent = if source.starts_with("http://")
            || source.starts_with("https://")
            || source.starts_with("magnet:")
            || (source.len() == 40 && !PathBuf::from(&source).exists()) {
            AddTorrent::from_url(source)
        } else {
            AddTorrent::from_local_filename(&source)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to read torrent file: {}", e)))?
        };

        let opts = RqbitAddTorrentOptions {
            paused: paused.unwrap_or(false),
            only_files,
            only_files_regex,
            overwrite: overwrite.unwrap_or(false),
            output_folder,
            ..Default::default()
        };

        let (id, handle) = self.runtime.block_on(async {
            let response = self.session.add_torrent(add_torrent, Some(opts)).await?;
            match response {
                AddTorrentResponse::Added(id, handle) | AddTorrentResponse::AlreadyManaged(id, handle) => {
                    Ok((id, handle))
                }
                AddTorrentResponse::ListOnly(_) => {
                    Err(anyhow::anyhow!("Unexpected list-only response"))
                }
            }
        }).map_err(|e: anyhow::Error| PyRuntimeError::new_err(format!("Failed to add torrent: {}", e)))?;

        Ok(TorrentHandle {
            handle,
            session: self.session.clone(),
            runtime: self.runtime.clone(),
            id,
        })
    }

    /// Get a torrent handle by ID
    ///
    /// Args:
    ///     torrent_id: The torrent ID
    ///
    /// Returns:
    ///     TorrentHandle if found, None otherwise
    fn get_torrent(&self, torrent_id: usize) -> Option<TorrentHandle> {
        self.session.get(librqbit::api::TorrentIdOrHash::Id(torrent_id)).map(|handle| {
            TorrentHandle {
                handle,
                session: self.session.clone(),
                runtime: self.runtime.clone(),
                id: torrent_id,
            }
        })
    }

    /// List all managed torrents
    ///
    /// Returns:
    ///     List of (torrent_id, info_hash) tuples
    fn list_torrents(&self) -> Vec<(usize, String)> {
        self.session.with_torrents(|torrents| {
            torrents
                .map(|(id, handle)| (id, handle.info_hash().as_string()))
                .collect()
        })
    }

    /// Delete a torrent
    ///
    /// Args:
    ///     torrent_id: The torrent ID to delete
    ///     delete_files: If True, also delete downloaded files
    fn delete_torrent(&self, torrent_id: usize, delete_files: bool) -> PyResult<()> {
        self.runtime.block_on(async {
            self.session.delete(librqbit::api::TorrentIdOrHash::Id(torrent_id), delete_files).await
        }).map_err(|e| PyRuntimeError::new_err(format!("Failed to delete torrent: {}", e)))
    }

    /// Stop the session and all managed torrents
    fn stop(&self) -> PyResult<()> {
        self.runtime.block_on(async {
            self.session.stop().await;
            Ok(())
        })
    }
}

/// Python wrapper for a managed torrent handle
#[pyclass]
struct TorrentHandle {
    handle: ManagedTorrentHandle,
    session: Arc<RqbitSession>,
    runtime: Arc<Runtime>,
    id: usize,
}

#[pymethods]
impl TorrentHandle {
    /// Get the torrent ID
    #[getter]
    fn id(&self) -> usize {
        self.id
    }

    /// Get the info hash as hex string
    #[getter]
    fn info_hash(&self) -> String {
        self.handle.info_hash().as_string()
    }

    /// Get torrent statistics
    ///
    /// Returns:
    ///     Dictionary with keys:
    ///     - total_bytes: Total size in bytes
    ///     - downloaded_bytes: Bytes downloaded so far
    ///     - uploaded_bytes: Bytes uploaded
    ///     - download_speed: Current download speed (MB/s)
    ///     - upload_speed: Current upload speed (MB/s)
    ///     - progress_percent: Download progress (0-100)
    ///     - state: Current state (Initializing, Live, Paused, Error)
    ///     - connected_peers: Number of connected peers
    ///     - seen_peers: Number of known peers
    fn stats(&self) -> PyResult<PyObject> {
        let stats = self.handle.stats();

        Python::with_gil(|py| {
            let dict = pyo3::types::PyDict::new_bound(py);
            dict.set_item("total_bytes", stats.total_bytes)?;
            dict.set_item("downloaded_bytes", stats.progress_bytes)?;
            dict.set_item("uploaded_bytes", stats.uploaded_bytes)?;

            // Extract speeds from live stats
            let (download_speed, upload_speed, connected_peers, seen_peers) = if let Some(ref live) = stats.live {
                (
                    live.download_speed.mbps,
                    live.upload_speed.mbps,
                    live.snapshot.peer_stats.live,
                    live.snapshot.peer_stats.seen,
                )
            } else {
                (0.0, 0.0, 0, 0)
            };

            dict.set_item("download_speed", download_speed)?;
            dict.set_item("upload_speed", upload_speed)?;

            let progress = if stats.total_bytes > 0 {
                (stats.progress_bytes as f64 / stats.total_bytes as f64) * 100.0
            } else {
                0.0
            };
            dict.set_item("progress_percent", progress)?;

            let state_str = format!("{:?}", stats.state);
            dict.set_item("state", state_str)?;

            dict.set_item("connected_peers", connected_peers)?;
            dict.set_item("seen_peers", seen_peers)?;

            Ok(dict.into())
        })
    }

    /// Pause the torrent
    fn pause(&self) -> PyResult<()> {
        self.runtime.block_on(async {
            self.session.pause(&self.handle).await
        }).map_err(|e| PyRuntimeError::new_err(format!("Failed to pause: {}", e)))
    }

    /// Check if torrent is paused
    #[getter]
    fn is_paused(&self) -> bool {
        self.handle.is_paused()
    }

    /// Check if torrent is live (actively downloading/uploading)
    #[getter]
    fn is_live(&self) -> bool {
        self.handle.live().is_some()
    }

    /// Get list of files in the torrent
    ///
    /// Returns:
    ///     List of dictionaries with keys:
    ///     - index: File index
    ///     - path: Relative file path
    ///     - size: File size in bytes
    ///     - included: Whether this file is being downloaded
    fn list_files(&self) -> PyResult<Vec<PyObject>> {
        Python::with_gil(|py| {
            self.handle.with_metadata(|metadata| {
                let info = &metadata.info;
                let only_files = self.handle.only_files();

                let files: Vec<PyObject> = info.iter_file_details()
                    .enumerate()
                    .map(|(idx, file_detail)| {
                        let dict = pyo3::types::PyDict::new_bound(py);
                        dict.set_item("index", idx).unwrap();
                        dict.set_item("path", file_detail.filename.to_string()).unwrap();
                        dict.set_item("size", file_detail.len).unwrap();
                        dict.set_item("included", only_files.as_ref()
                            .map(|of| of.contains(&idx))
                            .unwrap_or(true)
                        ).unwrap();
                        dict.into()
                    })
                    .collect();

                Ok(files)
            }).map_err(|e| PyRuntimeError::new_err(format!("Failed to get file list: {}", e)))?
        })
    }

    /// Update which files to download
    ///
    /// Args:
    ///     file_indices: List of file indices to download
    fn update_only_files(&self, file_indices: Vec<usize>) -> PyResult<()> {
        let file_set: std::collections::HashSet<usize> = file_indices.into_iter().collect();
        self.runtime.block_on(async {
            self.session.update_only_files(&self.handle, &file_set).await
        }).map_err(|e| PyRuntimeError::new_err(format!("Failed to update files: {}", e)))
    }

    /// Wait for the torrent to finish downloading
    ///
    /// Args:
    ///     timeout_secs: Optional timeout in seconds (default: wait forever)
    ///
    /// Returns:
    ///     True if finished, False if timed out
    #[pyo3(signature = (timeout_secs=None))]
    fn wait_until_completed(&self, timeout_secs: Option<u64>) -> PyResult<bool> {
        self.runtime.block_on(async {
            let timeout = timeout_secs.map(Duration::from_secs);

            match timeout {
                Some(t) => {
                    match tokio::time::timeout(t, self.handle.wait_until_completed()).await {
                        Ok(Ok(_)) => Ok(true),
                        Ok(Err(e)) => Err(PyRuntimeError::new_err(format!("Error waiting: {}", e))),
                        Err(_) => Ok(false), // Timeout
                    }
                }
                None => {
                    self.handle.wait_until_completed().await
                        .map_err(|e| PyRuntimeError::new_err(format!("Error waiting: {}", e)))?;
                    Ok(true)
                }
            }
        })
    }
}

/// Python module definition
#[pymodule]
fn pyrqbit(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Session>()?;
    m.add_class::<TorrentHandle>()?;
    Ok(())
}
