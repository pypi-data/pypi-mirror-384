"""AI 内容生成辅助模块 - 为页面生成个性化内容"""
from __future__ import annotations

import json
from typing import Dict, Any, Optional


class AIContentGenerator:
    """AI 内容生成器 - 为各种页面生成个性化内容"""
    
    def __init__(self, agent_instance):
        """初始化生成器
        
        Args:
            agent_instance: SmartWebAgent 实例
        """
        self.agent = agent_instance
    
    def generate_menu_content(
        self, 
        project_name: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """为菜单页面生成个性化内容"""
        
        prompt = f"""你是一个专业的网页内容创作者。
为"{project_name}"生成一个详细的菜单内容。

项目信息：
- 名称：{project_name}
- 描述：{context.get('description', '')}
- 特色：{context.get('features', '')}
- 位置：{context.get('location', '')}
- 目标客户：{context.get('target_audience', '')}

请生成一个完整的菜单，包含：
1. 2-4个类别（如：热饮、冷饮、轻食、甜点）
2. 每个类别3-5个项目
3. 每个项目包含：
   - name: 产品名称（有创意且符合品牌）
   - price: 价格（符合定位，使用"¥"符号）
   - description: 描述（简短吸引人，20字以内）
   - image_topic: 图片主题描述（英文，用于生成图片）

返回 JSON 格式：
{{
  "categories": [
    {{
      "name": "类别名称",
      "items": [
        {{
          "name": "产品名称",
          "price": "¥ XX",
          "description": "产品描述",
          "image_topic": "image description"
        }}
      ]
    }}
  ],
  "description": "菜单页面的副标题描述"
}}

重要：
- 内容要符合项目的定位和风格
- 价格要合理且有梯度
- 描述要诱人且真实
- 直接返回 JSON，不要其他内容
"""
        
        try:
            response = self.agent.client.chat.completions.create(
                model=self.agent.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的内容创作者，擅长为各类商业项目创作个性化内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            # 清理可能的 markdown 代码块标记
            if content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            return json.loads(content)
            
        except Exception as e:
            print(f"AI 生成菜单内容失败：{e}")
            # 返回空内容，让页面使用默认值
            return {}
    
    def generate_about_content(
        self, 
        project_name: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """为关于页面生成个性化内容"""
        
        prompt = f"""为"{project_name}"生成"关于我们"页面的内容。

项目信息：
- 名称：{project_name}
- 描述：{context.get('description', '')}
- 使命：{context.get('mission', '')}
- 特色：{context.get('features', '')}
- 创始年份：{context.get('year_founded', '2020')}

请生成以下内容（JSON格式）：
{{
  "headline": "页面主标题",
  "subtitle": "副标题（一句话介绍）",
  "story": {{
    "title": "品牌故事标题",
    "content": "品牌故事内容（100-150字）",
    "image_topic": "story image description"
  }},
  "values": ["价值观1", "价值观2", "价值观3", "价值观4"],
  "team": [
    {{
      "name": "团队成员姓名",
      "role": "职位",
      "description": "简介（20字以内）",
      "image_topic": "team member photo description"
    }}
  ],
  "achievements": [
    {{"value": "数值", "label": "标签"}},
    {{"value": "数值", "label": "标签"}}
  ],
  "cta_title": "行动号召标题",
  "cta_text": "行动号召文字"
}}

要求：
- 内容真实可信，避免夸大
- 团队成员生成2-3个核心岗位即可
- 成就数据要合理
- 符合品牌调性
"""
        
        try:
            response = self.agent.client.chat.completions.create(
                model=self.agent.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            return json.loads(content)
            
        except Exception as e:
            print(f"AI 生成关于内容失败：{e}")
            return {}
    
    def generate_contact_content(
        self, 
        project_name: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """为联系页面生成个性化文案"""
        
        prompt = f"""为"{project_name}"生成联系页面的文案。

项目信息：
- 名称：{project_name}
- 类型：{context.get('type', '咖啡店')}
- 特色：{context.get('features', '')}

生成以下文案（JSON格式）：
{{
  "headline": "联系页面标题",
  "subtitle": "副标题（欢迎语）",
  "form_title": "表单标题",
  "form_text": "表单说明文字",
  "response_time": "响应时间承诺"
}}

要求文案：
- 友好亲切
- 专业可信
- 简洁明了
"""
        
        try:
            response = self.agent.client.chat.completions.create(
                model=self.agent.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            return json.loads(content)
            
        except Exception as e:
            print(f"AI 生成联系内容失败：{e}")
            return {}
    
    def enhance_project_context(
        self, 
        project_name: str, 
        description: str
    ) -> Dict[str, Any]:
        """增强项目上下文信息，补充缺失的细节"""
        
        prompt = f"""分析项目"{project_name}"并补充必要的商业信息。

项目描述：{description}

请推断并生成以下信息（JSON格式）：
{{
  "type": "项目类型（如：咖啡店、餐厅、科技公司等）",
  "target_audience": "目标客户描述",
  "features": "核心特色（3-5个关键词）",
  "mission": "使命宣言（一句话）",
  "address": "合理的示例地址",
  "phone": "示例电话（使用 010-XXXX-XXXX 格式）",
  "email": "示例邮箱",
  "business_hours": "营业时间"
}}
"""
        
        try:
            response = self.agent.client.chat.completions.create(
                model=self.agent.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            return json.loads(content)
            
        except Exception as e:
            print(f"增强上下文失败：{e}")
            return {
                "type": "商业",
                "target_audience": "大众客户",
                "features": "品质、服务、创新",
                "mission": f"为客户提供优质的产品与服务",
                "address": "北京市朝阳区示例路123号",
                "phone": "010-8888-8888",
                "email": f"info@{project_name.lower().replace(' ', '')}.com",
                "business_hours": "周一至周五 9:00-18:00"
            }


def integrate_ai_generation(agent_instance, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """集成 AI 生成到工具调用中
    
    Args:
        agent_instance: SmartWebAgent 实例
        tool_name: 工具名称
        params: 工具参数
    
    Returns:
        增强后的参数，包含 AI 生成的内容
    """
    
    # 只处理特定的页面生成工具
    if tool_name not in ["create_menu_page", "create_about_page", "create_contact_page"]:
        return params
    
    # 提取项目信息
    project_name = params.get('project_name', '')
    file_path = params.get('file_path', '')
    
    # 获取或创建上下文
    context = params.get('context', {})
    if not context:
        # 尝试从 agent 的执行历史中提取上下文
        context = {
            'description': agent_instance.latest_user_request or '',
            'project_directory': agent_instance.project_directory
        }
    
    # 创建 AI 内容生成器
    generator = AIContentGenerator(agent_instance)
    
    # 根据工具类型生成相应内容
    ai_content = {}
    if tool_name == "create_menu_page":
        ai_content = generator.generate_menu_content(project_name, context)
    elif tool_name == "create_about_page":
        ai_content = generator.generate_about_content(project_name, context)
    elif tool_name == "create_contact_page":
        ai_content = generator.generate_contact_content(project_name, context)
    
    # 如果需要，增强上下文信息
    if not context.get('address') or not context.get('phone'):
        enhanced_context = generator.enhance_project_context(
            project_name,
            context.get('description', '')
        )
        context.update(enhanced_context)
    
    # 更新参数
    params['context'] = context
    params['ai_content'] = ai_content
    
    return params


__all__ = [
    'AIContentGenerator',
    'integrate_ai_generation'
]