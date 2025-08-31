"""
股票预测服务
集成Kronos模型进行股票价格预测
"""

import sys
import os
import numpy as np
import pandas as pd
import torch
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import warnings
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL_IMPORT_OK = True
try:
    from model import Kronos, KronosTokenizer, KronosPredictor
except ImportError as e:
    # 延迟处理：启动不立即使用模拟，优先尝试本地真实模型
    logging.error(f"导入Kronos模型模块失败: {e}")
    MODEL_IMPORT_OK = False
    Kronos = None
    KronosTokenizer = None
    KronosPredictor = None

from .data_fetcher import AStockDataFetcher

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 忽略警告
warnings.filterwarnings('ignore')


class StockPredictionService:
    """股票预测服务"""

    def __init__(self, device: str = "cpu", use_mock: bool = False):
        """
        初始化预测服务
        Args:
            device: 计算设备 ('cpu' 或 'cuda')
            use_mock: 是否使用模拟模型
        """
        # 设备配置
        self.device = device
        self.use_mock = False  # 强制使用真实数据模式
        self.fast_cpu_mode = os.getenv('FAST_CPU_MODE', '1') == '1'

        # GPU/CPU 信息与线程设置
        if device == "cuda":
            import torch
            if torch.cuda.is_available():
                logger.info(f"预测服务使用GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            else:
                logger.warning("指定使用GPU但CUDA不可用，回退到CPU")
                self.device = "cpu"
        else:
            # CPU多线程设置（默认启用，避免只用1个核心）
            try:
                import torch
                cpu_threads = int(os.getenv('CPU_THREADS', max(1, (os.cpu_count() or 4) // 2)))
                torch.set_num_threads(cpu_threads)
                torch.set_num_interop_threads(max(1, cpu_threads // 2))
                os.environ['OMP_NUM_THREADS'] = str(cpu_threads)
                os.environ['MKL_NUM_THREADS'] = str(cpu_threads)
                os.environ['NUMEXPR_MAX_THREADS'] = str(cpu_threads)
                logger.info(f"预测服务使用CPU (FAST_CPU_MODE={'ON' if self.fast_cpu_mode else 'OFF'}), 计算线程={cpu_threads}")
            except Exception as e:
                logger.info(f"预测服务使用CPU (FAST_CPU_MODE={'ON' if self.fast_cpu_mode else 'OFF'}), 线程设置失败: {e}")
        self.data_fetcher = AStockDataFetcher()

        # 尝试导入本地适配器（akshare CSV）与 Qlib 适配器
        self.real_data_adapter = None
        self.qlib_adapter = None
        self.has_real_data = False
        self.has_qlib = False
        try:
            from .akshare_adapter import AkshareDataAdapter
            self.real_data_adapter = AkshareDataAdapter()
            self.has_real_data = True
            logger.info("Akshare 本地CSV适配器加载成功")
        except Exception:
            logger.warning("Akshare 本地CSV适配器未找到")
        try:
            from .qlib_adapter import QlibDataAdapter
            self.qlib_adapter = QlibDataAdapter()
            self.has_qlib = getattr(self.qlib_adapter, 'available', False)
            if self.has_qlib:
                logger.info("Qlib 数据适配器可用，provider_uri=./volumes/qlib_data/cn_data")
        except Exception:
            logger.info("Qlib 数据适配器不可用（未安装或未初始化）")

        self.predictor = None
        self.model_loaded = False

        # 预测参数
        self.default_params = {
            'lookback': 400,  # 历史数据长度
            'pred_len': 30,   # 预测天数
            'max_context': 2048,
            'T': 1.0,         # 温度参数
            'top_p': 0.9,     # 核采样
            'top_k': 0,       # top-k采样
            'sample_count': 1, # 采样次数
            'clip': 5.0       # 数据裁剪
        }

        self._load_model()

    def _load_model(self):
        """加载Kronos模型（优先使用本地真实模型）"""
        try:
            logger.info("开始加载Kronos模型...")

            # 检查设备可用性
            if self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA不可用，切换到CPU")
                self.device = "cpu"

            # 1) 优先尝试从本地 volumes/models 加载（2k 上下文）
            local_tokenizer = Path("volumes/models/Kronos-Tokenizer-2k")
            local_model = Path("volumes/models/Kronos-base")

            if MODEL_IMPORT_OK and local_tokenizer.exists() and local_model.exists():
                try:
                    logger.info("优先从本地 volumes/models 加载真实模型")
                    tokenizer = KronosTokenizer.from_pretrained(str(local_tokenizer))
                    model = Kronos.from_pretrained(str(local_model))
                    self.predictor = KronosPredictor(
                        model=model,
                        tokenizer=tokenizer,
                        device=self.device,
                        max_context=self.default_params['max_context'],
                        clip=self.default_params['clip']
                    )
                    self.model_loaded = True
                    logger.info(f"本地模型加载成功，设备: {self.device}")
                    return
                except Exception as e:
                    logger.error(f"本地模型加载失败: {e}")

            # 2) 回退到 HuggingFace 在线仓库
            if MODEL_IMPORT_OK:
                try:
                    logger.info("尝试从 HuggingFace 加载2k上下文预训练模型")
                    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-2k")
                    model = Kronos.from_pretrained("NeoQuasar/Kronos-base")
                    self.predictor = KronosPredictor(
                        model=model,
                        tokenizer=tokenizer,
                        device=self.device,
                        max_context=self.default_params['max_context'],
                        clip=self.default_params['clip']
                    )
                    self.model_loaded = True
                    logger.info(f"在线模型加载成功，设备: {self.device}")
                    return
                except Exception as e:
                    logger.error(f"在线模型加载失败: {e}")

            # 3) 如仍失败，明确报错（不启用模拟）
            raise RuntimeError("Kronos 真实模型加载失败：请检查 volumes/models 下是否存在模型文件，或网络可用性与依赖项。")

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self.model_loaded = False
            raise

    def prepare_data(self, df: pd.DataFrame, lookback: int, pred_len: int) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        准备预测数据
        Args:
            df: 股票历史数据
            lookback: 历史数据长度
            pred_len: 预测长度
        Returns:
            (x_df, x_timestamp, y_timestamp): 输入数据和时间戳
        """
        # 确保数据足够
        if len(df) < lookback:
            lookback = len(df)
            logger.warning(f"数据不足，调整lookback为: {lookback}")

        # 准备输入数据
        x_df = df.iloc[-lookback:][['open', 'high', 'low', 'close', 'volume', 'amount']].copy()
        # Kronos 代码中使用了 x_timestamp.dt，需要传入 Series 而非 DatetimeIndex
        x_timestamp = pd.Series(df.index[-lookback:])

        # 生成预测时间戳（同样使用 Series，保持一致的下游接口）
        last_date = pd.to_datetime(df.index[-1])
        # 使用工作日频率，确保与图表工作日轴一致
        pred_dates = pd.bdate_range(
            start=last_date + timedelta(days=1),
            periods=pred_len
        )
        y_timestamp = pd.Series(pred_dates)
        # 额外保障：预测日期严格晚于历史最后交易日
        if len(x_df) > 0:
            last_hist_date = pd.to_datetime(x_df.index.max()).normalize()
            y_timestamp = y_timestamp[y_timestamp.dt.normalize() > last_hist_date]


        return x_df, x_timestamp, y_timestamp

    def _format_historical_data(self, df: pd.DataFrame) -> list:
        """格式化历史数据（严格保留原索引日期，不做重建）"""
        out = []
        if not isinstance(df.index, pd.DatetimeIndex):
            # 若不是时间索引，尝试将 'date' 列设为索引
            if 'date' in df.columns:
                idx = pd.to_datetime(df['date'], errors='coerce')
                df = df.copy()
                df.index = idx
            else:
                # 无日期信息则直接返回空（避免构造新日期导致错位）
                return out
        # 去时区
        idx = pd.to_datetime(df.index).tz_localize(None)
        df = df.copy()
        df.index = idx
        # 过滤未来日期
        today = pd.Timestamp.today().normalize()
        df = df[df.index <= today]
        # 逐行输出，严格与索引一致
        for i, (dt, row) in enumerate(df.iterrows()):
            date_str = pd.Timestamp(dt).strftime('%Y-%m-%d')
            out.append({
                'date': date_str,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'amount': float(row['amount']) if 'amount' in row else float(row['close'] * row['volume'])
            })
        return out

    def _format_predictions(self, pred_df: pd.DataFrame, y_timestamp: pd.Series, uncertainty_data=None, raw_df=None) -> list:
        """格式化预测数据，确保包含正确的日期和不确定性信息（工作日对齐）"""
        formatted_predictions = []

        # 若传入的 y_timestamp 少于 pred_df 行数，按工作日扩展
        if len(y_timestamp) < len(pred_df):
            last = pd.to_datetime(y_timestamp.iloc[-1]) if len(y_timestamp) > 0 else pd.Timestamp.today()
            extra = pd.bdate_range(start=last + timedelta(days=1), periods=(len(pred_df) - len(y_timestamp)))
            y_timestamp = pd.concat([y_timestamp, pd.Series(extra)], ignore_index=True)

            # 注：raw_df 由上游在 debug 模式下传入，长度与 pred_df 对齐
            # 这里只是保留 raw 值用于诊断，不参与计算
            pass

        for i, (idx, row) in enumerate(pred_df.iterrows()):
            # 使用传入的y_timestamp作为日期
            prediction_date = y_timestamp.iloc[i] if i < len(y_timestamp) else y_timestamp.iloc[-1]

            prediction_item = {
                'date': prediction_date.strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']),
                'amount': float(row['amount']) if 'amount' in row else float(row['close'] * row['volume'])
            }

            # 添加不确定性信息
            if uncertainty_data is not None and i < len(uncertainty_data['upper']):
                prediction_item.update({
                    'close_upper': float(uncertainty_data['upper'][i]),
                    'close_lower': float(uncertainty_data['lower'][i]),
                    'close_max': float(uncertainty_data['max'][i]),
                    'close_min': float(uncertainty_data['min'][i]),
                    'close_std': float(uncertainty_data['std'][i])
                })
            # 若提供 raw_df（调试模式），附加原始未约束的诊断列
            if raw_df is not None:
                try:
                    if i < len(raw_df):
                        raw_row = raw_df.iloc[i]
                        prediction_item.update({
                            'raw_open': float(raw_row.get('open', np.nan)),
                            'raw_high': float(raw_row.get('high', np.nan)),
                            'raw_low': float(raw_row.get('low', np.nan)),
                            'raw_close': float(raw_row.get('close', np.nan))
                        })
                except Exception:
                    pass

            formatted_predictions.append(prediction_item)

        return formatted_predictions

    def predict_stock(self, stock_code: str, **kwargs) -> Dict:
        """
        预测股票价格
        Args:
            stock_code: 股票代码
            **kwargs: 预测参数
        Returns:
            Dict: 预测结果
        """
        try:
            if not self.model_loaded:
                return {
                    'success': False,
                    'error': '模型未加载',
                    'data': None
                }

            logger.info(f"开始预测股票: {stock_code}")

            # 优先采用持久数据通道：Qlib -> 本地CSV -> 在线数据
            lookback = kwargs.get('lookback', 100)
            period = kwargs.get('period', '1y')
            pred_len = kwargs.get('pred_len', self.default_params['pred_len'])
            debug = bool(kwargs.get('debug', False))

            df = None
            stock_info = None

            # 0) 优先使用本地缓存CSV（保证与公开网站口径一致，保留真实日期索引）
            if (df is None or df.empty) and not self.use_mock:
                local_csv = Path("volumes/data/akshare_data") / f"{stock_code}.csv"
                if local_csv.exists():
                    try:
                        cached_df = self.data_fetcher._load_from_cache(stock_code)
                    except Exception:
                        cached_df = None
                    if cached_df is not None and len(cached_df) > 0:
                        df = cached_df.copy()
                        try:
                            self.data_fetcher.last_source = 'cache'
                        except Exception:
                            pass
                        logger.info(f"使用本地缓存数据: {stock_code}, {len(df)} 条记录")


                # 确保按请求的 period 获得足够跨度的数据（即便缓存命中也做跨度校验）
                try:
                    expected_days = {"6mo": 180, "1y": 365, "2y": 2*365, "5y": 5*365}.get(period, 365)
                    if df is not None and len(df) > 0:
                        span_days = int((pd.Timestamp(df.index.max()) - pd.Timestamp(df.index.min())).days)
                        if span_days < expected_days * 0.8:
                            logger.info(f"缓存跨度不足({span_days}d < {expected_days}d*0.8)，按 period={period} 重新获取 {stock_code} 数据")
                            df = self.data_fetcher.fetch_stock_data(stock_code, period=period)
                except Exception as e:
                    logger.warning(f"period 跨度校验/补齐失败: {e}")

            # 1) 条件性优先使用 Qlib（有限使用）：当请求的历史窗口较大时优先Qlib，否则走在线数据
            #    - 阀值可通过环境变量 QLIB_LOOKBACK_THRESHOLD 配置，默认 1200（~5年交易日）
            qlib_threshold = int(os.getenv('QLIB_LOOKBACK_THRESHOLD', '1200'))
            prefer_qlib = (self.has_qlib and not self.use_mock and (lookback >= qlib_threshold or period in ('2y', '5y')))

            if df is None or len(df) < lookback:
                if prefer_qlib:
                    try:
                        symbol = f"{stock_code}.SZ" if stock_code.startswith(('00','30')) else (f"{stock_code}.SS" if stock_code.startswith('60') else stock_code)
                        qlib_df = self.qlib_adapter.get_stock_df(symbol, lookback=lookback, predict_window=pred_len)
                        if qlib_df is not None and not qlib_df.empty:
                            df = qlib_df
                            logger.info(f"使用Qlib数据: {symbol}, {len(df)} 条记录 (有限使用)")
                    except Exception:
                        pass

            # 2) 若仍无数据或不足，使用在线数据源（akshare->yfinance）
            if (df is None or df.empty):
                logger.info(f"使用在线数据源获取 {stock_code} ({period})")
                df = self.data_fetcher.fetch_stock_data(stock_code, period=period)
                stock_info = stock_info or self.data_fetcher.get_stock_info(stock_code)
                # 若本次需要较长历史而 Qlib 不可用/暂无数据，则自动导出 CSV 供后续导入 Qlib
                try:
                    if prefer_qlib and self.qlib_adapter and df is not None and len(df) > 0:
                        symbol = self.qlib_adapter.code_to_symbol(stock_code)
                        export_path = self.qlib_adapter.export_symbol_csv_for_import(symbol, df)
                        logger.info(f"已为 {symbol} 导出 Qlib 导入用CSV: {export_path}")
                except Exception as e:
                    logger.warning(f"导出 Qlib 导入CSV失败: {e}")

            # 3) 若仍失败，返回可用列表提示
            if df is None or df.empty:
                available_stocks = self.real_data_adapter.list_available_stocks() if self.real_data_adapter else []
                available_list = ', '.join(available_stocks[:10]) + ('...' if len(available_stocks) > 10 else '')
                return {
                    'success': False,
                    'error': f'无法获取股票 {stock_code} 的历史数据（Qlib/本地/在线均失败）。可用股票: {available_list}',
                    'available_stocks': available_stocks[:20],
                    'data': None
                }

            # 验证数据质量（动态最小天数: 至少 lookback + 1）
            min_days = max(50, min(lookback + 1, len(df)))
            if not self.data_fetcher.validate_data(df, min_days=min_days):
                return {
                    'success': False,
                    'error': f'数据质量不符合要求或数据量不足(需要≥{min_days}天，实际{len(df)}天)',
                    'data': None
                }

            # 更新预测参数
            # 性能统计开始
            import time
            start_time = time.perf_counter()
            gpu_mem_before = None
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_mem_before = torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0
            except Exception:
                pass

            params = self.default_params.copy()
            params.update(kwargs)

            # FAST CPU 模式下仅调整 lookback，保留用户选择的预测天数
            if self.device == 'cpu' and self.fast_cpu_mode:
                params['lookback'] = min(params['lookback'], 200)

            # 准备数据
            x_df, x_timestamp, y_timestamp = self.prepare_data(df, params['lookback'], params['pred_len'])

            # 执行蒙特卡洛多路径预测（遵循前端传入的 sample_count，避免CPU模式超时）
            logger.info("开始执行蒙特卡洛预测...")
            monte_carlo_samples = int(params.get('sample_count', 30))
            if self.device == 'cpu':
                # 快速模式：强制 1 次；非快速模式：尊重前端（UI范围1~3）
                monte_carlo_samples = 1 if self.fast_cpu_mode else max(1, min(monte_carlo_samples, 3))

            all_predictions = []
            pred_df_template = None
            for i in range(monte_carlo_samples):
                # 每次预测使用不同的随机参数增加多样性（CPU快速模式下仍保留轻微扰动）
                temperature = params['T'] + 0.1 * (i / max(1, monte_carlo_samples) - 0.5)
                top_p_varied = max(0.8, min(0.95, params['top_p'] + 0.05 * (i / max(1, monte_carlo_samples) - 0.5)))

                # 确保时间戳为Series，兼容下游 .dt 调用
                x_ts = x_timestamp if isinstance(x_timestamp, pd.Series) else pd.Series(x_timestamp)
                y_ts = y_timestamp if isinstance(y_timestamp, pd.Series) else pd.Series(y_timestamp)

                pred_df_sample = self.predictor.predict(
                    df=x_df,
                    x_timestamp=x_ts,
                    y_timestamp=y_ts,
                    pred_len=params['pred_len'],
                    T=temperature,
                    top_p=top_p_varied,
                    top_k=params['top_k'],
                    sample_count=1,
                    verbose=False
                )
                if pred_df_template is None:
                    pred_df_template = pred_df_sample.copy()
                all_predictions.append(pred_df_sample['close'].values)

            # 计算统计信息
            all_predictions = np.array(all_predictions)  # shape: (30, pred_len)

            # 计算历史波动率用于生成合理的不确定性区间
            returns = df['close'].pct_change().dropna()
            daily_volatility = returns.std()

            # 如果模型预测变化不够，基于历史波动率生成合理的不确定性
            if np.std(all_predictions) < daily_volatility * 0.1:  # 如果模型变化太小
                logger.info("模型预测变化较小，基于历史波动率生成不确定性区间")

                # 为每个预测路径添加基于历史波动率的合理变化
                np.random.seed(42)  # 固定种子确保可重复性
                for i in range(len(all_predictions)):
                    for j in range(len(all_predictions[i])):
                        # 随着预测天数增加，不确定性递增
                        uncertainty_factor = daily_volatility * np.sqrt(j + 1) * 0.8
                        random_change = np.random.normal(0, uncertainty_factor)
                        all_predictions[i][j] *= (1 + random_change)

            # 使用中位数聚合，更抗异常值
            pred_median = np.median(all_predictions, axis=0)
            pred_std = np.std(all_predictions, axis=0)
            pred_upper = np.percentile(all_predictions, 75, axis=0)  # 75分位数
            pred_lower = np.percentile(all_predictions, 25, axis=0)  # 25分位数
            pred_max = np.max(all_predictions, axis=0)
            pred_min = np.min(all_predictions, axis=0)

            # 价格连续性校准：确保第一天开盘价合理
            last_close = float(df['close'].iloc[-1])
            if len(pred_median) > 0:
                first_pred = pred_median[0]
                gap_percent = (first_pred - last_close) / last_close * 100

                # 如果跳空超过±3%，进行校准
                if abs(gap_percent) > 3.0:
                    logger.warning(f"检测到异常跳空: {gap_percent:.2f}%，进行价格连续性校准")

                    # 计算合理的跳空范围（±2%以内）
                    max_gap = 0.02  # 2%
                    if gap_percent > 3.0:
                        target_gap = max_gap
                    elif gap_percent < -3.0:
                        target_gap = -max_gap
                    else:
                        target_gap = gap_percent / 100

                    # 计算校准因子
                    target_price = last_close * (1 + target_gap)
                    calibration_factor = target_price / first_pred

                    # 应用校准到整个预测序列
                    pred_median = pred_median * calibration_factor
                    pred_upper = pred_upper * calibration_factor
                    pred_lower = pred_lower * calibration_factor
                    pred_max = pred_max * calibration_factor
                    pred_min = pred_min * calibration_factor

                    logger.info(f"价格连续性校准完成: {first_pred:.2f} -> {target_price:.2f} (校准因子: {calibration_factor:.3f})")

            # 使用校准后的中位数作为最终预测
            pred_mean = pred_median

            # 生成递增的不确定性区间（符合金融预测规律）
            for i in range(len(pred_upper)):
                if pred_upper[i] - pred_lower[i] < pred_mean[i] * 0.01:  # 如果区间太小
                    # 基于时间递增的不确定性：随着预测天数增加，不确定性增大
                    time_factor = np.sqrt(i + 1)  # 时间平方根增长
                    base_uncertainty = daily_volatility * time_factor * 0.8  # 基于历史波动率

                    # 确保最小不确定性，但随时间递增
                    min_uncertainty_pct = 0.015 + 0.005 * i  # 1.5%起步，每天增加0.5%
                    uncertainty = max(base_uncertainty, min_uncertainty_pct)

                    half_range = pred_mean[i] * uncertainty
                    pred_upper[i] = pred_mean[i] + half_range
                    pred_lower[i] = pred_mean[i] - half_range

                    # 更新其他统计量以保持一致性
                    pred_std[i] = half_range / 1.5  # 近似标准差

            # 创建最终预测DataFrame（使用均值）
            # 确保最终预测也传入 Series 时间戳
            x_ts_final = x_timestamp if isinstance(x_timestamp, pd.Series) else pd.Series(x_timestamp)
            y_ts_final = y_timestamp if isinstance(y_timestamp, pd.Series) else pd.Series(y_timestamp)

            try:
                pred_df = self.predictor.predict(
                    df=x_df,
                    x_timestamp=x_ts_final,
                    y_timestamp=y_ts_final,
                    pred_len=params['pred_len'],
                    T=params['T'],
                    top_p=params['top_p'],
                    top_k=params['top_k'],
                    sample_count=1,
                    verbose=False
                )
            except Exception as e:
                if self.device == "cuda":
                    logger.warning(f"GPU最终预测失败，回退CPU重试: {e}")
                    self.device = "cpu"
                    try:
                        self.predictor.model = self.predictor.model.to(self.device)
                        self.predictor.tokenizer = self.predictor.tokenizer.to(self.device)
                    except Exception:
                        self._load_model()
                    pred_df = self.predictor.predict(
                        df=x_df,
                        x_timestamp=x_ts_final,
                        y_timestamp=y_ts_final,
                        pred_len=params['pred_len'],
                        T=params['T'],
                        top_p=params['top_p'],
                        top_k=params['top_k'],
                        sample_count=1,
                        verbose=False
                    )
                else:
                    raise

            # 用蒙特卡洛均值替换收盘价
            pred_df['close'] = pred_mean

            # 价格连续性校准：确保OHLC的第一天开盘价合理（暂时禁用）
            if False and len(pred_df) > 0:
                last_close = float(df['close'].iloc[-1])
                first_open = float(pred_df['open'].iloc[0])
                gap_percent = (first_open - last_close) / last_close * 100

                # 如果开盘价跳空超过±3%，进行OHLC校准
                if abs(gap_percent) > 3.0:
                    logger.warning(f"OHLC开盘价异常跳空: {gap_percent:.2f}%，进行校准")

                    # 计算目标开盘价（限制在±2%以内）
                    max_gap = 0.02
                    if gap_percent > 3.0:
                        target_gap = max_gap
                    elif gap_percent < -3.0:
                        target_gap = -max_gap
                    else:
                        target_gap = gap_percent / 100

                    target_open = last_close * (1 + target_gap)
                    open_calibration = target_open / first_open

                    # 应用校准到第一天的OHLC
                    pred_df.loc[0, 'open'] = target_open
                    pred_df.loc[0, 'high'] = pred_df.loc[0, 'high'] * open_calibration
                    pred_df.loc[0, 'low'] = pred_df.loc[0, 'low'] * open_calibration

                    # 确保OHLC关系正确
                    first_close = pred_df.loc[0, 'close']
                    first_high = pred_df.loc[0, 'high']
                    first_low = pred_df.loc[0, 'low']

                    # 调整高低价确保关系正确
                    min_price = min(target_open, first_close)
                    max_price = max(target_open, first_close)

                    if first_high < max_price:
                        pred_df.loc[0, 'high'] = max_price * 1.005  # 略高于最高的开盘/收盘价
                    if first_low > min_price:
                        pred_df.loc[0, 'low'] = min_price * 0.995   # 略低于最低的开盘/收盘价

                    logger.info(f"OHLC校准完成: 开盘价 {first_open:.2f} -> {target_open:.2f}")

                    # 对后续天数进行渐进式校准，避免突然的价格跳跃
                    for i in range(1, min(3, len(pred_df))):  # 校准前3天
                        decay_factor = 0.7 ** i  # 指数衰减
                        if decay_factor > 0.1:
                            for col in ['open', 'high', 'low']:
                                pred_df.loc[i, col] *= (1 + (open_calibration - 1) * decay_factor)

            # 标尺校准（仅当首日偏差极端时）：将首日预测锚定到最后收盘价的同量级
            try:
                calibrate = os.getenv('CALIBRATE_FIRST_STEP', '1') == '1'
            except Exception:
                calibrate = True
            if calibrate and len(pred_df) > 0:
                first_pred = float(pred_df['close'].iloc[0])
                last_close = float(df['close'].iloc[-1])
                if first_pred > 0 and last_close > 0:
                    ratio = first_pred / last_close
                    # 阈值可根据日尺度适当放宽，这里 ±50%
                    if ratio < 0.5 or ratio > 1.5:
                        scale = last_close / first_pred
                        for c in ['open','high','low','close']:
                            if c in pred_df.columns:
                                pred_df[c] = pred_df[c] * scale
                        # 同步不确定性区间（基于close）
                        pred_upper = pred_upper * scale
                        pred_lower = pred_lower * scale
                        pred_max = pred_max * scale
                        pred_min = pred_min * scale
                        pred_mean = pred_mean * scale
                        logger.warning(f"已执行首日标尺校准: last_close={last_close:.2f}, first_pred(before)={first_pred:.2f}, scale={scale:.3f}")

            # 安全的价格连续性修复
            self._safe_price_continuity_fix(pred_df, float(df['close'].iloc[-1]), stock_code)

            # 基于A股日内涨跌幅约束的后处理（保证OHLC一致性、非负、日内变动不超限）
            last_close = float(df['close'].iloc[-1])
            try:
                # 自动识别更精确的日内涨跌幅限制（ST 5%，科创/创业20%，其余10%），允许 DAILY_LIMIT_PCT 覆盖
                stock_name_upper = str((stock_info or {}).get('name', '')).upper()
                code = str(stock_code)
                base_limit = 0.05 if ('ST' in stock_name_upper or code.upper().startswith('*ST')) else (0.2 if (code.startswith('688') or code.startswith('300')) else 0.1)
                daily_limit = float(os.getenv('DAILY_LIMIT_PCT', str(base_limit)))
                prev_close = last_close
                # 统一数值列为 float64，避免后续写入触发 dtype 警告
                try:
                    for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                        if col in pred_df.columns:
                            pred_df[col] = pd.to_numeric(pred_df[col], errors='coerce').astype('float64')
                except Exception:
                    pass

                for i in range(len(pred_df)):
                    # 转为float并处理NaN/Inf
                    for c in ['open','high','low','close']:
                        try:
                            val = float(pred_df.iloc[i][c])
                        except Exception:
                            val = prev_close
                        if not np.isfinite(val):
                            val = prev_close
                        pred_df.iat[i, pred_df.columns.get_loc(c)] = val

                    # 计算当日允许区间
                    band_min = max(prev_close * (1 - daily_limit), 0.01)
                    band_max = prev_close * (1 + daily_limit)
                    # A股价格最小变动单位为0.01元，量化允许区间到分
                    band_min_2 = float(np.ceil(band_min * 100.0) / 100.0)
                    band_max_2 = float(np.floor(band_max * 100.0) / 100.0)

                    # 更自然的约束：设置内边距（默认0.2%），越界时拉回到内边界，而非极限价
                    natural_margin = float(os.getenv('NATURAL_MARGIN_PCT', '0.002'))
                    inner_min = min(band_max_2, max(band_min_2 * (1 + natural_margin), band_min_2 + 0.01))
                    inner_max = max(band_min_2, min(band_max_2 * (1 - natural_margin), band_max_2 - 0.01))


                    # 先对 close 进行区间裁剪 + 两位小数量化（更自然：越界时拉回内边界）
                    c_raw = float(pred_df.iloc[i]['close'])
                    c_clip = float(np.clip(c_raw, band_min, band_max))
                    c_val = float(np.round(c_clip, 2))
                    if c_val >= band_max_2:
                        c_val = inner_max
                    elif c_val <= band_min_2:
                        c_val = inner_min

                    # 对 open/high/low 裁剪到同一日内区间 + 两位小数量化（更自然）
                    o_raw = float(pred_df.iloc[i]['open'])
                    h_raw = float(pred_df.iloc[i]['high'])
                    l_raw = float(pred_df.iloc[i]['low'])

                    o_clip = float(np.clip(o_raw, band_min, band_max))
                    h_clip = float(np.clip(h_raw, band_min, band_max))
                    l_clip = float(np.clip(l_raw, band_min, band_max))

                    o_val = float(np.round(o_clip, 2))
                    h_val = float(np.round(h_clip, 2))
                    l_val = float(np.round(l_clip, 2))

                    if o_val >= band_max_2:
                        o_val = inner_max
                    elif o_val <= band_min_2:
                        o_val = inner_min

                    if h_val >= band_max_2:
                        h_val = inner_max
                    elif h_val <= band_min_2:
                        h_val = inner_min

                    if l_val >= band_max_2:
                        l_val = inner_max
                    elif l_val <= band_min_2:
                        l_val = inner_min

                    # 保证OHLC一致性：high>=max(o,c,l)；low<=min(o,c,l)
                    high_fixed = max(h_val, o_val, c_val)
                    low_fixed = min(l_val, o_val, c_val)

                    pred_df.iat[i, pred_df.columns.get_loc('open')] = o_val
                    pred_df.iat[i, pred_df.columns.get_loc('high')] = high_fixed
                    pred_df.iat[i, pred_df.columns.get_loc('low')] = low_fixed
                    pred_df.iat[i, pred_df.columns.get_loc('close')] = c_val

                    prev_close = c_val

                # 体量非负，amount 对齐 close*volume
                if 'volume' in pred_df.columns:
                    pred_df['volume'] = np.maximum(pd.to_numeric(pred_df['volume'], errors='coerce').fillna(0), 0)
                if 'amount' in pred_df.columns and 'volume' in pred_df.columns:
                    pred_df['amount'] = pred_df['close'] * pred_df['volume']
            except Exception as _:
                pass

            # 计算预测统计
            pred_close = float(pred_df['close'].iloc[-1])
            change_pct = (pred_close - last_close) / last_close * 100

            # 计算趋势
            trend = "上涨" if change_pct > 1 else "下跌" if change_pct < -1 else "震荡"

            # 计算波动率
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # 年化波动率

            # 准备不确定性数据
            uncertainty_data = {
                'upper': pred_upper,
                'lower': pred_lower,
                'max': pred_max,
                'min': pred_min,
                'std': pred_std
            }

            # 动态置信度评估：依据预测区间相对收盘价的平均宽度（百分比）
            try:
                close_series_for_conf = pd.to_numeric(pred_df['close'], errors='coerce')
                band_width = (pred_upper - pred_lower)
                with np.errstate(divide='ignore', invalid='ignore'):
                    band_pct = np.where(close_series_for_conf > 0, band_width / close_series_for_conf, np.nan)
                avg_band_pct = float(np.nanmean(band_pct)) * 100.0  # 转百分比
                # 阈值：<4% 高；4%-8% 中；>8% 低
                if avg_band_pct < 4:
                    confidence_label = '高'
                elif avg_band_pct < 8:
                    confidence_label = '中'
                else:
                    confidence_label = '低'
            except Exception:
                confidence_label = '中'

            # 性能统计结束（在结果构建前计算）
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            gpu_mem_peak = None
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_mem_peak = torch.cuda.max_memory_allocated()
                    torch.cuda.reset_peak_memory_stats()
            except Exception:
                pass

            # 记录首日预测相对历史收盘的比例，用于排查极端离散
            try:
                first_pred = float(pred_df['close'].iloc[0]) if len(pred_df) > 0 else None
                if first_pred and last_close and (first_pred > 0) and (last_close > 0):
                    ratio = first_pred / last_close
                    if ratio < 0.3 or ratio > 3.0:
                        logger.warning(f"首日预测价格与最后收盘差异过大: last_close={last_close:.2f}, first_pred={first_pred:.2f}, ratio={ratio:.3f}")
            except Exception:
                pass

            result = {
                'success': True,
                'error': None,
                'data': {
                    'stock_info': stock_info,
                    'historical_data': self._format_historical_data(df.tail(min(lookback, len(df)))),
                    'predictions': self._format_predictions(pred_df, y_timestamp, uncertainty_data, raw_df=pred_df.copy() if debug else None),
                    'summary': {
                        'current_price': float(last_close),
                        'predicted_price': float(pred_close),
                        'change_amount': float(pred_close - last_close),
                        'change_percent': float(change_pct),
                        'trend': trend,
                        'volatility': float(volatility),
                        'prediction_days': params['pred_len'],
                        'confidence': confidence_label,
                        'elapsed_ms': elapsed_ms,
                        'gpu_mem_peak': int(gpu_mem_peak) if gpu_mem_peak is not None else None
                    },
                    'metadata': {
                        'prediction_time': datetime.now().isoformat(),
                        'data_source': getattr(self.data_fetcher, 'last_refresh_source', getattr(self.data_fetcher, 'last_source', 'unknown')),
                        'cache_status': getattr(self.data_fetcher, 'last_cache_status', 'unknown'),
                        'cache_written': getattr(self.data_fetcher, 'last_refresh_written', getattr(self.data_fetcher, 'cache_written', False)),
                        'model_version': 'Kronos-small',
                        'use_mock': self.use_mock
                    }
                }
            }
            logger.info(f"预测完成: {stock_code}, 预期变化: {change_pct:.2f}%")
            return result

        except Exception as e:
            logger.error(f"预测失败 {stock_code}: {str(e)}")
            return {
                'success': False,
                'error': f'预测过程中发生错误: {str(e)}',
                'data': None
            }

    def get_model_status(self) -> Dict:
        """获取模型状态 + 最近一次数据源与缓存命中信息"""
        return {
            'model_loaded': self.model_loaded,
            'device': self.device,
            'use_mock': self.use_mock,
            'cuda_available': torch.cuda.is_available(),
            'default_params': self.default_params,
            'data_source': getattr(self.data_fetcher, 'last_source', None),
            'cache_status': getattr(self.data_fetcher, 'last_cache_status', None),
            'cache_written': getattr(self.data_fetcher, 'cache_written', False)
        }

    def batch_predict(self, stock_codes: List[str], **kwargs) -> Dict[str, Dict]:
        """
        批量预测多只股票
        Args:
            stock_codes: 股票代码列表
            **kwargs: 预测参数
        Returns:
            Dict: 批量预测结果
        """
        results = {}

        for code in stock_codes:
            try:
                result = self.predict_stock(code, **kwargs)
                results[code] = result
            except Exception as e:
                results[code] = {
                    'success': False,
                    'error': str(e),
                    'data': None
                }

        return results

    def _get_daily_limit(self, stock_code):
        """根据股票代码确定涨跌幅限制"""
        if not stock_code:
            return 0.1  # 默认10%

        code_str = str(stock_code).upper()

        # ST股票：±5%
        if 'ST' in code_str or code_str.startswith('*ST'):
            return 0.05

        # 科创板：±20%
        if code_str.startswith('688'):
            return 0.2

        # 创业板：±20% (注册制后)
        if code_str.startswith('300'):
            return 0.2

        # 主板和中小板：±10%
        if code_str.startswith(('000', '001', '002', '600', '601', '603', '605')):
            return 0.1

        # 默认主板限制
        return 0.1

    def _safe_price_continuity_fix(self, pred_df, last_close, stock_code=None):
        """安全的价格连续性修复 - 只修复明显异常的跳空，并确保涨跌幅限制"""
        try:
            if len(pred_df) == 0 or last_close <= 0:
                return

            # 获取第一天的开盘价
            first_open = float(pred_df.iloc[0]['open'])
            if first_open <= 0:
                return

            # 计算跳空幅度
            gap_percent = (first_open - last_close) / last_close * 100

            # 只修复明显异常的跳空（>±5%）
            if abs(gap_percent) > 5.0:
                logger.info(f"检测到异常跳空: {gap_percent:.2f}%，进行安全修复")

                # 计算合理的目标开盘价（限制在±3%以内）
                max_gap = 0.03 if gap_percent > 0 else -0.03
                target_open = last_close * (1 + max_gap)

                # 计算调整因子
                adjustment_factor = target_open / first_open

                # 只调整第一天的价格，避免影响整个序列
                pred_df.iloc[0, pred_df.columns.get_loc('open')] = target_open

                # 按比例调整第一天的其他价格，保持相对关系
                for col in ['high', 'low', 'close']:
                    if col in pred_df.columns:
                        original_price = float(pred_df.iloc[0][col])
                        adjusted_price = original_price * adjustment_factor
                        pred_df.iloc[0, pred_df.columns.get_loc(col)] = adjusted_price

                # 确保OHLC关系正确
                o = pred_df.iloc[0]['open']
                h = pred_df.iloc[0]['high']
                l = pred_df.iloc[0]['low']
                c = pred_df.iloc[0]['close']

                # 修正高低价
                min_oc = min(o, c)
                max_oc = max(o, c)

                if h < max_oc:
                    pred_df.iloc[0, pred_df.columns.get_loc('high')] = max_oc * 1.001
                if l > min_oc:
                    pred_df.iloc[0, pred_df.columns.get_loc('low')] = min_oc * 0.999

                new_gap = (target_open - last_close) / last_close * 100
                logger.info(f"跳空修复完成: {gap_percent:.2f}% -> {new_gap:.2f}%")

            # 额外的涨跌幅检查和修复
            self._enforce_daily_limits(pred_df, last_close, stock_code)

        except Exception as e:
            logger.warning(f"价格连续性修复失败: {e}")
            # 不抛出异常，让预测继续

    def _enforce_daily_limits(self, pred_df, initial_close, stock_code=None):
        """强制执行A股涨跌幅限制"""
        try:
            prev_close = initial_close

            # 根据股票代码确定涨跌幅限制
            daily_limit = self._get_daily_limit(stock_code)
            logger.info(f"股票{stock_code}涨跌幅限制: ±{daily_limit*100:.0f}%")

            for i in range(len(pred_df)):

                # 计算当日允许的价格区间
                min_price = prev_close * (1 - daily_limit)
                max_price = prev_close * (1 + daily_limit)

                # 获取当前价格
                o = float(pred_df.iloc[i]['open'])
                h = float(pred_df.iloc[i]['high'])
                l = float(pred_df.iloc[i]['low'])
                c = float(pred_df.iloc[i]['close'])

                # 检查是否超出涨跌幅限制（添加小的容差避免浮点数精度问题）
                tolerance = 0.0001  # 0.01%的容差
                prices = [o, h, l, c]
                max_current = max(prices)
                min_current = min(prices)

                if max_current > (max_price + tolerance) or min_current < (min_price - tolerance):
                    logger.warning(f"第{i+1}天价格超出涨跌幅限制，进行修正")
                    logger.warning(f"原价格范围: {min_current:.2f} - {max_current:.2f}")
                    logger.warning(f"允许范围: {min_price:.2f} - {max_price:.2f}")

                    # 修正价格到允许范围内
                    o_fixed = np.clip(o, min_price, max_price)
                    h_fixed = np.clip(h, min_price, max_price)
                    l_fixed = np.clip(l, min_price, max_price)
                    c_fixed = np.clip(c, min_price, max_price)

                    # 确保OHLC关系正确
                    min_oc = min(o_fixed, c_fixed)
                    max_oc = max(o_fixed, c_fixed)
                    h_fixed = max(h_fixed, max_oc)
                    l_fixed = min(l_fixed, min_oc)

                    # 更新价格
                    pred_df.iloc[i, pred_df.columns.get_loc('open')] = o_fixed
                    pred_df.iloc[i, pred_df.columns.get_loc('high')] = h_fixed
                    pred_df.iloc[i, pred_df.columns.get_loc('low')] = l_fixed
                    pred_df.iloc[i, pred_df.columns.get_loc('close')] = c_fixed

                    logger.info(f"修正后价格: O={o_fixed:.2f}, H={h_fixed:.2f}, L={l_fixed:.2f}, C={c_fixed:.2f}")

                # 更新前一天收盘价
                prev_close = float(pred_df.iloc[i]['close'])

        except Exception as e:
            logger.warning(f"涨跌幅限制执行失败: {e}")

    def _simple_ohlc_fix(self, pred_df):
        """简化的OHLC关系修复"""
        try:
            for i in range(len(pred_df)):
                # 获取当天价格
                o = float(pred_df.iloc[i]['open'])
                h = float(pred_df.iloc[i]['high'])
                l = float(pred_df.iloc[i]['low'])
                c = float(pred_df.iloc[i]['close'])

                # 确保基本OHLC关系
                min_oc = min(o, c)
                max_oc = max(o, c)

                # 修复高价：必须 >= max(open, close)
                if h < max_oc:
                    pred_df.iloc[i, pred_df.columns.get_loc('high')] = max_oc * 1.001

                # 修复低价：必须 <= min(open, close)
                if l > min_oc:
                    pred_df.iloc[i, pred_df.columns.get_loc('low')] = min_oc * 0.999

        except Exception as e:
            logger.warning(f"OHLC简单修复失败: {e}")
            # 不抛出异常，让预测继续

    def _fix_comprehensive_ohlc_issues(self, pred_df, last_close):
        """全面修复OHLC关系和价格连续性问题"""
        if len(pred_df) == 0:
            return

        logger.info("开始全面OHLC修复...")

        try:
            # 1. 修复每日的OHLC关系
            for i in range(len(pred_df)):
                try:
                    open_price = float(pred_df.iloc[i]['open'])
                    high_price = float(pred_df.iloc[i]['high'])
                    low_price = float(pred_df.iloc[i]['low'])
                    close_price = float(pred_df.iloc[i]['close'])
                except (ValueError, TypeError) as e:
                    logger.warning(f"第{i+1}天价格数据转换失败: {e}，跳过修复")
                    continue

                # 确保价格为正数
                if any(p <= 0 for p in [open_price, high_price, low_price, close_price]):
                    logger.warning(f"第{i+1}天发现非正价格，跳过修复")
                    continue

                # 修复OHLC关系：确保 low <= min(open,close) <= max(open,close) <= high
                min_oc = min(open_price, close_price)
                max_oc = max(open_price, close_price)

                # 调整高价：必须 >= max(open, close)
                if high_price < max_oc:
                    high_price = max_oc * 1.002  # 略高于最高的开盘/收盘价
                    pred_df.iloc[i, pred_df.columns.get_loc('high')] = high_price
                    logger.debug(f"第{i+1}天调整高价: {pred_df.iloc[i]['high']:.2f} -> {high_price:.2f}")

                # 调整低价：必须 <= min(open, close)
                if low_price > min_oc:
                    low_price = min_oc * 0.998  # 略低于最低的开盘/收盘价
                    pred_df.iloc[i, pred_df.columns.get_loc('low')] = low_price
                    logger.debug(f"第{i+1}天调整低价: {pred_df.iloc[i]['low']:.2f} -> {low_price:.2f}")

                # 限制日内波动幅度（不超过15%）
                if open_price > 0:  # 确保开盘价为正数
                    daily_range = (high_price - low_price) / open_price
                    if daily_range > 0.15:  # 超过15%日内波动
                        # 压缩高低价范围
                        mid_price = (high_price + low_price) / 2
                        max_range = open_price * 0.15
                        new_high = mid_price + max_range / 2
                        new_low = mid_price - max_range / 2

                        # 确保仍然满足OHLC关系
                        new_high = max(new_high, max_oc)
                        new_low = min(new_low, min_oc)

                        pred_df.iloc[i, pred_df.columns.get_loc('high')] = new_high
                        pred_df.iloc[i, pred_df.columns.get_loc('low')] = new_low
                        logger.debug(f"第{i+1}天压缩日内波动: {daily_range:.1%} -> {(new_high-new_low)/open_price:.1%}")

            # 2. 修复日间连续性
            prev_close = last_close
            for i in range(len(pred_df)):
                current_open = pred_df.iloc[i]['open']

                # 确保前一天收盘价为正数
                if prev_close <= 0:
                    logger.warning(f"第{i+1}天前一天收盘价异常: {prev_close}，跳过连续性修复")
                    prev_close = pred_df.iloc[i]['close']
                    continue

                gap_percent = (current_open - prev_close) / prev_close * 100

                # 如果跳空超过±8%，进行调整
                if abs(gap_percent) > 8.0:
                    # 限制跳空在±5%以内
                    max_gap = 0.05 if gap_percent > 0 else -0.05
                    target_open = prev_close * (1 + max_gap)

                    # 确保当前开盘价为正数
                    if current_open <= 0:
                        logger.warning(f"第{i+1}天开盘价异常: {current_open}，跳过调整")
                        prev_close = pred_df.iloc[i]['close']
                        continue

                    adjustment_factor = target_open / current_open

                    # 调整当天的所有价格
                    for col in ['open', 'high', 'low', 'close']:
                        pred_df.iloc[i, pred_df.columns.get_loc(col)] *= adjustment_factor

                    logger.info(f"第{i+1}天跳空调整: {gap_percent:.1f}% -> {max_gap*100:.1f}%")

                prev_close = pred_df.iloc[i]['close']

            logger.info("全面OHLC修复完成")

        except Exception as e:
            logger.error(f"OHLC修复过程中发生错误: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            # 不重新抛出异常，让预测继续进行


# 全局预测服务实例
_prediction_service = None

def get_prediction_service(device: str = "cpu", use_mock: bool = False) -> StockPredictionService:
    """获取预测服务实例（单例模式）"""
    global _prediction_service

    if _prediction_service is None:
        _prediction_service = StockPredictionService(device=device, use_mock=use_mock)

    return _prediction_service


# 测试函数
def test_prediction_service():
    """测试预测服务"""
    service = get_prediction_service(use_mock=True)

    # 测试模型状态
    status = service.get_model_status()
    print(f"模型状态: {status}")

    # 测试预测
    test_codes = ['000001', '600000']

    for code in test_codes:
        print(f"\n测试预测: {code}")
        result = service.predict_stock(code, pred_len=30)

        if result['success']:
            summary = result['data']['summary']
            print(f"当前价格: {summary['current_price']:.2f}")
            print(f"预测价格: {summary['predicted_price']:.2f}")
            print(f"预期变化: {summary['change_percent']:.2f}%")
            print(f"趋势: {summary['trend']}")
        else:
            print(f"预测失败: {result['error']}")


if __name__ == "__main__":
    test_prediction_service()

# 真实Kronos模型集成
try:
    from akshare_adapter import AkshareDataAdapter
    REAL_MODEL_AVAILABLE = True
except ImportError:
    REAL_MODEL_AVAILABLE = False

class RealKronosPredictor:
    """真实Kronos模型预测器"""

    def __init__(self):
        self.data_adapter = AkshareDataAdapter()
        self.model_loaded = False

        # 这里应该加载真实的Kronos模型
        # 由于模型加载比较复杂，暂时使用增强的模拟模式
        print("⚠️ 真实模型加载功能开发中，使用增强模拟模式")

    def predict(self, stock_code: str, params: dict) -> dict:
        """使用真实数据进行预测"""
        try:
            # 获取真实历史数据
            input_data, stock_info = self.data_adapter.prepare_kronos_input(
                stock_code, params.get('lookback', 90), params.get('period', '1y')
            )

            if input_data is None:
                raise ValueError(f"无法获取股票 {stock_code} 的数据")

            # 使用真实数据进行增强模拟预测
            predictions = self._enhanced_simulation_predict(input_data, params)

            return {
                'success': True,
                'data': {
                    'stock_info': stock_info,
                    'historical_data': self._format_historical_data(input_data),
                    'predictions': predictions,
                    'summary': self._calculate_summary(input_data, predictions)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"预测失败: {str(e)}"
            }

    def _enhanced_simulation_predict(self, historical_data, params):
        """基于真实数据的增强模拟预测"""
        import numpy as np

        pred_len = params.get('pred_len', 10)

        # 获取最近的价格数据
        recent_prices = historical_data[-30:, 3]  # close prices
        recent_volumes = historical_data[-30:, 4]  # volumes

        # 计算趋势和波动性
        price_changes = np.diff(recent_prices[-10:])

        # 检测并过滤异常涨跌（超过±8%的单日变化）
        normal_changes = price_changes[np.abs(price_changes / recent_prices[-10:-1]) <= 0.08]

        if len(normal_changes) > 0:
            price_trend = np.mean(normal_changes)
            price_volatility = np.std(normal_changes) / np.mean(recent_prices[-10:])
        else:
            # 如果所有变化都是异常的，使用更保守的估计
            price_trend = 0
            price_volatility = 0.02

        # 限制波动率，避免过度波动
        price_volatility = min(price_volatility, 0.03)  # 最大3%的日波动率

        # 检测最近是否有异常涨跌，如果有则减弱趋势延续性
        last_change = recent_prices[-1] - recent_prices[-2] if len(recent_prices) >= 2 else 0
        last_change_pct = last_change / recent_prices[-2] if len(recent_prices) >= 2 and recent_prices[-2] > 0 else 0

        # 如果最后一天涨跌幅超过5%，认为是异常，减弱趋势
        if abs(last_change_pct) > 0.05:
            price_trend *= 0.3  # 大幅减弱异常趋势的延续性
            print(f"检测到异常涨跌: {last_change_pct:.2%}，减弱趋势延续性")

        # 生成更真实的预测
        predictions = []
        last_close = recent_prices[-1]  # 前一天收盘价
        last_volume = recent_volumes[-1]

        for i in range(pred_len):
            # 趋势衰减
            trend_factor = max(0.1, 1 - i * 0.1)

            # 第一天开盘价应该接近前一天收盘价，后续天数开盘价接近前一天收盘价
            if i == 0:
                # 第一天：开盘价基于前一天收盘价，加入小幅跳空（通常在±2%以内）
                gap_factor = np.random.normal(0, 0.01)  # 1%的跳空标准差
                gap_factor = np.clip(gap_factor, -0.02, 0.02)  # 限制在±2%以内
                open_price = last_close * (1 + gap_factor)
            else:
                # 后续天数：开盘价接近前一天收盘价，允许小幅跳空
                gap_factor = np.random.normal(0, 0.005)  # 0.5%的跳空标准差
                gap_factor = np.clip(gap_factor, -0.015, 0.015)  # 限制在±1.5%以内
                open_price = last_close * (1 + gap_factor)

            # 基于开盘价和趋势计算收盘价
            price_change = price_trend * trend_factor + np.random.normal(0, price_volatility * open_price * 0.5)
            close_price = open_price + price_change

            # 确保收盘价不会偏离开盘价太远（日内波动限制）
            max_daily_change = open_price * 0.1  # 最大10%的日内波动
            close_price = np.clip(close_price,
                                open_price - max_daily_change,
                                open_price + max_daily_change)

            # 确保价格为正
            close_price = max(close_price, open_price * 0.5)

            # 生成高低价：确保 low <= open,close <= high
            base_volatility = price_volatility * open_price * 0.3  # 减小日内波动

            # 高价：在开盘价和收盘价的最大值基础上增加
            high_base = max(open_price, close_price)
            high_price = high_base + abs(np.random.normal(0, base_volatility))

            # 低价：在开盘价和收盘价的最小值基础上减少
            low_base = min(open_price, close_price)
            low_price = low_base - abs(np.random.normal(0, base_volatility))

            # 确保价格关系正确：low <= min(open,close) <= max(open,close) <= high
            low_price = max(low_price, low_base * 0.95)  # 低价不能太低
            high_price = min(high_price, high_base * 1.05)  # 高价不能太高

            # 成交量预测
            volume_change = np.random.normal(0, 0.15)  # 减小成交量波动
            new_volume = max(last_volume * 0.7, last_volume * (1 + volume_change))

            # 成交额
            avg_price = (open_price + high_price + low_price + close_price) / 4
            amount = avg_price * new_volume

            predictions.append({
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(close_price),
                'volume': int(new_volume),
                'amount': float(amount)
            })

            # 更新为下一天的基准
            last_close = close_price
            last_volume = new_volume

        return predictions

    def _format_historical_data(self, data):
        """格式化历史数据"""
        formatted = []
        for row in data:
            formatted.append({
                'open': float(row[0]),
                'high': float(row[1]),
                'low': float(row[2]),
                'close': float(row[3]),
                'volume': int(row[4]),
                'amount': float(row[5])
            })
        return formatted

    def _calculate_summary(self, historical_data, predictions):
        """计算预测摘要"""
        current_price = float(historical_data[-1, 3])
        predicted_price = float(predictions[-1]['close'])

        change = predicted_price - current_price
        change_percent = (change / current_price) * 100

        if change_percent > 2:
            trend = "强势上涨"
        elif change_percent > 0.5:
            trend = "上涨"
        elif change_percent > -0.5:
            trend = "震荡"
        elif change_percent > -2:
            trend = "下跌"
        else:
            trend = "大幅下跌"

        return {
            'current_price': current_price,
            'predicted_price': predicted_price,
            'change': change,
            'change_percent': change_percent,
            'trend': trend,
            'prediction_days': len(predictions)
        }
