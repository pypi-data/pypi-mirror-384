# 重定向功能使用说明

## 功能概述

现在系统会启动两个服务：
1. **主服务**：LangGraph API 服务器（端口 8001）
2. **重定向服务**：简单的 HTTP 重定向服务器（端口 9001）

## 使用方法

### 1. 启动服务

```bash
orcaagent chat --config examples/graph_chat_bot/orcaagent_redirect_test.json
```

### 2. 访问重定向服务

访问 `http://127.0.0.1:9001` 会自动重定向到：
```
https://agentchat.vercel.app/?apiUrl=http%3A//127.0.0.1%3A8001&assistantId=chatbot
```

### 3. 测试重定向功能

```bash
python test_redirect.py http://127.0.0.1:9001 https://agentchat.vercel.app
```

## 配置说明

在 `orcaagent.json` 中配置：

```json
{
  "ui_config": {
    "frontend_url": "https://agentchat.vercel.app"
  }
}
```

## 工作原理

1. **启动重定向服务器**：在端口 `主端口 + 1000` 启动一个简单的 HTTP 服务器
2. **处理重定向**：当访问根路径 `/` 时，返回 302 重定向响应
3. **传递参数**：重定向 URL 包含 `apiUrl` 和 `assistantId` 参数

## 调试信息

启动时会显示：
```
🔍 调试信息:
   - 基础 UI URL: https://agentchat.vercel.app
   - 重定向目标: https://agentchat.vercel.app/?apiUrl=http%3A//127.0.0.1%3A8001&assistantId=chatbot
   - Graph ID: chatbot
   - Port: 8001

✅ 已设置重定向环境变量: https://agentchat.vercel.app/?apiUrl=http%3A//127.0.0.1%3A8001&assistantId=chatbot
🔄 启动重定向服务器在端口 9001
🌐 重定向服务器已启动: http://127.0.0.1:9001 -> https://agentchat.vercel.app/?apiUrl=http%3A//127.0.0.1%3A8001&assistantId=chatbot

✅ 后端服务已就绪。
🔄 重定向服务器: http://127.0.0.1:9001
🎯 重定向目标: https://agentchat.vercel.app/?apiUrl=http%3A//127.0.0.1%3A8001&assistantId=chatbot
💡 访问 http://127.0.0.1:9001 会自动重定向到前端
```

## 故障排除

如果重定向不工作：

1. **检查端口**：确保重定向端口没有被占用
2. **检查网络**：确保能访问目标前端 URL
3. **查看日志**：检查是否有错误信息
4. **手动测试**：使用 curl 或浏览器测试重定向

```bash
curl -I http://127.0.0.1:9001
```

应该返回：
```
HTTP/1.0 302 Found
Location: https://agentchat.vercel.app/?apiUrl=http%3A//127.0.0.1%3A8001&assistantId=chatbot
```
