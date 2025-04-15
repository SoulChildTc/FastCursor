use rusqlite::{Connection, Result as SqliteResult};
use std::path::PathBuf;
use dirs;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AuthError {
    #[error("数据库错误: {0}")]
    Database(#[from] rusqlite::Error),
    
    #[error("环境错误: {0}")]
    Environment(String),
    
    #[error("未提供任何更新值")]
    NoUpdates,
    
    #[error("IO 错误: {0}")]
    Io(#[from] std::io::Error),
}

pub struct CursorAuthManager {
    db_path: PathBuf,
}

impl CursorAuthManager {
    pub fn new() -> Self {
        let db_path = if cfg!(target_os = "windows") {
            // Windows
            let appdata = std::env::var("APPDATA")
                .expect("APPDATA 环境变量未设置");
            PathBuf::from(appdata).join("Cursor").join("User").join("globalStorage").join("state.vscdb")
        } else if cfg!(target_os = "macos") {
            // macOS
            dirs::home_dir()
                .expect("无法获取用户主目录")
                .join("Library")
                .join("Application Support")
                .join("Cursor")
                .join("User")
                .join("globalStorage")
                .join("state.vscdb")
        } else {
            // Linux 和其他类 Unix 系统
            dirs::home_dir()
                .expect("无法获取用户主目录")
                .join(".config")
                .join("Cursor")
                .join("User")
                .join("globalStorage")
                .join("state.vscdb")
        };
        
        Self { db_path }
    }
    
    pub fn update_auth(
        &mut self,
        email: Option<String>,
        access_token: Option<String>,
        refresh_token: Option<String>,
    ) -> Result<(), AuthError> {
        let mut updates = Vec::new();
        
        // 登录状态
        updates.push(("cursorAuth/cachedSignUpType".to_string(), "Auth_0".to_string()));
        
        if let Some(email) = email {
            updates.push(("cursorAuth/cachedEmail".to_string(), email));
        }
        
        if let Some(access_token) = access_token {
            updates.push(("cursorAuth/accessToken".to_string(), access_token));
        }
        
        if let Some(refresh_token) = refresh_token {
            updates.push(("cursorAuth/refreshToken".to_string(), refresh_token));
        }
        
        if updates.is_empty() {
            return Err(AuthError::NoUpdates);
        }
        
        let conn = Connection::open(&self.db_path)?;
        
        for (key, value) in updates {
            // 检查键是否存在
            let count: i64 = conn.query_row(
                "SELECT COUNT(*) FROM itemTable WHERE key = ?",
                [&key],
                |row| row.get(0),
            )?;
            
            if count == 0 {
                // 键不存在，执行插入
                conn.execute(
                    "INSERT INTO itemTable (key, value) VALUES (?, ?)",
                    [&key, &value],
                )?;
            } else {
                // 键存在，执行更新
                conn.execute(
                    "UPDATE itemTable SET value = ? WHERE key = ?",
                    [&value, &key],
                )?;
            }
        }
        
        Ok(())
    }
} 