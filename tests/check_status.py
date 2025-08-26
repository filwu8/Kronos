#!/usr/bin/env python3
"""
检查API状态
"""

import requests

def check_api_status():
    """检查API状态"""
    try:
        response = requests.get('http://localhost:8000/health')
        data = response.json()
        
        print('🔍 API健康检查:')
        print(f'   模型已加载: {data["model_status"]["model_loaded"]}')
        print(f'   使用模拟: {data["model_status"]["use_mock"]}')
        print(f'   数据源: {data["model_status"]["data_source"]}')
        
        if not data["model_status"]["use_mock"]:
            print('✅ 当前使用真实数据模式')
        else:
            print('⚠️ 当前仍在模拟模式')
            
    except Exception as e:
        print(f'❌ 检查失败: {str(e)}')

if __name__ == "__main__":
    check_api_status()
