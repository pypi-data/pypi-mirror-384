#!/bin/bash

# 一键部署脚本 - 最简单的命令
# 用法：./one-click-deploy.sh

echo "🚀 一键启动 Agent Chat UI + Agent 服务..."

# 切换到项目根目录（如果脚本不在根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 执行部署脚本
./deploy.sh
