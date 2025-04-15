use std::path::PathBuf;
use std::process::Command;
use std::thread;
use std::time::Duration;
use anyhow::{Result, Context, anyhow};
use sysinfo::{System, Pid};
use dirs;

// 获取 Cursor 可执行文件的路径
fn get_cursor_path() -> Result<PathBuf> {
    if cfg!(target_os = "windows") {
        // Windows 默认安装路径
        let paths = vec![
            PathBuf::from(std::env::var("LOCALAPPDATA").unwrap_or_default())
                .join("Programs")
                .join("Cursor")
                .join("Cursor.exe"),
            PathBuf::from(std::env::var("APPDATA").unwrap_or_default())
                .join("Programs")
                .join("Cursor")
                .join("Cursor.exe"),
        ];
        
        for path in paths {
            if path.exists() {
                return Ok(path);
            }
        }
    } else if cfg!(target_os = "macos") {
        // macOS
        let path = PathBuf::from("/Applications/Cursor.app/Contents/MacOS/Cursor");
        if path.exists() {
            return Ok(path);
        }
    } else if cfg!(target_os = "linux") {
        // Linux
        let paths = vec![
            PathBuf::from("/usr/bin/cursor"),
            PathBuf::from("/usr/local/bin/cursor"),
        ];
        
        for path in paths {
            if path.exists() {
                return Ok(path);
            }
        }
    }
    
    Err(anyhow!("未找到 Cursor 可执行文件"))
}

// 重启 Cursor 进程
pub fn restart_cursor() -> Result<()> {
    println!("开始重启 Cursor...");
    
    // 先关闭现有进程
    if !exit_cursor(1)? {
        return Err(anyhow!("无法正确关闭现有 Cursor 进程, 请手动重启 Cursor"));
    }
    
    // 等待进程完全关闭
    thread::sleep(Duration::from_secs(1));
    
    // 获取 Cursor 可执行文件路径
    let cursor_path = get_cursor_path()?;
    
    // 启动新的 Cursor 进程
    #[cfg(target_os = "windows")]
    {
        Command::new(cursor_path)
            .spawn()
            .context("启动 Cursor 失败")?;
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        Command::new(cursor_path)
            .spawn()
            .context("启动 Cursor 失败")?;
    }
    
    println!("Cursor 已重启");
    Ok(())
}

// 退出 Cursor 进程
fn exit_cursor(timeout: u64) -> Result<bool> {
    println!("开始退出 Cursor...");
    
    let mut system = System::new_all();
    system.refresh_all();
    
    let mut cursor_processes = Vec::new();
    
    // 收集所有 Cursor 进程
    for (pid, process) in system.processes() {
        let name = process.name().to_lowercase();
        if name == "cursor" || name == "cursor.exe" {
            cursor_processes.push(*pid);
        }
    }
    
    if cursor_processes.is_empty() {
        println!("未发现运行中的 Cursor 进程");
        return Ok(true);
    }

    // 直接强制终止所有进程
    for pid in &cursor_processes {
        if let Some(process) = system.process(*pid) {
            process.kill();
        }
    }
    
    // 等待进程终止
    for _ in 0..timeout {
        system.refresh_all();
        
        let mut still_running = Vec::new();
        for pid in &cursor_processes {
            if system.process(*pid).is_some() {
                still_running.push(*pid);
            }
        }
        
        if still_running.is_empty() {
            println!("所有 Cursor 进程已强制关闭");
            return Ok(true);
        }
        
        thread::sleep(Duration::from_secs(1));
    }
    
    // 最终检查
    system.refresh_all();
    let mut final_running = Vec::new();
    
    for pid in &cursor_processes {
        if system.process(*pid).is_some() {
            final_running.push(*pid);
        }
    }
    
    if !final_running.is_empty() {
        let process_list = final_running
            .iter()
            .map(|pid| pid.to_string())
            .collect::<Vec<String>>()
            .join(", ");
        println!("以下进程未能关闭: {}", process_list);
        return Ok(false);
    }
    
    Ok(true)
} 