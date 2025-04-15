# Cursor 账号注册工具

这是一个用于自动化注册 Cursor 账号的工具。它可以帮助用户自动处理邮箱验证码并完成账号注册流程。

## 功能特点

- 支持多种邮件协议（IMAP 和 POP3）
- 支持临时邮箱服务
- 自动处理验证码
- 自动更新 Cursor 认证信息
- 跨平台支持（Windows、macOS、Linux）

## 安装要求

- Python 3.7+
- pip 包管理器

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/SoulChildTc/FastCursor.git
cd FastCursor
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
```
然后编辑 `.env` 文件，填入你的配置信息。

## 使用方法

在项目根目录下运行以下命令来注册账号：

```bash
python app.py
```

## mac 报错解决

```bash
sudo xattr -rd com.apple.quarantine /Applications/Cursor\ Helper.app/
```