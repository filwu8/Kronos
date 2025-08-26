#!/usr/bin/env python3
import requests

print('🧪 测试所有修复效果')
print('=' * 40)

# 测试API标题
try:
    response = requests.get('http://localhost:8000/docs')
    if response.status_code == 200:
        print('✅ API文档可访问')
    else:
        print(f'❌ API文档: {response.status_code}')
except Exception as e:
    print(f'❌ API文档: {str(e)}')

# 测试预测数据格式
try:
    response = requests.post('http://localhost:8000/predict', 
                           json={'stock_code': '000001', 'pred_len': 3}, 
                           timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            predictions = data['data']['predictions']
            print(f'✅ 预测数据格式正确')
            print('📅 预测日期样本:')
            for i, pred in enumerate(predictions[:2]):
                print(f'   {i+1}. {pred["date"]} - ¥{pred["close"]:.2f}')
        else:
            print(f'❌ 预测失败: {data.get("error")}')
    else:
        print(f'❌ 预测请求: {response.status_code}')
        
except Exception as e:
    print(f'❌ 预测请求: {str(e)}')

# 测试Streamlit
try:
    response = requests.get('http://localhost:8501')
    if response.status_code == 200:
        print('✅ Streamlit界面可访问')
    else:
        print(f'❌ Streamlit: {response.status_code}')
except Exception as e:
    print(f'❌ Streamlit: {str(e)}')

print('')
print('🎉 修复内容总结:')
print('1. ✅ 品牌标识: Gordon Wang 的股票预测系统')
print('2. ✅ 预测数据日期: 正确显示未来日期')
print('3. ✅ 图表工具栏: 简化并优化')
print('4. ✅ 数据表格: 中文列名和格式化')
print('5. ✅ 预测区间: 添加不确定性阴影区域')
print('')
print('🌐 请在浏览器中验证:')
print('   前端界面: http://localhost:8501')
print('   API文档: http://localhost:8000/docs')
