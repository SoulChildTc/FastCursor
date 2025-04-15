use std::path::{Path, PathBuf};
use std::fs;
use std::io::{self, Read, Write};
use uuid::Uuid;
use serde_json::{json};
use chrono::Local;
use anyhow::{Result, Context};
use dirs;

// 获取存储文件路径
fn get_storage_path() -> PathBuf {
    if cfg!(target_os = "windows") {
        // Windows
        let appdata = std::env::var("APPDATA")
            .expect("APPDATA 环境变量未设置");
        PathBuf::from(appdata).join("Cursor").join("User").join("globalStorage").join("storage.json")
    } else if cfg!(target_os = "macos") {
        // macOS
        dirs::home_dir()
            .expect("无法获取用户主目录")
            .join("Library")
            .join("Application Support")
            .join("Cursor")
            .join("User")
            .join("globalStorage")
            .join("storage.json")
    } else {
        // Linux 和其他类 Unix 系统
        dirs::home_dir()
            .expect("无法获取用户主目录")
            .join(".config")
            .join("Cursor")
            .join("User")
            .join("globalStorage")
            .join("storage.json")
    }
}

// 获取 main.js 文件路径
fn get_main_js_path() -> Option<PathBuf> {
    if cfg!(target_os = "macos") {
        // macOS
        Some(PathBuf::from("/Applications/Cursor.app/Contents/Resources/app/out/main.js"))
    } else if cfg!(target_os = "windows") {
        // Windows
        let local_appdata = std::env::var("LOCALAPPDATA").ok()?;
        Some(PathBuf::from(local_appdata)
            .join("Programs")
            .join("cursor")
            .join("resources")
            .join("app")
            .join("out")
            .join("main.js"))
    } else {
        None
    }
}

// 生成随机 ID (64位十六进制)
fn generate_random_id() -> String {
    format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple())
}

// 生成 UUID
fn generate_uuid() -> String {
    Uuid::new_v4().to_string()
}

// 创建文件备份
fn backup_file(file_path: &Path) -> Result<()> {
    if file_path.exists() {
        let backup_path = format!(
            "{}.backup_{}",
            file_path.to_string_lossy(),
            Local::now().format("%Y%m%d_%H%M%S")
        );
        fs::copy(file_path, &backup_path)
            .with_context(|| format!("无法创建备份文件: {}", backup_path))?;
        println!("已创建备份文件: {}", backup_path);
    }
    Ok(())
}

// 确保目录存在
fn ensure_dir_exists(path: &Path) -> io::Result<()> {
    if !path.exists() {
        fs::create_dir_all(path)?;
    }
    Ok(())
}

// 更新 main.js 文件中的 UUID 生成方式
fn update_main_js(file_path: &Path) -> Result<bool> {
    if !file_path.exists() {
        println!("警告: main.js 文件不存在: {}", file_path.display());
        return Ok(false);
    }

    // 创建备份
    backup_file(file_path)?;

    // 读取文件内容
    let mut content = String::new();
    let mut file = fs::File::open(file_path)?;
    file.read_to_string(&mut content)?;

    let new_content = if cfg!(target_os = "macos") {
        // macOS: 替换 ioreg 命令
        content.replace(
            "ioreg -rd1 -c IOPlatformExpertDevice",
            "UUID=$(uuidgen | tr '[:upper:]' '[:lower:]');echo \\\"IOPlatformUUID = \\\"$UUID\\\";",
        )
    } else if cfg!(target_os = "windows") {
        // Windows: 替换 REG.exe 命令
        content.replace(
            "${v5[s$()]}\\REG.exe QUERY HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid",
            "powershell -Command \"[guid]::NewGuid().ToString().ToLower()\"",
        )
    } else {
        println!("警告: 不支持的操作系统");
        return Ok(false);
    };

    // 写入修改后的内容
    let mut file = fs::File::create(file_path)?;
    file.write_all(new_content.as_bytes())?;

    // 验证修改
    let success_marker = if cfg!(target_os = "macos") {
        "UUID=$(uuidgen | tr '[:upper:]' '[:lower:]');echo \\\"IOPlatformUUID = \\\"$UUID\\\";"
    } else {
        "powershell -Command \"[guid]::NewGuid().ToString().ToLower()\""
    };

    if new_content.contains(success_marker) {
        println!("main.js 文件修改成功");
        Ok(true)
    } else {
        println!("警告: main.js 文件可能未被正确修改，请检查文件内容");
        println!("你可以从备份文件恢复: {}.backup_*", file_path.display());
        Ok(false)
    }
}

// 更新存储文件中的 ID
fn update_storage_file(file_path: &Path) -> Result<(String, String, String)> {
    // 生成新的 ID
    let new_machine_id = generate_random_id();
    let new_mac_machine_id = generate_random_id();
    let new_dev_device_id = generate_uuid();
    
    // 确保目录存在
    if let Some(parent) = file_path.parent() {
        ensure_dir_exists(parent)?;
    }
    
    // 读取或创建配置文件
    let mut data = if file_path.exists() {
        let file_content = fs::read_to_string(file_path)?;
        serde_json::from_str(&file_content).unwrap_or_else(|_| json!({}))
    } else {
        json!({})
    };
    
    // 更新 ID
    data["telemetry.machineId"] = json!(new_machine_id);
    data["telemetry.macMachineId"] = json!(new_mac_machine_id);
    data["telemetry.devDeviceId"] = json!(new_dev_device_id);
    data["telemetry.sqmId"] = json!(format!("{{{}}}", Uuid::new_v4().to_string().to_uppercase()));
    
    // 写入文件
    let file_content = serde_json::to_string_pretty(&data)?;
    fs::write(file_path, file_content)?;
    
    Ok((new_machine_id, new_mac_machine_id, new_dev_device_id))
}

// 重置机器 ID
pub fn reset_machine_id() -> Result<()> {
    // 获取配置文件路径
    let storage_path = get_storage_path();
    println!("配置文件路径: {}", storage_path.display());
    
    // 备份原文件
    backup_file(&storage_path)?;
    
    // 更新 ID
    let (machine_id, mac_machine_id, dev_device_id) = update_storage_file(&storage_path)?;
    
    // 输出结果
    println!("已成功修改 ID:");
    println!("machineId: {}", machine_id);
    println!("macMachineId: {}", mac_machine_id);
    println!("devDeviceId: {}", dev_device_id);

    // 处理 main.js
    if cfg!(target_os = "macos") || cfg!(target_os = "windows") {
        if let Some(main_js_path) = get_main_js_path() {
            update_main_js(&main_js_path)?;
        }
    }
    
    Ok(())
} 