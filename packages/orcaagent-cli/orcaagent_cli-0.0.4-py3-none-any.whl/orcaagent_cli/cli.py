"""OrcaAgent CLI commands."""

import multiprocessing
import os
import pathlib
import shutil
import sys
import time
import webbrowser
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Callable, Optional

import click
import click.exceptions
from click import secho

import orcaagent_cli.config
import orcaagent_cli.docker
import requests
from dotenv import dotenv_values
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from orcaagent_cli.analytics import log_command
from orcaagent_cli.config import Config
from orcaagent_cli.constants import (
    DEFAULT_CHAT_PORT,
    DEFAULT_CHAT_UI_URL,
    DEFAULT_CONFIG,
    DEFAULT_PORT,
)
from orcaagent_cli.docker import DockerCapabilities
from orcaagent_cli.exec import Runner, subp_exec
from orcaagent_cli.progress import Progress
from orcaagent_cli.templates import create_new
from orcaagent_cli.util import warn_non_wolfi_distro
from orcaagent_cli.version import __version__
from orcaagent_cli.templates import _get_templates_list

OPT_DOCKER_COMPOSE = click.option(
    "--docker-compose",
    "-d",
    help="进阶:指向包含额外服务配置的docker-compose.yml文件的路径。",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
)
OPT_CONFIG = click.option(
    "--config",
    "-c",
    help="""配置文件路径，用于声明依赖项(dependencies)、图结构(graphs)和环境变量。

    \b
     配置文件必须为JSON格式,包含以下键值：
    - "dependencies": OrcaAgent API服务器的依赖项数组。依赖项可为以下形式之一:
      - ".":搜索本地Python包,以及应用程序目录中的pyproject.toml、setup.py或requirements.txt文件
      - "./local_package"
      - "<package_name>"
    - "graphs": 图ID到编译图定义路径的映射,格式为 ./your_package/your_file.py:variable,其中
        "variable" 是 langgraph.graph.graph.CompiledGraph 的实例
    - "env": (可选) .env文件路径或环境变量与其值的映射
    - "python_version": (可选) 3.11、3.12或3.13。默认为3.11
    - "pip_config_file":(可选)指向 pip 配置文件的路径
    - "dockerfile_lines":(可选)在从父镜像导入后添加到 Dockerfile 的额外行数组

    \b
    例子:
        orcaagent up -c orcaagent.json

    \b
    例子:
    {
        "dependencies": [
            "langchain_openai",
            "./your_package"
        ],
        "graphs": {
            "my_graph_id": "./your_package/your_file.py:variable"
        },
        "env": "./.env"
    }

    \b
    例子:
    {
        "python_version": "3.11",
        "dependencies": [
            "langchain_openai",
            "."
        ],
        "graphs": {
            "my_graph_id": "./your_package/your_file.py:variable"
        },
        "env": {
            "OPENAI_API_KEY": "secret-key"
        }
    }

    Defaults to looking for orcaagent.json or langgraph.json in the current directory.""",
    default=DEFAULT_CONFIG,
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
)
OPT_PORT = click.option(
    "--port",
    "-p",
    type=int,
    default=DEFAULT_PORT,
    show_default=True,
    help="""
    暴露的端口

    \b
    示例:
        orcaagent up --port 8000
    \b
    """,
)
OPT_RECREATE = click.option(
    "--recreate/--no-recreate",
    default=False,
    show_default=True,
    help="即使容器的配置和镜像未发生变更，仍需重新创建容器",
)
OPT_PULL = click.option(
    "--pull/--no-pull",
    default=True,
    show_default=True,
    help="""
    拉取最新镜像。若需使用本地构建的镜像运行服务器，请使用 --no-pull 参数。

    \b
    示例:
        orcaagent up --no-pull
    \b
    """,
)
OPT_VERBOSE = click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="显示更多服务器日志输出",
)
OPT_WATCH = click.option("--watch", is_flag=True, help="文件更改后重新启动")
OPT_DEBUGGER_PORT = click.option(
    "--debugger-port",
    type=int,
    help="在本地拉取调试器镜像(debugger image)，并在指定端口提供用户界面服务",
)
OPT_DEBUGGER_BASE_URL = click.option(
    "--debugger-base-url",
    type=str,
    help="调试器访问OrcaAgent API所使用的URL。默认值为http://127.0.0.1:[PORT]",
)

OPT_POSTGRES_URI = click.option(
    "--postgres-uri",
    help="用于数据库的Postgres URI。默认启动本地数据库。",
)

OPT_API_VERSION = click.option(
    "--api-version",
    type=str,
    help="基础镜像使用的API服务器版本。若未指定,则使用最新版本。",
)

