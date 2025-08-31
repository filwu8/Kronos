#!/usr/bin/env python3
"""
调试测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.prediction_service import get_prediction_service

def debug_test():
    """调试测试"""
    print("🔍 开始调试测试...")
    
    try:
        # 直接调用预测服务
        service = get_prediction_service(use_mock=True)
        print("✅ 预测服务创建成功")
        
        # 简单预测
        result = service.predict_stock(
            stock_code='000001',
            pred_len=3,
            sample_count=1,
            lookback=100
        )
        
        if result['success']:
            print("✅ 预测成功")
            predictions = result['data']['predictions']
            print(f"返回{len(predictions)}天预测数据")
            
            # 显示第一天数据
            if predictions:
                first_day = predictions[0]
                print(f"第一天: O={first_day['open']:.2f}, H={first_day['high']:.2f}, L={first_day['low']:.2f}, C={first_day['close']:.2f}")
        else:
            print(f"❌ 预测失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 调试测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test()
