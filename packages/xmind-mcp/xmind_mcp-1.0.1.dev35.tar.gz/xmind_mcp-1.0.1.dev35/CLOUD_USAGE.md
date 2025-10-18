# 🌟 XMind MCP Server - 云端使用指南

## 🎯 无需下载代码的使用方案

### 1. 🚀 GitHub Codespaces（推荐）
**一键创建云端开发环境**

```
🖱️ 一键启动：https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=Master-Frank/XmindMcp
```

**特点：**
- ✅ 零配置，零安装
- ✅ 完整功能，在线IDE
- ✅ 自动启动MCP服务器
- ✅ 免费使用（每月有额度）

**使用步骤：**
1. 点击上方链接
2. 选择配置（默认即可）
3. 等待环境创建（1-2分钟）
4. 自动启动MCP服务器
5. 访问端口8080查看服务

---

### 2. 🐳 Docker Hub预构建镜像
**一条命令启动服务**

```bash
# 直接运行（无需拉代码）
docker run -d -p 8080:8080 --name xmind-mcp masterfrank/xmind-mcp-server:latest

# 或使用一键脚本
curl -sSL https://raw.githubusercontent.com/Master-Frank/XmindMcp/main/docker-quick-start.sh | bash
```

**特点：**
- ✅ 无需安装依赖
- ✅ 跨平台支持
- ✅ 隔离环境
- ✅ 一键启动

**验证服务：**
```bash
curl http://localhost:8080/health
```

---

### 3. 🔄 Replit在线运行
**浏览器中直接运行**

**一键导入：**
```
https://replit.com/github/Master-Frank/XmindMcp
```

**特点：**
- ✅ 纯浏览器操作
- ✅ 自动部署
- ✅ 在线访问
- ✅ 免费使用

**使用步骤：**
1. 访问上方链接
2. 登录Replit账号
3. 点击"Import from GitHub"
4. 等待自动部署
5. 获得在线访问地址

---

### 4. 📱 Web在线服务
**通过网页界面使用**

**访问地址：**
```
https://master-frank.github.io/XmindMcp/
```

**功能：**
- 📋 服务状态监控
- 🔗 快速访问入口
- 📖 API文档查看
- 🚀 多种启动方式

---

### 5. ☁️ GitHub Actions自动部署
**自动构建云端服务**

**触发方式：**
- 推送代码到main分支
- 手动触发工作流
- 定时任务执行

**输出：**
- 🐳 Docker镜像构建
- 🚀 自动部署服务
- 📊 构建状态报告

---

## 🔧 各方案对比

| 方案 | 技术门槛 | 启动速度 | 功能完整 | 成本 | 推荐场景 |
|------|----------|----------|----------|------|----------|
| GitHub Codespaces | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 免费 | 开发测试 |
| Docker镜像 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 免费 | 生产部署 |
| Replit | ⭐ | ⭐⭐ | ⭐⭐⭐ | 免费 | 快速体验 |
| Web界面 | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 免费 | 简单使用 |

---

## 🎯 快速选择指南

### 我是开发者 👨‍💻
**推荐：GitHub Codespaces**
- 完整开发环境
- 在线代码编辑
- 调试功能完善

### 我是普通用户 👤
**推荐：Docker或Web界面**
- 简单易用
- 无需技术背景
- 快速上手

### 我是企业用户 🏢
**推荐：Docker + 云服务**
- 可扩展性强
- 稳定可靠
- 易于维护

---

## 🚀 一键体验

### 最快体验（30秒）
```bash
# Docker用户
docker run -d -p 8080:8080 masterfrank/xmind-mcp-server:latest

# 访问 http://localhost:8080/docs
```

### 云端体验（2分钟）
```
1. 访问 GitHub Codespaces
2. 一键创建环境
3. 自动启动服务
4. 在线使用功能
```

### 浏览器体验（1分钟）
```
访问: https://master-frank.github.io/XmindMcp/
选择: 合适的启动方式
使用: 提供的在线服务
```

---

## 📞 技术支持

- 📧 GitHub Issues: [提交问题](https://github.com/Master-Frank/XmindMcp/issues)
- 📖 详细文档: [查看README](https://github.com/Master-Frank/XmindMcp/blob/main/README.md)
- 💬 讨论区: [GitHub Discussions](https://github.com/Master-Frank/XmindMcp/discussions)

**🎉 现在就开始您的XMind MCP之旅吧！**