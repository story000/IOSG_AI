#!/usr/bin/env python3
"""
测试JSON格式的融资表格生成
"""

from ai_filter import AIFundingFilter

def test_json_table_parsing():
    """测试JSON解析生成markdown表格"""
    
    # 创建筛选器
    filter = AIFundingFilter(provider="deepseek")
    
    # 模拟AI返回的JSON数据
    test_json = '''
    {
      "funding_list": [
        {
          "company": "Poseidon",
          "investors": "a16z, CyberFund",
          "sector": "AI",
          "amount": "$15M"
        },
        {
          "company": "Questflow",
          "investors": "CyberFund, Animoca Brands",
          "sector": "AI",
          "amount": "$6.5M"
        },
        {
          "company": "Quack AI",
          "investors": "Animoca Brands, Binance Labs",
          "sector": "DeFi",
          "amount": "$3.6M"
        }
      ]
    }
    '''
    
    print("=== 测试JSON解析生成Markdown表格 ===")
    print("模拟AI返回的JSON数据:")
    print(test_json)
    
    # 测试解析
    result = filter._parse_json_to_markdown_table(test_json)
    
    print("\n生成的Markdown表格:")
    print(result)
    
    print("\n=== 预期效果 ===")
    print("应该看到标准的markdown表格格式，包含：")
    print("- 表头：| 受资方 | 投资方 | 赛道 | 涉及金额 |")
    print("- 分隔符：|--------|--------|------|----------|")
    print("- 数据行：每条融资信息一行")

if __name__ == "__main__":
    test_json_table_parsing()