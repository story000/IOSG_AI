#!/usr/bin/env python3
"""
WebSocket连接诊断脚本
"""

import time
import requests
from flask_socketio import SocketIOTestClient
from app import app, socketio

def test_websocket_connection():
    """测试WebSocket连接"""
    print("🧪 测试WebSocket连接...")
    
    try:
        # 创建测试客户端
        client = SocketIOTestClient(app, socketio)
        
        # 测试连接
        received = client.get_received()
        print(f"连接消息: {received}")
        
        # 发送测试消息
        client.emit('test_connection', {'message': 'Test from diagnostic script'})
        
        # 等待响应
        time.sleep(1)
        received = client.get_received()
        print(f"收到响应: {received}")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

def test_ai_filter_api():
    """测试AI过滤API"""
    print("\n🧪 测试AI过滤API...")
    
    try:
        # 测试POST请求
        response = requests.post('http://localhost:8080/ai_filter', 
                               json={'provider': 'deepseek', 'api_key': ''})
        
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def test_log_capture():
    """测试日志捕获"""
    print("\n🧪 测试日志捕获...")
    
    try:
        from app import LogCapture, process_status
        
        # 重置状态
        process_status['test'] = {'running': False, 'progress': 0, 'logs': []}
        
        # 测试日志捕获
        with LogCapture('test'):
            print("这是一条测试日志")
            print("这是第二条测试日志")
        
        print(f"捕获的日志数量: {len(process_status['test']['logs'])}")
        for log in process_status['test']['logs']:
            print(f"  - {log['timestamp']}: {log['message']}")
            
        return len(process_status['test']['logs']) > 0
        
    except Exception as e:
        print(f"❌ 日志捕获测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("WebSocket 和 AI过滤 诊断测试")
    print("=" * 50)
    
    print("⚠️  请确保Flask应用正在运行 (python app.py)")
    input("按回车键开始测试...")
    
    websocket_ok = test_websocket_connection()
    api_ok = test_ai_filter_api()
    log_ok = test_log_capture()
    
    print("\n" + "=" * 50)
    print("📊 诊断结果:")
    print(f"WebSocket连接: {'✅ 正常' if websocket_ok else '❌ 失败'}")
    print(f"AI过滤API: {'✅ 正常' if api_ok else '❌ 失败'}")
    print(f"日志捕获: {'✅ 正常' if log_ok else '❌ 失败'}")
    
    if all([websocket_ok, api_ok, log_ok]):
        print("\n🎉 所有测试通过！WebSocket连接应该正常工作。")
    else:
        print("\n❌ 部分测试失败，请检查相关配置。")
        
    print("\n💡 调试建议:")
    print("1. 在浏览器中按F12打开开发者工具")
    print("2. 查看Console标签页的WebSocket连接日志")
    print("3. 点击'测试连接'按钮验证WebSocket")
    print("4. 检查后台控制台是否有WebSocket相关错误")