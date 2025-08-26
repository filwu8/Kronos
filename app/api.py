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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    sample_count: int = Field(1, ge=1, le=5, description="采样次数")


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

    # GPU检测和配置
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"检测到GPU: {gpu_name}")
        logger.info(f"GPU内存: {gpu_memory:.1f} GB")

        # 测试GPU兼容性
        try:
            test_tensor = torch.randn(10, 10, device="cuda")
            _ = torch.mm(test_tensor, test_tensor)
            device = "cuda"
            logger.info("✅ GPU兼容性测试通过，使用GPU")
        except Exception as e:
            device = "cpu"
            logger.warning(f"⚠️ GPU兼容性问题，使用CPU: {str(e)}")
            logger.info("💡 RTX 5090需要更新的PyTorch版本支持")
    else:
        device = "cpu"
        logger.info("未检测到GPU，使用CPU")

    # 允许环境变量覆盖
    device = os.getenv("DEVICE", device)

    # CPU优化配置
    if device == "cpu":
        torch.set_num_threads(8)  # 使用8个CPU线程
        logger.info("🚀 CPU优化：使用8线程并行计算")

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


@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: PredictionRequest):
    """
    预测单只股票价格
    """
    global prediction_service
    
    if prediction_service is None:
        raise HTTPException(status_code=503, detail="预测服务未初始化")
    
    try:
        logger.info(f"收到预测请求: {request.stock_code}")
        
        # 执行预测
        result = prediction_service.predict_stock(
            stock_code=request.stock_code,
            period=request.period,
            pred_len=request.pred_len,
            lookback=request.lookback,
            T=request.temperature,
            top_p=request.top_p,
            sample_count=request.sample_count
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return PredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预测请求处理失败: {str(e)}")
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
