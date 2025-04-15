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
git clone https://github.com/yourusername/cursor-account-register.git
cd cursor-account-register
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
python -m src.main your_email@example.com
```

或者：

```bash
cd src
python main.py your_email@example.com
```

## 配置说明

在 `.env` 文件中配置以下信息：

- 邮件服务器配置（IMAP/POP3）
- 临时邮箱配置（如果使用）
- 邮件协议选择

## 注意事项

- 请确保你的邮箱服务器允许 IMAP/POP3 访问
- 使用临时邮箱时需要注意服务的可用性
- 不要将你的邮箱密码提交到版本控制系统

## 贡献指南

欢迎提交 Pull Request 来改进这个项目。在提交之前，请确保：

1. 代码符合 PEP 8 规范
2. 添加了适当的测试
3. 更新了文档

## 许可证

MIT License 