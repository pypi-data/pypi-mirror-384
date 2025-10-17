#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EdgeOne Pages 部署工具
用于将构建好的网站文件夹或ZIP文件部署到腾讯云EdgeOne Pages
"""

import os
import json
import time
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API端点配置
BASE_API_URL1 = 'https://pages-api.cloud.tencent.com/v1'
BASE_API_URL2 = 'https://pages-api.edgeone.ai/v1'

class EdgeOneDeployError(Exception):
    """EdgeOne部署相关异常"""
    pass

class EdgeOneDeployer:
    """EdgeOne Pages 部署器"""

    def __init__(self):
        self.base_api_url = ""
        self.api_token = self._get_api_token()
        self.project_name = os.getenv('EDGEONE_PAGES_PROJECT_NAME', '')
        self.temp_project_name = None
        self.deployment_logs = []

    def _get_api_token(self) -> str:
        """获取API令牌"""
        token = os.getenv('EDGEONE_PAGES_API_TOKEN')
        if not token:
            raise EdgeOneDeployError(
                'Missing EDGEONE_PAGES_API_TOKEN. Please set it as an environment variable.'
            )
        return token

    def _get_temp_project_name(self) -> str:
        """生成临时项目名"""
        if not self.temp_project_name:
            # 基于当前工作目录生成项目名，或者如果有local_path，使用其基名
            import os
            if hasattr(self, 'local_path') and self.local_path:
                folder_name = os.path.basename(os.path.abspath(self.local_path))
            else:
                folder_name = os.path.basename(os.getcwd())

            # 清理文件夹名称，确保符合EdgeOne项目名称要求：只能包含小写字母、数字和短划线
            clean_name = ''.join(c.lower() if c.isalnum() else '-' for c in folder_name if c.isalnum() or c in '-_')
            # 移除开头和结尾的短划线，并去除连续的短划线
            clean_name = '-'.join(filter(None, clean_name.split('-')))

            if not clean_name or len(clean_name) < 3:
                clean_name = "local-upload"

            # 添加时间戳确保唯一性
            self.temp_project_name = f"{clean_name}-{int(time.time())}"
        return self.temp_project_name

    def _log(self, level: str, message: str) -> None:
        """记录日志"""
        log_entry = {
            'timestamp': time.time(),
            'level': level,
            'message': message
        }
        self.deployment_logs.append(log_entry)
        print(f"[{level}] {message}")

    async def _check_and_set_base_url(self) -> None:
        """检测并设置可用的API端点"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        body = {
            'Action': 'DescribePagesProjects',
            'PageNumber': 1,
            'PageSize': 10
        }

        # 测试第一个端点
        try:
            response1 = requests.post(BASE_API_URL1, headers=headers, json=body, timeout=10)
            json1 = response1.json()
            if json1.get('Code') == 0:
                self.base_api_url = BASE_API_URL1
                self._log('INFO', 'Using BASE_API_URL1 endpoint')
                return
        except Exception:
            pass

        # 测试第二个端点
        try:
            response2 = requests.post(BASE_API_URL2, headers=headers, json=body, timeout=10)
            json2 = response2.json()
            if json2.get('Code') == 0:
                self.base_api_url = BASE_API_URL2
                self._log('INFO', 'Using BASE_API_URL2 endpoint')
                return
        except Exception:
            pass

        raise EdgeOneDeployError(
            'Invalid EDGEONE_PAGES_API_TOKEN or API endpoints unreachable. '
            'Please check your API token and network connection.'
        )

    def _make_api_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发起API请求"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        body = {'Action': action, **data}

        try:
            response = requests.post(self.base_api_url, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise EdgeOneDeployError(f'API request failed: {str(e)}')

    def _describe_pages_projects(self, project_id: Optional[str] = None,
                                project_name: Optional[str] = None) -> Dict[str, Any]:
        """查询Pages项目"""
        filters = []
        if project_id:
            filters.append({'Name': 'ProjectId', 'Values': [project_id]})
        if project_name:
            filters.append({'Name': 'Name', 'Values': [project_name]})

        data = {
            'Filters': filters,
            'Offset': 0,
            'Limit': 10,
            'OrderBy': 'CreatedOn'
        }

        return self._make_api_request('DescribePagesProjects', data)

    def _create_pages_project(self) -> Dict[str, Any]:
        """创建Pages项目"""
        project_name = self.project_name or self._get_temp_project_name()

        # 验证和清理项目名称，确保符合EdgeOne要求
        def validate_project_name(name: str) -> str:
            """验证并清理项目名称，确保只包含小写字母、数字和短划线"""
            if not name or name == "your_project_name":
                # 如果名称无效，使用临时名称
                return self._get_temp_project_name()

            # 清理名称：转换为小写，替换无效字符为短划线
            clean_name = ''.join(c.lower() if c.isalnum() else '-' for c in name if c.isalnum() or c in '-_')
            # 移除开头和结尾的短划线，并去除连续的短划线
            clean_name = '-'.join(filter(None, clean_name.split('-')))

            if not clean_name or len(clean_name) < 3:
                return self._get_temp_project_name()

            return clean_name

        project_name = validate_project_name(project_name)

        data = {
            'Name': project_name,
            'Provider': 'Upload',
            'Channel': 'Custom',
            'Area': 'global'
        }

        self._log('INFO', f'Creating new project: {project_name}')
        result = self._make_api_request('CreatePagesProject', data)

        # 添加调试信息以了解API响应结构
        self._log('DEBUG', f'CreatePagesProject API response: {json.dumps(result, ensure_ascii=False, indent=2)}')

        if result.get('Code') != 0:
            raise EdgeOneDeployError(f"Failed to create project: {result.get('Message', 'Unknown error')}")

        # 检查API响应中是否有错误
        response_data = result.get('Data', {}).get('Response', {})
        if 'Error' in response_data:
            error_info = response_data['Error']
            raise EdgeOneDeployError(f"API Error [{error_info.get('Code', 'Unknown')}]: {error_info.get('Message', 'Unknown error')}")

        # 尝试从不同可能的响应结构中获取项目ID
        project_id = None
        if 'Data' in result and 'Response' in result['Data']:
            response = result['Data']['Response']
            # 尝试不同的可能字段名
            project_id = response.get('ProjectId') or response.get('ProjectID') or response.get('Id') or response.get('ID')

        if not project_id:
            # 如果没有找到项目ID，抛出详细错误
            raise EdgeOneDeployError(f"ProjectId not found in API response. Response structure: {json.dumps(result, ensure_ascii=False, indent=2)}")

        self._log('INFO', f'Created project with ID: {project_id}')
        return self._describe_pages_projects(project_id=project_id)

    def _get_or_create_project(self) -> str:
        """获取或创建项目，返回项目ID"""
        if self.project_name:
            # 查找现有项目
            result = self._describe_pages_projects(project_name=self.project_name)
            projects = result['Data']['Response']['Projects']
            if projects:
                self._log('INFO', f'Project {self.project_name} already exists')
                return projects[0]['ProjectId']

        # 创建新项目
        self._log('INFO', 'Creating new project')
        result = self._create_pages_project()
        projects = result['Data']['Response']['Projects']
        if not projects:
            raise EdgeOneDeployError('Failed to retrieve project after creation')

        return projects[0]['ProjectId']

    def _get_cos_temp_token(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """获取COS临时令牌"""
        if project_id:
            data = {'ProjectId': project_id}
        else:
            data = {'ProjectName': self._get_temp_project_name()}

        result = self._make_api_request('DescribePagesCosTempToken', data)

        if result.get('Code') != 0:
            raise EdgeOneDeployError(f"Failed to get COS token: {result.get('Message', 'Unknown error')}")

        return result['Data']['Response']

    def _validate_path(self, local_path: str) -> Tuple[bool, bool]:
        """验证路径，返回(是否存在, 是否为ZIP文件)"""
        path_obj = Path(local_path)

        if not path_obj.exists():
            raise EdgeOneDeployError(f'Path does not exist: {local_path}')

        is_zip = path_obj.suffix.lower() == '.zip'

        if not path_obj.is_dir() and not is_zip:
            raise EdgeOneDeployError('Path must be a directory or ZIP file')

        return True, is_zip

    def _list_folder_files(self, folder_path: str) -> List[Dict[str, Any]]:
        """递归列出文件夹中的所有文件"""
        files = []
        folder_path = Path(folder_path)

        for item in folder_path.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(folder_path)
                files.append({
                    'path': str(item),
                    'relative_path': str(relative_path).replace('\\', '/'),
                    'size': item.stat().st_size
                })

        if len(files) > 1000000:
            raise EdgeOneDeployError('Too many files (>1M), operation cancelled')

        return files

    def _upload_to_cos(self, local_path: str, cos_config: Dict[str, Any], is_zip: bool) -> str:
        """上传文件到COS"""
        try:
            # 这里需要安装 cos-python-sdk-v5
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise EdgeOneDeployError(
                'Missing cos-python-sdk-v5 dependency. Please install: pip install cos-python-sdk-v5'
            )

        credentials = cos_config['Credentials']
        bucket = cos_config['Bucket']
        region = cos_config['Region']
        target_path = cos_config['TargetPath']

        # 初始化COS客户端
        config = CosConfig(
            Region=region,
            SecretId=credentials['TmpSecretId'],
            SecretKey=credentials['TmpSecretKey'],
            Token=credentials['Token']
        )
        client = CosS3Client(config)

        if is_zip:
            # 上传ZIP文件
            filename = os.path.basename(local_path)
            key = f"{target_path}/{filename}"

            self._log('INFO', f'Uploading ZIP file: {filename}')

            with open(local_path, 'rb') as f:
                client.put_object(
                    Bucket=bucket,
                    Body=f,
                    Key=key
                )

            self._log('INFO', 'ZIP file upload completed')
            return key
        else:
            # 上传文件夹
            files = self._list_folder_files(local_path)
            self._log('INFO', f'Uploading {len(files)} files to COS')

            for file_info in files:
                key = f"{target_path}/{file_info['relative_path']}"

                with open(file_info['path'], 'rb') as f:
                    client.put_object(
                        Bucket=bucket,
                        Body=f,
                        Key=key
                    )

            self._log('INFO', 'Folder upload completed')
            return target_path

    def _create_pages_deployment(self, project_id: str, target_path: str,
                                is_zip: bool, env: str = 'Production') -> str:
        """创建Pages部署"""
        data = {
            'ProjectId': project_id,
            'ViaMeta': 'Upload',
            'Provider': 'Upload',
            'Env': env,
            'DistType': 'Zip' if is_zip else 'Folder',
            'TempBucketPath': target_path
        }

        self._log('INFO', f'Creating deployment in {env} environment')
        result = self._make_api_request('CreatePagesDeployment', data)

        if result.get('Code') != 0:
            raise EdgeOneDeployError(f"Deployment creation failed: {result.get('Message', 'Unknown error')}")

        if result.get('Data', {}).get('Response', {}).get('Error'):
            error_msg = result['Data']['Response']['Error']['Message']
            raise EdgeOneDeployError(f"Deployment creation failed: {error_msg}")

        return result['Data']['Response']['DeploymentId']

    def _describe_pages_deployments(self, project_id: str) -> Dict[str, Any]:
        """查询Pages部署状态"""
        data = {
            'ProjectId': project_id,
            'Offset': 0,
            'Limit': 50,
            'OrderBy': 'CreatedOn',
            'Order': 'Desc'
        }

        return self._make_api_request('DescribePagesDeployments', data)

    def _poll_deployment_status(self, project_id: str, deployment_id: str) -> Dict[str, Any]:
        """轮询部署状态直到完成"""
        self._log('INFO', 'Waiting for deployment to complete')

        while True:
            result = self._describe_pages_deployments(project_id)
            deployments = result['Data']['Response']['Deployments']

            deployment = None
            for deploy in deployments:
                if deploy['DeploymentId'] == deployment_id:
                    deployment = deploy
                    break

            if not deployment:
                raise EdgeOneDeployError(f'Deployment {deployment_id} not found')

            status = deployment['Status']
            self._log('INFO', f'Deployment status: {status}')

            if status != 'Process':
                return deployment

            time.sleep(5)

    def _describe_pages_encipher_token(self, url: str) -> Dict[str, Any]:
        """获取页面访问令牌"""
        data = {'Text': url}
        return self._make_api_request('DescribePagesEncipherToken', data)

    def _get_project_console_url(self, project_id: str) -> str:
        """获取项目控制台URL"""
        if self.base_api_url == BASE_API_URL1:
            return f"https://console.cloud.tencent.com/edgeone/pages/project/{project_id}/index"
        else:
            return f"https://console.tencentcloud.com/edgeone/pages/project/{project_id}/index"

    def _format_deployment_result(self, deployment: Dict[str, Any],
                                 project_id: str, env: str = 'Production') -> Dict[str, Any]:
        """格式化部署结果"""
        if deployment['Status'] != 'Success':
            raise EdgeOneDeployError(f"Deployment failed with status: {deployment['Status']}")

        # 获取项目信息
        project_result = self._describe_pages_projects(project_id=project_id)
        projects = project_result['Data']['Response']['Projects']
        if not projects:
            raise EdgeOneDeployError('Failed to retrieve project information')

        project = projects[0]

        # 检查是否有自定义域名
        if (env == 'Production' and
            project.get('CustomDomains') and
            len(project['CustomDomains']) > 0):

            custom_domain = project['CustomDomains'][0]
            if custom_domain['Status'] == 'Pass':
                return {
                    'type': 'custom',
                    'url': f"https://{custom_domain['Domain']}",
                    'project_id': project_id,
                    'project_name': project['Name'],
                    'console_url': self._get_project_console_url(project_id)
                }

        # 使用预设域名
        domain = deployment.get('PreviewUrl', '').replace('https://', '') or project['PresetDomain']

        # 获取访问令牌
        token_result = self._describe_pages_encipher_token(domain)

        if token_result.get('Code') != 0:
            raise EdgeOneDeployError(f"Failed to get access token: {token_result.get('Message', 'Unknown error')}")

        token_data = token_result['Data']['Response']
        token = token_data['Token']
        timestamp = token_data['Timestamp']

        url = f"https://{domain}?eo_token={token}&eo_time={timestamp}"

        return {
            'type': 'temporary',
            'url': url,
            'project_id': project_id,
            'project_name': project['Name'],
            'console_url': self._get_project_console_url(project_id)
        }

    def deploy_folder_or_zip(self, local_path: str, env: str = 'Production') -> str:
        """
        部署文件夹或ZIP文件到EdgeOne Pages

        Args:
            local_path: 本地文件夹或ZIP文件路径
            env: 部署环境，'Production' 或 'Preview'

        Returns:
            部署结果的JSON字符串
        """
        try:
            # 保存local_path以供其他方法使用
            self.local_path = local_path
            self.deployment_logs = []
            self._log('INFO', f'Starting deployment of {local_path}')

            # 验证路径
            _, is_zip = self._validate_path(local_path)

            # 检查API端点
            import asyncio
            asyncio.run(self._check_and_set_base_url())

            # 获取或创建项目
            project_id = self._get_or_create_project()
            self._log('INFO', f'Using project ID: {project_id}')

            # 获取COS配置
            cos_config = self._get_cos_temp_token(project_id)

            # 上传到COS
            target_path = self._upload_to_cos(local_path, cos_config, is_zip)

            # 创建部署
            deployment_id = self._create_pages_deployment(project_id, target_path, is_zip, env)

            # 等待部署完成
            time.sleep(5)  # 等待5秒让部署开始
            deployment = self._poll_deployment_status(project_id, deployment_id)

            # 格式化结果
            result = self._format_deployment_result(deployment, project_id, env)

            # 准备返回结果
            logs_text = "\n".join([f"{log['level']}: {log['message']}" for log in self.deployment_logs])

            final_result = {
                'status': 'success',
                'deployment_logs': logs_text,
                'result': result
            }

            return json.dumps(final_result, ensure_ascii=False, indent=2)

        except Exception as e:
            # 错误处理
            logs_text = "\n".join([f"{log['level']}: {log['message']}" for log in self.deployment_logs])
            error_result = {
                'status': 'error',
                'deployment_logs': logs_text,
                'error': str(e)
            }
            raise EdgeOneDeployError(json.dumps(error_result, ensure_ascii=False, indent=2))


# 为了兼容原来的函数调用方式
def deploy_folder_or_zip_to_edgeone(local_path: str, env: str = 'Production') -> str:
    """
    部署文件夹或ZIP文件到EdgeOne Pages（函数式接口）

    Args:
        local_path: 本地文件夹或ZIP文件的绝对路径
        env: 部署环境，'Production' 或 'Preview'

    Returns:
        部署结果的JSON字符串
    """
    deployer = EdgeOneDeployer()
    return deployer.deploy_folder_or_zip(local_path, env)