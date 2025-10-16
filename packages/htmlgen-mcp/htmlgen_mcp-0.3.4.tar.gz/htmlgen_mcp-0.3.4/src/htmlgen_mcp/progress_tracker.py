"""进度跟踪模块 - 支持集群环境下的任务进度查询"""
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib


class ProgressTracker:
    """任务进度跟踪器 - 支持分布式环境"""
    
    def __init__(self, nas_base_path: str = "/app/mcp-servers/mcp-servers/html_agent"):
        """
        初始化进度跟踪器
        
        Args:
            nas_base_path: NAS 基础路径
        """
        self.nas_base = Path(nas_base_path)
        self.progress_dir = self.nas_base / "mcp_data" / "make_web" / "progress"
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        
    def create_task(self, task_type: str, description: str) -> str:
        """
        创建新任务并返回任务 ID
        
        Args:
            task_type: 任务类型 (plan_site, execute_plan, etc.)
            description: 任务描述
            
        Returns:
            任务 ID
        """
        # 生成唯一任务 ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        node_id = os.environ.get("NODE_ID", "node0")
        random_suffix = hashlib.md5(f"{timestamp}{description}".encode()).hexdigest()[:8]
        task_id = f"{task_type}_{node_id}_{timestamp}_{random_suffix}"
        
        # 创建任务记录
        task_info = {
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "node_id": node_id,
            "events": [],
            "current_step": None,
            "total_steps": None
        }
        
        self._save_task_info(task_id, task_info)
        return task_id
    
    def update_progress(
        self, 
        task_id: str, 
        progress: int, 
        status: str = "running",
        message: str = None,
        current_step: int = None,
        total_steps: int = None,
        data: Dict[str, Any] = None
    ) -> None:
        """
        更新任务进度
        
        Args:
            task_id: 任务 ID
            progress: 进度百分比 (0-100)
            status: 任务状态 (pending/running/completed/failed)
            message: 进度消息
            current_step: 当前步骤
            total_steps: 总步骤数
            data: 附加数据
        """
        task_info = self._load_task_info(task_id)
        if not task_info:
            task_info = {"task_id": task_id, "events": []}
        
        # 更新基本信息
        task_info["progress"] = progress
        task_info["status"] = status
        task_info["updated_at"] = datetime.now().isoformat()
        
        if current_step is not None:
            task_info["current_step"] = current_step
        if total_steps is not None:
            task_info["total_steps"] = total_steps
            
        # 添加事件记录
        event = {
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "status": status,
            "message": message
        }
        if data:
            event["data"] = data
            
        task_info["events"].append(event)
        
        # 保存更新
        self._save_task_info(task_id, task_info)
        
        # 同时写入流式日志（用于实时查询）
        self._append_progress_log(task_id, event)
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务进度
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务进度信息
        """
        return self._load_task_info(task_id)
    
    def get_task_events(
        self, 
        task_id: str, 
        since_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取任务事件（支持增量查询）
        
        Args:
            task_id: 任务 ID
            since_timestamp: 从此时间戳之后的事件
            
        Returns:
            事件列表
        """
        task_info = self._load_task_info(task_id)
        if not task_info:
            return []
        
        events = task_info.get("events", [])
        
        if since_timestamp:
            # 过滤出指定时间后的事件
            events = [
                e for e in events 
                if e.get("timestamp", "") > since_timestamp
            ]
        
        return events
    
    def list_tasks(
        self, 
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        列出任务列表
        
        Args:
            task_type: 筛选任务类型
            status: 筛选任务状态
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        tasks = []
        
        # 扫描所有任务文件
        for task_file in self.progress_dir.glob("*.json"):
            if task_file.name.endswith("_log.json"):
                continue  # 跳过日志文件
                
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_info = json.load(f)
                    
                # 应用过滤条件
                if task_type and task_info.get("task_type") != task_type:
                    continue
                if status and task_info.get("status") != status:
                    continue
                    
                # 精简信息，不包含完整事件列表
                summary = {
                    "task_id": task_info.get("task_id"),
                    "task_type": task_info.get("task_type"),
                    "description": task_info.get("description"),
                    "status": task_info.get("status"),
                    "progress": task_info.get("progress"),
                    "created_at": task_info.get("created_at"),
                    "updated_at": task_info.get("updated_at"),
                    "current_step": task_info.get("current_step"),
                    "total_steps": task_info.get("total_steps")
                }
                tasks.append(summary)
                
            except Exception:
                continue
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return tasks[:limit]
    
    def get_realtime_progress(self, task_id: str) -> Dict[str, Any]:
        """
        获取实时进度（用于 SSE 流式传输）
        
        Args:
            task_id: 任务 ID
            
        Returns:
            实时进度信息
        """
        task_info = self._load_task_info(task_id)
        if not task_info:
            return {
                "task_id": task_id,
                "status": "not_found",
                "progress": 0
            }
        
        # 计算详细进度
        progress_detail = {
            "task_id": task_id,
            "status": task_info.get("status", "unknown"),
            "progress": task_info.get("progress", 0),
            "current_step": task_info.get("current_step"),
            "total_steps": task_info.get("total_steps"),
            "message": None
        }
        
        # 获取最新消息
        events = task_info.get("events", [])
        if events:
            latest_event = events[-1]
            progress_detail["message"] = latest_event.get("message")
            progress_detail["last_update"] = latest_event.get("timestamp")
        
        # 如果有步骤信息，计算步骤进度
        if progress_detail["current_step"] and progress_detail["total_steps"]:
            step_progress = (progress_detail["current_step"] / progress_detail["total_steps"]) * 100
            progress_detail["step_progress"] = round(step_progress, 1)
        
        return progress_detail
    
    def _save_task_info(self, task_id: str, task_info: Dict[str, Any]) -> None:
        """保存任务信息到 NAS"""
        task_file = self.progress_dir / f"{task_id}.json"
        
        # 原子性写入（先写临时文件，再重命名）
        temp_file = task_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        
        # 重命名（原子操作）
        temp_file.replace(task_file)
    
    def _load_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """从 NAS 加载任务信息"""
        task_file = self.progress_dir / f"{task_id}.json"
        
        if not task_file.exists():
            return None
            
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _append_progress_log(self, task_id: str, event: Dict[str, Any]) -> None:
        """追加进度日志（用于流式查询）"""
        log_file = self.progress_dir / f"{task_id}_log.jsonl"
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False))
                f.write('\n')
        except Exception:
            pass
    
    def cleanup_old_tasks(self, days_to_keep: int = 7) -> int:
        """
        清理旧任务
        
        Args:
            days_to_keep: 保留天数
            
        Returns:
            清理的任务数量
        """
        cleaned = 0
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        for task_file in self.progress_dir.glob("*.json"):
            try:
                # 检查文件修改时间
                if task_file.stat().st_mtime < cutoff_time:
                    task_file.unlink()
                    
                    # 同时删除对应的日志文件
                    log_file = task_file.with_suffix('.jsonl')
                    if log_file.exists():
                        log_file.unlink()
                    
                    cleaned += 1
            except Exception:
                continue
        
        return cleaned


