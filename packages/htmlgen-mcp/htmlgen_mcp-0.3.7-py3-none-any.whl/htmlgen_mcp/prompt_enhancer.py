"""提示词增强模块 - 确保AI使用真实数据而非生成示例"""


class PromptEnhancer:
    """提示词增强器，用于改进AI对真实数据的处理"""
    
    @staticmethod
    def enhance_for_real_data(base_prompt: str, context_data: str = None) -> str:
        """
        增强提示词，确保AI使用真实数据
        
        Args:
            base_prompt: 基础提示词
            context_data: 上下文数据内容
            
        Returns:
            增强后的提示词
        """
        if not context_data:
            return base_prompt
            
        # 分析数据类型
        data_type = PromptEnhancer._analyze_data_type(context_data)
        
        # 根据数据类型生成特定的指令
        specific_instructions = PromptEnhancer._get_specific_instructions(data_type, context_data)
        
        enhanced = f"""
{base_prompt}

【🔴 极其重要的数据使用规则 🔴】
=====================================
以下是必须严格遵守的数据使用规则：

1. 【数据来源】下面提供的是真实的业务数据，不是示例或模板
2. 【使用要求】必须100%使用这些数据，不得修改、省略或虚构
3. 【禁止行为】严禁生成以下虚构内容：
   - ❌ 虚构的客户评价（如"设计质感与转化率提升明显"）
   - ❌ 虚构的定价方案（如"¥9,999起步套餐"）
   - ❌ 虚构的服务内容（如"品牌升级与重构"）
   - ❌ 占位符内容（如"Lorem ipsum"或"示例文本"）
   
4. 【正确做法】：
   - ✅ 完整展示所有提供的数据项
   - ✅ 保持数据的原始格式和内容
   - ✅ 使用合适的布局展示（卡片、列表、表格等）
   - ✅ 可以添加导航、样式，但内容必须是提供的真实数据

【必须使用的真实数据】
=====================================
{context_data}
=====================================

{specific_instructions}

【工具调用要求】
=====================================
在调用以下工具时，必须包含真实数据：
- create_html_file: content参数必须包含上述真实数据
- add_content_section: 必须使用真实数据填充内容
- create_text_content: 文本内容必须来自上述数据
- add_hero_section: 标题和描述要反映真实业务
- create_card_grid: 卡片内容必须是真实数据项

【验证要求】
=====================================
生成的每个HTML文件都必须包含：
1. 完整的数据列表（不得遗漏任何一项）
2. 准确的名称和地址信息
3. 正确的数据展示格式

记住：这是一个数据展示任务，不是创意写作任务！
"""
        return enhanced
    
    @staticmethod
    def _analyze_data_type(context_data: str) -> str:
        """
        分析数据类型
        
        Args:
            context_data: 上下文数据
            
        Returns:
            数据类型标识
        """
        lower_data = context_data.lower()
        
        # 检测不同类型的数据
        if "咖啡" in context_data or "coffee" in lower_data or "店" in context_data:
            if "地址" in context_data or "address" in lower_data:
                return "store_list"
                
        if "产品" in context_data or "product" in lower_data:
            return "product_list"
            
        if "菜单" in context_data or "menu" in lower_data:
            return "menu_list"
            
        if "价格" in context_data or "price" in lower_data:
            return "pricing_list"
            
        if "联系" in context_data or "contact" in lower_data:
            return "contact_info"
            
        return "general_list"
    
    @staticmethod
    def _get_specific_instructions(data_type: str, context_data: str) -> str:
        """
        根据数据类型生成特定指令
        
        Args:
            data_type: 数据类型
            context_data: 上下文数据
            
        Returns:
            特定的指令
        """
        # 计算数据项数量
        item_count = context_data.count('\n1.') + context_data.count('\n2.') + \
                     context_data.count('\n3.') + context_data.count('\n-')
        
        if data_type == "store_list":
            return f"""
【针对店铺列表的特定要求】
- 必须展示所有{item_count}个店铺
- 每个店铺必须包含：名称、地址
- 使用卡片布局，每行2-3个
- 可以添加地图链接按钮
- 可以按区域或品牌分组展示
"""
        
        elif data_type == "product_list":
            return f"""
【针对产品列表的特定要求】
- 必须展示所有产品信息
- 保持原始的产品名称和描述
- 使用产品卡片或展示网格
- 可以添加产品图片占位符
"""
        
        elif data_type == "menu_list":
            return f"""
【针对菜单的特定要求】
- 必须展示完整菜单
- 保持原始的菜品名称和价格
- 可以按类别分组
- 使用清晰的表格或列表格式
"""
        
        else:
            return f"""
【通用数据展示要求】
- 必须展示所有数据项（共约{item_count}项）
- 保持数据的原始格式
- 使用适合的布局展示
- 不得添加虚构内容
"""
    
    @staticmethod
    def validate_content_usage(generated_content: str, original_data: str) -> dict:
        """
        验证生成的内容是否正确使用了原始数据
        
        Args:
            generated_content: 生成的内容
            original_data: 原始数据
            
        Returns:
            验证结果
        """
        # 提取原始数据中的关键项
        key_items = []
        lines = original_data.split('\n')
        for line in lines:
            line = line.strip()
            # 提取店名或关键信息
            if '. ' in line and line[0].isdigit():
                item = line.split('. ', 1)[1] if '. ' in line else line
                if '(' in item:
                    item = item.split('(')[0].strip()
                key_items.append(item)
            elif '- 地址：' in line:
                address = line.replace('- 地址：', '').strip()
                key_items.append(address)
        
        # 检查每个关键项是否在生成的内容中
        missing_items = []
        found_items = []
        
        for item in key_items:
            if item in generated_content:
                found_items.append(item)
            else:
                missing_items.append(item)
        
        # 检测虚构内容的特征
        fake_content_patterns = [
            "转化率提升",
            "品牌形象",
            "¥9,999",
            "¥29,999",
            "¥59,999",
            "起步套餐",
            "专业套餐",
            "旗舰套餐",
            "Alex Chen",
            "Liang Wu",
            "Yvonne Zhao",
            "设计质感",
            "交付质量",
            "Lorem ipsum",
            "示例文本"
        ]
        
        detected_fake = [pattern for pattern in fake_content_patterns 
                        if pattern in generated_content]
        
        return {
            "valid": len(missing_items) == 0 and len(detected_fake) == 0,
            "found_items": found_items,
            "missing_items": missing_items,
            "detected_fake_content": detected_fake,
            "coverage_rate": len(found_items) / len(key_items) if key_items else 0,
            "has_fake_content": len(detected_fake) > 0
        }


# 导出便捷函数
def enhance_prompt_for_real_data(prompt: str, context: str = None) -> str:
    """增强提示词以使用真实数据"""
    enhancer = PromptEnhancer()
    return enhancer.enhance_for_real_data(prompt, context)


def validate_data_usage(content: str, original: str) -> dict:
    """验证数据使用情况"""
    enhancer = PromptEnhancer()
    return enhancer.validate_content_usage(content, original)