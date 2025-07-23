#!/usr/bin/env python3
"""
测试paragraph_water_info配置加载和AI总结功能
"""

from ai_filter import AIFundingFilter

def test_paragraph_water_config():
    """测试研报AI总结配置"""
    print("=== paragraph_water_info 配置测试 ===")
    
    # 创建筛选器
    filter = AIFundingFilter(provider="openai")  # 使用OpenAI测试
    
    if not filter.api_key:
        print("❌ API密钥未配置")
        return
    
    # 验证配置加载
    paragraph_config = filter.config.get('paragraph_water_info', {})
    
    if not paragraph_config:
        print("❌ 未找到paragraph_water_info配置")
        return
    
    print("✅ 配置加载成功!")
    
    # 显示prompt模板信息
    prompt_template = paragraph_config.get('prompt_template', '')
    print(f"📋 prompt模板长度: {len(prompt_template)} 字符")
    
    if prompt_template:
        print(f"📝 prompt模板预览 (前300字符):")
        preview = prompt_template[:300].replace('\n', '\\n')
        print(f"   {preview}...")
    
    # 测试模板格式化
    test_article = """
    这是一篇关于DeFi协议的长文章，详细分析了市场趋势和技术发展。
    文章包含多个段落，每个段落都有深入的分析和见解。
    作者通过数据和案例，展示了DeFi领域的发展机遇和挑战。
    这些信息对于投资者和开发者来说都具有重要的参考价值。
    """ * 10  # 模拟长文章
    
    try:
        formatted_prompt = prompt_template.format(article_text=test_article)
        print(f"✅ prompt模板格式化测试成功")
        print(f"   格式化后总长度: {len(formatted_prompt)} 字符")
        
        # 显示格式化后的prompt预览
        print(f"📄 格式化prompt预览 (前200字符):")
        print(f"   {formatted_prompt[:200]}...")
        
    except Exception as e:
        print(f"❌ prompt模板格式化测试失败: {e}")
    
    # 模拟AI总结测试（不实际调用API）
    print(f"\n🤖 AI总结功能测试:")
    print(f"   测试文章长度: {len(test_article)} 字符")
    print(f"   预期总结格式包含: 段落精炼、水下信息提取、金句提炼")
    
    # 如果有API密钥，可以进行实际测试
    api_test = input("是否进行实际AI总结测试？(y/n): ").strip().lower()
    if api_test == 'y':
        print("🚀 开始实际AI总结测试...")
        try:
            result = filter._summarize_report_with_ai(test_article)
            print(f"✅ AI总结成功!")
            print(f"📄 总结结果预览:")
            print(result[:500] + "..." if len(result) > 500 else result)
        except Exception as e:
            print(f"❌ AI总结测试失败: {e}")

if __name__ == "__main__":
    test_paragraph_water_config()