OPT_CHAT_HOST = click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Agent 后端监听的主机地址。",
)
OPT_CHAT_PORT = click.option(
    "--port",
    "-p",
    type=int,
    default=DEFAULT_CHAT_PORT,
    show_default=True,
    help="Agent 后端监听端口。",
)
OPT_CHAT_API_URL = click.option(
    "--api-url",
    type=str,
    help="直接指定供前端使用的 API 地址，默认根据 host/port 推导。",
)
OPT_CHAT_GRAPH = click.option(
    "--graph-id",
    "-g",
    type=str,
    help="指定要启动的 graph ID，不指定则使用配置中的第一个 graph。",
)
OPT_CHAT_UI_URL = click.option(
    "--ui-url",
    type=str,
    default=DEFAULT_CHAT_UI_URL,
    show_default=True,
    help="agent-chat-ui 的基础地址，可为本地或远程部署。",
)
OPT_CHAT_UI_PARAM = click.option(
    "--ui-param",
    type=str,
    default="apiUrl",
    show_default=True,
    help="前端用于接收后端地址的查询参数名。",
)
OPT_CHAT_WAIT = click.option(
    "--wait-timeout",
    type=float,
    default=30.0,
    show_default=True,
    help="等待后端启动成功的超时时间（秒）。",
)
OPT_CHAT_NO_BROWSER = click.option(
    "--no-browser",
    is_flag=True,
    help="不自动打开浏览器。",
)
OPT_SERVER_LOG_LEVEL = click.option(
    "--server-log-level",
    type=str,
    default="WARNING",
    help="设置API服务器的日志级别。",
)


@click.group()
@click.version_option(version=__version__, prog_name="ORCAAGENT CLI")
def cli():
    pass


@OPT_RECREATE
@OPT_PULL
@OPT_PORT
@OPT_DOCKER_COMPOSE
@OPT_CONFIG
@OPT_VERBOSE
@OPT_DEBUGGER_PORT
@OPT_DEBUGGER_BASE_URL
@OPT_WATCH
@OPT_POSTGRES_URI
@OPT_API_VERSION
@click.option(
    "--image",
    type=str,
    default=None,
    help="用于 langgraph-api 服务的 Docker 镜像。若指定此项，则跳过构建过程并直接使用该镜像。"
    "当您需要基于已通过 `orcaagent build` 构建的镜像进行测试时，此选项非常实用。",
)
@click.option(
    "--base-image",
    default=None,
    # help="用于 OrcaAgent API 服务器的基础镜像。通过版本标签固定到特定版本。默认使用 langchain/langgraph-api 或 langchain/langgraphjs-api。"
    # "\n\n    \b\n示例:\n    --base-image langchain/langgraph-server:0.2.18  # 固定到特定补丁版本\n    --base-image langchain/langgraph-server:0.2  # 固定到次要版本(Python)",
    help="用于 langgraph-api 服务器的基础镜像。通过版本标签固定到特定版本。默认使用 langchain/langgraph-api 或 langchain/langgraphjs-api。"
)
@click.option(
    "--wait",
    is_flag=True,
    help="请等待服务启动完毕后再返回。此操作隐含 --detach 参数效果。",
)
@cli.command(help="🚀 启动 OrcaAgent API server.")
@log_command
def up(
    config: pathlib.Path,
    docker_compose: Optional[pathlib.Path],
    port: int,
    recreate: bool,
    pull: bool,
    watch: bool,
    wait: bool,
    verbose: bool,
    debugger_port: Optional[int],
    debugger_base_url: Optional[str],
    postgres_uri: Optional[str],
    api_version: Optional[str],
    image: Optional[str],
    base_image: Optional[str],
):
    # 自动查找配置文件
    if config.name == DEFAULT_CONFIG and not config.exists():
        config_candidates = ["orcaagent.json", "langgraph.json"]
        for candidate in config_candidates:
            candidate_path = pathlib.Path(candidate)
            if candidate_path.exists():
                config = candidate_path
                break
        else:
            raise click.UsageError(
                f"未找到配置文件。请确保以下文件之一存在: {', '.join(config_candidates)}"
            )
    elif not config.exists():
        raise click.UsageError(f"配置文件不存在: {config}")

    click.secho("启动 LangGraph API 服务器...", fg="green")
    click.secho(
        """本地开发环境需设置环境变量 LANGSMITH_API_KEY 以访问 LangGraph 平台。
            生产环境需设置环境变量 LANGGRAPH_CLOUD_LICENSE_KEY 获取许可证密钥""",
        fg="yellow",
        err=True,
    )
    with Runner() as runner, Progress(message="Pulling...") as set:
        capabilities = orcaagent_cli.docker.check_capabilities(runner)
        args, stdin = prepare(
            runner,
            capabilities=capabilities,
            config_path=config,
            docker_compose=docker_compose,
            port=port,
            pull=pull,
            watch=watch,
            verbose=verbose,
            debugger_port=debugger_port,
            debugger_base_url=debugger_base_url,
            postgres_uri=postgres_uri,
            api_version=api_version,
            image=image,
            base_image=base_image,
        )
        
        # 获取第一个 graph 的 ID 作为 assistant_id
        config_json = orcaagent_cli.config.validate_config_file(config)
        if config_json is None:
            raise click.UsageError(f"配置文件验证失败: {config}")
        assistant_id = next(iter(config_json.get("graphs", {})), None)
        if assistant_id is None:
            raise click.UsageError("配置文件中未找到任何 graph")
        
        # add up + options
        args.extend(["up", "--remove-orphans"])
        if recreate:
            args.extend(["--force-recreate", "--renew-anon-volumes"])
            try:
                runner.run(subp_exec("docker", "volume", "rm", "langgraph-data"))
            except click.exceptions.Exit:
                pass
        if watch:
            args.append("--watch")
        if wait:
            args.append("--wait")
        else:
            args.append("--abort-on-container-exit")
        # run docker compose
        set("Building...")

        def on_stdout(line: str):
            if "unpacking to docker.io" in line:
                set("Starting...")
            elif "Application startup complete" in line:
                debugger_origin = (
                    f"http://localhost:{debugger_port}"
                    if debugger_port
                    else "https://smith.langchain.com"
                )
                debugger_base_url_query = (
                    debugger_base_url or f"http://127.0.0.1:{port}"
                )
                set("")
                sys.stdout.write(
                    f"""Ready!
- API: http://localhost:{port}
- Docs: http://localhost:{port}/docs
- LangGraph Studio: {debugger_origin}/studio/?baseUrl={debugger_base_url_query}
- Chat UI: https://agentchat.vercel.app/?apiUrl=http://localhost:{port}&assistantId={assistant_id}
"""
                )
                sys.stdout.flush()
                return True

        if capabilities.compose_type == "plugin":
            compose_cmd = ["docker", "compose"]
        elif capabilities.compose_type == "standalone":
            compose_cmd = ["docker-compose"]

        runner.run(
            subp_exec(
                *compose_cmd,
                *args,
                input=stdin,
                verbose=verbose,
                on_stdout=on_stdout,
            )
        )


