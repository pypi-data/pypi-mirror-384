"""项目配置管理 - 跨平台支持"""
import os
import sys
import platform
import tempfile
from pathlib import Path
from datetime import datetime


class ProjectConfig:
    """项目配置管理器 - 支持 Windows/macOS/Linux"""
    
    @staticmethod
    def get_system_info() -> dict:
        """获取系统信息"""
        return {
            'system': platform.system(),  # 'Windows', 'Darwin' (macOS), 'Linux'
            'platform': sys.platform,      # 'win32', 'darwin', 'linux'
            'home': Path.home(),
            'temp': Path(tempfile.gettempdir())
        }
    
    @staticmethod
    def get_default_output_dir() -> Path:
        """获取默认的项目输出目录（跨平台）
        
        优先级：
        1. 环境变量 WEB_AGENT_OUTPUT_DIR
        2. 系统特定的文档目录
        3. 用户主目录下的隐藏目录
        4. 系统临时目录
        """
        
        # 1. 检查环境变量（所有平台通用）
        env_dir = os.environ.get('WEB_AGENT_OUTPUT_DIR')
        if env_dir:
            output_dir = Path(env_dir)
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                return output_dir
            except Exception as e:
                print(f"⚠️ 无法创建环境变量指定的目录: {e}")
        
        system_info = ProjectConfig.get_system_info()
        home = system_info['home']
        system = system_info['system']
        
        # 2. 系统特定的文档目录
        if system == 'Windows':
            # Windows: 使用 Documents 文件夹
            docs_candidates = [
                home / 'Documents' / 'WebProjects',
                home / 'My Documents' / 'WebProjects',  # 旧版 Windows
                Path(os.environ.get('USERPROFILE', home)) / 'Documents' / 'WebProjects'
            ]
        elif system == 'Darwin':  # macOS
            # macOS: Documents 文件夹
            docs_candidates = [
                home / 'Documents' / 'WebProjects',
                home / 'Projects' / 'WebProjects'  # 有些用户喜欢用 Projects 文件夹
            ]
        else:  # Linux 及其他 Unix-like 系统
            # Linux: 遵循 XDG 标准
            xdg_documents = os.environ.get('XDG_DOCUMENTS_DIR')
            docs_candidates = []
            if xdg_documents:
                docs_candidates.append(Path(xdg_documents) / 'WebProjects')
            docs_candidates.extend([
                home / 'Documents' / 'WebProjects',
                home / 'projects' / 'web',  # Linux 用户常用小写
                home / 'Projects' / 'Web'
            ])
        
        # 尝试创建文档目录
        for doc_dir in docs_candidates:
            try:
                if doc_dir.parent.exists():
                    doc_dir.mkdir(parents=True, exist_ok=True)
                    return doc_dir
            except Exception:
                continue
        
        # 3. 用户主目录下的隐藏目录（所有平台）
        if system == 'Windows':
            # Windows 使用 AppData
            app_data = os.environ.get('APPDATA')
            if app_data:
                hidden_dirs = [
                    Path(app_data) / 'WebAgent' / 'projects',
                    home / 'AppData' / 'Roaming' / 'WebAgent' / 'projects'
                ]
            else:
                hidden_dirs = [home / '.web-agent' / 'projects']
        else:
            # macOS 和 Linux 使用点开头的隐藏目录
            hidden_dirs = [
                home / '.web-agent' / 'projects',
                home / '.local' / 'share' / 'web-agent' / 'projects'  # XDG 标准
            ]
        
        for hidden_dir in hidden_dirs:
            try:
                hidden_dir.mkdir(parents=True, exist_ok=True)
                return hidden_dir
            except Exception:
                continue
        
        # 4. 系统临时目录（最后的选择）
        temp_base = system_info['temp']
        temp_dir = temp_base / 'web-agent-projects'
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
            print(f"⚠️ 使用临时目录: {temp_dir}")
            print(f"💡 建议设置环境变量 WEB_AGENT_OUTPUT_DIR 到更合适的位置")
            return temp_dir
        except Exception as e:
            # 如果连临时目录都无法创建，使用当前工作目录
            print(f"⚠️ 无法创建临时目录: {e}")
            fallback = Path.cwd() / 'web-projects'
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
    
    @staticmethod
    def create_project_directory(
        project_name: str,
        base_dir: Path = None,
        use_timestamp: bool = True
    ) -> Path:
        """创建项目目录
        
        Args:
            project_name: 项目名称
            base_dir: 基础目录，如果不提供则使用默认目录
            use_timestamp: 是否在目录名中添加时间戳（避免冲突）
            
        Returns:
            创建的项目目录路径
        """
        if base_dir is None:
            base_dir = ProjectConfig.get_default_output_dir()
        
        # 清理项目名称，移除特殊字符
        safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.strip().replace(' ', '-').lower()
        
        if use_timestamp:
            # 添加时间戳避免冲突
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dir_name = f"{safe_name}-{timestamp}"
        else:
            dir_name = safe_name
        
        project_dir = base_dir / dir_name
        
        # 如果目录已存在且不使用时间戳，添加序号
        if project_dir.exists() and not use_timestamp:
            counter = 1
            while (base_dir / f"{dir_name}-{counter}").exists():
                counter += 1
            project_dir = base_dir / f"{dir_name}-{counter}"
        
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建标准子目录结构
        (project_dir / "assets" / "css").mkdir(parents=True, exist_ok=True)
        (project_dir / "assets" / "js").mkdir(parents=True, exist_ok=True)
        (project_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
        
        # 创建项目信息文件
        info_file = project_dir / ".project-info.json"
        import json
        project_info = {
            "name": project_name,
            "created_at": datetime.now().isoformat(),
            "generator": "htmlgen-mcp",
            "version": "0.3.0"
        }
        info_file.write_text(json.dumps(project_info, ensure_ascii=False, indent=2))
        
        return project_dir
    
    @staticmethod
    def get_user_projects_list(base_dir: Path = None) -> list:
        """获取用户已创建的项目列表
        
        Returns:
            项目信息列表
        """
        if base_dir is None:
            base_dir = ProjectConfig.get_default_output_dir()
        
        projects = []
        if not base_dir.exists():
            return projects
        
        for item in base_dir.iterdir():
            if item.is_dir():
                info_file = item / ".project-info.json"
                if info_file.exists():
                    try:
                        import json
                        info = json.loads(info_file.read_text())
                        info['path'] = str(item)
                        projects.append(info)
                    except:
                        # 如果没有info文件，仍然添加基本信息
                        projects.append({
                            'name': item.name,
                            'path': str(item),
                            'created_at': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
        
        # 按创建时间倒序排序
        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return projects
    
    @staticmethod
    def clean_old_projects(
        base_dir: Path = None,
        days_to_keep: int = 7,
        max_projects: int = 20
    ) -> int:
        """清理旧项目
        
        Args:
            base_dir: 基础目录
            days_to_keep: 保留最近几天的项目
            max_projects: 最多保留多少个项目
            
        Returns:
            删除的项目数量
        """
        if base_dir is None:
            base_dir = ProjectConfig.get_default_output_dir()
        
        projects = ProjectConfig.get_user_projects_list(base_dir)
        deleted = 0
        
        # 如果项目数超过限制，删除最旧的
        if len(projects) > max_projects:
            for project in projects[max_projects:]:
                try:
                    import shutil
                    shutil.rmtree(project['path'])
                    deleted += 1
                except:
                    pass
        
        # 删除超过指定天数的项目
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for project in projects:
            try:
                created_at = datetime.fromisoformat(project.get('created_at', ''))
                if created_at < cutoff_date:
                    import shutil
                    shutil.rmtree(project['path'])
                    deleted += 1
            except:
                pass
        
        return deleted


# 便捷函数
def get_project_directory(project_name: str = None) -> str:
    """获取项目目录（供 MCP 工具使用）
    
    Args:
        project_name: 项目名称，如果不提供则生成默认名称
        
    Returns:
        项目目录路径字符串
    """
    if not project_name:
        project_name = f"web-project-{datetime.now().strftime('%Y%m%d')}"
    
    config = ProjectConfig()
    project_dir = config.create_project_directory(project_name, use_timestamp=True)
    
    print(f"📁 项目将生成在: {project_dir}")
    print(f"💡 提示: 可通过设置环境变量 WEB_AGENT_OUTPUT_DIR 来自定义输出目录")
    
    return str(project_dir)


def list_recent_projects(limit: int = 10) -> list:
    """列出最近的项目
    
    Args:
        limit: 返回的项目数量
        
    Returns:
        项目列表
    """
    config = ProjectConfig()
    projects = config.get_user_projects_list()
    return projects[:limit]


def clean_temp_projects() -> int:
    """清理临时项目
    
    Returns:
        删除的项目数量
    """
    config = ProjectConfig()
    
    # 如果使用的是 /tmp 目录，更积极地清理
    output_dir = config.get_default_output_dir()
    if str(output_dir).startswith('/tmp'):
        # 临时目录只保留1天，最多10个项目
        return config.clean_old_projects(days_to_keep=1, max_projects=10)
    else:
        # 其他目录保留7天，最多20个项目
        return config.clean_old_projects(days_to_keep=7, max_projects=20)


# 导出的功能
__all__ = [
    'ProjectConfig',
    'get_project_directory',
    'list_recent_projects', 
    'clean_temp_projects'
]