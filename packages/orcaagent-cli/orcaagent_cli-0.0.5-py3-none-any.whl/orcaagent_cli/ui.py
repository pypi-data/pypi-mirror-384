"""Frontend UI management module for OrcaAgent CLI."""

import asyncio
import json
import multiprocessing
import os
import pathlib
import shutil
import signal
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

import click
from dotenv import dotenv_values


class UIManager:
    """管理前端UI进程的类"""

    def __init__(self, ui_path: pathlib.Path, port: int = 3000):
        self.ui_path = ui_path
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.web_path = ui_path / "agent-chat-app" / "apps" / "web"
        self.api_path = ui_path / "agent-chat-app" / "apps" / "agents"

    def _find_free_port(self, start_port: int) -> int:
        """找到一个空闲的端口"""
        port = start_port
        while port < start_port + 100:  # 最多尝试100个端口
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(("", port))
                    return port
                except OSError:
                    port += 1
        raise RuntimeError(f"无法找到空闲端口 (尝试范围: {start_port}-{start_port + 99})")

    def _check_port_available(self, port: int) -> bool:
        """检查指定端口是否可用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("", port))
                return True
            except OSError:
                return False

    def _create_env_file(self, backend_url: str, assistant_id: str, langsmith_api_key: str = "") -> None:
        """创建前端环境配置文件（生产环境配置）"""
        # 根据官方指导配置生产环境变量
        env_content = f"""# 前端环境配置 (由OrcaAgent CLI自动生成)
