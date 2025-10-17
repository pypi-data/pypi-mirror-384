# 🚀 一键部署指南

现在你可以用一个简单的命令启动整个 Agent Chat UI + Agent 全栈项目！

## 🎯 最简单的方式

在项目根目录直接运行：

```bash
# 方式1：使用专用的一键脚本
./one-click-deploy.sh

# 方式2：使用主部署脚本
./deploy.sh
```

## ⚡ 快速开始

### 1. 首次使用 - 配置环境变量

```bash
# 编辑环境变量文件
nano agent-chat-ui/.env
# 或者
vim agent-chat-ui/.env
# 或者
code agent-chat-ui/.env
```

填入你的 API 密钥：
```env
ANTHROPIC_API_KEY=你的_anthropic_api_key
TAVILY_API_KEY=你的_tavily_api_key
# 可选
OPENAI_API_KEY=你的_openai_api_key
```

### 2. 一键启动

```bash
# 启动整个全栈项目
./one-click-deploy.sh
```

### 3. 访问应用

部署完成后，你可以通过以下地址访问：

- 🌐 **前端界面**: http://localhost:3000
- 🔗 **智能体 API**: http://localhost:2024
- 📚 **API 文档**: http://localhost:2024/docs
- 🌐 **Nginx 代理**: http://localhost:80

## 🛠️ 工作原理

### 自动配置检测

脚本会自动：
1. ✅ 检查 Docker 和 Docker Compose 是否安装
2. ✅ 创建环境变量文件（如果不存在）
3. ✅ 验证配置文件是否存在
4. ✅ 停止之前的服务
5. ✅ 使用 `orcaagent up --config orcaagent.json --wait` 启动整个编排

### 智能编排启动

- **后端服务**: 通过 `orcaagent up` 自动构建和启动智能体服务
- **前端服务**: 通过 Docker Compose 启动 Next.js 应用和 Nginx 代理
- **网络通信**: 前端通过 `NEXT_PUBLIC_API_URL=http://agents:2024` 与后端通信

## 🛑 停止服务

```bash
# 停止所有服务
cd agent-chat-ui && docker-compose down
```

## 📊 查看日志

```bash
# 查看所有服务日志
cd agent-chat-ui && docker-compose logs -f

# 查看特定服务日志
cd agent-chat-ui && docker-compose logs -f web
cd agent-chat-ui && docker-compose logs -f agents
cd agent-chat-ui && docker-compose logs -f nginx
```

## 🔧 故障排除

### 如果前端无法访问后端

检查环境变量配置：
```bash
# 查看当前环境变量
cd agent-chat-ui && cat .env
```

确保 `NEXT_PUBLIC_API_URL` 指向正确的后端地址。

### 如果服务启动失败

1. **检查端口占用**:
   ```bash
   lsof -i :3000
   lsof -i :2024
   ```

2. **清理 Docker 缓存**:
   ```bash
   docker system prune -af
   ```

3. **查看详细日志**:
   ```bash
   cd agent-chat-ui && docker-compose logs -f --tail=100
   ```

### 如果需要重新配置

```bash
# 重新生成环境变量文件
rm agent-chat-ui/.env
./one-click-deploy.sh
```

## 🎨 自定义配置

如果你需要修改部署配置：

1. **修改环境变量**: 编辑 `agent-chat-ui/.env`
2. **修改 Docker 配置**: 编辑 `agent-chat-ui/docker-compose.yml`
3. **修改智能体配置**: 编辑 `orcaagent.json`

## ✨ 高级用法

### 开发模式

如果你想分别启动服务进行开发：

```bash
# 终端1：启动后端
orcaagent up --config orcaagent.json --port 2024

# 终端2：启动前端（开发模式）
cd agent-chat-ui && npm run dev
```

### 生产部署

```bash
# 生产模式部署
NODE_ENV=production ./one-click-deploy.sh
```

## 📝 技术细节

- **后端**: 使用 `orcaagent up` 自动构建和部署 LangGraph API 服务器
- **前端**: 使用 Docker Compose 构建和部署 Next.js 应用
- **代理**: Nginx 作为反向代理提供统一访问入口
- **通信**: 前后端通过 Docker 网络内部通信，无需暴露过多端口

## 🎯 下一步

1. ✅ 配置你的 API 密钥
2. ✅ 运行 `./one-click-deploy.sh`
3. ✅ 在浏览器中访问 http://localhost:3000
4. 🚀 开始使用你的 Agent Chat UI！

享受一键部署的便利吧！🎉
