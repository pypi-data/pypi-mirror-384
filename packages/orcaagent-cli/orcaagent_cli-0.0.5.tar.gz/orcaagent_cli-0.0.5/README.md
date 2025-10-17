# OrcaAgent CLI

OrcaAgent 官方命令行工具，提供创建、开发和部署 OrcaAgent 应用程序的全套功能。

## 安装

### 1. 通过命令行直接安装
```bash
pip install orcaagent-cli 
```


## 命令

### `orcaagent new` 🌱
从模板创建一个全新的OrcaAgent应用程序
```bash
orcaagent new 
```
#### 示例

1. 在当前目录下命令行输入orcaagent new
```bash
orcaagent new 
```
命令行会显示
```bash
📂 请指定应用程序的创建路径。 [.]: 
```
2. 定义应用程序路径
```bash
#比如定义在当前目录下创建一个名为test-project的应用程序
test-project
```
命令行会显示
```bash
🎉 成功获取 2 个模板配置
1. new-langgraph-project - 一个基础的、使用 ReAct 框架的单智能体。
2. ReAct Agent - 一个基础的、使用 ReAct 框架的单智能体。
请输入你想选的模板 (默认 1): 1

```
3. 选择一个可用模板
```bash
#比如选择1
1
```
最后，在你当前目录下会生成一个名为test-project的基于Langgraph chatbot应用程序子目录
## 🚀 一键启动前后端

### 多进程启动开发环境

使用 `--with-ui` 参数可以同时启动前端UI和后端API，实现真正的"一键启动前后端"：

```bash
# 启动开发环境（前后端一起启动）
orcaagent dev --with-ui

# 指定端口
orcaagent dev --with-ui --port 8000 --ui-port 3001

# 启动聊天环境（前后端一起启动）
orcaagent chat --with-ui --config orcaagent.json
```

### 特性优势

- ✅ **真正的并行启动**: 前端和后端服务同时启动，无等待时间
- ✅ **生产环境就绪**: 符合agent-chat-ui官方生产部署指导
- ✅ **API代理支持**: 使用API Passthrough模式确保安全性
- ✅ **智能端口分配**: 自动检测和分配可用端口，避免冲突
- ✅ **热重载支持**: 前端热重载独立工作，不影响后端
- ✅ **优雅关闭**: Ctrl+C 统一停止所有服务
- ✅ **自动浏览器打开**: 启动完成后自动打开聊天界面
- ✅ **URL参数隐藏**: 通过中间页面避免敏感参数显示在浏览器地址栏
- ✅ **错误隔离**: 前端错误不会影响后端，反之亦然

### 使用场景

**开发模式** (`orcaagent dev --with-ui`):
- 适合日常开发，需要热重载功能
- 前端和后端独立调试和开发
- 完整的开发体验和错误隔离

**聊天模式** (`orcaagent chat --with-ui`):
- 适合演示和测试场景
- 快速启动完整的聊天应用
- 一键启动后即可与AI助手对话

### 环境配置

在使用 `--with-ui` 模式时，请确保设置以下环境变量：

```bash
# LangSmith API密钥（用于生产环境认证）
export LANGSMITH_API_KEY="your-langsmith-api-key"
```

如果不设置此环境变量，前端将无法通过API代理访问后端服务。

### API代理机制

前端应用采用API代理模式来与后端服务通信：

**API代理地址：** `http://localhost:3000/api`
**后端服务地址：** `http://localhost:2024`

**工作原理：**
1. 前端发送请求到：`http://localhost:3000/api/threads`
2. API代理转发请求到：`http://localhost:2024/threads`
3. 后端处理并返回响应
4. API代理将响应返回给前端

**优势：**
- 🔒 **安全性**：前端无需直接知道后端地址
- 🌐 **跨域解决**：避免CORS问题
- 🔑 **认证处理**：统一处理认证和授权
- ⚖️ **负载均衡**：便于扩展和路由控制

**环境变量配置：**
- `NEXT_PUBLIC_API_URL=http://localhost:3000/api` （前端API代理地址）
- `LANGGRAPH_API_URL=http://localhost:2024` （后端服务地址）
- `LANGSMITH_API_KEY=your-key` （认证密钥）

