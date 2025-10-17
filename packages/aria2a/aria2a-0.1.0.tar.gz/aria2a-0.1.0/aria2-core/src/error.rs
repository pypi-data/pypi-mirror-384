use thiserror::Error;

#[derive(Error, Debug)]
pub enum Aria2Error {
    #[error("Transport error: {0}")]
    Transport(#[from] reqwest::Error),
    #[error("RPC error: code {code}, message: {message}")]
    Rpc { code: i64, message: String },
    #[error("Timeout error")]
    Timeout,
    #[error("Serialization error: {0}")]
    Serde(#[from] serde_json::Error),
    #[error("Invalid GID: {0}")]
    InvalidGid(String),
}