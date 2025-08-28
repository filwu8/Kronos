#!/usr/bin/env python3
"""
E2E 测试: /predict 在GPU不兼容（RTX 5090 sm 架构）时自动回退CPU并返回200
"""
import requests
import time

API = "http://localhost:8000"


def wait_api_ready(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{API}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def test_predict_cpu_fallback():
    assert wait_api_ready(), "API未就绪"

    # 检查模型状态，允许 device 为 cuda 或 cpu（若GPU不兼容会自动切到cpu）
    r = requests.get(f"{API}/model/status", timeout=5)
    assert r.status_code == 200
    status = r.json()
    print("模型状态:", status)

    # 发起预测请求（最小参数集）
    payload = {
        "stock_code": "000001",
        "pred_len": 10,
        "period": "1y",
        "lookback": 200,
        "temperature": 1.0,
        "top_p": 0.9,
        "sample_count": 1,
    }
    r = requests.post(f"{API}/predict", json=payload, timeout=120)
    print("/predict:", r.status_code, r.text[:200])

    assert r.status_code == 200, f"/predict 返回非200: {r.status_code}"
    data = r.json()
    assert data.get("success") is True, f"预测失败: {data.get('error')}"

    # 校验关键字段
    d = data["data"]
    assert "stock_info" in d and "historical_data" in d and "predictions" in d and "summary" in d
    assert isinstance(d["predictions"], list) and len(d["predictions"]) > 0


if __name__ == "__main__":
    test_predict_cpu_fallback()

