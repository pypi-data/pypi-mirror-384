# 🚀 全栈项目部署指南

本项目支持两种部署方式：
1. **统一部署**（推荐）- 使用 `orcaagent up` 部署整个全栈应用
2. **分别部署** - 单独部署前端和后端

## 方法一：统一部署（推荐）

使用统一的部署脚本，一键部署前后端：

```bash
# 配置环境变量
cp agent-chat-ui/env.example agent-chat-ui/.env
# 编辑 .env 文件，填入你的 API 密钥

# 一键部署
./deploy.sh
```

### 部署脚本功能

- ✅ 自动检查 Docker 和 Docker Compose
- ✅ 自动创建环境变量文件（首次部署）
- ✅ 使用 `orcaagent up` 部署后端服务
- ✅ 自动启动前端服务和 Nginx 代理
- ✅ 健康检查和服务状态验证

### 访问地址

部署完成后，你可以通过以下地址访问服务：

- 🌐 **前端界面**: http://localhost:3000
- 🔗 **智能体 API**: http://localhost:2024
- 📚 **API 文档**: http://localhost:2024/docs
- 🌐 **Nginx 代理**: http://localhost:80

## 方法二：分别部署

### 部署后端

```bash
# 使用 orcaagent 部署后端
orcaagent up --config orcaagent.json --port 2024
```

### 部署前端

```bash
cd agent-chat-ui

# 安装依赖
npm install

# 构建镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

## 环境变量配置

在 `agent-chat-ui/.env` 文件中配置以下变量：

```env
# 必需的 API 密钥
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# 可选的 API 密钥
OPENAI_API_KEY=your_openai_api_key_here

# 生产环境配置
NODE_ENV=production

# 服务端口
WEB_PORT=3000
AGENTS_PORT=2024

# 域名配置（如果使用自定义域名）
DOMAIN=your-domain.com
```

## 查看日志

```bash
cd agent-chat-ui
docker-compose logs -f
```

## 停止服务

```bash
cd agent-chat-ui
docker-compose down
```

## 故障排除

### 前端页面空白
1. 检查浏览器控制台是否有错误
2. 确认后端 API 服务正在运行：`curl http://localhost:2024/info`
3. 检查环境变量是否正确配置

### API 调用失败
1. 检查后端服务日志：`docker-compose logs agents`
2. 确认 API 密钥配置正确
3. 检查网络连接和防火墙设置

### Docker 相关问题
1. 清理 Docker 缓存：`docker system prune -a`
2. 重启 Docker 服务
3. 检查磁盘空间是否充足

## 项目结构

```
orcaagent-cli/              # 项目根目录
├── orcaagent.json         # 统一配置文件
├── deploy.sh              # 统一部署脚本
└── agent-chat-ui/         # 前端项目
    ├── docker-compose.yml  # 前端部署配置
    ├── Dockerfile.web     # 前端镜像构建
    ├── Dockerfile.agents  # 后端镜像构建
    └── .env              # 环境变量配置
```

## 开发环境部署

开发时可以使用以下命令：

```bash
# 开发模式部署前端
cd agent-chat-ui
npm run dev

# 在另一个终端部署后端
orcaagent up --config ../orcaagent.json --port 2024
```

这样前端会运行在 http://localhost:3000，后端 API 在 http://localhost:2024。
