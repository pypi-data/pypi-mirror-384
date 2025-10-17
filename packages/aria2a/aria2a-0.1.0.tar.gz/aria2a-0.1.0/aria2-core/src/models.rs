extern crate serde;
use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
#[allow(non_snake_case)]
pub struct Download {
    pub gid: String,
    pub status: String,
    pub totalLength: String,
    pub completedLength: String,
    pub uploadLength: String,
    pub downloadSpeed: String,
    pub uploadSpeed: String,
    pub infoHash: Option<String>,
    pub numSeeders: Option<String>,
    pub seeder: Option<String>,
    pub pieceLength: String,
    pub numPieces: String,
    pub connections: String,
    pub errorCode: Option<String>,
    pub errorMessage: Option<String>,
    pub followedBy: Option<Vec<String>>,
    pub following: Option<String>,
    pub belongsTo: Option<String>,
    pub dir: String,
    pub files: Vec<File>,
    pub bittorrent: Option<Bittorrent>,
    pub bitfield: Option<String>,
    pub verifyIntegrityPending: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
#[allow(non_snake_case)]
pub struct File {
    pub index: String,
    pub path: String,
    pub length: String,
    pub completedLength: String,
    pub selected: String,
    pub uris: Vec<Uri>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Uri {
    pub uri: String,
    pub status: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Bittorrent {
    pub announce_list: Option<Vec<Vec<String>>>,
    pub comment: Option<String>,
    pub creation_date: Option<i64>,
    pub mode: Option<String>,
    pub info: Option<BittorrentInfo>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct BittorrentInfo {
    pub name: String,
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct GlobalStat {
    #[serde(rename = "downloadSpeed")]
    pub download_speed: Option<String>,
    #[serde(rename = "uploadSpeed")]
    pub upload_speed: String,
    #[serde(rename = "numActive")]
    pub num_active: String,
    #[serde(rename = "numWaiting")]
    pub num_waiting: String,
    #[serde(rename = "numStopped")]
    pub num_stopped: String,
    #[serde(rename = "numStoppedTotal")]
    pub num_stopped_total: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Version {
    pub version: String,
    #[serde(rename = "enabledFeatures")]
    pub enabled_features: Vec<String>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct SessionInfo {
    #[serde(rename = "sessionId")]
    pub session_id: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Peer {
    pub peer_id: String,
    pub ip: String,
    pub port: String,
    pub bitfield: String,
    pub am_choking: bool,
    pub peer_choking: bool,
    pub download_speed: String,
    pub upload_speed: String,
    pub seeder: bool,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Server {
    pub index: String,
    pub servers: Vec<ServerInfo>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct ServerInfo {
    pub uri: String,
    pub current_uri: String,
    pub download_speed: String,
}