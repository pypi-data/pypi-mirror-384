use aria2_core::{Aria2Client, raw::RpcRequest};
use serde_json::json;
use warp::Filter;

#[tokio::test]
async fn test_add_uri() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.addUri" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": "1234567890"
                });
                warp::reply::json(&response)
            } else {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                });
                warp::reply::json(&response)
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.add_uri(vec!["http://example.com".to_string()], None).await;
    assert_eq!(result.unwrap(), "1234567890");
}

#[tokio::test]
async fn test_tell_active() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.tellActive" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": [{
                        "gid": "123",
                        "status": "active",
                        "totalLength": "1000",
                        "completedLength": "500",
                        "uploadLength": "0",
                        "downloadSpeed": "100",
                        "uploadSpeed": "0",
                        "bitfield": null,
                        "infoHash": null,
                        "numSeeders": null,
                        "seeder": null,
                        "pieceLength": "1024",
                        "numPieces": "1",
                        "connections": "1",
                        "errorCode": null,
                        "errorMessage": null,
                        "followedBy": null,
                        "following": null,
                        "belongsTo": null,
                        "dir": "/tmp",
                        "files": [],
                        "bittorrent": null,
                        "verifiedLength": null,
                        "verifyIntegrityPending": null
                    }]
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.tell_active().await;
    let downloads = result.unwrap();
    assert_eq!(downloads.len(), 1);
    assert_eq!(downloads[0].gid, "123");
}

#[tokio::test]
async fn test_change_option() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.changeOption" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": "OK"
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let options = json!({"max-download-limit": "100K"});
    let result = client.change_option("123", options).await;
    assert_eq!(result.unwrap(), "OK");
}

#[tokio::test]
async fn test_tell_status() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.tellStatus" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": {
                        "gid": "123",
                        "status": "active",
                        "totalLength": "1000",
                        "completedLength": "500",
                        "uploadLength": "0",
                        "downloadSpeed": "100",
                        "uploadSpeed": "0",
                        "bitfield": null,
                        "infoHash": null,
                        "numSeeders": null,
                        "seeder": null,
                        "pieceLength": "1024",
                        "numPieces": "1",
                        "connections": "1",
                        "errorCode": null,
                        "errorMessage": null,
                        "followedBy": null,
                        "following": null,
                        "belongsTo": null,
                        "dir": "/tmp",
                        "files": [],
                        "bittorrent": null,
                        "verifiedLength": null,
                        "verifyIntegrityPending": null
                    }
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.tell_status("123").await;
    let download = result.unwrap();
    assert_eq!(download.gid, "123");
    assert_eq!(download.status, "active");
}

#[tokio::test]
async fn test_get_global_stat() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.getGlobalStat" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": {
                        "downloadSpeed": "1000",
                        "uploadSpeed": "500",
                        "numActive": "2",
                        "numWaiting": "1",
                        "numStopped": "3",
                        "numStoppedTotal": "5"
                    }
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.get_global_stat().await;
    let stat = result.unwrap();
    assert_eq!(stat.download_speed, "1000");
    assert_eq!(stat.num_active, "2");
}

#[tokio::test]
async fn test_get_version() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.getVersion" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": {
                        "version": "1.36.0",
                        "enabledFeatures": ["BitTorrent", "HTTP", "HTTPS"]
                    }
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.get_version().await;
    let version = result.unwrap();
    assert_eq!(version.version, "1.36.0");
    assert!(version.enabled_features.contains(&"BitTorrent".to_string()));
}

#[tokio::test]
async fn test_remove() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.remove" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": "OK"
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.remove("123").await;
    assert_eq!(result.unwrap(), "OK");
}

#[tokio::test]
async fn test_get_session_id() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.getSessionInfo" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": {
                        "sessionId": "session123"
                    }
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.get_session_id().await;
    assert_eq!(result.unwrap(), "session123");
}

#[tokio::test]
async fn test_get_download_results() {
    let filter = warp::post()
        .and(warp::body::json())
        .map(|req: RpcRequest| {
            if req.method == "aria2.tellWaiting" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": [{
                        "gid": "waiting1",
                        "status": "waiting",
                        "totalLength": "1000",
                        "completedLength": "0",
                        "uploadLength": "0",
                        "downloadSpeed": "0",
                        "uploadSpeed": "0",
                        "bitfield": null,
                        "infoHash": null,
                        "numSeeders": null,
                        "seeder": null,
                        "pieceLength": "1024",
                        "numPieces": "1",
                        "connections": "0",
                        "errorCode": null,
                        "errorMessage": null,
                        "followedBy": null,
                        "following": null,
                        "belongsTo": null,
                        "dir": "/tmp",
                        "files": [],
                        "bittorrent": null,
                        "verifiedLength": null,
                        "verifyIntegrityPending": null
                    }]
                });
                warp::reply::json(&response)
            } else if req.method == "aria2.tellStopped" {
                let response = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": [{
                        "gid": "stopped1",
                        "status": "complete",
                        "totalLength": "2000",
                        "completedLength": "2000",
                        "uploadLength": "0",
                        "downloadSpeed": "0",
                        "uploadSpeed": "0",
                        "bitfield": null,
                        "infoHash": null,
                        "numSeeders": null,
                        "seeder": null,
                        "pieceLength": "1024",
                        "numPieces": "2",
                        "connections": "0",
                        "errorCode": null,
                        "errorMessage": null,
                        "followedBy": null,
                        "following": null,
                        "belongsTo": null,
                        "dir": "/tmp",
                        "files": [],
                        "bittorrent": null,
                        "verifiedLength": null,
                        "verifyIntegrityPending": null
                    }]
                });
                warp::reply::json(&response)
            } else {
                warp::reply::json(&serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": { "code": 1, "message": "Method not found" }
                }))
            }
        });

    let (addr, server) = warp::serve(filter).bind_ephemeral(([127, 0, 0, 1], 0));
    tokio::spawn(server);

    let client = Aria2Client::new(format!("http://{}", addr), None);
    let result = client.get_download_results(0, 10).await;
    let downloads = result.unwrap();
    assert_eq!(downloads.len(), 2);
    assert_eq!(downloads[0].gid, "waiting1");
    assert_eq!(downloads[1].gid, "stopped1");
}