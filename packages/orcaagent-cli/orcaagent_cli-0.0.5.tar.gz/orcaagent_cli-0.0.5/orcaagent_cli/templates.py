import os
import sys
from typing import Optional

import click


TEMPLATES: dict[str, dict[str, str]] = {
    "react-agent": {
        "description": "A ReAct-patterned agent template provided by OrcaAgent.",
        "zip_url": "https://github.com/OrcaAgent-AI/react-agent/archive/refs/heads/main.zip",
    },
    "planner-agent": {
        "description": "A Planner-patterned agent template provided by OrcaAgent.",
        "zip_url": "https://github.com/OrcaAgent-AI/planner-agent/archive/refs/heads/main.zip",
    },
}
# Generate TEMPLATE_IDS programmatically
TEMPLATE_ID_TO_CONFIG = {
    f"{name.lower().replace(' ', '-')}": (name, detail['zip_url'])
    for name, detail in TEMPLATES.items()

}



def _get_templates_list():
    """获取OrcaAgent-templates组织下的仓库列表 - 同步包装器"""
    import requests
    
    click.secho("📥 开始拉取OrcaAgent模板列表...", fg="yellow")

    try:
        # 调用GitHub API获取公开仓库列表（不使用鉴权，避免私有仓库访问）
        url = "https://api.github.com/orgs/OrcaAgent-AI/repos?type=public"
        headers = {
            'User-Agent': 'OrcaAgent-CLI',
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28',

        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 解析仓库列表，只保留模板仓库
        repos = response.json()
        
        # 过滤出标记为模板的仓库
        template_repos = [
            {"name": repo['name'], "description": repo.get('description') or 'No description'}
            for repo in repos
            if repo.get('is_template', False)  # 只保留 is_template 为 True 的仓库
        ]
        
        # 如果没有找到模板仓库，回退到固定模板
        if not template_repos:
            click.secho(f"⚠️ 未找到模板仓库，使用固定模板列表", fg="yellow")
            return [
                {"name": name, "description": detail["description"]}
                for name, detail in TEMPLATES.items()
            ]
        
        click.secho(f"🎉 成功获取 {len(template_repos)} 个模板仓库", fg="green", bold=True)
        return template_repos

    except requests.exceptions.HTTPError as e:
        # 检查是否为 401/403 等错误
        if e.response is not None:
            status_code = e.response.status_code
            if status_code == 401:
                click.secho(f"⚠️  GitHub API 鉴权失败 ({status_code})，使用固定模板列表", fg="yellow")
            elif status_code == 403:
                click.secho("⚠️  GitHub API 限流 (rate limit)，使用固定模板列表", fg="yellow")
                click.secho("💡 提示: 设置 GITHUB_TOKEN 可提高限流额度", fg="blue")
            else:
                click.secho(f"⚠️  GitHub API 错误 ({status_code})，使用固定模板列表", fg="yellow")
            # 回退到固定模板
            fixed_repo_list=[
                {"name": name, "description": detail["description"]}
                for name, detail in TEMPLATES.items()
            ]
            return fixed_repo_list
        else:
            click.secho(f"❌ 请求失败: {str(e)[:50]}...", fg="red")
            return ()
    except requests.exceptions.RequestException as e:
        click.secho(f"❌ 请求失败: {str(e)[:50]}...", fg="red")
        return ()
    except Exception as e:
        click.secho(f"❌ 执行失败: {str(e)[:50]}...", fg="red")
        return ()
    
def _choose_template() -> str:

    """Presents a list of templates to the user and prompts them to select one.

    Returns:
        str: The URL of the selected template.
    """
    click.secho("🌟 请选择一个模板:", bold=True, fg="yellow")
    
    # 获取并显示远程模板列表
    remote_templates = _get_templates_list()

    for idx, template in enumerate(remote_templates):
        click.secho(f"{idx+1}. ", nl=False, fg="cyan")
        click.secho(template['name'], fg="cyan", nl=False)
        click.secho(f" - {template['description']}", fg="white")

    # Get the template choice from the user, defaulting to the first template if blank
    template_choice: Optional[int] = click.prompt(
        "请输入你想选的模板 (默认 1)",
        type=int,
        default=1,
        show_default=False,
    )
    if 1 <= template_choice <= len(remote_templates):
        selected_template = remote_templates[template_choice - 1]
    else:
        click.secho("❌ 选项无效，请重新选择。", fg="red")
        return _choose_template()

    # Prompt the user to choose between Python or JS/TS version
    click.secho(
        f"\n你选择了: {selected_template['name']} - {selected_template['description']}",
        fg="green",
    )
    return selected_template['name']

from urllib import request, error
import shutil
from zipfile import ZipFile
from io import BytesIO
import os
import sys

def _download_repo_with_requests(template: str, path: str) -> None:
    """Download a ZIP archive from the given URL and extracts it to the specified path.

    Args:
        repo_url: The URL of the repository to download.
        path: The path where the repository should be extracted.
    """
    click.secho(f"📥 正在下载模板 {template} 的 ZIP 文件...", fg="yellow")
    zip_url = f"https://github.com/OrcaAgent-AI/{template}/archive/refs/heads/main.zip"
    click.secho(f"URL: {zip_url}", fg="yellow")
    try:
        with request.urlopen(zip_url) as response:
            if response.status == 200:
                with ZipFile(BytesIO(response.read())) as zip_file:
                    zip_file.extractall(path)
                    # Move extracted contents to path
                    for item in os.listdir(path):
                        if item.endswith("-main"):
                            extracted_dir = os.path.join(path, item)
                            for filename in os.listdir(extracted_dir):
                                shutil.move(os.path.join(extracted_dir, filename), path)
                            shutil.rmtree(extracted_dir)
                click.secho(
                    f"🎉 成功下载并解压模板 {template} 到 {path}", fg="green"
                )
    except error.HTTPError as e:
        click.secho(
            f"❌ 错误: 下载仓库失败\n详情: {e}\n",
            fg="red",
            bold=True,
            err=True,
        )
        sys.exit(1)


def create_new(path: Optional[str], template: Optional[str]) -> None:
    """Create a new LangGraph/OrcaAgent project at the specified PATH using the chosen TEMPLATE.

    Args:
        path: The path where the new project will be created.
        template: The name of the template to use.
    """
    # Prompt for path if not provided
    if not path:
        path = click.prompt(
            "📂 请指定应用程序的创建路径。", default="."
        )
    click.secho(f"🌟 path: {path} 你选择了: {template}", fg="green")
    path = os.path.abspath(path)  # Ensure path is absolute

    # Check if path exists and is not empty
    if os.path.exists(path) and os.listdir(path):
        click.secho(
            "❌ 指定的目录已存在且非空。 "
            "终止操作以防止覆盖文件。",
            fg="red",
            bold=True,
        )
        sys.exit(1)


    # Download and extract the template
    if template:
        # 如果是远程模板，使用模板名称下载
        _download_repo_with_requests(template, path)
    else:
        template_url = _choose_template()
        # 交互式选择的模板
        _download_repo_with_requests(template_url, path)

    click.secho(f"🎉 成功在 {path} 创建新项目", fg="green", bold=True)
