#!/usr/bin/env python3
"""
测试DeepSeek API配置的简单脚本
"""

import os
import sys

def test_deepseek_config():
    """测试DeepSeek配置"""
    print("🧪 测试DeepSeek API配置...")
    
    # 检查环境变量
    env_key = os.getenv('DEEPSEEK_API_KEY', '')
    print(f"环境变量DEEPSEEK_API_KEY: {'已设置' if env_key and env_key != 'sk-your-deepseek-key-here' else '未设置'}")
    
    # 检查代码中的配置
    try:
        from ai_filter import AIFundingFilter
        filter_instance = AIFundingFilter(provider="deepseek")
        
        if filter_instance.api_key and filter_instance.api_key != 'sk-your-deepseek-key-here':
            print("✅ DeepSeek API密钥配置正确")
            print(f"API端点: {filter_instance.base_url}")
            print(f"模型: {filter_instance.model}")
            print(f"密钥前缀: {filter_instance.api_key[:10]}...")
            return True
        else:
            print("❌ DeepSeek API密钥未配置")
            print("\n配置方法:")
            print("1. 编辑 ai_filter.py 第21行，取消注释并填入真实密钥:")
            print('   self.deepseek_key = "sk-your-actual-deepseek-key-here"')
            print("2. 或设置环境变量:")
            print('   export DEEPSEEK_API_KEY=sk-your-actual-deepseek-key-here')
            return False
            
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_api_connection():
    """测试API连接"""
    print("\n🌐 测试API连接...")
    
    try:
        from ai_filter import AIFundingFilter
        filter_instance = AIFundingFilter(provider="deepseek")
        
        if not filter_instance.api_key:
            print("⏭️ 跳过连接测试 (API密钥未配置)")
            return False
        
        # 简单的API测试
        test_articles = [{
            'title': '测试项目完成100万美元种子轮融资',
            'content_text': '这是一个测试融资新闻。'
        }]
        
        print("发送测试请求...")
        result = filter_instance.filter_batch_articles(test_articles, "project")
        
        if result['success']:
            print("✅ API连接成功!")
            print(f"响应: {result['ai_response']}")
            return True
        else:
            print("❌ API调用失败")
            print(f"错误: {result['ai_response']}")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("DeepSeek API 配置测试")
    print("=" * 50)
    
    config_ok = test_deepseek_config()
    
    if config_ok:
        api_ok = test_api_connection()
        
        print("\n" + "=" * 50)
        print("📊 测试结果:")
        print(f"配置状态: {'✅ 正常' if config_ok else '❌ 失败'}")
        print(f"连接状态: {'✅ 正常' if api_ok else '❌ 失败'}")
        
        if config_ok and api_ok:
            print("\n🎉 DeepSeek API配置完成！可以正常使用AI过滤功能。")
        elif config_ok:
            print("\n⚠️ 配置正确但连接失败，请检查网络或API密钥是否有效。")
        else:
            print("\n❌ 请先配置DeepSeek API密钥。")
    else:
        print("\n❌ 请先配置DeepSeek API密钥，然后重新运行测试。")