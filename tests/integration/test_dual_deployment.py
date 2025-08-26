#!/usr/bin/env python3
"""
双版本部署一致性测试
验证Docker版本和本地版本功能完全一致
"""

import requests
import time
import json
from typing import Dict, Any, List

class DeploymentTester:
    """部署测试器"""
    
    def __init__(self):
        self.test_results = {
            'local': {},
            'docker': {}
        }
    
    def test_api_health(self, base_url: str) -> Dict[str, Any]:
        """测试API健康状态"""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'device': data.get('model_status', {}).get('device'),
                    'model_loaded': data.get('model_status', {}).get('model_loaded'),
                    'use_mock': data.get('model_status', {}).get('use_mock')
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_prediction(self, base_url: str, stock_code: str = '000001') -> Dict[str, Any]:
        """测试预测功能"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/predict",
                json={'stock_code': stock_code, 'pred_len': 5},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data['data']['summary']
                    return {
                        'success': True,
                        'response_time': end_time - start_time,
                        'stock_name': data['data']['stock_info']['name'],
                        'current_price': summary['current_price'],
                        'predicted_price': summary['predicted_price'],
                        'change_percent': summary['change_percent'],
                        'trend': summary['trend'],
                        'historical_count': len(data['data']['historical_data']),
                        'prediction_count': len(data['data']['predictions'])
                    }
                else:
                    return {'success': False, 'error': data.get('error')}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_data_consistency(self, base_url: str) -> Dict[str, Any]:
        """测试数据一致性"""
        try:
            # 多次请求同一股票，检查数据一致性
            results = []
            for _ in range(3):
                response = requests.post(
                    f"{base_url}/predict",
                    json={'stock_code': '000001', 'pred_len': 3},
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        results.append(data['data']['summary']['current_price'])
            
            if len(results) >= 2:
                # 检查价格是否一致（真实数据应该相同）
                consistent = all(abs(price - results[0]) < 0.01 for price in results)
                return {
                    'success': True,
                    'consistent': consistent,
                    'prices': results,
                    'variance': max(results) - min(results) if results else 0
                }
            else:
                return {'success': False, 'error': '测试数据不足'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_performance(self, base_url: str) -> Dict[str, Any]:
        """测试性能"""
        try:
            times = []
            for i in range(5):
                start_time = time.time()
                response = requests.post(
                    f"{base_url}/predict",
                    json={'stock_code': '000001', 'pred_len': 3},
                    timeout=20
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        times.append(end_time - start_time)
            
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                return {
                    'success': True,
                    'average_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'test_count': len(times)
                }
            else:
                return {'success': False, 'error': '性能测试失败'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_full_test(self, deployment_type: str, base_url: str):
        """运行完整测试"""
        print(f"\n🧪 测试 {deployment_type.upper()} 版本 ({base_url})")
        print("-" * 50)
        
        results = {}
        
        # 1. 健康检查
        print("1. 🏥 健康检查...")
        health_result = self.test_api_health(base_url)
        results['health'] = health_result
        
        if health_result['success']:
            print(f"   ✅ API正常 (设备: {health_result['device']})")
        else:
            print(f"   ❌ API异常: {health_result['error']}")
            self.test_results[deployment_type] = results
            return
        
        # 2. 预测功能
        print("2. 🔮 预测功能...")
        prediction_result = self.test_prediction(base_url)
        results['prediction'] = prediction_result
        
        if prediction_result['success']:
            print(f"   ✅ 预测成功 ({prediction_result['response_time']:.2f}s)")
            print(f"   📊 {prediction_result['stock_name']}: ¥{prediction_result['current_price']:.2f}")
        else:
            print(f"   ❌ 预测失败: {prediction_result['error']}")
        
        # 3. 数据一致性
        print("3. 🔄 数据一致性...")
        consistency_result = self.test_data_consistency(base_url)
        results['consistency'] = consistency_result
        
        if consistency_result['success']:
            if consistency_result['consistent']:
                print(f"   ✅ 数据一致")
            else:
                print(f"   ⚠️ 数据不一致 (方差: {consistency_result['variance']:.4f})")
        else:
            print(f"   ❌ 一致性测试失败: {consistency_result['error']}")
        
        # 4. 性能测试
        print("4. ⚡ 性能测试...")
        performance_result = self.test_performance(base_url)
        results['performance'] = performance_result
        
        if performance_result['success']:
            print(f"   ✅ 平均响应时间: {performance_result['average_time']:.2f}s")
            print(f"   📊 范围: {performance_result['min_time']:.2f}s - {performance_result['max_time']:.2f}s")
        else:
            print(f"   ❌ 性能测试失败: {performance_result['error']}")
        
        self.test_results[deployment_type] = results
    
    def compare_versions(self):
        """比较两个版本"""
        print("\n📊 版本对比分析")
        print("=" * 60)
        
        local_results = self.test_results.get('local', {})
        docker_results = self.test_results.get('docker', {})
        
        if not local_results or not docker_results:
            print("❌ 缺少测试数据，无法进行对比")
            return
        
        # 功能一致性对比
        print("\n🔍 功能一致性:")
        
        # 健康状态对比
        local_health = local_results.get('health', {})
        docker_health = docker_results.get('health', {})
        
        if local_health.get('success') and docker_health.get('success'):
            device_match = local_health.get('device') == docker_health.get('device')
            mock_match = local_health.get('use_mock') == docker_health.get('use_mock')
            
            print(f"   设备配置: {'✅ 一致' if device_match else '❌ 不一致'}")
            print(f"   模拟模式: {'✅ 一致' if mock_match else '❌ 不一致'}")
        
        # 预测结果对比
        local_pred = local_results.get('prediction', {})
        docker_pred = docker_results.get('prediction', {})
        
        if local_pred.get('success') and docker_pred.get('success'):
            price_diff = abs(local_pred.get('current_price', 0) - docker_pred.get('current_price', 0))
            trend_match = local_pred.get('trend') == docker_pred.get('trend')
            
            print(f"   当前价格: {'✅ 一致' if price_diff < 0.01 else f'❌ 差异 {price_diff:.4f}'}")
            print(f"   趋势预测: {'✅ 一致' if trend_match else '❌ 不一致'}")
        
        # 性能对比
        print("\n⚡ 性能对比:")
        local_perf = local_results.get('performance', {})
        docker_perf = docker_results.get('performance', {})
        
        if local_perf.get('success') and docker_perf.get('success'):
            local_time = local_perf.get('average_time', 0)
            docker_time = docker_perf.get('average_time', 0)
            
            print(f"   本地版本: {local_time:.2f}s")
            print(f"   Docker版本: {docker_time:.2f}s")
            
            if docker_time > 0:
                ratio = local_time / docker_time
                if ratio < 0.8:
                    print(f"   📈 本地版本快 {(1-ratio)*100:.1f}%")
                elif ratio > 1.2:
                    print(f"   📉 Docker版本快 {(ratio-1)*100:.1f}%")
                else:
                    print(f"   ⚖️ 性能相当")
        
        # 总体评估
        print("\n🎯 总体评估:")
        
        local_score = self._calculate_score(local_results)
        docker_score = self._calculate_score(docker_results)
        
        print(f"   本地版本得分: {local_score}/100")
        print(f"   Docker版本得分: {docker_score}/100")
        
        if abs(local_score - docker_score) <= 5:
            print("   ✅ 两版本功能基本一致")
        else:
            print("   ⚠️ 两版本存在显著差异")
    
    def _calculate_score(self, results: Dict[str, Any]) -> int:
        """计算版本得分"""
        score = 0
        
        # 健康检查 (25分)
        if results.get('health', {}).get('success'):
            score += 25
        
        # 预测功能 (35分)
        if results.get('prediction', {}).get('success'):
            score += 35
        
        # 数据一致性 (25分)
        consistency = results.get('consistency', {})
        if consistency.get('success') and consistency.get('consistent'):
            score += 25
        
        # 性能 (15分)
        performance = results.get('performance', {})
        if performance.get('success'):
            avg_time = performance.get('average_time', 10)
            if avg_time < 3:
                score += 15
            elif avg_time < 5:
                score += 10
            elif avg_time < 10:
                score += 5
        
        return score

def main():
    """主测试函数"""
    print("🔬 RTX 5090 GPU股票预测系统 - 双版本一致性测试")
    print("=" * 70)
    
    tester = DeploymentTester()
    
    # 测试本地版本
    print("🏠 测试本地版本...")
    try:
        tester.run_full_test('local', 'http://localhost:8000')
    except Exception as e:
        print(f"❌ 本地版本测试失败: {str(e)}")
    
    # 测试Docker版本 (假设运行在不同端口)
    print("\n🐳 测试Docker版本...")
    try:
        tester.run_full_test('docker', 'http://localhost:8001')  # 假设Docker版本在8001端口
    except Exception as e:
        print(f"❌ Docker版本测试失败: {str(e)}")
    
    # 对比分析
    tester.compare_versions()
    
    # 保存测试结果
    with open('tests/results/dual_deployment_test.json', 'w', encoding='utf-8') as f:
        json.dump(tester.test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 测试结果已保存到: tests/results/dual_deployment_test.json")

if __name__ == "__main__":
    main()