### URL参数隐藏

为了提升安全性和用户体验，前端配置参数不再显示在浏览器地址栏中：

**原来的方式（显示参数）：**
```
http://localhost:3000?apiUrl=http://localhost:2024&assistantId=agent
```

**现在的方式（隐藏参数）：**
```
http://localhost:3000/chat
```

参数通过以下方式安全传递：
1. **直接访问**：浏览器直接访问带参数的根路径 `/?apiUrl=...&assistantId=...`
2. **参数处理**：根页面自动读取URL参数并存储到 `localStorage`
3. **界面跳转**：自动跳转到聊天页面 `/chat` 或显示配置表单
4. **配置读取**：前端应用从 `localStorage` 读取配置参数

这样既保证了功能正常，又避免了敏感信息在URL中的暴露。

### 路由结构

前端应用采用以下路由结构：
- **`/`** - 配置页面：显示参数配置表单，支持手动设置和自动跳转
- **`/chat`** - 聊天界面：显示完整的聊天应用界面

用户可以：
- 直接访问 `http://localhost:3000` 进入配置页面
- 配置完成后点击"启动聊天"按钮跳转到聊天界面
- 或者通过参数自动跳转：`/?apiUrl=...&assistantId=...` → 自动跳转到 `/chat`

### 故障排除

#### 前端启动问题

如果前端服务启动失败，请尝试以下解决方案：

1. **包管理器兼容性**
   ```bash
   # 手动安装依赖（如果自动检测失败）
   cd agent-chat-ui/agent-chat-app/apps/web
   npm install
   ```

2. **端口冲突**
   ```bash
   # 检查端口3000是否被占用
   lsof -i :3000

   # 释放端口（如果需要）
   kill -9 <PID>
   ```

3. **调试模式启动**
   ```bash
   # 使用调试模式查看详细启动日志
   orcaagent dev --with-ui --debug-ui
   ```

4. **手动启动前端**
   ```bash
   # 如果CLI启动仍有问题，可以手动启动前端
   cd agent-chat-ui/agent-chat-app/apps/web
   npm run dev -- --port 3000 --hostname 127.0.0.1
   ```

### `orcaagent dev` 🏃‍♀️
在开发模式下运行LangGraph API server，并启用热重载
```bash
orcaagent dev [OPTIONS]
  --with-ui                  同时启动前端UI服务，实现一键启动前后端
  --ui-port INTEGER          前端UI服务端口号 (default: 3000)
  --debug-ui                 显示前端UI服务的详细启动日志，用于调试问题
  --host TEXT                调试host (default: 127.0.0.1)
  --port INTEGER             调试port (default: 2024)
  --no-reload                禁止热重载
  --debug-port INTEGER       允许远程调试
  --no-browser               跳过浏览器打开
  -c, --config FILE          配置文件路径 (default: orcaagent.json)
```
#### 示例

  ##### 1.进入要运行的项目目录下 eg.examples/graph_chat_bot 
  ##### 2.创建虚拟环境并激活
  ##### 3.运行orcaagent命令
   ```bash
      cd examples/graph_chat_bot
      uv venv
      source .venv/bin/activate
      pip install -e "langgraph-cli[inmem]"
      orcaagent dev
   ```

### `orcaagent up` 🚀
在Docker中运行Langgraph API server
```bash
orcaagent up [OPTIONS]
  -p, --port INTEGER        要暴露的端口号 (default: 8123)
  --wait                    等待服务启动
  --watch                   文件变化时重启
  --verbose                 显示详细日志
  -c, --config FILE         配置文件路径
  -d, --docker-compose      额外服务文件
```

### `orcaagent build`
为你的OrcaAgent应用程序构建一个Docker镜像

```bash
orcaagent build -t IMAGE_TAG [OPTIONS]
  --platform TEXT         目标平台 (e.g., linux/amd64,linux/arm64)
  --pull / --no-pull      使用最新/本地基础镜像
  -c, --config FILE       配置文件路径
```

### `orcaagent dockerfile`

自定义部署的Dockerfile生成
```bash
orcaagent dockerfile SAVE_PATH [OPTIONS]
  -c, --config FILE       配置文件路径
```




## License

MIT