def _build(
    runner,
    set: Callable[[str], None],
    config: pathlib.Path,
    config_json: dict,
    base_image: Optional[str],
    api_version: Optional[str],
    pull: bool,
    tag: str,
    passthrough: Sequence[str] = (),
    install_command: Optional[str] = None,
    build_command: Optional[str] = None,
):
    # pull latest images
    if pull:
        runner.run(
            subp_exec(
                "docker",
                "pull",
                orcaagent_cli.config.docker_tag(config_json, base_image, api_version),
                verbose=True,
            )
        )
    set("构建...")
    # apply options
    args = [
        "-f",
        "-",  # stdin
        "-t",
        tag,
    ]
    # determine build context: use current directory for JS projects, config parent for Python
    is_js_project = config_json.get("node_version") and not config_json.get(
        "python_version"
    )
    # build/install commands only apply to JS projects for now
    # without install/build command, JS projects will follow the old behavior
    if is_js_project and (build_command or install_command):
        build_context = str(pathlib.Path.cwd())
    else:
        build_context = str(config.parent)

    # apply config
    stdin, additional_contexts = orcaagent_cli.config.config_to_docker(
        config,
        config_json,
        base_image,
        api_version,
        install_command,
        build_command,
        build_context,
    )
    # add additional_contexts
    if additional_contexts:
        for k, v in additional_contexts.items():
            args.extend(["--build-context", f"{k}={v}"])
    runner.run(
        subp_exec(
            "docker",
            "build",
            *args,
            *passthrough,
            build_context,
            input=stdin,
            verbose=True,
        )
    )


