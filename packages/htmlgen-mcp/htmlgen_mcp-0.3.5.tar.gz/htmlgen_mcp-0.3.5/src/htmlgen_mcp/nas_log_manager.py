"""简化的 NAS 日志管理器 - 直接在 NAS 上读写日志"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from datetime import datetime


class NASLogManager:
    """NAS 日志管理器 - 所有操作直接在 NAS 上进行"""
    
    def __init__(self, nas_base_path: str = "/app/mcp-servers/mcp-servers/html_agent"):
        self.nas_base = Path(nas_base_path)
        
        # 日志存储目录
        self.logs_dir = self.nas_base / "mcp_data" / "make_web" / "progress_logs"
        self.jobs_dir = self.nas_base / "mcp_data" / "make_web" / "jobs"
        self.index_dir = self.nas_base / "mcp_data" / "make_web" / "job_index"
        
        # 创建目录
        for dir_path in [self.logs_dir, self.jobs_dir, self.index_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_job_log(self, job_id: str, plan_id: Optional[str] = None) -> str:
        """
        创建任务日志文件
        
        Args:
            job_id: 任务 ID
            plan_id: 计划 ID（可选）
            
        Returns:
            日志文件路径
        """
        # 日志文件路径
        log_file = self.logs_dir / f"{job_id}.jsonl"
        
        # 创建索引文件（用于快速查找）
        index_data = {
            "job_id": job_id,
            "plan_id": plan_id,
            "log_file": str(log_file),
            "created_at": datetime.now().isoformat(),
            "node_id": os.environ.get("NODE_ID", "unknown")
        }
        
        # 保存 job_id 索引
        job_index_file = self.index_dir / f"{job_id}.json"
        with open(job_index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        # 如果有 plan_id，也创建索引
        if plan_id:
            plan_index_file = self.index_dir / f"{plan_id}.json"
            with open(plan_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        # 初始化日志文件
        if not log_file.exists():
            with open(log_file, 'w', encoding='utf-8') as f:
                init_event = {
                    "timestamp": time.time(),
                    "event": "job_created",
                    "job_id": job_id,
                    "plan_id": plan_id,
                    "created_at": datetime.now().isoformat()
                }
                f.write(json.dumps(init_event, ensure_ascii=False) + '\n')
        
        return str(log_file)
    
    def find_log_file(self, identifier: str) -> Optional[str]:
        """
        查找日志文件路径（支持 job_id 和 plan_id）
        
        Args:
            identifier: job_id 或 plan_id
            
        Returns:
            日志文件路径，如果找不到返回 None
        """
        # 方法1: 检查索引文件
        index_file = self.index_dir / f"{identifier}.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    log_file = index_data.get("log_file")
                    if log_file and Path(log_file).exists():
                        return log_file
            except Exception:
                pass
        
        # 方法2: 直接检查是否是 job_id
        direct_log = self.logs_dir / f"{identifier}.jsonl"
        if direct_log.exists():
            return str(direct_log)
        
        # 方法3: 扫描所有索引文件查找 plan_id
        for index_file in self.index_dir.glob("*.json"):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    if (index_data.get("job_id") == identifier or 
                        index_data.get("plan_id") == identifier):
                        log_file = index_data.get("log_file")
                        if log_file and Path(log_file).exists():
                            return log_file
            except Exception:
                continue
        
        return None
    
    def write_progress(self, identifier: str, event: Dict[str, Any]) -> bool:
        """
        写入进度事件
        
        Args:
            identifier: job_id 或 plan_id
            event: 进度事件
            
        Returns:
            是否写入成功
        """
        log_file_path = self.find_log_file(identifier)
        
        # 如果找不到日志文件，尝试创建
        if not log_file_path:
            # 假设 identifier 是 job_id
            log_file_path = self.create_job_log(identifier)
        
        try:
            # 添加时间戳
            if "timestamp" not in event:
                event["timestamp"] = time.time()
            
            # 追加写入日志
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
                f.flush()  # 立即刷新到 NAS
            
            return True
            
        except Exception as e:
            print(f"写入进度失败 {identifier}: {e}")
            return False
    
    def read_progress(self, identifier: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        读取进度事件
        
        Args:
            identifier: job_id 或 plan_id
            limit: 返回事件数量限制
            
        Returns:
            进度事件列表
        """
        log_file_path = self.find_log_file(identifier)
        if not log_file_path:
            return []
        
        events = []
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 从最新的开始读取
                for line in reversed(lines[-limit:]):
                    if line.strip():
                        try:
                            event = json.loads(line)
                            events.insert(0, event)  # 保持时间顺序
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            print(f"读取进度失败 {identifier}: {e}")
        
        return events
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        获取所有任务列表
        
        Returns:
            任务列表
        """
        jobs = []
        
        # 扫描所有索引文件
        for index_file in self.index_dir.glob("*.json"):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    # 只添加 job_id 的记录，避免重复
                    if index_data.get("job_id") == index_file.stem:
                        jobs.append(index_data)
            except Exception:
                continue
        
        # 按创建时间排序
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return jobs
    
    def job_exists(self, identifier: str) -> bool:
        """
        检查任务是否存在
        
        Args:
            identifier: job_id 或 plan_id
            
        Returns:
            任务是否存在
        """
        return self.find_log_file(identifier) is not None
    
    def get_job_summary(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        获取任务摘要信息
        
        Args:
            identifier: job_id 或 plan_id
            
        Returns:
            任务摘要
        """
        log_file_path = self.find_log_file(identifier)
        if not log_file_path:
            return None
        
        try:
            # 读取最近的几个事件
            events = self.read_progress(identifier, limit=10)
            if not events:
                return None
            
            # 获取最新事件
            latest_event = events[-1] if events else {}
            first_event = events[0] if events else {}
            
            summary = {
                "identifier": identifier,
                "log_file": log_file_path,
                "total_events": len(events),
                "first_event_time": first_event.get("timestamp"),
                "latest_event_time": latest_event.get("timestamp"),
                "latest_status": latest_event.get("status", "unknown"),
                "latest_message": latest_event.get("message", ""),
            }
            
            # 尝试获取索引信息
            index_file = self.index_dir / f"{identifier}.json"
            if index_file.exists():
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                        summary.update({
                            "job_id": index_data.get("job_id"),
                            "plan_id": index_data.get("plan_id"),
                            "created_at": index_data.get("created_at"),
                            "node_id": index_data.get("node_id")
                        })
                except Exception:
                    pass
            
            return summary
            
        except Exception as e:
            print(f"获取任务摘要失败 {identifier}: {e}")
            return None


# 全局实例
_nas_log_manager: Optional[NASLogManager] = None


def get_nas_log_manager() -> NASLogManager:
    """获取 NAS 日志管理器实例（单例）"""
    global _nas_log_manager
    if _nas_log_manager is None:
        nas_path = os.environ.get(
            "NAS_STORAGE_PATH",
            "/app/mcp-servers/mcp-servers/html_agent"
        )
        _nas_log_manager = NASLogManager(nas_path)
    return _nas_log_manager


# 便捷函数
def log_progress(job_id: str, **kwargs):
    """记录进度的便捷函数"""
    manager = get_nas_log_manager()
    return manager.write_progress(job_id, kwargs)


def query_progress(identifier: str, limit: int = 20):
    """查询进度的便捷函数"""
    manager = get_nas_log_manager()
    return manager.read_progress(identifier, limit)


def ensure_job_log(job_id: str, plan_id: Optional[str] = None):
    """确保任务日志存在的便捷函数"""
    manager = get_nas_log_manager()
    return manager.create_job_log(job_id, plan_id)