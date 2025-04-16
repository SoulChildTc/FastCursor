# Cursor 账号注册工具

这是一个用于自动化注册 Cursor 账号的工具。它可以帮助用户自动处理邮箱验证码并完成账号注册流程。

## 功能特点

- 支持多种邮件协议（IMAP 和 POP3）
- 支持临时邮箱服务
- 自动处理验证码
- 自动更新 Cursor 认证信息
- 跨平台支持（Windows、macOS、Linux）

## 环境要求

- Python 3.10 或更高版本
- pip 包管理器
- Chrome 浏览器（用于自动化操作）

## 详细安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/SoulChildTc/FastCursor.git
cd FastCursor
```

### 2. 创建虚拟环境
```bash
uv venv
```

### 2. 安装 Python 依赖

```bash
uv pip install -r requirements.txt
```

### 3. 配置文件

```bash
cp .env.example .env
```

### 4. 运行项目

```bash
uv run app.py
```

### 常见问题解决

#### macOS 用户注意事项

如果在 macOS 上运行遇到文件损坏问题，请执行以下命令：

```bash
sudo xattr -rd com.apple.quarantine /Applications/Cursor\ Helper.app/
```

#### 其他常见问题

1. 如果遇到 Chrome 驱动相关错误：
   - 确保已安装最新版本的 Chrome 浏览器
   - 检查 ChromeDriver 版本是否与 Chrome 浏览器版本匹配

2. 邮箱验证码接收问题：
   - 检查邮箱配置是否正确
   - 确认邮箱服务器是否支持 IMAP/POP3
   - 如果使用 Gmail，需要开启"不够安全的应用访问权限"

## 注意事项

- 本工具仅用于学习和研究目的
- 请勿滥用此工具进行批量注册
- 使用过程中遵守相关服务条款

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 许可证

MIT License