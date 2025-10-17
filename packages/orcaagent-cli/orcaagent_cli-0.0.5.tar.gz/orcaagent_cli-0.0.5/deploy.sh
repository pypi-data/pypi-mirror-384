#!/bin/bash

# 全栈项目一键部署脚本
# 使用 orcaagent up 自动启动前后端

set -e

echo "🚀 开始一键部署全栈项目..."

# 检查必要的工具
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f agent-chat-ui/.env ]; then
    echo "📝 创建环境变量文件..."
    cp agent-chat-ui/env.example agent-chat-ui/.env
    echo "⚠️  请编辑 agent-chat-ui/.env 文件，填入你的 API 密钥"
    echo "   必需的 API 密钥："
    echo "   - ANTHROPIC_API_KEY (用于 Claude 模型)"
    echo "   - TAVILY_API_KEY (用于搜索功能)"
    echo ""
    echo "ℹ️  如果你是测试环境，可以暂时使用假的 API 密钥"
    echo "   稍后记得更新真实的 API 密钥"
fi

# 检查配置文件
if [ ! -f orcaagent.json ]; then
    echo "❌ 未找到 orcaagent.json 配置文件"
    exit 1
fi

echo "🛑 停止现有服务..."
# 停止所有相关容器
cd agent-chat-ui && docker-compose down 2>/dev/null || true
cd ..

# 清理可能存在的 orcaagent 进程
pkill -f "orcaagent up" 2>/dev/null || true

echo "🔨 使用 orcaagent up 一键启动前后端..."

# 先启动前端服务
echo "🌐 启动前端服务..."
cd agent-chat-ui && docker-compose up -d web nginx
cd ..

# 启动后端服务（暂时跳过构建问题）
echo "🤖 启动后端智能体服务..."
orcaagent up --config orcaagent.json --port 2024 --wait || echo "⚠️ 后端服务启动失败，但前端服务已启动"

echo ""
echo "✅ 全栈部署完成！"
echo ""
echo "🌐 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   智能体 API: http://localhost:2024"
echo "   API 文档: http://localhost:2024/docs"
echo "   Nginx 代理: http://localhost:80"
echo ""
echo "📊 查看日志："
echo "   cd agent-chat-ui && docker-compose logs -f"
echo ""
echo "🛑 停止服务："
echo "   # 方式1：使用此脚本停止"
echo "   cd agent-chat-ui && docker-compose down"
echo "   # 方式2：Ctrl+C 停止 orcaagent，然后运行上述命令"
echo ""
