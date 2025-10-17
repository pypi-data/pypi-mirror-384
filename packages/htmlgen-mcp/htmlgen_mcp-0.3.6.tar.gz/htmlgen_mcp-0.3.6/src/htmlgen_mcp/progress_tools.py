"""进度查询工具 - MCP 接口"""
from typing import Dict, Optional, List, Any
from htmlgen_mcp.progress_tracker import get_progress_tracker


async def query_task_progress(task_id: str) -> Dict[str, Any]:
    """
    查询任务进度
    
    Args:
        task_id: 任务 ID（执行任务时返回的 task_id）
        
    Returns:
        包含任务进度信息的字典：
        - task_id: 任务 ID
        - status: 任务状态 (pending/running/completed/failed)
        - progress: 进度百分比 (0-100)
        - message: 最新进度消息
        - current_step: 当前步骤
        - total_steps: 总步骤数
        - created_at: 创建时间
        - updated_at: 最后更新时间
    """
    tracker = get_progress_tracker()
    progress = tracker.get_realtime_progress(task_id)
    
    if progress.get("status") == "not_found":
        return {
            "status": "error",
            "message": f"未找到任务: {task_id}",
            "task_id": task_id
        }
    
    return {
        "status": "success",
        "data": progress
    }


async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    列出任务列表
    
    Args:
        task_type: 筛选任务类型 (plan_site/execute_plan/create_simple_site)
        status: 筛选任务状态 (pending/running/completed/failed)
        limit: 返回数量限制（默认20）
        
    Returns:
        任务列表，包含每个任务的摘要信息
    """
    tracker = get_progress_tracker()
    tasks = tracker.list_tasks(task_type=task_type, status=status, limit=limit)
    
    return {
        "status": "success",
        "count": len(tasks),
        "tasks": tasks
    }


async def get_task_events(
    task_id: str,
    since_timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取任务事件历史（支持增量查询）
    
    Args:
        task_id: 任务 ID
        since_timestamp: 从此时间戳之后的事件（ISO格式）
        
    Returns:
        任务的事件列表，包含详细的执行步骤
    """
    tracker = get_progress_tracker()
    
    # 先检查任务是否存在
    task_info = tracker.get_task_progress(task_id)
    if not task_info:
        return {
            "status": "error",
            "message": f"未找到任务: {task_id}",
            "task_id": task_id
        }
    
    # 获取事件列表
    events = tracker.get_task_events(task_id, since_timestamp)
    
    return {
        "status": "success",
        "task_id": task_id,
        "task_status": task_info.get("status"),
        "task_progress": task_info.get("progress"),
        "event_count": len(events),
        "events": events
    }


async def get_task_details(task_id: str) -> Dict[str, Any]:
    """
    获取任务完整详情
    
    Args:
        task_id: 任务 ID
        
    Returns:
        任务的完整信息，包含所有事件历史
    """
    tracker = get_progress_tracker()
    task_info = tracker.get_task_progress(task_id)
    
    if not task_info:
        return {
            "status": "error",
            "message": f"未找到任务: {task_id}",
            "task_id": task_id
        }
    
    return {
        "status": "success",
        "data": task_info
    }


async def cleanup_old_tasks(days_to_keep: int = 7) -> Dict[str, Any]:
    """
    清理旧任务记录
    
    Args:
        days_to_keep: 保留天数（默认7天）
        
    Returns:
        清理结果
    """
    tracker = get_progress_tracker()
    cleaned = tracker.cleanup_old_tasks(days_to_keep)
    
    return {
        "status": "success",
        "message": f"已清理 {cleaned} 个旧任务",
        "cleaned_count": cleaned,
        "days_kept": days_to_keep
    }


# SSE 流式进度查询（用于实时监控）
async def stream_task_progress(task_id: str):
    """
    流式获取任务进度（生成器）
    
    用于 SSE 实时推送进度更新
    
    Args:
        task_id: 任务 ID
        
    Yields:
        进度更新事件
    """
    import asyncio
    tracker = get_progress_tracker()
    
    last_timestamp = None
    while True:
        # 获取最新进度
        progress = tracker.get_realtime_progress(task_id)
        
        # 如果任务完成或失败，发送最终状态并退出
        if progress.get("status") in ["completed", "failed", "not_found"]:
            yield {
                "event": "done",
                "data": progress
            }
            break
        
        # 获取增量事件
        events = tracker.get_task_events(task_id, last_timestamp)
        if events:
            # 更新时间戳
            last_timestamp = events[-1].get("timestamp")
            
            # 发送事件
            for event in events:
                yield {
                    "event": "progress",
                    "data": event
                }
        
        # 等待一小段时间再查询
        await asyncio.sleep(0.5)