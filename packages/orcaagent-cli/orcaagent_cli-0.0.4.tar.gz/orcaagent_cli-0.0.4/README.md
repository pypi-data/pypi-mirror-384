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
### `orcaagent dev` 🏃‍♀️
在开发模式下运行LangGraph API server，并启用热重载
```bash
orcaagent dev [OPTIONS]
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


