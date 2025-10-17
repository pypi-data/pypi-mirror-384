#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSE 模式优化补丁 - 解决超时问题"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

async def read_progress_file_async(
    file_path: str, 
    limit: int = 20,
    chunk_size: int = 8192
) -> tuple[List[Dict[str, Any]], int]:
    """异步读取进度日志文件，避免阻塞"""
    events: List[Dict[str, Any]] = []
    total_lines = 0
    
    try:
        # 使用异步方式读取文件
        loop = asyncio.get_event_loop()
        
        # 异步读取文件内容
        def read_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines
        
        lines = await loop.run_in_executor(None, read_file)
        total_lines = len(lines)
        
        # 处理最后的 limit 行
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
                
        return events, total_lines
        
    except Exception as e:
        raise Exception(f"读取进度文件失败: {str(e)}")


async def check_file_exists_async(file_path: str) -> bool:
    """异步检查文件是否存在"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, os.path.exists, file_path)


def create_streaming_response(data: Dict[str, Any], chunk_size: int = 100) -> List[Dict[str, Any]]:
    """
    将大响应分块，适用于 SSE 流式传输
    避免一次性发送大量数据导致超时
    """
    if 'events' in data and len(data['events']) > chunk_size:
        # 分块发送事件
        chunks = []
        events = data['events']
        
        for i in range(0, len(events), chunk_size):
            chunk_data = data.copy()
            chunk_data['events'] = events[i:i + chunk_size]
            chunk_data['chunk_index'] = i // chunk_size
            chunk_data['total_chunks'] = (len(events) + chunk_size - 1) // chunk_size
            chunks.append(chunk_data)
        
        return chunks
    
    return [data]


async def get_progress_optimized(
    plan_id: Optional[str] = None,
    job_id: Optional[str] = None,
    log_path: Optional[str] = None,
    limit: int = 20,
    _job_registry: Dict = None,
    _progress_log_by_job: Dict = None,
    _progress_log_by_id: Dict = None,
    project_root: str = None
) -> Dict[str, Any]:
    """
    SSE 优化版的 get_progress 函数
    - 使用异步 I/O 避免阻塞
    - 添加超时控制
    - 支持流式响应
    """
    try:
        # 设置操作超时（SSE 环境下更短的超时）
        timeout = 10  # 10秒超时
        
        async def _get_progress():
            if limit <= 0:
                limit = 20
            
            job_info = None
            resolved_path = None
            
            # 查找日志文件路径
            if job_id and _job_registry:
                job_info = _job_registry.get(job_id)
                if job_info and not plan_id:
                    plan_id = job_info.get("plan_id")
                if _progress_log_by_job and job_id in _progress_log_by_job:
                    resolved_path = _progress_log_by_job[job_id]
                elif job_info and job_info.get("progress_log"):
                    resolved_path = job_info.get("progress_log")
            
            if not resolved_path and plan_id and _progress_log_by_id and plan_id in _progress_log_by_id:
                resolved_path = _progress_log_by_id[plan_id]
            
            if log_path:
                resolved_path = log_path
            
            # 解析路径
            if resolved_path:
                if not os.path.isabs(resolved_path):
                    candidate = os.path.join(project_root or os.getcwd(), resolved_path)
                    if await check_file_exists_async(candidate):
                        resolved_path = candidate
                    else:
                        alt = os.path.sep + resolved_path.lstrip(os.path.sep)
                        if await check_file_exists_async(alt):
                            resolved_path = alt
            
            # 检查文件是否存在
            if not resolved_path or not await check_file_exists_async(resolved_path):
                return {
                    "status": "error",
                    "message": "未找到进度日志，请确认 job_id/plan_id 或提供 log_path"
                }
            
            # 异步读取文件
            events, total_lines = await read_progress_file_async(resolved_path, limit)
            
            response = {
                "status": "success",
                "plan_id": plan_id,
                "job_id": job_id,
                "log_path": resolved_path,
                "events": events,
                "total_records": total_lines,
                "returned": len(events),
            }
            
            # 添加任务信息
            if job_info:
                snapshot_keys = [
                    "job_id", "status", "plan_id", "progress_log",
                    "started_at", "updated_at", "completed_at",
                    "project_directory", "model", "upload_status",
                    "website_url", "upload_completed_at"
                ]
                job_snapshot = {
                    k: job_info.get(k) for k in snapshot_keys 
                    if job_info.get(k) is not None
                }
                
                if job_info.get("status") == "completed":
                    job_snapshot["result_summary"] = {
                        "report": job_info.get("result", {}).get("report"),
                        "created_files": job_info.get("result", {}).get("created_files"),
                    }
                    if job_info.get("upload_result"):
                        job_snapshot["upload_result"] = job_info.get("upload_result")
                
                if job_info.get("status") == "failed":
                    job_snapshot["error"] = job_info.get("error")
                
                if job_info.get("upload_error"):
                    job_snapshot["upload_error"] = job_info.get("upload_error")
                
                response["job"] = job_snapshot
            
            return response
        
        # 使用超时控制
        result = await asyncio.wait_for(_get_progress(), timeout=timeout)
        return result
        
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": f"操作超时（{timeout}秒）- SSE 模式下请减少 limit 参数值"
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc)
        }