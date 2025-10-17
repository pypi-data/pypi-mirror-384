use serde::{Deserialize, Serialize};
use serde_json::Value;
use crate::error::Aria2Error;
use std::time::Duration;

#[derive(Serialize, Deserialize, Debug)]
pub struct RpcRequest {
    pub jsonrpc: String,
    pub id: String,
    pub method: String,
    pub params: Option<Vec<Value>>,
}

impl RpcRequest {
    pub fn new(id: String, method: String, params: Option<Vec<Value>>) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            method,
            params,
        }
    }
}

#[derive(Deserialize, Debug)]
pub struct RpcError {
    pub code: i64,
    pub message: String,
    pub data: Option<Value>,
}

#[derive(Deserialize, Debug)]
pub enum RpcResponse<T> {
    #[serde(rename = "result")]
    Success(T),
    #[serde(rename = "error")]
    Error(RpcError),
}

#[derive(Clone)]
pub struct Client {
    endpoint: String,
    secret: Option<String>,
    timeout: Duration,
    retries: usize,
}

impl Client {
    pub fn new(endpoint: String, secret: Option<String>) -> Self {
        Self {
            endpoint,
            secret,
            timeout: Duration::from_secs(10),
            retries: 3,
        }
    }

    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout = timeout;
        self
    }

    pub fn with_retries(mut self, retries: usize) -> Self {
        self.retries = retries;
        self
    }

    pub fn call<T>(&self, method: &str, params: Vec<Value>) -> Result<T, Aria2Error>
    where
        T: for<'de> Deserialize<'de>,
    {
        let mut params = params;
        if let Some(ref secret) = self.secret {
            params.insert(0, Value::String(format!("token:{}", secret)));
        }
        let request = RpcRequest::new("1".to_string(), method.to_string(), Some(params));
        
        // Use blocking client
        let client = reqwest::blocking::Client::builder()
            .timeout(self.timeout)
            .build()
            .unwrap_or_else(|_| reqwest::blocking::Client::new());
            
        let response = client
            .post(&self.endpoint)
            .json(&request)
            .send()?;
            
        let response_text = response.text()?;
        
        // Parse manually since untagged enum is causing issues
        let value: Value = serde_json::from_str(&response_text)?;
        if let Some(result) = value.get("result") {
            // Debug for getGlobalStat
            if method == "aria2.getGlobalStat" {
                println!("DEBUG: Trying to deserialize: {}", result);
            }
            let result: T = serde_json::from_value(result.clone())?;
            Ok(result)
        } else if let Some(error) = value.get("error") {
            let error: RpcError = serde_json::from_value(error.clone())?;
            Err(Aria2Error::Rpc { code: error.code, message: error.message })
        } else {
            Err(Aria2Error::Rpc { code: -1, message: "Invalid response format".to_string() })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_rpc_request_serialize() {
        let req = RpcRequest::new("1".to_string(), "aria2.addUri".to_string(), Some(vec![json!(["http://example.com"])]));
        let json_str = serde_json::to_string(&req).unwrap();
        assert!(json_str.contains("\"method\":\"aria2.addUri\""));
        assert!(json_str.contains("\"jsonrpc\":\"2.0\""));
    }

    #[test]
    fn test_rpc_response_success_deserialize() {
        let json = r#"{"jsonrpc":"2.0","id":"1","result":"123"}"#;
        let response: RpcResponse<String> = serde_json::from_str(json).unwrap();
        match response {
            RpcResponse::Success(result) => assert_eq!(result, "123"),
            _ => panic!("Expected success"),
        }
    }

    #[test]
    fn test_rpc_response_error_deserialize() {
        let json = r#"{"jsonrpc":"2.0","id":"1","error":{"code":1,"message":"error"}}"#;
        let response: RpcResponse<String> = serde_json::from_str(json).unwrap();
        match response {
            RpcResponse::Error(error) => {
                assert_eq!(error.code, 1);
                assert_eq!(error.message, "error");
            }
            _ => panic!("Expected error"),
        }
    }
}