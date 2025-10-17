"""改进的进度日志管理 - 解决集群环境下的查询问题"""
import json
import time
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
import threading
import fcntl


class ImprovedProgressManager:
    """改进的进度管理器 - 支持 job_id 和 plan_id 查询"""
    
    def __init__(self, nas_base_path: str = "/app/mcp-servers/mcp-servers/html_agent"):
        self.nas_base = Path(nas_base_path)
        self.progress_base = self.nas_base / "mcp_data" / "make_web"
        
        # 分离不同类型的存储
        self.jobs_dir = self.progress_base / "jobs"
        self.plans_dir = self.progress_base / "plans"
        self.logs_dir = self.progress_base / "logs"
        self.mappings_dir = self.progress_base / "mappings"
        
        # 创建所有必要的目录
        for dir_path in [self.jobs_dir, self.plans_dir, self.logs_dir, self.mappings_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存，减少文件 I/O
        self._cache = {}
        self._cache_lock = threading.Lock()
    
    def register_job(self, job_id: str, plan_id: Optional[str] = None, 
                    description: str = "", project_path: str = "") -> str:
        """
        注册新任务
        
        Args:
            job_id: 任务 ID
            plan_id: 关联的计划 ID（可选）
            description: 任务描述
            project_path: 项目路径
            
        Returns:
            进度日志文件路径
        """
        # 生成日志文件路径
        log_file = self.logs_dir / f"{job_id}.jsonl"
        
        # 创建任务信息
        job_info = {
            "job_id": job_id,
            "plan_id": plan_id,
            "description": description,
            "project_path": project_path,
            "log_file": str(log_file),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "node_id": os.environ.get("NODE_ID", "unknown"),
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存任务信息
        job_file = self.jobs_dir / f"{job_id}.json"
        self._safe_write_json(job_file, job_info)
        
        # 如果有 plan_id，创建映射
        if plan_id:
            self._create_mapping(plan_id, job_id, "plan_to_job")
            self._create_mapping(job_id, plan_id, "job_to_plan")
        
        # 创建日志文件映射
        self._create_mapping(job_id, str(log_file), "job_to_log")
        if plan_id:
            self._create_mapping(plan_id, str(log_file), "plan_to_log")
        
        # 更新缓存
        with self._cache_lock:
            self._cache[f"job:{job_id}"] = job_info
            if plan_id:
                self._cache[f"plan:{plan_id}:job"] = job_id
                self._cache[f"plan:{plan_id}:log"] = str(log_file)
        
        return str(log_file)
    
    def find_log_path(self, identifier: str) -> Optional[str]:
        """
        根据 job_id 或 plan_id 查找日志文件路径
        
        Args:
            identifier: job_id 或 plan_id
            
        Returns:
            日志文件路径，如果找不到返回 None
        """
        # 先检查缓存
        with self._cache_lock:
            # 尝试作为 job_id 查找
            cached_job = self._cache.get(f"job:{identifier}")
            if cached_job:
                return cached_job.get("log_file")
            
            # 尝试作为 plan_id 查找
            cached_log = self._cache.get(f"plan:{identifier}:log")
            if cached_log:
                return cached_log
        
        # 方法1: 直接查找日志文件
        direct_log = self.logs_dir / f"{identifier}.jsonl"
        if direct_log.exists():
            return str(direct_log)
        
        # 方法2: 从任务信息中查找
        job_file = self.jobs_dir / f"{identifier}.json"
        if job_file.exists():
            try:
                job_info = self._safe_read_json(job_file)
                if job_info and "log_file" in job_info:
                    # 更新缓存
                    with self._cache_lock:
                        self._cache[f"job:{identifier}"] = job_info
                    return job_info["log_file"]
            except Exception:
                pass
        
        # 方法3: 从映射中查找
        mapping = self._load_mapping(identifier, "job_to_log")
        if mapping:
            return mapping
        
        mapping = self._load_mapping(identifier, "plan_to_log")
        if mapping:
            return mapping
        
        # 方法4: 扫描所有任务文件（最后的手段）
        for job_file in self.jobs_dir.glob("*.json"):
            try:
                job_info = self._safe_read_json(job_file)
                if job_info:
                    # 检查 job_id
                    if job_info.get("job_id") == identifier:
                        log_file = job_info.get("log_file")
                        if log_file:
                            # 更新缓存
                            with self._cache_lock:
                                self._cache[f"job:{identifier}"] = job_info
                            return log_file
                    
                    # 检查 plan_id
                    if job_info.get("plan_id") == identifier:
                        log_file = job_info.get("log_file")
                        if log_file:
                            # 更新缓存
                            with self._cache_lock:
                                self._cache[f"plan:{identifier}:log"] = log_file
                            return log_file
            except Exception:
                continue
        
        return None
    
    def write_progress(self, job_id: str, event: Dict[str, Any]) -> bool:
        """
        写入进度事件
        
        Args:
            job_id: 任务 ID
            event: 进度事件
            
        Returns:
            是否写入成功
        """
        log_path = self.find_log_path(job_id)
        if not log_path:
            # 如果找不到日志文件，自动注册任务
            log_path = self.register_job(job_id)
        
        try:
            # 添加时间戳
            if "timestamp" not in event:
                event["timestamp"] = time.time()
            
            # 原子写入（追加模式）
            log_file = Path(log_path)
            temp_file = log_file.parent / f".{log_file.name}.tmp"
            
            # 使用文件锁
            with open(log_path, 'a', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(event, ensure_ascii=False))
                    f.write('\n')
                    f.flush()
                    os.fsync(f.fileno())  # 强制刷新到磁盘
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # 更新任务状态
            self._update_job_status(job_id, event)
            
            return True
            
        except Exception as e:
            print(f"写入进度失败: {e}")
            return False
    
    def read_progress(self, identifier: str, limit: int = 100, 
                     since_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        读取进度事件
        
        Args:
            identifier: job_id 或 plan_id
            limit: 返回事件数量限制
            since_timestamp: 从此时间戳之后的事件
            
        Returns:
            进度事件列表
        """
        log_path = self.find_log_path(identifier)
        if not log_path or not Path(log_path).exists():
            return []
        
        events = []
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            # 过滤时间戳
                            if since_timestamp and event.get("timestamp", 0) <= since_timestamp:
                                continue
                            events.append(event)
                            # 限制数量
                            if len(events) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"读取进度失败: {e}")
        
        return events
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            job_id: 任务 ID
            
        Returns:
            任务状态信息
        """
        # 先检查缓存
        with self._cache_lock:
            cached = self._cache.get(f"job:{job_id}")
            if cached and time.time() - cached.get("_cache_time", 0) < 5:  # 5秒缓存
                return cached
        
        # 从文件读取
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            try:
                job_info = self._safe_read_json(job_file)
                if job_info:
                    # 更新缓存
                    job_info["_cache_time"] = time.time()
                    with self._cache_lock:
                        self._cache[f"job:{job_id}"] = job_info
                    return job_info
            except Exception:
                pass
        
        return None
    
    def _create_mapping(self, key: str, value: str, mapping_type: str):
        """创建映射关系"""
        mapping_file = self.mappings_dir / f"{mapping_type}.json"
        
        # 读取现有映射
        mappings = {}
        if mapping_file.exists():
            try:
                mappings = self._safe_read_json(mapping_file) or {}
            except Exception:
                mappings = {}
        
        # 更新映射
        mappings[key] = value
        
        # 保存映射
        self._safe_write_json(mapping_file, mappings)
    
    def _load_mapping(self, key: str, mapping_type: str) -> Optional[str]:
        """加载映射关系"""
        mapping_file = self.mappings_dir / f"{mapping_type}.json"
        
        if mapping_file.exists():
            try:
                mappings = self._safe_read_json(mapping_file)
                if mappings:
                    return mappings.get(key)
            except Exception:
                pass
        
        return None
    
    def _update_job_status(self, job_id: str, event: Dict[str, Any]):
        """更新任务状态"""
        job_file = self.jobs_dir / f"{job_id}.json"
        
        # 读取现有信息
        job_info = {}
        if job_file.exists():
            job_info = self._safe_read_json(job_file) or {}
        
        # 更新状态
        if "status" in event:
            job_info["status"] = event["status"]
        if "progress" in event:
            job_info["progress"] = event["progress"]
        
        job_info["updated_at"] = datetime.now().isoformat()
        job_info["last_event"] = event
        
        # 保存更新
        self._safe_write_json(job_file, job_info)
        
        # 更新缓存
        job_info["_cache_time"] = time.time()
        with self._cache_lock:
            self._cache[f"job:{job_id}"] = job_info
    
    def _safe_write_json(self, file_path: Path, data: Dict):
        """安全写入 JSON 文件（原子操作）"""
        temp_file = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # 先写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            # 原子重命名
            temp_file.replace(file_path)
            
        except Exception as e:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _safe_read_json(self, file_path: Path) -> Optional[Dict]:
        """安全读取 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def cleanup_old_logs(self, days_to_keep: int = 7) -> int:
        """清理旧的日志文件"""
        cleaned = 0
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        for log_file in self.logs_dir.glob("*.jsonl"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned += 1
            except Exception:
                continue
        
        return cleaned


# 全局实例
_progress_manager: Optional[ImprovedProgressManager] = None


def get_progress_manager() -> ImprovedProgressManager:
    """获取进度管理器实例（单例）"""
    global _progress_manager
    if _progress_manager is None:
        nas_path = os.environ.get(
            "NAS_STORAGE_PATH",
            "/app/mcp-servers/mcp-servers/html_agent"
        )
        _progress_manager = ImprovedProgressManager(nas_path)
    return _progress_manager