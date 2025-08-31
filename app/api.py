"""
FastAPI后端服务
提供股票预测API接口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import os

from .prediction_service import get_prediction_service

# 配置日志（支持环境变量 LOG_LEVEL；可选落盘到 volumes/logs/api_server.log）
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)

try:
    from pathlib import Path
    log_dir = Path("volumes") / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / "api_server.log", encoding="utf-8")
    fh.setLevel(getattr(logging, log_level, logging.INFO))
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
except Exception:
    pass

# 创建FastAPI应用
app = FastAPI(
    title="Gordon Wang 的股票预测API",
    description="基于RTX 5090 GPU加速的智能股票价格预测服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
prediction_service = None


# Pydantic模型定义
class PredictionRequest(BaseModel):
    """预测请求模型"""
    stock_code: str = Field(..., description="股票代码，如：000001、600000")
    period: str = Field("1y", description="历史数据周期：1y, 2y, 5y")
    pred_len: int = Field(30, ge=1, le=120, description="预测天数，1-120天")
    lookback: int = Field(1000, ge=50, le=5000, description="历史数据长度，RTX 5090支持大数据量")
    temperature: float = Field(1.0, ge=0.1, le=2.0, description="采样温度")
    top_p: float = Field(0.9, ge=0.1, le=1.0, description="核采样概率")
    sample_count: int = Field(1, ge=1, le=10, description="采样次数，高性能模式支持更多")
    debug: bool = Field(False, description="调试模式：返回原始预测(未约束)用于诊断")


class BatchPredictionRequest(BaseModel):
    """批量预测请求模型"""
    stock_codes: List[str] = Field(..., description="股票代码列表")
    period: str = Field("1y", description="历史数据周期")
    pred_len: int = Field(30, ge=1, le=60, description="预测天数")


class StockInfo(BaseModel):
    """股票信息模型"""
    code: str
    name: str
    market: str
    source: str


class PredictionSummary(BaseModel):
    """预测摘要模型"""
    current_price: float
    predicted_price: float
    change_amount: float
    change_percent: float
    trend: str
    volatility: float
    prediction_days: int
    confidence: str


class PredictionResponse(BaseModel):
    """预测响应模型"""
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global prediction_service

    logger.info("正在启动股票预测服务...")

    # 强制使用真实数据模式
    use_mock = False  # 强制关闭模拟模式

    # 设备选择：优先读取 DEVICE 环境变量（auto/cpu/cuda），auto 时按可用性选择
    import torch
    prefer = os.getenv("DEVICE", "auto").lower()
    device = "cpu"
    if prefer == "cuda":
        if torch.cuda.is_available():
            device = "cuda"
        else:
            logger.warning("指定 DEVICE=cuda 但 CUDA 不可用，回退到 CPU")
    elif prefer == "cpu":
        device = "cpu"
    else:
        # auto 模式
        device = "cuda" if torch.cuda.is_available() else "cpu"

    # 如选择为 CUDA，做一次极小计算烟雾测试，避免不兼容架构导致运行时错误
    if device == "cuda":
        try:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"检测到GPU: {gpu_name}")
            logger.info(f"GPU内存: {gpu_memory:.1f} GB")
            torch.zeros((1, 1), device="cuda").matmul(torch.ones((1, 1), device="cuda"))
            logger.info("GPU烟雾测试通过，使用GPU运行")
        except Exception as e:
            logger.warning(f"GPU烟雾测试失败，回退到CPU: {e}")
            device = "cpu"
    else:
        logger.info("未选择或未检测到GPU，使用CPU")

    # CPU优化配置
    if device == "cpu":
        try:
            cpu_threads = int(os.getenv('CPU_THREADS', max(1, (os.cpu_count() or 4) // 2)))
            torch.set_num_threads(cpu_threads)
            logger.info(f"🚀 CPU优化：使用{cpu_threads}线程并行计算")
        except Exception as e:
            logger.warning(f"设置CPU线程失败: {e}")

    try:
        prediction_service = get_prediction_service(device=device, use_mock=use_mock)
        logger.info("预测服务启动成功 - 使用真实数据模式")
    except Exception as e:
        logger.error(f"预测服务启动失败: {str(e)}")
        # 即使失败也要启动，但仍尝试真实模式
        prediction_service = get_prediction_service(device="cpu", use_mock=False)


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Kronos股票预测API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    global prediction_service

    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")

    status = prediction_service.get_model_status()

    return {
        "status": "healthy",
        "model_status": status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/model/status")
async def model_status():
    """返回模型与数据获取的当前状态（供前端轮询展示）"""
    global prediction_service
    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")
    return prediction_service.get_model_status()


@app.post("/refresh/{stock_code}")
async def refresh_stock(stock_code: str, period: str = "1y"):
    """增量刷新某只股票的缓存，支持指定 period（默认1y）"""
    global prediction_service
    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")
    try:
        fetcher = prediction_service.data_fetcher
        info = fetcher.refresh_stock_cache(stock_code, period=period)
        if not info:
            raise HTTPException(status_code=502, detail="在线数据源无返回或解析失败")
        return {"success": True, "data": info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: PredictionRequest):
    """
    预测单只股票价格
    """
    global prediction_service
    import time

    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")

    start_time = time.time()
    try:
        logger.info(f"收到预测请求: {request.stock_code}, 参数: lookback={request.lookback}, sample_count={request.sample_count}, pred_len={request.pred_len}")

        # 执行预测
        result = prediction_service.predict_stock(
            stock_code=request.stock_code,
            period=request.period,
            pred_len=request.pred_len,
            lookback=request.lookback,
            T=request.temperature,
            top_p=request.top_p,
            sample_count=request.sample_count,
            debug=request.debug
        )

        elapsed_time = time.time() - start_time
        logger.info(f"预测完成: {request.stock_code}, 耗时: {elapsed_time:.2f}秒")

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        # 添加性能信息到响应
        if result.get('data'):
            result['data']['performance'] = {
                'elapsed_time': round(elapsed_time, 2),
                'parameters': {
                    'lookback': request.lookback,
                    'sample_count': request.sample_count,
                    'pred_len': request.pred_len
                }
            }

        return PredictionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"预测请求处理失败: {str(e)}, 耗时: {elapsed_time:.2f}秒")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@app.post("/predict/batch")
async def batch_predict(request: BatchPredictionRequest):
    """
    批量预测多只股票
    """
    global prediction_service

    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")

    if len(request.stock_codes) > 10:
        raise HTTPException(status_code=400, detail="批量预测最多支持10只股票")

    try:
        logger.info(f"收到批量预测请求: {request.stock_codes}")

        # 执行批量预测
        results = prediction_service.batch_predict(
            stock_codes=request.stock_codes,
            period=request.period,
            pred_len=request.pred_len
        )

        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"批量预测请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@app.get("/stocks/{stock_code}/info")
async def get_stock_info(stock_code: str):
    """
    获取股票基本信息
    """
    global prediction_service

    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")

    try:
        info = prediction_service.data_fetcher.get_stock_info(stock_code)
        return {
            "success": True,
            "data": info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取股票信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")


@app.get("/stocks/{stock_code}/history")
async def get_stock_history(
    stock_code: str,
    period: str = "1y",
    limit: int = 100
):
    """
    获取股票历史数据
    """
    global prediction_service

    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")

    try:
        df = prediction_service.data_fetcher.fetch_stock_data(stock_code, period=period)

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票数据: {stock_code}")

        # 限制返回数据量
        if len(df) > limit:
            df = df.tail(limit)

        # 转换为字典格式
        data = df.reset_index().to_dict('records')

        return {
            "success": True,
            "data": {
                "stock_code": stock_code,
                "period": period,
                "count": len(data),
                "history": data
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


@app.get("/model/status")
async def get_model_status():
    """
    获取模型状态信息
    """
    global prediction_service

    if prediction_service is None:
        return {
            "model_loaded": False,
            "error": "预测服务未初始化"
        }

    status = prediction_service.get_model_status()
    return status


# 实时系统资源监控（CPU/GPU）
@app.get("/metrics/usage")
async def get_system_usage():
    """返回当前 CPU 或 GPU 的实时利用率与内存占用（轻量采样）"""
    try:
        import psutil
        import time
        import torch
    except Exception as e:
        return {"success": False, "error": f"依赖缺失: {e}"}

    # CPU 基础信息
    cpu_percent = psutil.cpu_percent(interval=0.3)  # 轻量阻塞 0.3s 采样
    mem = psutil.virtual_memory()
    mem_percent = mem.percent
    mem_used_gb = round(mem.used / 1024**3, 2)
    mem_total_gb = round(mem.total / 1024**3, 2)

    usage = {
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "percent": cpu_percent,
            "mem_percent": mem_percent,
            "mem_used_gb": mem_used_gb,
            "mem_total_gb": mem_total_gb,
        }
    }

    # 若可用，补充 GPU 信息
    if torch.cuda.is_available():
        gpu_info = {"available": True}
        try:
            # 显存使用
            device = torch.device("cuda:0")
            allocated_gb = round(torch.cuda.memory_allocated(device) / 1024**3, 2)
            reserved_gb = round(torch.cuda.memory_reserved(device) / 1024**3, 2)
            total_gb = round(torch.cuda.get_device_properties(device).total_memory / 1024**3, 2)

            # 利用率（优先 NVML，如无则仅返回显存）
            util_percent = None
            temperature = None
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                util_percent = int(util.gpu)
                temperature = int(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
                pynvml.nvmlShutdown()
            except Exception:
                # 没有 NVML 时，仍返回显存占用信息
                pass

            gpu_info.update({
                "name": torch.cuda.get_device_name(0),
                "util_percent": util_percent,  # 可能为 None 表示不可用
                "temperature": temperature,    # 可能为 None 表示不可用
                "mem_allocated_gb": allocated_gb,
                "mem_reserved_gb": reserved_gb,
                "mem_total_gb": total_gb,
                "mem_percent": round((allocated_gb / total_gb) * 100, 1) if total_gb else None,
            })
        except Exception as e:
            gpu_info.update({"error": str(e)})
        usage["gpu"] = gpu_info

    return {"success": True, "data": usage}


@app.get("/api/docs")
async def get_api_docs():
    """
    API文档信息
    """
    return {
        "title": "Kronos股票预测API",
        "description": "基于Kronos模型的A股股票价格预测服务",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict": "预测单只股票价格",
            "POST /predict/batch": "批量预测多只股票",
            "GET /stocks/{code}/info": "获取股票基本信息",
            "GET /stocks/{code}/history": "获取股票历史数据",
            "GET /health": "健康检查",
            "GET /model/status": "模型状态"
        },
        "examples": {
            "stock_codes": ["000001", "600000", "000002.SZ", "600036.SS"],
            "prediction_request": {
                "stock_code": "000001",
                "period": "1y",
                "pred_len": 30,
                "temperature": 1.0,
                "top_p": 0.9
            }
        }
    }


# 错误处理
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "success": False,
        "error": "接口不存在",
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "success": False,
        "error": "内部服务器错误",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    # 启动服务
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
