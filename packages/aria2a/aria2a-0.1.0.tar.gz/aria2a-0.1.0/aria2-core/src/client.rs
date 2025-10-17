use crate::raw;
use crate::models::{Download, Uri, File, Peer, Server, GlobalStat, Version, SessionInfo};
use crate::error::Aria2Error;
use serde_json::{Value, json};
use std::collections::HashMap;

#[derive(Clone)]
pub struct Aria2Client {
    raw: raw::Client,
}

impl Aria2Client {
    pub fn new(endpoint: String, secret: Option<String>) -> Self {
        Self {
            raw: raw::Client::new(endpoint, secret),
        }
    }

    pub fn with_timeout(mut self, timeout: std::time::Duration) -> Self {
        self.raw = self.raw.with_timeout(timeout);
        self
    }

    pub fn with_retries(mut self, retries: usize) -> Self {
        self.raw = self.raw.with_retries(retries);
        self
    }

    pub fn add_uri(&self, uris: Vec<String>, options: Option<Value>) -> Result<String, Aria2Error> {
        let params = vec![json!(uris), options.unwrap_or(json!({}))];
        self.raw.call("aria2.addUri", params)
    }

    pub fn tell_active(&self) -> Result<Vec<Download>, Aria2Error> {
        self.raw.call("aria2.tellActive", vec![])
    }

    pub fn change_option(&self, gid: &str, options: Value) -> Result<String, Aria2Error> {
        let params = vec![json!(gid), options];
        self.raw.call("aria2.changeOption", params)
    }

    pub fn tell_status(&self, gid: &str) -> Result<Download, Aria2Error> {
        self.raw.call("aria2.tellStatus", vec![json!(gid)])
    }

    pub fn get_uris(&self, gid: &str) -> Result<Vec<Uri>, Aria2Error> {
        self.raw.call("aria2.getUris", vec![json!(gid)])
    }

    pub fn get_files(&self, gid: &str) -> Result<Vec<File>, Aria2Error> {
        self.raw.call("aria2.getFiles", vec![json!(gid)])
    }

    pub fn get_peers(&self, gid: &str) -> Result<Vec<Peer>, Aria2Error> {
        self.raw.call("aria2.getPeers", vec![json!(gid)])
    }

    pub fn get_servers(&self, gid: &str) -> Result<Vec<Server>, Aria2Error> {
        self.raw.call("aria2.getServers", vec![json!(gid)])
    }

    pub fn tell_waiting(&self, offset: i64, num: i64) -> Result<Vec<Download>, Aria2Error> {
        self.raw.call("aria2.tellWaiting", vec![json!(offset), json!(num)])
    }

    pub fn tell_stopped(&self, offset: i64, num: i64) -> Result<Vec<Download>, Aria2Error> {
        self.raw.call("aria2.tellStopped", vec![json!(offset), json!(num)])
    }

    pub fn get_option(&self, gid: &str) -> Result<HashMap<String, Value>, Aria2Error> {
        self.raw.call("aria2.getOption", vec![json!(gid)])
    }

    pub fn get_global_option(&self) -> Result<HashMap<String, Value>, Aria2Error> {
        self.raw.call("aria2.getGlobalOption", vec![])
    }

    pub fn change_global_option(&self, options: Value) -> Result<String, Aria2Error> {
        self.raw.call("aria2.changeGlobalOption", vec![options])
    }

    pub fn get_global_stat(&self) -> Result<GlobalStat, Aria2Error> {
        self.raw.call("aria2.getGlobalStat", vec![])
    }

    pub fn get_version(&self) -> Result<Version, Aria2Error> {
        self.raw.call("aria2.getVersion", vec![])
    }

    pub fn get_session_info(&self) -> Result<SessionInfo, Aria2Error> {
        self.raw.call("aria2.getSessionInfo", vec![])
    }

    pub fn purge_download_result(&self) -> Result<String, Aria2Error> {
        self.raw.call("aria2.purgeDownloadResult", vec![])
    }

    pub fn remove_download_result(&self, gid: &str) -> Result<String, Aria2Error> {
        self.raw.call("aria2.removeDownloadResult", vec![json!(gid)])
    }

    pub fn save_session(&self, filename: Option<&str>) -> Result<String, Aria2Error> {
        let params = match filename {
            Some(fname) => vec![json!(fname)],
            None => vec![]
        };
        self.raw.call("aria2.saveSession", params)
    }

