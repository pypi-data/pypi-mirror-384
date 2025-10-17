#![allow(non_local_definitions)]

use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use pyo3::types::PyDict;
use aria2_core::{Aria2Client, Aria2Error, SecureDaemonManager, models::{Download, GlobalStat, Version, Peer, Server, Uri, File, SessionInfo}};
use serde_json;

struct PyDownload(Download);
struct PyGlobalStat(GlobalStat);
struct PyVersion(Version);
struct PyPeer(Peer);
struct PyServer(Server);
struct PyUri(Uri);
struct PyFile(File);
struct PySessionInfo(SessionInfo);

impl IntoPy<PyObject> for PyDownload {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("gid", self.0.gid).unwrap();
        dict.set_item("status", self.0.status).unwrap();
        dict.set_item("total_length", self.0.totalLength).unwrap();
        dict.set_item("completed_length", self.0.completedLength).unwrap();
        dict.set_item("download_speed", self.0.downloadSpeed).unwrap();
        dict.set_item("upload_speed", self.0.uploadSpeed).unwrap();
        dict.set_item("dir", self.0.dir).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PyGlobalStat {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        match self.0.download_speed {
            Some(speed) => dict.set_item("download_speed", speed).unwrap(),
            None => dict.set_item("download_speed", "0").unwrap(),
        }
        dict.set_item("upload_speed", self.0.upload_speed).unwrap();
        dict.set_item("num_active", self.0.num_active).unwrap();
        dict.set_item("num_waiting", self.0.num_waiting).unwrap();
        dict.set_item("num_stopped", self.0.num_stopped).unwrap();
        dict.set_item("num_stopped_total", self.0.num_stopped_total).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PyVersion {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("version", self.0.version).unwrap();
        dict.set_item("enabled_features", self.0.enabled_features).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PyPeer {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("peer_id", self.0.peer_id).unwrap();
        dict.set_item("ip", self.0.ip).unwrap();
        dict.set_item("port", self.0.port).unwrap();
        dict.set_item("bitfield", self.0.bitfield).unwrap();
        dict.set_item("am_choking", self.0.am_choking).unwrap();
        dict.set_item("peer_choking", self.0.peer_choking).unwrap();
        dict.set_item("download_speed", self.0.download_speed).unwrap();
        dict.set_item("upload_speed", self.0.upload_speed).unwrap();
        dict.set_item("seeder", self.0.seeder).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PyServer {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("index", self.0.index).unwrap();
        let servers: Vec<PyObject> = self.0.servers.into_iter()
            .map(|s| {
                let server_dict = PyDict::new_bound(py);
                server_dict.set_item("uri", s.uri).unwrap();
                server_dict.set_item("current_uri", s.current_uri).unwrap();
                server_dict.set_item("download_speed", s.download_speed).unwrap();
                server_dict.into()
            })
            .collect();
        dict.set_item("servers", servers).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PyUri {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("uri", self.0.uri).unwrap();
        dict.set_item("status", self.0.status).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PyFile {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("index", self.0.index).unwrap();
        dict.set_item("path", self.0.path).unwrap();
        dict.set_item("length", self.0.length).unwrap();
        dict.set_item("completed_length", self.0.completedLength).unwrap();
        dict.set_item("selected", self.0.selected).unwrap();
        let uris: Vec<PyObject> = self.0.uris.into_iter()
            .map(|u| PyUri(u).into_py(py))
            .collect();
        dict.set_item("uris", uris).unwrap();
        dict.into()
    }
}

impl IntoPy<PyObject> for PySessionInfo {
    fn into_py(self, py: Python) -> PyObject {
        let dict = PyDict::new_bound(py);
        dict.set_item("session_id", self.0.session_id).unwrap();
        dict.into()
    }
}

#[pyclass]
struct PyAria2Client {
    client: Aria2Client,
}

#[pymethods]
impl PyAria2Client {
    #[new]
    #[pyo3(signature = (endpoint=None, secret=None, timeout_seconds=None))]
    fn new(endpoint: Option<String>, secret: Option<String>, timeout_seconds: Option<f64>) -> Self {
        let mut client = Aria2Client::new(
            endpoint.unwrap_or_else(|| "http://localhost:6800/jsonrpc".to_string()),
            secret,
        );

        if let Some(timeout) = timeout_seconds {
            client = client.with_timeout(std::time::Duration::from_secs_f64(timeout));
        }

        Self {
            client,
        }
    }

    #[pyo3(signature = (uris, options=None))]
    fn add_uri(&self, uris: Vec<String>, options: Option<&Bound<'_, PyAny>>) -> PyResult<String> {
        let options = options
            .and_then(|o| o.extract::<String>().ok())
            .and_then(|s| serde_json::from_str(&s).ok());
        self.client.add_uri(uris, options).map_err(to_py_err)
    }

    fn tell_active(&self) -> PyResult<Vec<PyDownload>> {
        let downloads = self.client.tell_active().map_err(to_py_err)?;
        Ok(downloads.into_iter().map(PyDownload).collect())
    }

    fn change_option(&self, gid: String, options: String) -> PyResult<String> {
        let options: serde_json::Value = serde_json::from_str(&options).map_err(|e| PyException::new_err(e.to_string()))?;
        self.client.change_option(&gid, options).map_err(to_py_err)
    }

    fn tell_status(&self, gid: String) -> PyResult<PyDownload> {
        let download = self.client.tell_status(&gid).map_err(to_py_err)?;
        Ok(PyDownload(download))
    }

    fn get_global_stat(&self) -> PyResult<PyGlobalStat> {
        let stat = self.client.get_global_stat().map_err(to_py_err)?;
        Ok(PyGlobalStat(stat))
    }

    fn get_version(&self) -> PyResult<PyVersion> {
        let version = self.client.get_version().map_err(to_py_err)?;
        Ok(PyVersion(version))
    }

    fn remove(&self, gid: String) -> PyResult<String> {
        self.client.remove(&gid).map_err(to_py_err)
    }

    fn pause(&self, gid: String) -> PyResult<String> {
        self.client.pause(&gid).map_err(to_py_err)
    }

    fn unpause(&self, gid: String) -> PyResult<String> {
        self.client.unpause(&gid).map_err(to_py_err)
    }

    fn tell_waiting(&self, offset: i64, num: i64) -> PyResult<Vec<PyDownload>> {
        let downloads = self.client.tell_waiting(offset, num).map_err(to_py_err)?;
        Ok(downloads.into_iter().map(PyDownload).collect())
    }

    fn tell_stopped(&self, offset: i64, num: i64) -> PyResult<Vec<PyDownload>> {
        let downloads = self.client.tell_stopped(offset, num).map_err(to_py_err)?;
        Ok(downloads.into_iter().map(PyDownload).collect())
    }

    fn get_session_id(&self) -> PyResult<String> {
        self.client.get_session_id().map_err(to_py_err)
    }

    fn get_download_results(&self, offset: i64, num: i64) -> PyResult<Vec<PyDownload>> {
        let downloads = self.client.get_download_results(offset, num).map_err(to_py_err)?;
        Ok(downloads.into_iter().map(PyDownload).collect())
    }

    fn get_uris(&self, gid: String) -> PyResult<Vec<PyUri>> {
        let uris = self.client.get_uris(&gid).map_err(to_py_err)?;
        Ok(uris.into_iter().map(PyUri).collect())
    }

    fn get_files(&self, gid: String) -> PyResult<Vec<PyFile>> {
        let files = self.client.get_files(&gid).map_err(to_py_err)?;
        Ok(files.into_iter().map(PyFile).collect())
    }

    fn get_peers(&self, gid: String) -> PyResult<Vec<PyPeer>> {
        let peers = self.client.get_peers(&gid).map_err(to_py_err)?;
        Ok(peers.into_iter().map(PyPeer).collect())
    }

    fn get_servers(&self, gid: String) -> PyResult<Vec<PyServer>> {
        let servers = self.client.get_servers(&gid).map_err(to_py_err)?;
        Ok(servers.into_iter().map(PyServer).collect())
    }

    fn get_option(&self, gid: String) -> PyResult<String> {
        let options = self.client.get_option(&gid).map_err(to_py_err)?;
        serde_json::to_string(&options).map_err(|e| PyException::new_err(e.to_string()))
    }

    fn get_global_option(&self) -> PyResult<String> {
        let options = self.client.get_global_option().map_err(to_py_err)?;
        serde_json::to_string(&options).map_err(|e| PyException::new_err(e.to_string()))
    }

    fn change_global_option(&self, options: String) -> PyResult<String> {
        let options: serde_json::Value = serde_json::from_str(&options).map_err(|e| PyException::new_err(e.to_string()))?;
        self.client.change_global_option(options).map_err(to_py_err)
    }

    fn get_session_info(&self) -> PyResult<PySessionInfo> {
        let session_info = self.client.get_session_info().map_err(to_py_err)?;
        Ok(PySessionInfo(session_info))
    }

    fn purge_download_result(&self) -> PyResult<String> {
        self.client.purge_download_result().map_err(to_py_err)
    }

    fn remove_download_result(&self, gid: String) -> PyResult<String> {
        self.client.remove_download_result(&gid).map_err(to_py_err)
    }

    #[pyo3(signature = (filename=None))]
    fn save_session(&self, filename: Option<String>) -> PyResult<String> {
        self.client.save_session(filename.as_deref()).map_err(to_py_err)
    }

    #[pyo3(signature = (torrent, uris=None, options=None))]
    fn add_torrent(&self, torrent: String, uris: Option<Vec<String>>, options: Option<String>) -> PyResult<String> {
        let options = options
            .and_then(|s| serde_json::from_str(&s).ok());
        self.client.add_torrent(&torrent, uris, options).map_err(to_py_err)
    }

    #[pyo3(signature = (metalink, options=None))]
    fn add_metalink(&self, metalink: String, options: Option<String>) -> PyResult<Vec<String>> {
        let options = options
            .and_then(|s| serde_json::from_str(&s).ok());
        self.client.add_metalink(&metalink, options).map_err(to_py_err)
    }

    fn force_remove(&self, gid: String) -> PyResult<String> {
        self.client.force_remove(&gid).map_err(to_py_err)
    }

    fn force_pause(&self, gid: String) -> PyResult<String> {
        self.client.force_pause(&gid).map_err(to_py_err)
    }

    fn pause_all(&self) -> PyResult<String> {
        self.client.pause_all().map_err(to_py_err)
    }

    fn force_pause_all(&self) -> PyResult<String> {
        self.client.force_pause_all().map_err(to_py_err)
    }

    fn unpause_all(&self) -> PyResult<String> {
        self.client.unpause_all().map_err(to_py_err)
    }

    fn change_uri(&self, gid: String, file_index: i64, del_uris: Vec<String>, add_uris: Vec<String>) -> PyResult<String> {
        self.client.change_uri(&gid, file_index, del_uris, add_uris).map_err(to_py_err)
    }

    fn shutdown(&self) -> PyResult<String> {
        self.client.shutdown().map_err(to_py_err)
    }

    fn force_shutdown(&self) -> PyResult<String> {
        self.client.force_shutdown().map_err(to_py_err)
    }

    fn system_list_methods(&self) -> PyResult<Vec<String>> {
        self.client.system_list_methods().map_err(to_py_err)
    }

    fn system_list_notifications(&self) -> PyResult<Vec<String>> {
        self.client.system_list_notifications().map_err(to_py_err)
    }

    // Batch operations
    #[pyo3(signature = (uri_list, options=None))]
    fn add_uris(&self, uri_list: Vec<Vec<String>>, options: Option<String>) -> PyResult<Vec<String>> {
        let options = options
            .and_then(|s| serde_json::from_str(&s).ok());
        self.client.add_uris(uri_list, options).map_err(to_py_err)
    }

    fn batch_pause(&self, gids: Vec<String>) -> PyResult<Vec<PyObject>> {
        let results = self.client.batch_pause(gids).map_err(to_py_err)?;
        Python::with_gil(|py| {
            Ok(results.into_iter().map(|result| match result {
                Ok(gid) => gid.into_py(py),
                Err(err) => to_py_err(err).into_py(py),
            }).collect())
        })
    }

    fn batch_remove(&self, gids: Vec<String>) -> PyResult<Vec<PyObject>> {
        let results = self.client.batch_remove(gids).map_err(to_py_err)?;
        Python::with_gil(|py| {
            Ok(results.into_iter().map(|result| match result {
                Ok(gid) => gid.into_py(py),
                Err(err) => to_py_err(err).into_py(py),
            }).collect())
        })
    }

    // Daemon management methods
    fn check_daemon(&self) -> PyResult<bool> {
        match self.client.get_version() {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }
}

fn to_py_err(err: Aria2Error) -> PyErr {
    match err {
        Aria2Error::Rpc { code, message } => PyException::new_err(format!("RPC Error {}: {}", code, message)),
        _ => PyException::new_err(err.to_string()),
    }
}

#[pyclass]
struct PySecureDaemonManager {
    manager: SecureDaemonManager,
}

#[pymethods]
impl PySecureDaemonManager {
    #[new]
    #[pyo3(signature = (secret=None, port=None, directory=None))]
    fn new(secret: Option<String>, port: Option<u16>, directory: Option<String>) -> Self {
        println!("DEBUG: PySecureDaemonManager::new called with secret: {:?}, port: {:?}, directory: {:?}", secret, port, directory);
        let secret = secret.unwrap_or_else(|| "aria2python".to_string());
        let port = port.unwrap_or(6800);
        Self {
            manager: SecureDaemonManager::new(secret, port, directory),
        }
    }

    fn is_daemon_running(&self) -> bool {
        self.manager.is_daemon_running()
    }

    fn start_daemon(&mut self) -> PyResult<()> {
        match self.manager.start_daemon() {
            Ok(()) => Ok(()),
            Err(e) => Err(PyException::new_err(format!("Failed to start daemon: {}", e))),
        }
    }

    fn stop_daemon(&mut self) -> PyResult<()> {
        match self.manager.stop_daemon() {
            Ok(()) => Ok(()),
            Err(e) => Err(PyException::new_err(format!("Failed to stop daemon: {}", e))),
        }
    }
}

#[pymodule]
fn aria2a(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyAria2Client>()?;
    m.add_class::<PySecureDaemonManager>()?;
    Ok(())
}