# 全局进度跟踪器实例
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """获取进度跟踪器实例（单例）"""
    global _progress_tracker
    if _progress_tracker is None:
        nas_path = os.environ.get(
            "NAS_STORAGE_PATH",
            "/app/mcp-servers/mcp-servers/html_agent"
        )
        _progress_tracker = ProgressTracker(nas_path)
    return _progress_tracker


# 便捷函数
def track_task(task_type: str, description: str):
    """
    任务跟踪装饰器
    
    使用方式：
    @track_task("plan_site", "生成网站计划")
    async def plan_site(description: str):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracker = get_progress_tracker()
            task_id = tracker.create_task(task_type, description)
            
            try:
                # 标记任务开始
                tracker.update_progress(task_id, 0, "running", "任务开始执行")
                
                # 执行任务
                result = await func(*args, **kwargs)
                
                # 标记任务完成
                tracker.update_progress(task_id, 100, "completed", "任务执行成功")
                
                # 在结果中添加任务 ID
                if isinstance(result, dict):
                    result["task_id"] = task_id
                
                return result
                
            except Exception as e:
                # 标记任务失败
                tracker.update_progress(
                    task_id, 
                    tracker.get_task_progress(task_id).get("progress", 0),
                    "failed", 
                    f"任务执行失败: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator