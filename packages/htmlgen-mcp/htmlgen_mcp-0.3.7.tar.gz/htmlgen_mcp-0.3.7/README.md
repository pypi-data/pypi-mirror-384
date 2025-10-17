# HTML Generator MCP

一个基于 Model Context Protocol (MCP) 的智能网页生成服务，支持AI驱动的网站创建、实时进度追踪和自动部署功能。

## ✨ 主要特性

- 🤖 **AI驱动生成**: 使用大语言模型智能分析需求，生成个性化网站
- 📊 **实时进度追踪**: 支持任务状态监控和进度查询
- 🚀 **自动部署上传**: 构建完成后自动打包上传到云端
- 🎨 **现代化设计**: 响应式布局，支持移动端适配
- 🔧 **灵活配置**: 支持多种模型和自定义配置

## 🚀 快速开始

### 安装

```bash
pip install agent-mcp
```

### 基本使用

1. **创建网站计划**
```python
import asyncio
from MCP.web_agent_server import create_simple_site

async def main():
    result = await create_simple_site(
        description="创建一个现代化的咖啡店网站",
        site_title="星巴克咖啡",
        context_content="地址：北京市朝阳区，营业时间：7:00-22:00"
    )
    print(f"计划ID: {result['plan_id']}")

asyncio.run(main())
```

2. **执行构建（含自动上传）**
```python
from MCP.web_agent_server import execute_plan

result = await execute_plan(
    plan_id="your_plan_id",
    project_root="/path/to/project",
    auto_upload=True,  # 🎯 构建完成后自动上传
    save_output=True
)
```

3. **查询进度**
```python
from MCP.web_agent_server import get_progress

progress = await get_progress(job_id=result["job_id"])
print(f"状态: {progress['job']['status']}")

# 如果启用了自动上传
if progress['job'].get('upload_status') == 'success':
    print(f"网站地址: {progress['job']['website_url']}")
```

## 🛠️ MCP 工具

- `create_simple_site()` - 生成网站计划
- `execute_plan()` - 执行网站构建
- `get_progress()` - 查询构建进度
- `upload_project_to_mcp_server()` - 手动上传项目
- `deploy_folder_or_zip()` - 部署到EdgeOne Pages

## 🔧 环境配置

创建 `.env` 文件：

```env
# AI模型配置
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your_api_key
WEB_AGENT_MODEL=qwen3-coder-plus-2025-09-23

# 项目路径（可选）
WEB_AGENT_PROJECT_ROOT=/path/to/projects

# EdgeOne Pages 部署（可选）
EDGEONE_PAGES_API_TOKEN=your_token
EDGEONE_PAGES_PROJECT_NAME=your_project
```

## 🎯 自动上传功能

构建完成时自动上传到云端，无需手动操作：

```python
# 启动带自动上传的构建
result = await execute_plan(
    plan_id="plan_id",
    project_root="./my-website",
    auto_upload=True  # 关键参数
)

# 监听进度变化
while True:
    progress = await get_progress(job_id=result["job_id"])

    status = progress['job']['status']
    if status == 'completed':
        upload_status = progress['job'].get('upload_status')
        if upload_status == 'success':
            print(f"🎉 网站已上线: {progress['job']['website_url']}")
            break
        elif upload_status == 'failed':
            print("❌ 上传失败")
            break

    await asyncio.sleep(2)
```

## 📋 进度状态

- **构建阶段**: `running` → `completed`
- **上传阶段**: `uploading` → `success`/`failed`
- **最终结果**: `website_url` (成功时)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