@OPT_CONFIG
@OPT_PULL
@click.option(
    "--tag",
    "-t",
    help="""Docker镜像标签。

    \b
    示例:
        orcaagent build -t my-image

    \b
    """,
    required=True,
)
@click.option(
    "--base-image",
    help="用于OrcaAgent API服务器的基础镜像。通过版本标签固定到特定版本。默认使用langchain/orcaagent-api。"
    "\n\n    \b\n示例:\n    --base-image langchain/orcaagent-server:0.2.18  # 固定到特定补丁版本\n    --base-image langchain/orcaagent-server:0.2  # 固定到次要版本(Python)",
)
@OPT_API_VERSION
@click.option(
    "--install-command",
    help="自定义安装命令，需从构建上下文根目录运行。若未提供，则根据包管理器文件自动检测。",
)
@click.option(
    "--build-command",
    help="自定义构建命令，需在 orcaagent.json 目录下运行。若未提供，则使用默认构建流程。",
)
@click.argument("docker_build_args", nargs=-1, type=click.UNPROCESSED)
@cli.command(
    help="📦 构建OrcaAgent API服务器的Docker镜像。",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@log_command
def build(
    config: pathlib.Path,
    docker_build_args: Sequence[str],
    base_image: Optional[str],
    api_version: Optional[str],
    pull: bool,
    tag: str,
    install_command: Optional[str],
    build_command: Optional[str],
):
    # 自动查找配置文件
    if config.name == DEFAULT_CONFIG and not config.exists():
        config_candidates = ["orcaagent.json", "langgraph.json"]
        for candidate in config_candidates:
            candidate_path = pathlib.Path(candidate)
            if candidate_path.exists():
                config = candidate_path
                break
        else:
            raise click.UsageError(
                f"未找到配置文件。请确保以下文件之一存在: {', '.join(config_candidates)}"
            )
    elif not config.exists():
        raise click.UsageError(f"配置文件不存在: {config}")

    with Runner() as runner, Progress(message="拉取...") as set:
        if shutil.which("docker") is None:
            raise click.UsageError("Docker 未安装") from None
        config_json = orcaagent_cli.config.validate_config_file(config)
        if config_json is None:
            raise click.UsageError(f"配置文件验证失败: {config}")
        warn_non_wolfi_distro(config_json)
        _build(
            runner,
            set,
            config,
            config_json,
            base_image,
            api_version,
            pull,
            tag,
            docker_build_args,
            install_command,
            build_command,
        )


def _get_docker_ignore_content() -> str:
    """返回 .dockerignore 文件的内容。

    该文件用于将文件和目录排除在 Docker 构建上下文之外。

    虽然可能过于宽泛，但宁可谨慎也不要后悔。

    主要目标是默认排除 .env 文件。
    """
    return """\
# # 忽略 node_modules 及其他依赖目录
node_modules
bower_components
vendor

# 忽略日志和临时文件
*.log
*.tmp
*.swp

# 忽略 .env 文件及其他环境配置文件
.env
.env.*
*.local

# 忽略 git 相关文件
.git
.gitignore

# 忽略 Docker 相关文件及配置
.dockerignore
docker-compose.yml

# 忽略构建和缓存目录
dist
build
.cache
__pycache__

# 忽略IDE和编辑器配置
.vscode
.idea
*.sublime-project
*.sublime-workspace
.DS_Store  # macOS专属

# 忽略测试和覆盖率文件
coverage
*.coverage
*.test.js
*.spec.js
tests
"""


@OPT_CONFIG
@click.argument("save_path", type=click.Path(resolve_path=True))
@cli.command(
    help="🐳 为OrcaAgent API服务器生成一个包含Docker暴露Docker Compose选项的Dockerfile。"
)
@click.option(
    # Add a flag for adding a docker-compose.yml file as part of the output
    "--add-docker-compose",
    help=(
        "添加额外文件以运行 OrcaAgent API 服务器 "
        "docker-compose。这些文件包括一个 docker-compose.yml 文件、.env 文件， "
        "和一个 .dockerignore 文件。"
    ),
    is_flag=True,
)
@click.option(
    "--base-image",
        help="用于OrcaAgent API服务器的基础镜像。通过版本标签固定到特定版本。默认使用langchain/orcaagent-api。"
    "\n\n    \b\n示例:\n    --base-image langchain/orcaagent-server:0.2.18  # 固定到特定补丁版本\n    --base-image langchain/orcaagent-server:0.2  # 固定到次要版本(Python)",
)
@OPT_API_VERSION
@log_command
def dockerfile(
    save_path: str,
    config: pathlib.Path,
    add_docker_compose: bool,
    base_image: Optional[str] = None,
    api_version: Optional[str] = None,
) -> None:
    # 自动查找配置文件
    if config.name == DEFAULT_CONFIG and not config.exists():
        config_candidates = ["orcaagent.json", "langgraph.json"]
        for candidate in config_candidates:
            candidate_path = pathlib.Path(candidate)
            if candidate_path.exists():
                config = candidate_path
                break
        else:
            raise click.UsageError(
                f"未找到配置文件。请确保以下文件之一存在: {', '.join(config_candidates)}"
            )
    elif not config.exists():
        raise click.UsageError(f"配置文件不存在: {config}")

    save_path = pathlib.Path(save_path).absolute()
    secho(f"🔍 验证路径为 {config} 的配置", fg="yellow")
    config_json = orcaagent_cli.config.validate_config_file(config)
    if config_json is None:
        raise click.UsageError(f"配置文件验证失败: {config}")
    warn_non_wolfi_distro(config_json)
    secho("✅ 配置验证通过！", fg="green")

    secho(f"📝 在 {save_path} 生成 Dockerfile", fg="yellow")
    dockerfile, additional_contexts = orcaagent_cli.config.config_to_docker(
        config,
        config_json,
        base_image=base_image,
        api_version=api_version,
    )
    with open(str(save_path), "w", encoding="utf-8") as f:
        f.write(dockerfile)
    secho("✅ 创建:Dockerfile", fg="green")

    if additional_contexts:
        additional_contexts_str = ",".join(
            f"{k}={v}" for k, v in additional_contexts.items()
        )
        secho(
            f"""📝 使用这些额外的构建上下文运行 Docker build `--build-context {additional_contexts_str}`""",
            fg="yellow",
        )

    if add_docker_compose:
        # Add docker compose and related files
        # Add .dockerignore file in the same directory as the Dockerfile
        with open(str(save_path.parent / ".dockerignore"), "w", encoding="utf-8") as f:
            f.write(_get_docker_ignore_content())
        secho("✅ 创建: .dockerignore", fg="green")

        # Generate a docker-compose.yml file
        path = str(save_path.parent / "docker-compose.yml")
        with open(path, "w", encoding="utf-8") as f:
            with Runner() as runner:
                capabilities = orcaagent_cli.docker.check_capabilities(runner)

            compose_dict = orcaagent_cli.docker.compose_as_dict(
                capabilities,
                port=8123,
                base_image=base_image,
            )
            # Add .env file to the docker-compose.yml for the langgraph-api service
            compose_dict["services"]["langgraph-api"]["env_file"] = [".env"]
            # Add the Dockerfile to the build context
            compose_dict["services"]["langgraph-api"]["build"] = {
                "context": ".",
                "dockerfile": save_path.name,
            }
            # Add the base_image as build arg if provided
            if base_image:
                compose_dict["services"]["langgraph-api"]["build"]["args"] = {
                    "BASE_IMAGE": base_image
                }
            f.write(orcaagent_cli.docker.dict_to_yaml(compose_dict))
            secho("✅ 创建: docker-compose.yml", fg="green")

        # Check if the .env file exists in the same directory as the Dockerfile
        if not (save_path.parent / ".env").exists():
            # Also add an empty .env file
            with open(str(save_path.parent / ".env"), "w", encoding="utf-8") as f:
                f.writelines(
                    [
                        # 取消注释以下行以添加您的LangSmith API密钥",
                        "\n",
                        "# LANGSMITH_API_KEY=您的-API-密钥",
                        "\n",
                        "# 或如果您拥有LangGraph平台许可证密钥,"
                        "请取消注释以下行：",
                        "\n",
                        "# LANGGRAPH_CLOUD_LICENSE_KEY=您的许可证密钥",
                        "\n",
                        "# 其他环境变量请添加在下方...",
                    ]
                )

            secho("✅ 创建: .env", fg="green")
        else:
            # Do nothing since the .env file already exists. Not a great
            # idea to overwrite in case the user has added custom env vars set
            # in the .env file already.
            secho("➖ 跳过: .env. 已经存在!", fg="yellow")

    secho(
        f"🎉 所有文件已成功生成于路径 {save_path.parent}!",
        fg="cyan",
        bold=True,
    )


@click.option(
    "--host",
    default="127.0.0.1",
    help="用于绑定开发服务器的网络接口。出于安全考虑，建议使用默认值 127.0.0.1。仅在可信网络中使用 0.0.0.0。",
)
@click.option(
    "--port",
    default=2024,
    type=int,
    help="开发服务器绑定端口号。示例:orcaagent dev --port 8000",
)
@click.option(
    "--no-reload",
    is_flag=True,
    help="在检测到代码更改时禁用自动重新加载",
)
@click.option(
    "--config",
    type=str,
    default=None,
    help="配置文件的路径用于声明依赖关系(dependencies)、图结构(graphs)和环境变量。默认会依次查找 orcaagent.json 和 langgraph.json",
)
@click.option(
    "--n-jobs-per-worker",
    default=None,
    type=int,
    help="每个工作进程可处理的最大并发任务数。默认值:10",
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="跳过服务器启动时自动打开浏览器",
)
@click.option(
    "--debug-port",
    default=None,
    type=int,
    help="通过监听指定端口启用远程调试。需安装 debugpy 模块。",
)
@click.option(
    "--wait-for-client",
    is_flag=True,
    help="在启动服务器之前，请等待调试器客户端连接到调试端口。",
    default=False,
)
@click.option(
    "--studio-url",
    type=str,
    default=None,
    help="要连接的OrcaAgent Studio实例的URL. 默认 https://smith.langchain.com",
)
@click.option(
    "--allow-blocking",
    is_flag=True,
    help="请勿对代码中的同步 I/O 阻塞操作触发错误。",
    default=False,
)
@click.option(
    "--tunnel",
    is_flag=True,
    help="通过公共隧道(此处指Cloudflare)暴露本地服务器,以便在远程前端访问时避免浏览器或网络阻止本地连接。",
    default=False,
)
@OPT_SERVER_LOG_LEVEL
@OPT_CHAT_UI_URL
@OPT_CHAT_UI_PARAM
@cli.command(
    "dev",
    help="🏃‍♀️‍➡️ 以开发模式运行 OrcaAgent API 服务器，支持热重载和调试功能",
)
@log_command
def dev(
    host: str,
    port: int,
    no_reload: bool,
    config: str,
    ui_url: str,
    n_jobs_per_worker: Optional[int],
    no_browser: bool,
    debug_port: Optional[int],
    wait_for_client: bool,
    studio_url: Optional[str],
    allow_blocking: bool,
    tunnel: bool,
    server_log_level: str,
    ui_param: str,
    graph_id: Optional[str] = None,
):
    """CLI entrypoint for running the OrcaAgent API server."""
    try:
        from langgraph_api.cli import run_server  # type: ignore
    except ImportError:
        py_version_msg = ""
        if sys.version_info < (3, 11):
            py_version_msg = (
                "\n\n注意:in-mem server需要安装 Python 3.11 或更高版本。"
                f" 您当前使用的 Python {sys.version_info.major}.{sys.version_info.minor}."
                ' 请在安装"orcaagent-cli[inmem]"之前升级您的Python版本。'
            )
        try:
            from importlib import util

            if not util.find_spec("langgraph_api"):
                raise click.UsageError(
                    "所需包 'langgraph-api' 未安装.\n"
                    "请用以下命令安装:\n\n"
                    '    pip install -U "langgraph-cli[inmem]"'
                    f"{py_version_msg}"
                ) from None
        except ImportError:
            raise click.UsageError(
                "无法验证包安装。请确保 Python 已更新，并\n"
                "通过 'inmem' 扩展安装 langgraph-cli:pip install -U \"langgraph-cli[inmem]\""
                f"{py_version_msg}"
            ) from None
        raise click.UsageError(
            "无法导入 run_server。这很可能意味着您的安装不完整。"
            "请确保 langgraph-cli 是通过 'inmem' 附加选项安装的:pip install -U \"langgraph-cli[inmem]\""
            f"{py_version_msg}"
        ) from None

    # 自动查找配置文件
    if config is None:
        config_candidates = ["orcaagent.json", "langgraph.json"]
        for candidate in config_candidates:
            if pathlib.Path(candidate).exists():
                config = candidate
                break
        else:
            raise click.UsageError(
                f"未找到配置文件。请确保以下文件之一存在: {', '.join(config_candidates)}"
            )
    elif not pathlib.Path(config).exists():
        raise click.UsageError(f"配置文件不存在: {config}")

    config_json = orcaagent_cli.config.validate_config_file(pathlib.Path(config))
    if config_json is None:
        raise click.UsageError(f"配置文件验证失败: {config}")
    if config_json.get("node_version"):
        raise click.UsageError(
            "此版本的 OrcaAgent CLI 不支持用于 JS graphs的内存服务器。请改用 `npx @langchain/langgraph-cli`。"
        ) from None

    cwd = os.getcwd()
    sys.path.append(cwd)
    dependencies = config_json.get("dependencies", [])
    for dep in dependencies:
        dep_path = pathlib.Path(cwd) / dep
        if dep_path.is_dir() and dep_path.exists():
            sys.path.append(str(dep_path))

    graphs = config_json.get("graphs", {})
    selected_graph_id, graph_spec = _resolve_graph_entry(config_json, graph_id)
    
    # UI URL 优先级：命令行参数 > 配置文件 > 默认值
    if ui_url == DEFAULT_CHAT_UI_URL:
        # 命令行未指定 ui_url，尝试从配置读取
        ui_config = config_json.get("ui_config")
        if ui_config and isinstance(ui_config, dict):
            config_ui_url = ui_config.get("chat_ui_url")
            if config_ui_url:
                ui_url = config_ui_url
                secho(f"🔗 使用配置文件中的 UI URL: {ui_url}", fg="blue")
            else:
                secho(f"🔗 使用默认 UI URL: {ui_url}", fg="yellow")
        else:
            secho(f"🔗 使用默认 UI URL: {ui_url}", fg="yellow")
        # 如果配置文件中也没有设置，ui_url 保持为 DEFAULT_CHAT_UI_URL
    
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    agent_url = f"http://{display_host}:{port}"
    # 构建前端 URL
    parsed = urlparse(ui_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query[ui_param] = agent_url
    query["assistantId"] = selected_graph_id
    final_ui_url = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
    
    # 设置默认的DATABASE_URI环境变量（用于内存模式）
    if "DATABASE_URI" not in os.environ:
        os.environ["DATABASE_URI"] = "sqlite:///./langgraph.db"
    
    secho( f"🧠 正在启动 graph '{selected_graph_id}' ( {graph_spec} ) 于 {host}:{port}...")
    secho(f"🔗 Chat URL: {final_ui_url}", fg="green")
    run_server(
        host,
        port,
        not no_reload,
        graphs,
        n_jobs_per_worker=n_jobs_per_worker,
        open_browser=not no_browser,
        debug_port=debug_port,
        env=config_json.get("env"),
        store=config_json.get("store"),
        wait_for_client=wait_for_client,
        auth=config_json.get("auth"),
        http=config_json.get("http"),
        ui_config=config_json.get("ui_config"),
        studio_url=studio_url,
        allow_blocking=allow_blocking,
        tunnel=tunnel,
        server_level=server_log_level,
    )

@click.argument("template", required=False)
@click.argument("path", required=False)
@cli.command("new", help="🌱 从模板创建一个新的OrcaAgent项目")
@log_command
def new(path: Optional[str], template: Optional[str]) -> None:
    """Create a new OrcaAgent project from a template."""
    return create_new(path, template)


def prepare_args_and_stdin(
    *,
    capabilities: DockerCapabilities,
    config_path: pathlib.Path,
    config: Config,
    docker_compose: Optional[pathlib.Path],
    port: int,
    watch: bool,
    debugger_port: Optional[int] = None,
    debugger_base_url: Optional[str] = None,
    postgres_uri: Optional[str] = None,
    api_version: Optional[str] = None,
    # Like "my-tag" (if you already built it locally)
    image: Optional[str] = None,
    # Like "langchain/langgraphjs-api" or "langchain/langgraph-api
    base_image: Optional[str] = None,
) -> tuple[list[str], str]:
    assert config_path.exists(), f"未找到配置文件: {config_path}"
    # prepare args
    stdin = orcaagent_cli.docker.compose(
        capabilities,
        port=port,
        debugger_port=debugger_port,
        debugger_base_url=debugger_base_url,
        postgres_uri=postgres_uri,
        image=image,  # Pass image to compose YAML generator
        base_image=base_image,
        api_version=api_version,
    )
    args = [
        "--project-directory",
        str(config_path.parent),
    ]
    # apply options
    if docker_compose:
        args.extend(["-f", str(docker_compose)])
    args.extend(["-f", "-"])  # stdin
    # apply config
    stdin += orcaagent_cli.config.config_to_compose(
        config_path,
        config,
        watch=watch,
        base_image=orcaagent_cli.config.default_base_image(config),
        api_version=api_version,
        image=image,
    )
    return args, stdin


def prepare(
    runner,
    *,
    capabilities: DockerCapabilities,
    config_path: pathlib.Path,
    docker_compose: Optional[pathlib.Path],
    port: int,
    pull: bool,
    watch: bool,
    verbose: bool,
    debugger_port: Optional[int] = None,
    debugger_base_url: Optional[str] = None,
    postgres_uri: Optional[str] = None,
    api_version: Optional[str] = None,
    image: Optional[str] = None,
    base_image: Optional[str] = None,
) -> tuple[list[str], str]:
    """Prepare the arguments and stdin for running the OrcaAgent API server."""
    config_json = orcaagent_cli.config.validate_config_file(config_path)
    if config_json is None:
        raise click.UsageError(f"配置文件验证失败: {config_path}")
    warn_non_wolfi_distro(config_json)
    # pull latest images
    if pull:
        runner.run(
            subp_exec(
                "docker",
                "pull",
                orcaagent_cli.config.docker_tag(config_json, base_image, api_version),
                verbose=verbose,
            )
        )

    args, stdin = prepare_args_and_stdin(
        capabilities=capabilities,
        config_path=config_path,
        config=config_json,
        docker_compose=docker_compose,
        port=port,
        watch=watch,
        debugger_port=debugger_port,
        debugger_base_url=debugger_base_url or f"http://127.0.0.1:{port}",
        postgres_uri=postgres_uri,
        api_version=api_version,
        image=image,
        base_image=base_image,
    )
    return args, stdin


def _resolve_graph_entry(config: Config, graph_id: Optional[str]) -> tuple[str, str]:
    graphs = config.get("graphs", {})
    if not graphs:
        raise click.UsageError("orcaagent.json 中未定义任何 graph。")

    if graph_id is not None:
        try:
            return graph_id, graphs[graph_id]
        except KeyError as exc:
            available = ", ".join(graphs.keys()) or "<empty>"
            raise click.UsageError(
                f"未找到 graph '{graph_id}'。可用 graph: {available}"
            ) from exc

    # 保持 JSON 原有顺序，默认取第一个 graph
    graph_id, graph_spec = next(iter(graphs.items()))
    return graph_id, graph_spec


def _load_env_vars(env_config: object, base_dir: pathlib.Path) -> dict[str, str]:
    if env_config is None:
        return {}

    if isinstance(env_config, str):
        env_path = (base_dir / env_config).resolve()
        if not env_path.exists():
            raise click.UsageError(f"找不到 env 文件: {env_path}")
        values = {
            key: value
            for key, value in dotenv_values(env_path).items()
            if value is not None
        }
        return values

    if isinstance(env_config, dict):
        return {str(key): "" if value is None else str(value) for key, value in env_config.items()}

    raise click.UsageError("env 配置必须是字符串路径或键值映射。")


def _pythonpath_from_dependencies(
    dependencies: Sequence[str],
    project_root: pathlib.Path,
) -> list[str]:
    python_paths: list[str] = []
    for dep in dependencies:
        if dep in (".", "./"):
            python_paths.append(str(project_root))
            continue

        dep_path = (project_root / dep).resolve()
        if dep_path.exists() and dep_path.is_dir():
            python_paths.append(str(dep_path))

    return python_paths


def _collect_env_overrides(config: Config, project_root: pathlib.Path) -> dict[str, str]:
    overrides = _load_env_vars(config.get("env"), project_root)

    python_paths = _pythonpath_from_dependencies(
        config.get("dependencies", []),
        project_root,
    )
    if python_paths:
        existing = os.environ.get("PYTHONPATH")
        combined = os.pathsep.join(python_paths + ([existing] if existing else []))
        overrides["PYTHONPATH"] = combined

    return overrides


def _wait_for_backend(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout
    check_paths = ("/health", "/.well-known/ready", "/")

    while time.monotonic() < deadline:
        for path in check_paths:
            try:
                response = requests.get(f"{url}{path}", timeout=interval)
                if response.status_code < 500:
                    return True
            except requests.RequestException:
                continue
        time.sleep(interval)

    return False


@contextmanager
def _temporary_env(overrides: dict[str, str]):
    if not overrides:
        yield
        return

    original: dict[str, Optional[str]] = {}
    for key, value in overrides.items():
        original[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        for key, previous in original.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _run_backend(host, port, selected_graph_id, config_json, server_log_level):
    """简化版的后端启动函数，替代已删除的_chat_backend_main"""
    try:
        from langgraph_api.cli import run_server
    except ImportError:
        raise RuntimeError("langgraph-api包未安装，无法启动后端服务")
    
    # 只启动指定的graph
    graphs = {selected_graph_id: config_json["graphs"][selected_graph_id]}
    
    run_server(
        host,
        port,
        reload=False,  # chat模式不需要热重载
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

@OPT_SERVER_LOG_LEVEL
@OPT_CHAT_NO_BROWSER
@OPT_CHAT_WAIT
@OPT_CHAT_UI_PARAM
@OPT_CHAT_UI_URL
@OPT_CHAT_API_URL
@OPT_CHAT_GRAPH
@OPT_CHAT_PORT
@OPT_CHAT_HOST
@OPT_CONFIG
@cli.command(
    "chat",
    help="💬 启动已编排的 graph，并在浏览器中打开 agent-chat-ui。",
)
@log_command
def chat(
    config: pathlib.Path,
    host: str,
    port: int,
    api_url: Optional[str],
    ui_url: str,
    ui_param: str,
    wait_timeout: float,
    no_browser: bool,
    server_log_level: str,
    graph_id: Optional[str] = None,
):
    """Launch selected graph backend and connect it to agent-chat-ui."""

    # 自动查找配置文件
    config_path = pathlib.Path(config).resolve()
    if config_path.name == DEFAULT_CONFIG and not config_path.exists():
        config_candidates = ["orcaagent.json", "langgraph.json"]
        for candidate in config_candidates:
            candidate_path = pathlib.Path(candidate).resolve()
            if candidate_path.exists():
                config_path = candidate_path
                break
        else:
            raise click.UsageError(
                f"未找到配置文件。请确保以下文件之一存在: {', '.join(config_candidates)}"
            )
    elif not config_path.exists():
        raise click.UsageError(f"配置文件不存在: {config_path}")

    config_json = orcaagent_cli.config.validate_config_file(config_path)
    if config_json is None:
        raise click.UsageError(f"配置文件验证失败: {config_path}")

    selected_graph_id, graph_spec = _resolve_graph_entry(config_json, graph_id)

    project_root = config_path.parent.resolve()
    env_overrides = _collect_env_overrides(config_json, project_root)

    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    agent_url = api_url or f"http://{display_host}:{port}"

    # UI URL 优先级：命令行参数 > 配置文件 > 默认值
    if ui_url == DEFAULT_CHAT_UI_URL:
        # 命令行未指定 ui_url，尝试从配置读取
        ui_config = config_json.get("ui_config")
        if ui_config and isinstance(ui_config, dict):
            config_ui_url = ui_config.get("chat_ui_url")
            if config_ui_url:
                ui_url = config_ui_url
                secho(f"🔗 使用配置文件中的 UI URL: {ui_url}", fg="blue")
            else:
                secho(f"🔗 使用默认 UI URL: {ui_url}", fg="yellow")
        else:
            secho(f"🔗 使用默认 UI URL: {ui_url}", fg="yellow")
        # 如果配置文件中也没有设置，ui_url 保持为 DEFAULT_CHAT_UI_URL
    
    # 构建前端 URL
    parsed = urlparse(ui_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query[ui_param] = agent_url
    query["assistantId"] = selected_graph_id
    final_ui_url = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    click.echo(
        f"🧠 正在启动 graph '{selected_graph_id}' ( {graph_spec} ) 于 {host}:{port}..."
    )

    backend_process = multiprocessing.Process(
        target=_run_backend,
        args=(host, port, selected_graph_id, config_json, server_log_level),
        daemon=True,
    )

    with _temporary_env(env_overrides):
        backend_process.start()

    if not backend_process.is_alive():
        raise click.ClickException("后端进程启动失败，请检查依赖和配置。")

    click.echo("⏳ 等待后端服务就绪...")
    if _wait_for_backend(agent_url, timeout=wait_timeout):
        click.echo("✅ 后端服务已就绪。")
    else:
        click.echo(
            "⚠️ 未能在预期时间内确认后端可用。请手动检查，继续尝试连接 UI。"
        )

    if not no_browser:
        click.echo(f"🌐 打开 agent-chat-ui: {final_ui_url}")
        try:
            webbrowser.open(final_ui_url)
        except Exception as exc:  # pragma: no cover - platform dependent
            click.echo(f"⚠️ 无法自动打开浏览器: {exc}")
            click.echo(f"请手动访问: {final_ui_url}")
    else:
        click.echo("🚫 已跳过自动打开浏览器。")
        click.echo(f"请手动访问: {final_ui_url}")

    click.echo("\n--- 按 Ctrl+C 停止后端服务 ---")
    try:
        while backend_process.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        click.echo("\n🛑 收到中断信号，正在停止后端...")
    finally:
        if backend_process.is_alive():
            backend_process.terminate()
            backend_process.join()
        click.echo("👋 已退出 chat 会话。")

@cli.command("template", help="📋 查询模板列表")
def template():
    """查询模板列表"""
    remote_templates = _get_templates_list()

    for idx, template in enumerate(remote_templates):
        click.secho(f"{idx+1}. ", nl=False, fg="cyan")
        click.secho(template['name'], fg="cyan", nl=False)
        click.secho(f" - {template['description']}", fg="white")