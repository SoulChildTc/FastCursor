// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

// 导入必要的模块
mod cursor_auth;
mod reset_machine;
mod process;

use cursor_auth::CursorAuthManager;
use reset_machine::reset_machine_id;
use process::restart_cursor;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::State;

// 定义应用状态
pub struct AppState {
    auth_manager: Mutex<CursorAuthManager>,
}

// 定义响应结构
#[derive(Serialize, Deserialize)]
struct ApiResponse {
    success: bool,
    message: String,
}

// 更新 Cursor 认证信息
#[tauri::command]
async fn update_cursor_auth(
    state: State<'_, AppState>,
    email: Option<String>,
    access_token: Option<String>,
    refresh_token: Option<String>,
) -> Result<ApiResponse, String> {
    let mut auth_manager = state.auth_manager.lock().unwrap();
    match auth_manager.update_auth(email, access_token, refresh_token) {
        Ok(_) => Ok(ApiResponse {
            success: true,
            message: "认证信息更新成功".to_string(),
        }),
        Err(e) => Ok(ApiResponse {
            success: false,
            message: format!("认证信息更新失败: {}", e),
        }),
    }
}

// 重置 Cursor 机器 ID
#[tauri::command]
async fn reset_cursor_machine_id_command(restart: bool) -> Result<ApiResponse, String> {
    match reset_machine_id() {
        Ok(_) => {
            if restart {
                match restart_cursor() {
                    Ok(_) => Ok(ApiResponse {
                        success: true,
                        message: "机器 ID 重置成功，Cursor 已重启".to_string(),
                    }),
                    Err(e) => Ok(ApiResponse {
                        success: true,
                        message: format!("机器 ID 重置成功，但 Cursor 重启失败: {}", e),
                    }),
                }
            } else {
                Ok(ApiResponse {
                    success: true,
                    message: "机器 ID 重置成功".to_string(),
                })
            }
        },
        Err(e) => Ok(ApiResponse {
            success: false,
            message: format!("机器 ID 重置失败: {}", e),
        }),
    }
}

// 从远程服务器获取账号信息并更新
#[tauri::command]
async fn change_account_command(state: State<'_, AppState>, api_url: String) -> Result<ApiResponse, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/account", api_url);
    
    match client.get(&url).send().await {
        Ok(response) => {
            match response.json::<serde_json::Value>().await {
                Ok(data) => {
                    if let Some(code) = data.get("code").and_then(|c| c.as_u64()) {
                        if code != 200 {
                            let message = data.get("message")
                                .and_then(|m| m.as_str())
                                .unwrap_or("未知错误");
                            return Ok(ApiResponse {
                                success: false,
                                message: format!("获取账号失败: {}", message),
                            });
                        }
                        
                        if let Some(account_data) = data.get("data") {
                            let email = account_data.get("email")
                                .and_then(|e| e.as_str())
                                .map(|s| s.to_string());
                            
                            let token = account_data.get("token")
                                .and_then(|t| t.as_str())
                                .map(|s| s.to_string());
                            
                            if let (Some(email), Some(token)) = (email.clone(), token.clone()) {
                                let mut auth_manager = state.auth_manager.lock().unwrap();
                                match auth_manager.update_auth(Some(email), Some(token.clone()), Some(token)) {
                                    Ok(_) => {
                                        // 更新成功后重置机器 ID
                                        match reset_machine_id() {
                                            Ok(_) => {
                                                match restart_cursor() {
                                                    Ok(_) => Ok(ApiResponse {
                                                        success: true,
                                                        message: "账号切换成功，Cursor 已重启".to_string(),
                                                    }),
                                                    Err(e) => Ok(ApiResponse {
                                                        success: true,
                                                        message: format!("账号切换成功，但 Cursor 重启失败: {}", e),
                                                    }),
                                                }
                                            },
                                            Err(e) => Ok(ApiResponse {
                                                success: false,
                                                message: format!("账号切换成功，但机器 ID 重置失败: {}", e),
                                            }),
                                        }
                                    },
                                    Err(e) => Ok(ApiResponse {
                                        success: false,
                                        message: format!("认证信息更新失败: {}", e),
                                    }),
                                }
                            } else {
                                Ok(ApiResponse {
                                    success: false,
                                    message: "获取账号信息不完整".to_string(),
                                })
                            }
                        } else {
                            Ok(ApiResponse {
                                success: false,
                                message: "响应中缺少 data 字段".to_string(),
                            })
                        }
                    } else {
                        Ok(ApiResponse {
                            success: false,
                            message: "响应中缺少 code 字段".to_string(),
                        })
                    }
                },
                Err(e) => Ok(ApiResponse {
                    success: false,
                    message: format!("解析响应失败: {}", e),
                }),
            }
        },
        Err(e) => Ok(ApiResponse {
            success: false,
            message: format!("请求失败: {}", e),
        }),
    }
}

pub fn init_app() {
    // 初始化应用状态
    let app_state = AppState {
        auth_manager: Mutex::new(CursorAuthManager::new()),
    };
    
    tauri::Builder::default()
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            update_cursor_auth,
            reset_cursor_machine_id_command,
            change_account_command,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