    pub fn add_torrent(&self, torrent: &str, uris: Option<Vec<String>>, options: Option<Value>) -> Result<String, Aria2Error> {
        let params = vec![
            json!(torrent),
            uris.as_ref().map(|u| json!(u)).unwrap_or(Value::Null),
            options.unwrap_or(Value::Null)
        ];
        self.raw.call("aria2.addTorrent", params)
    }

    pub fn add_metalink(&self, metalink: &str, options: Option<Value>) -> Result<Vec<String>, Aria2Error> {
        let params = vec![json!(metalink), options.unwrap_or(Value::Null)];
        self.raw.call("aria2.addMetalink", params)
    }

    pub fn remove(&self, gid: &str) -> Result<String, Aria2Error> {
        self.raw.call("aria2.remove", vec![json!(gid)])
    }

    pub fn force_remove(&self, gid: &str) -> Result<String, Aria2Error> {
        self.raw.call("aria2.forceRemove", vec![json!(gid)])
    }

    pub fn pause(&self, gid: &str) -> Result<String, Aria2Error> {
        self.raw.call("aria2.pause", vec![json!(gid)])
    }

    pub fn unpause(&self, gid: &str) -> Result<String, Aria2Error> {
        self.raw.call("aria2.unpause", vec![json!(gid)])
    }

    pub fn force_pause(&self, gid: &str) -> Result<String, Aria2Error> {
        self.raw.call("aria2.forcePause", vec![json!(gid)])
    }

    pub fn pause_all(&self) -> Result<String, Aria2Error> {
        self.raw.call("aria2.pauseAll", vec![])
    }

    pub fn force_pause_all(&self) -> Result<String, Aria2Error> {
        self.raw.call("aria2.forcePauseAll", vec![])
    }

    pub fn unpause_all(&self) -> Result<String, Aria2Error> {
        self.raw.call("aria2.unpauseAll", vec![])
    }

    pub fn change_uri(&self, gid: &str, file_index: i64, del_uris: Vec<String>, add_uris: Vec<String>) -> Result<String, Aria2Error> {
        let params = vec![json!(gid), json!(file_index), json!(del_uris), json!(add_uris)];
        self.raw.call("aria2.changeUri", params)
    }

    pub fn shutdown(&self) -> Result<String, Aria2Error> {
        self.raw.call("aria2.shutdown", vec![])
    }

    pub fn force_shutdown(&self) -> Result<String, Aria2Error> {
        self.raw.call("aria2.forceShutdown", vec![])
    }

    pub fn system_list_methods(&self) -> Result<Vec<String>, Aria2Error> {
        self.raw.call("system.listMethods", vec![])
    }

    pub fn system_list_notifications(&self) -> Result<Vec<String>, Aria2Error> {
        self.raw.call("system.listNotifications", vec![])
    }

    // Additional utility methods
    pub fn get_session_id(&self) -> Result<String, Aria2Error> {
        let session_info = self.get_session_info()?;
        Ok(session_info.session_id)
    }

    pub fn get_download_results(&self, offset: i64, num: i64) -> Result<Vec<Download>, Aria2Error> {
        // Get both waiting and stopped downloads as "results"
        let mut results = Vec::new();
        
        let waiting = self.tell_waiting(offset, num)?;
        results.extend(waiting);
        
        let stopped = self.tell_stopped(offset, num)?;
        results.extend(stopped);
        
        Ok(results)
    }

    // Batch operations
    pub fn add_uris(&self, uri_list: Vec<Vec<String>>, options: Option<Value>) -> Result<Vec<String>, Aria2Error> {
        let mut gids = Vec::new();
        for uris in uri_list {
            let gid = self.add_uri(uris, options.clone())?;
            gids.push(gid);
        }
        Ok(gids)
    }

    pub fn batch_pause(&self, gids: Vec<String>) -> Result<Vec<Result<String, Aria2Error>>, Aria2Error> {
        let mut results = Vec::new();
        for gid in gids {
            let result = self.pause(&gid);
            results.push(result);
        }
        Ok(results)
    }

    pub fn batch_remove(&self, gids: Vec<String>) -> Result<Vec<Result<String, Aria2Error>>, Aria2Error> {
        let mut results = Vec::new();
        for gid in gids {
            let result = self.remove(&gid);
            results.push(result);
        }
        Ok(results)
    }
}
