#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smart Web Agent MCP 服务

基于 SmartWebAgent 提供网页生成的规划与执行接口，兼容 Model Context Protocol。
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
import zipfile
import tempfile
import aiohttp
from typing import Any, Dict, Optional

# 确保项目根目录在模块搜索路径中
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 当前文件在 src/htmlgen_mcp/ 下，所以需要向上两级到项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastmcp import FastMCP  # type: ignore

import uuid
from pathlib import Path

from htmlgen_mcp.agents.smart_web_agent import SmartWebAgent
from htmlgen_mcp.nas_storage import get_nas_storage
from htmlgen_mcp.nas_log_manager import get_nas_log_manager, ensure_job_log, log_progress, query_progress
from datetime import datetime

# 使用 NAS 作为默认存储路径
NAS_PATH = os.environ.get("NAS_STORAGE_PATH", "/app/mcp-servers/mcp-servers/html_agent")
DEFAULT_PROJECT_ROOT = os.path.abspath(
    os.environ.get("WEB_AGENT_PROJECT_ROOT", f"{NAS_PATH}/projects")
)
DEFAULT_MODEL = os.environ.get("WEB_AGENT_MODEL", "qwen3-coder-plus-2025-09-23")
DEFAULT_BASE_URL = os.environ.get(
    "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)

mcp = FastMCP("smart-web-agent")

# MCP 服务持久化目录：使用 NAS 路径以便集群共享
MCP_SERVICE_NAME = os.environ.get("MCP_SERVICE_NAME", "make_web")
MCP_DATA_ROOT = Path(
    os.environ.get("MCP_DATA_DIR", f"{NAS_PATH}/mcp_data/{MCP_SERVICE_NAME}")
)
MCP_DATA_ROOT.mkdir(parents=True, exist_ok=True)

# 简单的缓存：记录最近一次生成的计划，避免“create_simple_site → execute_plan”时需手动传递
PLAN_CACHE_DIR = MCP_DATA_ROOT / "plan_cache"
PLAN_CACHE_DIR.mkdir(exist_ok=True)

# 进度日志目录，存储每个任务的实时进度
PROGRESS_LOG_DIR = MCP_DATA_ROOT / "progress_logs"
PROGRESS_LOG_DIR.mkdir(exist_ok=True)

# 任务状态目录，每个任务一个 JSON 文件
JOB_STATE_DIR = MCP_DATA_ROOT / "jobs" / "state"
JOB_STATE_DIR.mkdir(parents=True, exist_ok=True)

# 上下文缓存目录
CONTEXT_CACHE_DIR = MCP_DATA_ROOT / "context_cache"
CONTEXT_CACHE_DIR.mkdir(exist_ok=True)

_PLAN_CACHE: dict[tuple[str, str], Dict[str, Any]] = {}
_PLAN_CACHE_BY_ID: dict[str, Dict[str, Any]] = {}
_PROGRESS_LOG_BY_ID: dict[str, str] = {}
_PROGRESS_LOG_BY_JOB: dict[str, str] = {}
_JOB_REGISTRY: dict[str, Dict[str, Any]] = {}
_CONTEXT_CACHE_BY_ID: dict[str, Dict[str, Any]] = {}


def _job_state_path(job_id: str) -> Path:
    return JOB_STATE_DIR / f"{job_id}.json"


def _persist_job_state(job_id: str) -> None:
    job = _JOB_REGISTRY.get(job_id)
    if not job:
        return
    job_copy = {k: v for k, v in job.items() if k not in {"agent"}}
    job_copy["updated_at"] = time.time()
    
    # 同时保存到本地和 NAS
    path = _job_state_path(job_id)
    try:
        path.write_text(
            json.dumps(job_copy, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
    
    # 保存到 NAS 日志
    try:
        log_manager = get_nas_log_manager()
        plan_id = job.get("plan_id")
        log_manager.create_job_log(job_id, plan_id)
        log_progress(job_id, status="registered", job_info=job_copy)
    except Exception:
        pass


def _load_job_states() -> None:
    for path in JOB_STATE_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            job_id = data.get("job_id") or path.stem
            if not job_id:
                continue
            if data.get("status") == "running":
                data["status"] = "stopped"
                data["message"] = "任务在服务器重启时中断，请重新执行"
            _JOB_REGISTRY[job_id] = data
            progress_log = data.get("progress_log")
            if progress_log:
                if not os.path.isabs(progress_log):
                    progress_log = os.path.join(PROJECT_ROOT, progress_log)
                _PROGRESS_LOG_BY_JOB[job_id] = progress_log
                plan_id = data.get("plan_id")
                if plan_id and plan_id not in _PROGRESS_LOG_BY_ID:
                    _PROGRESS_LOG_BY_ID[plan_id] = progress_log
        except Exception:
            continue


_load_job_states()


def _context_cache_path(context_id: str) -> Path:
    return CONTEXT_CACHE_DIR / f"{context_id}.json"


def _load_context_cache() -> None:
    for path in CONTEXT_CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            context_id = data.get("context_id") or path.stem
            if not context_id:
                continue
            data.setdefault("path", str(path))
            _CONTEXT_CACHE_BY_ID[context_id] = data
        except Exception:
            continue


_load_context_cache()


def _resolve_cached_context(context_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not context_id:
        return None
    cached = _CONTEXT_CACHE_BY_ID.get(context_id)
    if cached:
        return cached
    path = _context_cache_path(context_id)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("path", str(path))
            _CONTEXT_CACHE_BY_ID[context_id] = data
            return data
        except Exception:
            return None
    return None


def _resolve_project_directory(project_root: Optional[str]) -> str:
    base = project_root or DEFAULT_PROJECT_ROOT
    abs_path = os.path.abspath(base)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def _build_agent(
    project_directory: str,
    model: Optional[str] = None,
    *,
    show_code: bool = False,
    verbose: bool = False,
    save_output: bool = False,
    force_single_page: bool = True,
) -> SmartWebAgent:
    return SmartWebAgent(
        project_directory=project_directory,
        model=model or DEFAULT_MODEL,
        show_code=show_code,
        verbose=verbose,
        save_output=save_output,
        force_single_page=force_single_page,
    )


def _prepare_agent_run(agent: SmartWebAgent, description: str) -> None:
    agent.execution_start_time = time.time()
    agent.execution_history = []
    agent.created_files = []
    agent.latest_user_request = description
    agent.current_plan = None


def _decode_plan(agent: SmartWebAgent, plan: Any) -> Dict[str, Any]:
    if isinstance(plan, str):
        plan = json.loads(plan)
    if not isinstance(plan, dict):
        raise ValueError("plan 应该是 JSON 对象")
    source_description = plan.pop("__source_description", None)
    plan.pop("__plan_id", None)
    plan.pop("__plan_path", None)
    if source_description:
        agent.latest_user_request = source_description
    repaired = agent._repair_plan_tools_sequence(plan)
    if not agent._validate_plan(repaired):
        raise ValueError("执行计划不完整或格式错误")
    agent.current_plan = repaired
    return repaired


def _create_plan(agent: SmartWebAgent, description: str) -> Dict[str, Any]:
    _prepare_agent_run(agent, description)
    enhanced = agent._enhance_user_input(description)
    plan = agent._get_execution_plan_with_retry(enhanced)
    if not plan:
        raise RuntimeError("未能生成执行计划，请检查描述或模型配置")
    if not isinstance(plan, dict):
        raise ValueError("模型返回的计划格式异常，应为 JSON 对象")
    plan_id = uuid.uuid4().hex
    plan_path = PLAN_CACHE_DIR / f"{plan_id}.json"

    plan_for_storage = plan.copy()
    plan_for_storage["__source_description"] = description
    plan_path.write_text(
        json.dumps(plan_for_storage, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    plan["__source_description"] = description

    _PLAN_CACHE_BY_ID[plan_id] = {
        "plan": plan,
        "project_directory": agent.project_directory,
        "description": description,
        "source_description": description,
        "path": str(plan_path),
        "plan_id": plan_id,
    }

    cache_key = (agent.project_directory, description)
    _PLAN_CACHE[cache_key] = {
        "plan": plan,
        "plan_id": plan_id,
        "description": description,
        "source_description": description,
    }

    plan["__plan_id"] = plan_id
    plan["__plan_path"] = str(plan_path)
    return plan


def _execute_plan(
    agent: SmartWebAgent,
    plan: Dict[str, Any],
    *,
    progress_log_path: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    progress_events: list[Dict[str, Any]] = []

    def _collect(event: Dict[str, Any]) -> None:
        if isinstance(event, dict):
            progress_events.append(event)
            
            # 写入本地日志
            if progress_log_path:
                try:
                    log_record = dict(event)
                    log_record.setdefault("timestamp", time.time())
                    with open(progress_log_path, "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(log_record, ensure_ascii=False))
                        log_file.write("\n")
                except Exception:
                    pass
            
            # 同时写入 NAS 日志
            if job_id:
                try:
                    log_progress(job_id, **event)
                except Exception:
                    pass

    results = agent._execute_plan_with_recovery(
        plan,
        confirm_each_step=False,  # 后台执行模式，不需要确认
        progress_callback=_collect,
    )

    if any(
        r.get("status") == "success"
        and r.get("tool") in {"create_html_file", "create_css_file"}
        for r in results
    ):
        agent._run_consistency_review(plan)

    report = agent._generate_execution_report(plan, results)

    return {
        "report": report,
        "progress": progress_events,
        "results": results,
        "created_files": list(agent.created_files),
    }


# @mcp.tool()
# async def plan_site(
#     description: str,
#     project_root: Optional[str] = None,
#     context_id: Optional[str] = None,
#     context_content: Optional[str] = None,
# ) -> Dict[str, Any]:
#     """根据需求与上下文生成网页构建计划，所有信息都会交由 AI 模型统一分析。
#
#     ⚠️ 重要参数说明：
#     - description: 网站建设需求或目标，侧重描述要实现的结构、功能、风格
#     - context_content: 🔥 核心参数！网页制作所需的全部原始文本或数据
#       * 例如：地图查询结果、咖啡馆信息、产品数据、营业时间、地址等
#       * 这是模型获取上下文内容的唯一入口，不会自动从 description 推断
#       * 请把需要引用的完整信息直接放入该参数
#       * 支持各种格式：文本、JSON字符串、结构化数据等
#
#     其他参数：
#     - project_root: 可选，自定义项目根目录；缺省时使用默认目录
#     - context_id: 可选，引用已缓存的上下文快照以复用历史资料
#
#     返回值说明：
#     - status: 操作状态 ("success" 或 "error")
#     - plan_id: 生成的计划唯一标识符，用于后续执行
#     - plan_path: 计划 JSON 文件的保存路径
#     - project_directory: 解析后的项目目录路径
#     - model: 使用的 AI 模型名称
#
#     💡 使用提示：
#     如果你先用其他工具（如地图查询）获取了数据，请将结果完整传递给 context_content，
#     这样 AI 就能基于真实数据生成个性化网站。
#     """
#     try:
#         project_dir = _resolve_project_directory(project_root)
#         agent = _build_agent(project_dir)
#
#         # 直接使用 description，如果有额外的上下文则附加
#         final_description = description
#
#         # 如果提供了 context_content，附加到描述中
#         if context_content:
#             final_description = f"{description}\n\n【附加内容】\n{context_content}"
#
#         # 如果提供了 context_id，尝试获取缓存的内容
#         elif context_id:
#             cached = _resolve_cached_context(context_id)
#             if cached:
#                 cached_content = cached.get("context")
#                 if cached_content:
#                     # 尝试解析JSON格式的增强数据
#                     try:
#                         enhanced_data = json.loads(cached_content)
#                         if "original_content" in enhanced_data:
#                             cached_content = enhanced_data["original_content"]
#                     except (json.JSONDecodeError, TypeError):
#                         pass  # 使用原始内容
#
#                     if cached_content:
#                         final_description = f"{description}\n\n【缓存内容】\n{cached_content}"
#
#         # 让 AI 模型直接处理所有内容
#         plan = await asyncio.to_thread(_create_plan, agent, final_description)
#         plan_id = plan.pop("__plan_id", None)
#         plan_path = plan.pop("__plan_path", None)
#
#         return {
#             "status": "success",
#             "plan_id": plan_id,
#             "plan_path": plan_path,
#             "project_directory": project_dir,
#             "model": agent.model,
#             "message": "计划已生成，AI模型已分析所提供的全部内容"
#         }
#     except Exception as exc:
#         return {
#             "status": "error",
#             "message": str(exc),
#             "traceback": traceback.format_exc(),
#         }


@mcp.tool()
async def execute_plan(
    plan_id: str,
    *,
    project_root: str,
    # auto_plan: bool = False,  # 已禁用，没有实际作用
    # confirm_each_step: bool = False,  # 后台执行模式下用户无法交互确认
    # show_code: bool = False,  # 后台执行时用户看不到输出
    # verbose: bool = False,  # 后台执行时详细日志意义不大
    save_output: bool = False,
    progress_log: Optional[str] = None,
    auto_upload: bool = False,
    upload_url: str = "https://www.mcpcn.cc/api/fileUploadAndDownload/uploadMcpFile",
) -> Dict[str, Any]:
    """执行网页构建计划，始终以后台模式运行。

    参数详细说明：
    - plan_id: 计划的唯一标识符
        由 plan_site 工具返回的计划ID，用于从缓存或文件系统中查找对应的执行计划。
        例如："a1b2c3d4e5f6..." 这样的32位十六进制字符串。

    - project_root: 网站文件生成的目标目录路径
        指定项目文件的输出位置，可以是绝对路径或相对路径。
        例如："/path/to/my/website" 或 "./my-project"
        如果目录不存在，系统会自动创建。

    - save_output: 是否保存执行过程的详细输出到文件
        True: 会自动创建进度日志文件，记录所有执行步骤和结果
        False: 不创建进度日志文件，只保留基本的任务状态信息
        建议在调试或需要详细追踪时设置为 True

    - progress_log: 自定义进度日志文件的保存路径（可选）
        如果指定：使用该路径保存进度日志（JSONL格式）
        如果未指定但 save_output=True：自动在 ~/.mcp/make_web/progress_logs 目录创建时间戳命名的日志文件（可通过环境变量覆盖）
        如果都未指定：不记录进度日志
        路径可以是绝对路径或相对于 project_root 的相对路径

    - auto_upload: 是否在构建完成后自动上传到MCP服务器
        True: 构建完成后自动打包为ZIP并上传，返回访问URL
        False: 仅构建，不上传
        默认为 False

    - upload_url: 文件上传API地址
        默认为 "https://www.mcpcn.cc/api/fileUploadAndDownload/uploadMcpFile"
        只在 auto_upload=True 时生效

    执行流程：
    - 任务始终在后台异步执行，立即返回 job_id 和 progress_log 路径
    - 使用 get_progress(job_id=..., limit=...) 可以实时查询执行状态和进度
    - 支持通过进度日志文件追踪详细的执行步骤和结果
    - 执行完成后可以获取完整的执行报告和生成的文件列表
    - 🎯 新增：auto_upload=True时，构建完成(100%)后自动上传并返回访问URL
    """
    try:
        project_dir = _resolve_project_directory(project_root)

        # 移除 auto_plan 检查，因为参数已被移除

        if progress_log:
            progress_log_path = (
                progress_log
                if os.path.isabs(progress_log)
                else os.path.join(project_dir, progress_log)
            )
        elif save_output:
            progress_log_path = os.path.join(
                PROGRESS_LOG_DIR, f"agent_progress_{int(time.time())}.jsonl"
            )
        else:
            progress_log_path = None

        if progress_log_path:
            try:
                Path(progress_log_path).parent.mkdir(parents=True, exist_ok=True)
                Path(progress_log_path).write_text("", encoding="utf-8")
            except Exception:
                progress_log_path = None

        agent = _build_agent(
            project_dir,
            save_output=save_output,
        )

        # 通过 plan_id 查询计划
        cached_by_id = _PLAN_CACHE_BY_ID.get(plan_id)

        # 尝试多种文件命名格式
        possible_paths = [
            PLAN_CACHE_DIR / f"{plan_id}.json",  # 标准格式
            PLAN_CACHE_DIR
            / f"simple_site_plan_{plan_id}.json",  # create_simple_site格式
        ]

        plan_path = None
        for path in possible_paths:
            if path.exists():
                plan_path = path
                break

        if not cached_by_id and plan_path:
            try:
                cached_plan_file = json.loads(plan_path.read_text(encoding="utf-8"))
                source_description = None
                if isinstance(cached_plan_file, dict):
                    source_description = cached_plan_file.get("__source_description")
                    # 提取实际的plan部分，而不是整个文件内容
                    actual_plan = cached_plan_file.get("plan")
                    if not actual_plan:
                        # 如果没有plan字段，可能是旧格式，直接使用文件内容
                        actual_plan = cached_plan_file

                cached_by_id = {
                    "plan": actual_plan,  # 传递实际的plan内容
                    "project_directory": project_dir,
                    "plan_id": plan_id,
                    "description": source_description
                    or cached_plan_file.get("description"),
                    "source_description": source_description,
                }
                _PLAN_CACHE_BY_ID[plan_id] = cached_by_id
            except Exception:
                cached_by_id = None

        if not cached_by_id:
            raise ValueError(
                f"未找到 plan_id '{plan_id}' 对应的计划，请先调用 create_simple_site 生成计划"
            )

        plan_dict = _decode_plan(agent, cached_by_id.get("plan"))
        effective_description = (
            cached_by_id.get("source_description")
            or cached_by_id.get("description")
            or plan_dict.get("task_analysis")
            or plan_dict.get("project_name")
            or plan_dict.get("site_type")
            or "Web Project Execution"
        )

        _prepare_agent_run(agent, effective_description)
        agent.current_plan = plan_dict

        # 始终以后台模式执行
        job_id = uuid.uuid4().hex
        job_info = {
            "job_id": job_id,
            "status": "running",
            "plan_id": plan_id,
            "description": effective_description,
            "project_directory": project_dir,
            "model": agent.model,
            "progress_log": progress_log_path,
            "started_at": time.time(),
            "updated_at": time.time(),
        }
        _JOB_REGISTRY[job_id] = job_info

        if plan_id and progress_log_path:
            _PROGRESS_LOG_BY_ID[plan_id] = progress_log_path
        if progress_log_path:
            _PROGRESS_LOG_BY_JOB[job_id] = progress_log_path

        _persist_job_state(job_id)

        asyncio.create_task(
            _run_execution_job(
                job_id,
                agent,
                plan_dict,
                progress_log_path=progress_log_path,
                auto_upload=auto_upload,
                upload_url=upload_url,
            )
        )

        if auto_upload:
            message = (
                "执行已在后台启动（含自动上传）：调用 get_progress(job_id='{}', limit=20) "
                "可获取构建和上传进度。完成后将返回网站访问URL。"
            ).format(job_id)
        else:
            message = (
                "执行已在后台启动：调用 get_progress(job_id='{}', limit=20) "
                "或传入 progress_log='{}' 可获取实时进度"
            ).format(job_id, progress_log_path or "<未启用进度日志>")

        return {
            "status": "started",
            "job_id": job_id,
            "plan_id": plan_id,
            "progress_log": progress_log_path,
            "auto_upload": auto_upload,
            "upload_url": upload_url if auto_upload else None,
            "message": message,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }


async def _run_execution_job(
    job_id: str,
    agent: SmartWebAgent,
    plan_dict: Dict[str, Any],
    *,
    progress_log_path: Optional[str],
    auto_upload: bool = False,
    upload_url: str = "https://www.mcpcn.cc/api/fileUploadAndDownload/uploadMcpFile",
) -> None:
    job_info = _JOB_REGISTRY.get(job_id)
    if not job_info:
        return

    try:
        result = await asyncio.to_thread(
            _execute_plan,
            agent,
            plan_dict,
            progress_log_path=progress_log_path,
        )
        job_info["status"] = "completed"
        job_info["result"] = result
        job_info["completed_at"] = time.time()
        _persist_job_state(job_id)

        # 🎯 关键：任务完成后自动上传
        if auto_upload and job_info.get("project_directory"):
            try:
                # 记录上传开始
                job_info["upload_status"] = "uploading"
                _persist_job_state(job_id)

                upload_result = await upload_project_to_mcp_server(
                    folder_path=job_info["project_directory"], upload_url=upload_url
                )

                # 记录上传结果
                job_info["upload_result"] = upload_result
                job_info["upload_status"] = upload_result["status"]
                if upload_result["status"] == "success":
                    job_info["website_url"] = upload_result["url"]
                    job_info["upload_completed_at"] = time.time()

                    # 添加到进度日志
                    if progress_log_path:
                        upload_event = {
                            "timestamp": time.time(),
                            "type": "upload_completed",
                            "status": "success",
                            "website_url": upload_result["url"],
                            "message": upload_result["message"],
                        }
                        try:
                            with open(
                                progress_log_path, "a", encoding="utf-8"
                            ) as log_file:
                                log_file.write(
                                    json.dumps(upload_event, ensure_ascii=False)
                                )
                                log_file.write("\n")
                        except Exception:
                            pass

                _persist_job_state(job_id)
            except Exception as upload_exc:
                job_info["upload_status"] = "failed"
                job_info["upload_error"] = str(upload_exc)
                _persist_job_state(job_id)

    except Exception as exc:
        job_info["status"] = "failed"
        job_info["error"] = {
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        _persist_job_state(job_id)
    finally:
        job_info["updated_at"] = time.time()
        _persist_job_state(job_id)


@mcp.tool()
async def create_simple_site(
    description: str,
    site_title: str = "我的网站",
    project_root: Optional[str] = None,
    model: Optional[str] = None,
    context_id: Optional[str] = None,
    context_content: Optional[str] = None,
) -> Dict[str, Any]:
    """使用AI分析需求，生成简单但美观的网站计划。

    ⚠️ 重要参数说明：
    - description: 网站需求描述，例如"个人作品展示网站"、"小餐厅官网"、"博客网站"等
    - site_title: 网站标题
    - context_content: 🔥 核心参数！用于传递网页制作所需的所有原始数据内容
      * 例如：咖啡馆列表、产品介绍、菜单内容、地址信息、营业时间等
      * 这是AI获取具体业务信息的唯一渠道，请务必将查询到的详细信息完整传入
      * 如果有地图查询结果、API返回数据等，都应该放在这个参数中
      * 格式可以是文本、JSON字符串或结构化数据的字符串表示

    其他参数：
    - project_root: 项目根目录，缺省使用默认目录
    - model: 使用的AI模型，缺省使用默认模型
    - context_id: 可选，引用已缓存的上下文快照以复用历史资料

    图片配置参数（可选）：
    - image_style: 图片风格 (professional|artistic|minimal|vibrant|luxury)
    - image_topics: 用户自定义的图片主题列表，如 ["modern office", "team collaboration"]
    - include_gallery: 是否在网站中包含图片画廊功能
    - image_provider: 图片提供商 (pollinations|dicebear|robohash)

    返回值说明：
    - status: 操作状态 ("success" 或 "error")
    - plan_id: 生成的计划唯一标识符，用于后续执行
    - plan_path: 计划 JSON 文件的保存路径
    - project_directory: 解析后的项目目录路径
    - plan: 生成的简化执行计划概览
    - context_id: 上下文缓存ID（如果使用了上下文）

    使用流程：
    1. 调用此工具生成计划，获得 plan_id
    2. 使用 plan_id 调用 execute_plan 执行构建
    3. 使用 plan_id 调用 get_progress 查询进度

    💡 使用提示：
    如果你有地图查询结果、API数据等，请将完整信息传递给 context_content 参数，
    这样AI就能基于真实数据来生成个性化的网站内容。
    """
    try:
        # 使用指定模型或默认模型
        used_model = model or DEFAULT_MODEL

        # 确定项目目录
        if project_root:
            if not os.path.isabs(project_root):
                project_directory = os.path.join(DEFAULT_PROJECT_ROOT, project_root)
            else:
                project_directory = project_root
        else:
            # 使用站点标题作为目录名
            safe_title = "".join(
                c if c.isalnum() or c in "._-" else "_" for c in site_title
            )
            project_directory = os.path.join(DEFAULT_PROJECT_ROOT, safe_title)

        # 处理上下文
        context_data = ""
        actual_context_id = context_id

        if context_id and context_id in _CONTEXT_CACHE_BY_ID:
            # 使用缓存的上下文
            cached_context = _CONTEXT_CACHE_BY_ID[context_id]
            context_data = cached_context.get("content", "")
        elif context_content:
            # 使用新提供的上下文内容
            context_data = context_content
            # 生成新的上下文ID并缓存
            actual_context_id = str(uuid.uuid4())
            _CONTEXT_CACHE_BY_ID[actual_context_id] = {
                "content": context_content,
                "created_at": time.time(),
                "site_title": site_title,
                "description": description,
            }

        # 创建AI代理进行分析
        agent = SmartWebAgent(
            project_directory=project_directory,
            model=used_model,
            show_code=False,
            verbose=False,
            force_single_page=True,
        )

        # 构建针对简单网站的提示，包含上下文和图片要求
        context_section = ""
        if context_data:
            context_section = f"""

**上下文内容**:
{context_data}

**重要说明**: 请根据上述上下文内容来定制网站的具体内容，确保生成的网页与提供的信息高度匹配。"""

        simple_prompt = f"""请为以下需求设计一个简单但美观的网站：

**网站需求**: {description}
**网站标题**: {site_title}{context_section}

**设计要求**:
1. 保持简洁但要有视觉吸引力
2. 使用轻量级CSS（不超过300行）
3. 包含基础但实用的功能
4. 响应式设计，适配移动端
5. 良好的配色和排版
6. 智能图片集成，根据内容类型匹配合适主题
7. 如果有上下文内容，请充分利用这些信息来丰富网页内容

请生成一个包含3-6个步骤的简化执行计划，每个步骤要简洁明确。
重点关注：页面结构、样式设计、图片集成、必要功能。避免复杂特效。

输出格式要求：
- 每个步骤都要具体可执行
- 优先使用简单模板函数而非复杂模板
- 注重实用性和美观性的平衡
- 充分利用提供的上下文信息来生成个性化内容
"""

        # 生成简化计划（仅规划，不执行）
        plan = agent._get_execution_plan(simple_prompt)

        # 在计划中标记为简单网站类型和相关信息
        plan["site_type"] = "simple"
        plan["complexity"] = "简单但美观"
        plan["css_limit"] = "不超过300行"
        plan["model_used"] = used_model
        plan["has_context"] = bool(context_data)
        if actual_context_id:
            plan["context_id"] = actual_context_id

        # 生成唯一的计划ID
        plan_id = str(uuid.uuid4())

        # 构建完整的源描述（包含上下文）
        source_description = description
        if context_data:
            source_description = f"{description}\n\n【附加内容】\n{context_data}"

        # 在计划中添加源描述字段
        plan["__source_description"] = source_description
        plan["__plan_id"] = plan_id

        # 保存计划到缓存（结构与 create_simple_site 保持一致，便于 execute_plan 复用逻辑）
        cached_entry = {
            "plan": plan,
            "project_directory": project_directory,
            "description": description,
            "source_description": source_description,
            "site_title": site_title,
            "plan_id": plan_id,
        }

        _PLAN_CACHE_BY_ID[plan_id] = cached_entry
        cache_key = (project_directory, description)
        _PLAN_CACHE[cache_key] = cached_entry

        # 将上下文信息关联到计划
        if actual_context_id:
            _PROGRESS_LOG_BY_ID[plan_id] = actual_context_id

        # 保存计划到文件
        plan_filename = f"simple_site_plan_{plan_id}.json"
        plan_path = PLAN_CACHE_DIR / plan_filename

        try:
            # 构建完整的源描述（包含上下文）
            source_description = description
            if context_data:
                source_description = f"{description}\n\n【附加内容】\n{context_data}"

            plan_data = {
                "plan_id": plan_id,
                "site_title": site_title,
                "description": description,
                "project_directory": project_directory,
                "model": used_model,
                "plan_type": "simple_site",
                "created_at": time.time(),
                "plan": plan,
                "__source_description": source_description,  # 添加完整的源描述字段
            }
            if actual_context_id:
                plan_data["context_id"] = actual_context_id
                plan_data["has_context"] = True

            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan_data, f, ensure_ascii=False, indent=2)
        except Exception:
            # 文件保存失败不影响主流程
            pass

        # 生成计划概览
        tools_sequence = plan.get("tools_sequence", [])
        plan_overview = {
            "description": plan.get("description", "简单网站构建计划"),
            "steps": len(tools_sequence),
            "step_list": [
                step.get("description", step.get("tool", "")) for step in tools_sequence
            ],
            "estimated_files": plan.get("estimated_files", "3-5个文件"),
            "features": plan.get("features", ["响应式设计", "轻量级样式", "基础交互"]),
            "has_context": bool(context_data),
        }

        result = {
            "status": "success",
            "message": f"简单网站计划生成成功，包含{len(tools_sequence)}个执行步骤",
            "plan_id": plan_id,
            "plan_path": str(plan_path),
            "project_directory": project_directory,
            "plan": plan_overview,
            "model_used": used_model,
            "next_step": f"使用 execute_plan(plan_id='{plan_id}') 开始构建网站",
        }

        if actual_context_id:
            result["context_id"] = actual_context_id
            result["context_used"] = True

        return result

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
async def get_progress(
    plan_id: Optional[str] = None,
    job_id: Optional[str] = None,
    log_path: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """查询网页构建任务的执行进度和状态。

    参数说明：
    - plan_id: create_simple_site 返回的 ID，可定位默认的进度日志。
    - job_id: execute_plan(background=true) 返回的任务 ID，可直接查询后台任务状态。
    - log_path: 进度日志 JSONL 文件的路径（绝对或相对），优先级最高。
    - limit: 返回的最新事件数量（默认 20 条）。

    使用提示：
    1. 推荐直接传入 execute_plan 返回的 job_id 和 progress_log。
    2. 若未提供 log_path，本工具会按 job_id -> plan_id 的顺序尝试查找已缓存的日志。
    3. 返回内容包括最新事件列表、日志路径以及（若有）任务快照或结果摘要，可用于持续追踪构建进度。
    """

    try:
        # SSE 模式优化：使用异步 I/O
        loop = asyncio.get_event_loop()
        
        if limit <= 0:
            limit = 20

        job_info = None
        resolved_path = None

        if job_id:
            job_info = _JOB_REGISTRY.get(job_id)
            if job_info and not plan_id:
                plan_id = job_info.get("plan_id")
            if job_id in _PROGRESS_LOG_BY_JOB:
                resolved_path = _PROGRESS_LOG_BY_JOB[job_id]
            elif job_info and job_info.get("progress_log"):
                resolved_path = job_info.get("progress_log")

        if not resolved_path and plan_id and plan_id in _PROGRESS_LOG_BY_ID:
            resolved_path = _PROGRESS_LOG_BY_ID[plan_id]

        if log_path:
            resolved_path = log_path

        if resolved_path:
            if not os.path.isabs(resolved_path):
                candidate = os.path.join(PROJECT_ROOT, resolved_path)
                # 异步检查文件存在
                exists = await loop.run_in_executor(None, os.path.exists, candidate)
                if exists:
                    resolved_path = candidate
                else:
                    alt = os.path.sep + resolved_path.lstrip(os.path.sep)
                    exists_alt = await loop.run_in_executor(None, os.path.exists, alt)
                    if exists_alt:
                        resolved_path = alt

        # 异步检查最终路径
        path_exists = await loop.run_in_executor(
            None, lambda: resolved_path and os.path.exists(resolved_path)
        )
        
        if not path_exists:
            return {
                "status": "error",
                "message": "未找到进度日志，请确认 job_id/plan_id 或提供 log_path（注意绝对路径需以/开头，扩展名为 .jsonl）",
            }

        # 异步读取文件
        def read_file():
            events = []
            total = 0
            try:
                with open(resolved_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    total = len(lines)
                    for line in lines[-limit:]:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(json.loads(line))
                        except Exception:
                            continue
            except Exception:
                pass
            return events, total
        
        events, total_lines = await loop.run_in_executor(None, read_file)

        response: Dict[str, Any] = {
            "status": "success",
            "plan_id": plan_id,
            "job_id": job_id,
            "log_path": resolved_path,
            "events": events,
            "total_records": total_lines,
            "returned": len(events),
        }

        if job_info:
            snapshot_keys = [
                "job_id",
                "status",
                "plan_id",
                "progress_log",
                "started_at",
                "updated_at",
                "completed_at",
                "project_directory",
                "model",
                "upload_status",
                "website_url",
                "upload_completed_at",
            ]
            job_snapshot = {
                k: job_info.get(k) for k in snapshot_keys if job_info.get(k) is not None
            }

            if job_info.get("status") == "completed":
                job_snapshot["result_summary"] = {
                    "report": job_info.get("result", {}).get("report"),
                    "created_files": job_info.get("result", {}).get("created_files"),
                }
                # 添加上传结果信息
                if job_info.get("upload_result"):
                    job_snapshot["upload_result"] = job_info.get("upload_result")

            if job_info.get("status") == "failed":
                job_snapshot["error"] = job_info.get("error")

            # 添加上传错误信息
            if job_info.get("upload_error"):
                job_snapshot["upload_error"] = job_info.get("upload_error")

            response["job"] = job_snapshot

        return response
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
async def upload_project_to_mcp_server(
    folder_path: str,
    upload_url: str = "https://www.mcpcn.cc/api/fileUploadAndDownload/uploadMcpFile",
) -> Dict[str, Any]:
    """将项目文件夹打包成ZIP并上传到MCP服务器。

    参数说明：
    - folder_path: 项目文件夹的绝对路径
    - upload_url: 上传API地址，默认为MCP服务器地址

    返回值：
    - status: 上传状态 ("success" 或 "error")
    - url: 上传成功后返回的文件访问URL
    - zip_path: 临时ZIP文件路径（用于调试）
    - message: 状态信息
    """
    try:
        # 验证文件夹路径
        if not os.path.exists(folder_path):
            return {"status": "error", "message": f"项目文件夹不存在: {folder_path}"}

        if not os.path.isdir(folder_path):
            return {"status": "error", "message": f"路径不是文件夹: {folder_path}"}

        # 创建临时ZIP文件
        project_name = os.path.basename(folder_path.rstrip("/"))
        temp_dir = tempfile.gettempdir()
        zip_filename = f"{project_name}_{int(time.time())}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        # 打包项目文件
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径，保持目录结构
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

        # 检查ZIP文件大小
        zip_size = os.path.getsize(zip_path)
        if zip_size > 50 * 1024 * 1024:  # 50MB限制
            os.remove(zip_path)
            return {
                "status": "error",
                "message": f"ZIP文件过大: {zip_size / 1024 / 1024:.1f}MB，超过50MB限制",
            }

        # 上传文件
        async with aiohttp.ClientSession() as session:
            with open(zip_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field(
                    "file", f, filename=zip_filename, content_type="application/zip"
                )

                async with session.post(upload_url, data=data) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        return {
                            "status": "error",
                            "message": f"上传失败，HTTP {response.status}: {response_text}",
                        }

                    # 解析响应JSON
                    try:
                        result = json.loads(response_text)
                        if result.get("code") == 0 and result.get("data", {}).get(
                            "url"
                        ):
                            # 清理临时文件
                            try:
                                os.remove(zip_path)
                            except:
                                pass

                            return {
                                "status": "success",
                                "url": result["data"]["url"],
                                "message": f"项目 '{project_name}' 上传成功",
                                "zip_size": f"{zip_size / 1024:.1f}KB",
                            }
                        else:
                            return {
                                "status": "error",
                                "message": f"上传失败: {result.get('msg', '未知错误')}",
                                "response": response_text,
                            }
                    except json.JSONDecodeError:
                        return {
                            "status": "error",
                            "message": f"响应解析失败: {response_text}",
                        }

    except Exception as exc:
        # 清理临时文件
        if "zip_path" in locals() and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass

        return {
            "status": "error",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
async def deploy_folder_or_zip(
    folder_path: str, env: str = "Production"
) -> Dict[str, Any]:
    """将构建好的网站文件夹或ZIP文件部署到EdgeOne Pages。

    参数说明：
    - folder_path: 本地文件夹或ZIP文件的绝对路径
        指定要部署的前端构建产物位置，可以是：
        * 构建好的静态网站文件夹（如 ./dist, ./build 等）
        * 包含网站文件的ZIP压缩包
        系统会自动检测路径类型并采用相应的上传策略

    - env: 部署环境（可选）
        * "Production": 生产环境部署，使用自定义域名（如已配置）
        * "Preview": 预览环境部署，生成临时预览链接
        默认为 "Production"

    环境变量要求：
    - EDGEONE_PAGES_API_TOKEN: EdgeOne Pages API访问令牌（必需）
    - EDGEONE_PAGES_PROJECT_NAME: 项目名称（可选，未指定时自动创建临时项目）

    返回值说明：
    - status: 部署状态 ("success" 或 "error")
    - deployment_logs: 详细的部署过程日志
    - result: 部署结果信息
        * type: 域名类型 ("custom" 自定义域名 或 "temporary" 临时域名)
        * url: 网站访问URL
        * project_id: EdgeOne项目ID
        * project_name: 项目名称
        * console_url: EdgeOne控制台管理链接

    使用场景：
    1. 将本地开发的静态网站部署上线
    2. 将构建工具（如Webpack、Vite等）生成的dist目录部署
    3. 将打包好的网站ZIP文件快速部署
    4. 创建网站的预览版本进行测试

    部署流程：
    1. 验证本地路径和文件
    2. 检测可用的API端点
    3. 获取或创建EdgeOne项目
    4. 上传文件到腾讯云COS
    5. 创建部署任务并等待完成
    6. 生成访问链接和管理信息

    ⚠️ 注意事项：
    - 需要有效的EdgeOne Pages API令牌
    - 确保网络连接正常，上传可能需要一些时间
    - 大文件或大量文件的上传会相应增加部署时间
    - 临时域名链接包含时效性访问令牌
    """
    try:
        # 导入EdgeOne部署工具
        from htmlgen_mcp.agents.web_tools.edgeone_deploy import deploy_folder_or_zip_to_edgeone

        # 验证环境变量
        api_token = os.getenv("EDGEONE_PAGES_API_TOKEN")
        if not api_token:
            return {
                "status": "error",
                "message": "Missing EDGEONE_PAGES_API_TOKEN environment variable. Please set your EdgeOne Pages API token.",
            }

        # 验证路径格式
        if not os.path.isabs(folder_path):
            return {
                "status": "error",
                "message": f"Path must be absolute: {folder_path}",
            }

        # 验证环境参数
        if env not in ["Production", "Preview"]:
            return {
                "status": "error",
                "message": "env must be 'Production' or 'Preview'",
            }

        # 执行部署
        result_json = await asyncio.to_thread(
            deploy_folder_or_zip_to_edgeone, folder_path, env
        )
        result = json.loads(result_json)

        return {
            "status": "success",
            "message": f"Deployment to {env} environment completed successfully",
            "deployment_logs": result.get("deployment_logs", ""),
            "result": result.get("result", {}),
        }

    except Exception as exc:
        error_message = str(exc)

        # 如果是EdgeOne部署错误，尝试解析JSON格式的错误信息
        try:
            if error_message.startswith("{"):
                error_data = json.loads(error_message)
                return {
                    "status": "error",
                    "message": error_data.get("error", error_message),
                    "deployment_logs": error_data.get("deployment_logs", ""),
                    "traceback": traceback.format_exc(),
                }
        except:
            pass

        return {
            "status": "error",
            "message": error_message,
            "traceback": traceback.format_exc(),
        }


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    print("🚀 Smart Web Agent MCP 服务器已启动")
    print(f"📁 默认项目根目录: {DEFAULT_PROJECT_ROOT}")
    print(f"🤖 默认模型: {DEFAULT_MODEL}")
    print(f"🌐 默认API地址: {DEFAULT_BASE_URL}")
    print("🌐 EdgeOne Pages 部署工具已加载")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