# 生产环境配置 - API Passthrough模式
NEXT_PUBLIC_API_URL=http://localhost:3000/api
LANGGRAPH_API_URL={backend_url}
NODE_ENV=development
"""

        # 如果提供了LangSmith API密钥，添加到环境变量中
        if langsmith_api_key:
            env_content += f"LANGSMITH_API_KEY={langsmith_api_key}\n"

        env_file = self.web_path / ".env.local"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)

        click.secho(f"✅ 创建前端环境配置: {env_file}", fg="green")

        # 显示配置信息
        click.secho("📋 生产环境配置:", fg="blue")
        click.secho(f"   前端API代理: http://localhost:3000/api", fg="cyan")
        click.secho(f"   后端服务地址: {backend_url}", fg="cyan")
        click.secho("   ⚠️ 注意: assistantId通过localStorage传递，不在环境变量中", fg="yellow")

    def _check_dependencies(self) -> bool:
        """检查前端依赖是否已安装"""
        node_modules = self.web_path / "node_modules"
        package_json = self.web_path / "package.json"

        if not package_json.exists():
            click.secho(f"❌ 前端项目不完整: {self.web_path}", fg="red")
            return False

        if not node_modules.exists():
            click.secho("📦 安装前端依赖...", fg="yellow")
            try:
                # 检测可用的包管理器，优先使用项目指定的包管理器
                package_manager = self._detect_package_manager()

                # 需要在项目根目录安装依赖，因为有workspace配置
                project_root = self.ui_path / "agent-chat-app"

                result = subprocess.run(
                    [package_manager, "install"],
                    cwd=project_root,  # 在项目根目录安装依赖
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode != 0:
                    click.secho(f"❌ 前端依赖安装失败: {result.stderr}", fg="red")
                    return False
                click.secho(f"✅ 前端依赖安装完成 (使用{package_manager})", fg="green")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                click.secho(f"❌ 前端依赖安装失败: {e}", fg="red")
                return False

        return True

    def _show_port_info(self, port: int) -> None:
        """显示端口占用信息"""
        try:
            import psutil
            import socket as sock_module

            # 查找占用端口的进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    for conn in proc.connections():
                        if conn.laddr and conn.laddr.port == port:
                            click.secho(f"   进程PID: {proc.info['pid']}", fg="yellow")
                            click.secho(f"   进程名: {proc.info['name']}", fg="yellow")
                            if proc.info['cmdline']:
                                click.secho(f"   命令行: {' '.join(proc.info['cmdline'])}", fg="yellow")
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            click.secho("   (安装psutil可查看更多进程信息: pip install psutil)", fg="yellow")

    def _detect_package_manager(self) -> str:
        """检测可用的包管理器，优先使用项目指定的包管理器"""
        # 检查根项目的packageManager字段
        root_package_json = self.ui_path / "agent-chat-app" / "package.json"
        if root_package_json.exists():
            try:
                import json
                with open(root_package_json, 'r') as f:
                    package_data = json.load(f)
                    if "packageManager" in package_data:
                        specified_manager = package_data["packageManager"].split("@")[0]
                        if self._is_package_manager_available(specified_manager):
                            click.secho(f"📋 使用项目指定的包管理器: {specified_manager}", fg="blue")
                            return specified_manager
            except (json.JSONDecodeError, KeyError):
                pass

        # 检测可用的包管理器，按优先级排序
        managers = ["npm", "pnpm", "yarn"]
        for manager in managers:
            if self._is_package_manager_available(manager):
                click.secho(f"📋 使用检测到的包管理器: {manager}", fg="blue")
                return manager

        # 如果都没有，返回npm作为默认选项
        click.secho("⚠️ 未检测到任何包管理器，使用npm作为默认选项", fg="yellow")
        return "npm"

    def _is_package_manager_available(self, manager: str) -> bool:
        """检查指定的包管理器是否可用"""
        try:
            result = subprocess.run(
                [manager, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _wait_for_service_with_logging(self, url: str, timeout: float = 120.0) -> bool:
        """等待前端服务启动完成（带日志记录）"""
        import requests
        import threading

        click.secho(f"📡 等待前端服务就绪: {url}", fg="blue")
        click.secho(f"⏰ 超时时间: {timeout}秒", fg="blue")

        deadline = time.time() + timeout
        last_log_time = 0

        while time.time() < deadline:
            try:
                response = requests.get(url, timeout=2.0)
                if response.status_code < 500:
                    click.secho("✅ 前端服务响应正常!", fg="green")
                    return True
            except requests.RequestException as e:
                current_time = time.time()
                # 每5秒显示一次日志，避免刷屏
                if current_time - last_log_time > 5:
                    elapsed = current_time - (deadline - timeout)
                    remaining = timeout - elapsed
                    click.secho(f"⏳ 等待中... 已等待 {elapsed:.1f}秒，剩余 {remaining:.1f}秒", fg="yellow")
                    last_log_time = current_time
                time.sleep(0.5)
                continue

        click.secho(f"❌ 前端服务启动超时 ({timeout}秒)", fg="red")
        return False

    def _wait_for_service_with_realtime_logging(self, url: str, timeout: float = 180.0) -> bool:
        """等待前端服务启动完成（实时显示日志）"""
        import requests
        import threading
        import queue

        click.secho(f"📡 等待前端服务就绪: {url}", fg="blue")
        click.secho(f"⏰ 超时时间: {timeout}秒", fg="blue")
        click.secho("📜 实时日志:", fg="cyan")

        deadline = time.time() + timeout
        log_queue = queue.Queue()

        def log_reader():
            """读取进程输出并放入队列"""
            while self.process and self.process.poll() is None:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        log_queue.put(line.strip())

        # 启动日志读取线程
        log_thread = threading.Thread(target=log_reader, daemon=True)
        log_thread.start()

        try:
            while time.time() < deadline:
                # 显示实时日志
                while not log_queue.empty():
                    line = log_queue.get()
                    click.secho(f"  {line}", fg="white")

                try:
                    response = requests.get(url, timeout=2.0)
                    if response.status_code < 500:
                        click.secho("✅ 前端服务响应正常!", fg="green")
                        return True
                except requests.RequestException:
                    time.sleep(0.5)
                    continue

            click.secho(f"❌ 前端服务启动超时 ({timeout}秒)", fg="red")
            return False

        finally:
            # 显示剩余日志
            click.secho("📜 显示剩余日志:", fg="cyan")
            while not log_queue.empty():
                line = log_queue.get()
                click.secho(f"  {line}", fg="white")

    def _show_process_output(self) -> None:
        """显示前端进程的输出日志"""
        if self.process and self.process.stdout:
            click.secho("📄 前端进程输出日志:", fg="cyan")

            # 读取剩余的输出
            try:
                remaining_output = []
                while True:
                    line = self.process.stdout.readline()
                    if not line and self.process.poll() is not None:
                        break
                    if line:
                        remaining_output.append(line.strip())

                # 显示最后20行日志
                if remaining_output:
                    click.secho("最近的日志输出:", fg="yellow")
                    for line in remaining_output[-20:]:
                        click.secho(f"  {line}", fg="white")
                else:
                    click.secho("  (无日志输出)", fg="yellow")
            except Exception as e:
                click.secho(f"  读取日志时出错: {e}", fg="red")

    def _wait_for_service(self, url: str, timeout: float = 30.0) -> bool:
        """等待前端服务启动完成（检查主页）"""
        import requests

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                response = requests.get(url, timeout=1.0)
                if response.status_code < 500:
                    return True
            except requests.RequestException:
                time.sleep(0.5)
                continue
        return False

    def start(self, backend_url: str, assistant_id: str, langsmith_api_key: str = "", debug_ui: bool = False) -> bool:
        """启动前端UI服务（生产环境配置）"""
        click.secho("🚀 启动前端UI服务（生产模式）...", fg="green")

        # 检查依赖
        if not self._check_dependencies():
            return False

        # 创建生产环境配置（使用固定端口3000）
        self._create_env_file(backend_url, assistant_id, langsmith_api_key)

        try:
            # 启动前端服务（生产模式）
            # 根据官方指导，前端应该从端口3000开始查找可用端口，通过/api代理访问后端
            start_port = 3000  # 默认起始端口

            # 查找空闲端口
            try:
                frontend_port = self._find_free_port(start_port)
                if frontend_port != start_port:
                    click.secho(f"ℹ️ 端口 {start_port} 已被占用，使用端口 {frontend_port}", fg="yellow")
            except RuntimeError as e:
                click.secho(f"❌ {e}", fg="red")
                return False

            self.port = frontend_port  # 更新端口为找到的可用端口

            # 使用检测到的包管理器启动web应用
            package_manager = self._detect_package_manager()

            # 直接在web应用目录运行next dev命令
            if package_manager == "npm":
                # 对于npm，在web应用目录运行dev脚本，并传递端口参数
                cmd = ["npm", "run", "dev", "--", "--port", str(frontend_port), "--hostname", "127.0.0.1"]
            else:
                # 对于pnpm/yarn，在web应用目录运行dev脚本
                cmd = [package_manager, "run", "dev", "--", "--port", str(frontend_port), "--hostname", "127.0.0.1"]

            click.secho(f"📍 前端目录: {self.web_path}", fg="blue")
            click.secho(f"🚀 执行命令: {' '.join(cmd)}", fg="blue")
            click.secho(f"📋 前端将在端口 {frontend_port} 上运行，通过API代理(/api)连接到后端", fg="blue")

            if debug_ui:
                click.secho("🔍 调试模式: 显示实时启动日志", fg="cyan")
                click.secho("⏳ 启动中，请稍候...", fg="yellow")

            # 启动前端进程，捕获所有输出用于调试
            self.process = subprocess.Popen(
                cmd,
                cwd=self.web_path,  # 在web应用目录运行
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env={**os.environ, "NODE_ENV": "development"}
            )

            # 根据调试模式选择等待方式
            ui_url = f"http://127.0.0.1:{self.port}"
            if debug_ui:
                # 调试模式：显示实时日志并等待
                success = self._wait_for_service_with_realtime_logging(ui_url, timeout=180.0)
            else:
                # 普通模式：使用原有等待逻辑
                success = self._wait_for_service_with_logging(ui_url, timeout=120.0)

            if success:
                click.secho(f"✅ 前端UI服务启动成功: http://127.0.0.1:{frontend_port}", fg="green")
                return True
            else:
                click.secho("❌ 前端UI服务启动超时或失败", fg="red")
                if not debug_ui:
                    click.secho("💡 提示: 使用 --debug-ui 参数可查看详细启动日志", fg="yellow")
                click.secho("📋 前端服务日志:", fg="yellow")
                self._show_process_output()
                self.stop()
                return False

        except (OSError, subprocess.SubprocessError) as e:
            click.secho(f"❌ 前端UI服务启动失败: {e}", fg="red")
            click.secho("🔍 错误详情:", fg="red")
            import traceback
            click.secho(traceback.format_exc(), fg="red")
            return False

    def stop(self) -> None:
        """停止前端UI服务"""
        if self.process and self.process.poll() is None:
            click.secho("🛑 停止前端UI服务...", fg="yellow")
            try:
                # 先尝试优雅停止
                self.process.terminate()
                try:
                    self.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    # 强制停止
                    self.process.kill()
                    self.process.wait()

                click.secho("✅ 前端UI服务已停止", fg="green")
            except Exception as e:
                click.secho(f"⚠️ 停止前端UI服务时出错: {e}", fg="yellow")

    def is_running(self) -> bool:
        """检查前端服务是否在运行"""
        return self.process is not None and self.process.poll() is None


class ProcessManager:
    """多进程管理器"""

    def __init__(self):
        self.backend_process: Optional[multiprocessing.Process] = None
        self.frontend_manager: Optional[UIManager] = None
        self.ui_path: Optional[pathlib.Path] = None

    def _run_backend(self, host: str, port: int, selected_graph_id: str,
                    config_json: Dict, server_log_level: str) -> None:
        """后端进程运行函数"""
        try:
            from langgraph_api.cli import run_server
        except ImportError:
            click.secho("❌ langgraph-api包未安装，无法启动后端服务", fg="red")
            sys.exit(1)

        # 只启动指定的graph
        graphs = {selected_graph_id: config_json["graphs"][selected_graph_id]}

        # 设置环境变量
        os.environ["DATABASE_URI"] = "sqlite:///./langgraph.db"

        run_server(
            host,
            port,
            reload=False,  # 多进程模式下不需要热重载
            graphs=graphs,
            n_jobs_per_worker=None,
            open_browser=False,  # 由主进程控制浏览器打开
            debug_port=None,
            env=config_json.get("env"),
            store=config_json.get("store"),
            wait_for_client=False,
            auth=config_json.get("auth"),
            http=config_json.get("http"),
            ui=config_json.get("ui"),
            ui_config=config_json.get("ui_config"),
            studio_url=None,
            allow_blocking=False,
            tunnel=False,
            server_level=server_log_level,
        )

    def start_backend(self, host: str, port: int, selected_graph_id: str,
                     config_json: Dict, server_log_level: str) -> None:
        """启动后端进程"""
        click.secho(f"🧠 启动后端API服务: {host}:{port}", fg="green")

        self.backend_process = multiprocessing.Process(
            target=self._run_backend,
            args=(host, port, selected_graph_id, config_json, server_log_level),
            daemon=True,
        )

        self.backend_process.start()

        if not self.backend_process.is_alive():
            raise click.ClickException("后端进程启动失败，请检查依赖和配置。")

    def start_frontend(self, ui_path: pathlib.Path, backend_url: str,
                      assistant_id: str, port: int = 3000, langsmith_api_key: str = "", debug_ui: bool = False) -> bool:
        """启动前端服务（生产环境配置）"""
        self.ui_path = ui_path
        self.frontend_manager = UIManager(ui_path, port)
        return self.frontend_manager.start(backend_url, assistant_id, langsmith_api_key, debug_ui)

    def stop_all(self) -> None:
        """停止所有服务"""
        if self.frontend_manager:
            self.frontend_manager.stop()

        if self.backend_process and self.backend_process.is_alive():
            click.secho("🛑 停止后端API服务...", fg="yellow")
            self.backend_process.terminate()
            self.backend_process.join(timeout=5.0)
            if self.backend_process.is_alive():
                self.backend_process.kill()
            click.secho("✅ 后端API服务已停止", fg="green")

    def wait_for_backend_ready(self, backend_url: str, timeout: float = 30.0) -> bool:
        """等待后端服务就绪"""
        import requests

        deadline = time.time() + timeout
        check_paths = ["/health", "/.well-known/ready", "/"]

        while time.time() < deadline:
            for path in check_paths:
                try:
                    response = requests.get(f"{backend_url}{path}", timeout=1.0)
                    if response.status_code < 500:
                        click.secho("✅ 后端服务已就绪", fg="green")
                        return True
                except requests.RequestException:
                    continue
            time.sleep(0.5)

        click.secho("⚠️ 未能在预期时间内确认后端可用", fg="yellow")
        return False


def find_ui_path() -> Optional[pathlib.Path]:
    """查找前端UI项目路径"""
    current_dir = pathlib.Path.cwd()

    # 优先查找同级目录下的agent-chat-ui
    ui_path = current_dir / "agent-chat-ui"
    if ui_path.exists() and (ui_path / "agent-chat-app").exists():
        return ui_path

    # 在上级目录中查找
    parent_ui_path = current_dir.parent / "agent-chat-ui"
    if parent_ui_path.exists() and (parent_ui_path / "agent-chat-app").exists():
        return parent_ui_path

    return None


def setup_signal_handlers(process_manager: ProcessManager) -> None:
    """设置信号处理器"""

    def signal_handler(signum, frame):
        click.secho(f"\n🛑 收到信号 {signum}，正在停止服务...", fg="yellow")
        process_manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
