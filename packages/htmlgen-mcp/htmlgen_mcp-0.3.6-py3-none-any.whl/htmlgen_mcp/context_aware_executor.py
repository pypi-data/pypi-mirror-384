"""上下文感知的执行器 - 确保 context_content 被正确使用"""
import json
from typing import Dict, Any, Optional


class ContextAwareExecutor:
    """确保上下文内容在执行过程中被正确传递和使用"""
    
    @staticmethod
    def inject_context_to_tools(plan: Dict[str, Any], context_content: str) -> Dict[str, Any]:
        """
        将上下文内容注入到工具调用序列中
        
        Args:
            plan: 执行计划
            context_content: 上下文内容（如咖啡馆列表）
            
        Returns:
            修改后的计划
        """
        if not context_content:
            return plan
            
        # 获取工具序列
        tools_sequence = plan.get("tools_sequence", [])
        
        # 遍历每个工具调用，注入上下文
        for tool in tools_sequence:
            tool_name = tool.get("tool", "")
            
            # 对于创建 HTML 文件的工具，注入具体内容
            if tool_name == "create_html_file":
                # 修改内容参数，确保包含实际数据
                original_content = tool.get("parameters", {}).get("content", "")
                
                # 如果是主页面，替换内容
                if "index.html" in tool.get("parameters", {}).get("file_name", ""):
                    tool["parameters"]["content"] = generate_html_with_context(
                        context_content,
                        tool.get("parameters", {}).get("title", "网站")
                    )
                    
            # 对于创建内容的工具，也要注入上下文
            elif tool_name in ["add_content_section", "create_content", "add_text_content"]:
                # 确保内容参数包含实际数据
                tool["parameters"]["context_data"] = context_content
                
        return plan
    
    @staticmethod
    def enhance_prompt_with_context(prompt: str, context_content: str) -> str:
        """
        增强提示词，明确要求使用上下文内容
        
        Args:
            prompt: 原始提示词
            context_content: 上下文内容
            
        Returns:
            增强后的提示词
        """
        if not context_content:
            return prompt
            
        enhanced = f"""
{prompt}

【重要：必须使用以下具体数据】
以下是必须在网页中展示的实际内容，请完整地将这些信息整合到网页中：

{context_content}

要求：
1. 必须将上述所有咖啡馆信息完整展示在网页中
2. 使用卡片或列表形式展示每个咖啡馆
3. 包含咖啡馆名称和地址
4. 可以添加适当的样式和布局，但内容必须准确
5. 不要生成虚构的内容，只使用提供的实际数据
"""
        return enhanced


def generate_html_with_context(context_content: str, title: str = "咖啡馆指南") -> str:
    """
    根据上下文内容生成 HTML
    
    Args:
        context_content: 咖啡馆列表等具体内容
        title: 网站标题
        
    Returns:
        完整的 HTML 内容
    """
    # 解析咖啡馆信息
    cafes = []
    lines = context_content.split('\n')
    current_cafe = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 识别咖啡馆名称（带序号的行）
        if line[0].isdigit() and '. ' in line:
            if current_cafe:
                cafes.append(current_cafe)
            # 提取咖啡馆名称
            name = line.split('. ', 1)[1] if '. ' in line else line
            current_cafe = {'name': name, 'address': ''}
            
        # 识别地址（- 开头的行）
        elif line.startswith('- 地址：'):
            if current_cafe:
                current_cafe['address'] = line.replace('- 地址：', '').strip()
                
    # 添加最后一个咖啡馆
    if current_cafe:
        cafes.append(current_cafe)
    
    # 生成 HTML
    cafe_cards = []
    for cafe in cafes:
        card = f'''
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="bi bi-cup-hot-fill text-brown"></i> {cafe['name']}
                        </h5>
                        <p class="card-text">
                            <i class="bi bi-geo-alt-fill text-muted"></i>
                            <span class="text-muted">{cafe['address']}</span>
                        </p>
                        <a href="#" class="btn btn-outline-primary btn-sm">
                            <i class="bi bi-map"></i> 查看地图
                        </a>
                    </div>
                </div>
            </div>'''
        cafe_cards.append(card)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="assets/css/style.css" rel="stylesheet">
    <style>
        .text-brown {{ color: #6f4e37; }}
        .hero-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 0;
        }}
        .card {{
            transition: transform 0.3s;
            border-radius: 15px;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="bi bi-cup-hot-fill text-brown"></i> {title}
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#cafes">咖啡馆列表</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#about">关于</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero 区域 -->
    <section class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 fw-bold mb-4">{title}</h1>
            <p class="lead mb-4">探索大族广场周边的精品咖啡馆</p>
            <p class="mb-4">共收录 {len(cafes)} 家咖啡馆，均在步行范围内</p>
            <a href="#cafes" class="btn btn-light btn-lg">
                <i class="bi bi-arrow-down-circle"></i> 浏览咖啡馆
            </a>
        </div>
    </section>

    <!-- 咖啡馆列表 -->
    <section id="cafes" class="py-5">
        <div class="container">
            <h2 class="text-center mb-5">咖啡馆列表</h2>
            <div class="row">
                {"".join(cafe_cards)}
            </div>
        </div>
    </section>

    <!-- 关于区域 -->
    <section id="about" class="py-5 bg-light">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-6">
                    <h2>关于本指南</h2>
                    <p class="lead">为您精选大族广场附近的咖啡馆</p>
                    <p>本指南收录了北京市大兴区大族广场周边1公里范围内的所有知名咖啡馆，包括星巴克、Peet's Coffee、M Stand等品牌，以及特色独立咖啡馆。</p>
                    <p>无论您是需要商务洽谈的安静环境，还是休闲放松的舒适空间，都能在这里找到合适的选择。</p>
                </div>
                <div class="col-md-6">
                    <div class="p-4 bg-white rounded shadow">
                        <h4><i class="bi bi-info-circle-fill text-primary"></i> 实用信息</h4>
                        <ul class="list-unstyled mt-3">
                            <li class="mb-2">
                                <i class="bi bi-geo-alt text-muted"></i> 
                                位置：北京市大兴区荣华南路
                            </li>
                            <li class="mb-2">
                                <i class="bi bi-clock text-muted"></i> 
                                营业时间：大部分 7:00-22:00
                            </li>
                            <li class="mb-2">
                                <i class="bi bi-wifi text-muted"></i> 
                                设施：WiFi、充电插座
                            </li>
                            <li class="mb-2">
                                <i class="bi bi-car-front text-muted"></i> 
                                交通：地铁亦庄线荣昌东街站
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 页脚 -->
    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container text-center">
            <p class="mb-0">© 2024 {title}. 信息仅供参考，请以实际为准。</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="assets/js/main.js"></script>
</body>
</html>'''
    
    return html