"""NAS 共享存储配置 - 解决集群环境文件一致性问题"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import fcntl
import hashlib
import time


class NASStorage:
    """NAS 存储管理器 - 确保所有节点访问同一份数据"""
    
    def __init__(self, nas_base_path: str = "/app/mcp-servers/mcp-servers/html_agent"):
        """
        初始化 NAS 存储
        
        Args:
            nas_base_path: NAS 挂载路径
        """
        self.nas_base = Path(nas_base_path)
        self.projects_dir = self.nas_base / "projects"
        self.cache_dir = self.nas_base / "cache"
        self.locks_dir = self.nas_base / "locks"
        self.metadata_dir = self.nas_base / "metadata"
        
        # 创建必要的目录结构
        self._init_directories()
        
    def _init_directories(self):
        """初始化目录结构"""
        for dir_path in [
            self.projects_dir,
            self.cache_dir,
            self.locks_dir,
            self.metadata_dir,
            self.cache_dir / "plans",
            self.cache_dir / "contexts",
            self.cache_dir / "jobs"
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_project_path(self, project_name: str, create: bool = True) -> Path:
        """
        获取项目路径
        
        Args:
            project_name: 项目名称
            create: 是否创建目录
            
        Returns:
            项目完整路径
        """
        # 生成唯一的项目目录名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in project_name if c.isalnum() or c in ('-', '_'))
        project_dir = self.projects_dir / f"{safe_name}_{timestamp}"
        
        if create:
            project_dir.mkdir(parents=True, exist_ok=True)
            # 创建项目元数据
            self._save_project_metadata(project_dir, project_name)
            
        return project_dir
    
    def _save_project_metadata(self, project_dir: Path, project_name: str):
        """保存项目元数据"""
        metadata = {
            "project_name": project_name,
            "project_path": str(project_dir),
            "created_at": datetime.now().isoformat(),
            "node_id": os.environ.get("NODE_ID", "unknown"),
            "server_instance": os.environ.get("HOSTNAME", "unknown")
        }
        
        metadata_file = self.metadata_dir / f"{project_dir.name}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def save_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> Path:
        """
        保存计划到 NAS
        
        Args:
            plan_id: 计划 ID
            plan_data: 计划数据
            
        Returns:
            保存的文件路径
        """
        plan_path = self.cache_dir / "plans" / f"{plan_id}.json"
        
        # 添加时间戳和节点信息
        plan_data["saved_at"] = datetime.now().isoformat()
        plan_data["node_id"] = os.environ.get("NODE_ID", "unknown")
        
        # 使用文件锁确保原子写入
        with self._file_lock(plan_path):
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, ensure_ascii=False, indent=2)
        
        return plan_path
    
    def load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        从 NAS 加载计划
        
        Args:
            plan_id: 计划 ID
            
        Returns:
            计划数据，如果不存在则返回 None
        """
        plan_path = self.cache_dir / "plans" / f"{plan_id}.json"
        
        if not plan_path.exists():
            return None
            
        with self._file_lock(plan_path, exclusive=False):
            with open(plan_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def save_job_state(self, job_id: str, job_data: Dict[str, Any]) -> Path:
        """
        保存任务状态到 NAS
        
        Args:
            job_id: 任务 ID
            job_data: 任务数据
            
        Returns:
            保存的文件路径
        """
        job_path = self.cache_dir / "jobs" / f"{job_id}.json"
        
        # 添加更新时间
        job_data["updated_at"] = datetime.now().isoformat()
        job_data["node_id"] = os.environ.get("NODE_ID", "unknown")
        
        with self._file_lock(job_path):
            with open(job_path, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, ensure_ascii=False, indent=2)
        
        return job_path
    
    def load_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        从 NAS 加载任务状态
        
        Args:
            job_id: 任务 ID
            
        Returns:
            任务数据，如果不存在则返回 None
        """
        job_path = self.cache_dir / "jobs" / f"{job_id}.json"
        
        if not job_path.exists():
            return None
            
        with self._file_lock(job_path, exclusive=False):
            with open(job_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def list_projects(self, limit: int = 20) -> list:
        """
        列出最近的项目
        
        Args:
            limit: 返回的项目数量
            
        Returns:
            项目列表
        """
        projects = []
        
        # 读取所有元数据文件
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    project_info = json.load(f)
                    projects.append(project_info)
            except Exception:
                continue
        
        # 按创建时间排序
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return projects[:limit]
    
    def _file_lock(self, file_path: Path, exclusive: bool = True):
        """
        文件锁上下文管理器
        
        Args:
            file_path: 文件路径
            exclusive: 是否独占锁
            
        Returns:
            锁对象
        """
        # 使用单独的锁文件
        lock_file = self.locks_dir / f"{file_path.name}.lock"
        
        class FileLock:
            def __init__(self, lock_path: Path, exclusive: bool):
                self.lock_path = lock_path
                self.exclusive = exclusive
                self.lock_fd = None
                
            def __enter__(self):
                self.lock_path.parent.mkdir(parents=True, exist_ok=True)
                self.lock_fd = open(self.lock_path, 'w')
                
                # 获取文件锁
                flag = fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH
                
                # 重试机制
                max_retries = 10
                for i in range(max_retries):
                    try:
                        fcntl.flock(self.lock_fd, flag | fcntl.LOCK_NB)
                        break
                    except IOError:
                        if i == max_retries - 1:
                            raise
                        time.sleep(0.1 * (i + 1))  # 指数退避
                
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.lock_fd:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                    self.lock_fd.close()
                    
                # 清理过期的锁文件
                try:
                    if self.lock_path.exists():
                        # 如果锁文件超过1小时，删除它
                        if time.time() - self.lock_path.stat().st_mtime > 3600:
                            self.lock_path.unlink(missing_ok=True)
                except Exception:
                    pass
        
        return FileLock(lock_file, exclusive)
    
    def generate_unique_id(self, prefix: str = "") -> str:
        """
        生成唯一 ID（结合时间戳、节点 ID 和随机数）
        
        Args:
            prefix: ID 前缀
            
        Returns:
            唯一 ID
        """
        node_id = os.environ.get("NODE_ID", "default")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        random_str = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        
        if prefix:
            return f"{prefix}_{node_id}_{timestamp}_{random_str}"
        return f"{node_id}_{timestamp}_{random_str}"
    
    def cleanup_old_projects(self, days_to_keep: int = 7) -> int:
        """
        清理旧项目
        
        Args:
            days_to_keep: 保留天数
            
        Returns:
            删除的项目数量
        """
        deleted_count = 0
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                try:
                    # 检查修改时间
                    if project_dir.stat().st_mtime < cutoff_time:
                        shutil.rmtree(project_dir)
                        
                        # 删除对应的元数据
                        metadata_file = self.metadata_dir / f"{project_dir.name}.json"
                        metadata_file.unlink(missing_ok=True)
                        
                        deleted_count += 1
                except Exception:
                    continue
        
        return deleted_count


# 全局 NAS 存储实例
_nas_storage: Optional[NASStorage] = None


def get_nas_storage() -> NASStorage:
    """获取 NAS 存储实例（单例）"""
    global _nas_storage
    if _nas_storage is None:
        nas_path = os.environ.get(
            "NAS_STORAGE_PATH", 
            "/app/mcp-servers/mcp-servers/html_agent"
        )
        _nas_storage = NASStorage(nas_path)
    return _nas_storage


# 导出的便捷函数
def save_project_file(project_name: str, relative_path: str, content: str) -> str:
    """
    保存项目文件到 NAS
    
    Args:
        project_name: 项目名称
        relative_path: 相对路径
        content: 文件内容
        
    Returns:
        保存的完整路径
    """
    storage = get_nas_storage()
    project_dir = storage.get_project_path(project_name)
    
    file_path = project_dir / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)


def load_project_file(project_path: str, relative_path: str) -> Optional[str]:
    """
    从 NAS 加载项目文件
    
    Args:
        project_path: 项目路径
        relative_path: 相对路径
        
    Returns:
        文件内容，如果不存在则返回 None
    """
    file_path = Path(project_path) / relative_path
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()