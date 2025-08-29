## Kronos 四步流水线（2k 上下文版）

- 目标：严格按“配置→数据→微调→回测”的步骤，产出可运行的训练与评估流
- 环境：Windows + .venv；数据与模型与结果统一保存在 volumes/

### Step 1 配置您的实验
- 文件：finetune/config.py
- 关键参数：instrument、时间窗、lookback_window、predict_window、max_context=2048
- 保存路径：dataset_path / save_path / backtest_result_path

### Step 2 准备数据集
- 命令：
  - python -m venv .venv
  - .venv\\Scripts\\activate
  - pip install -r app/requirements.txt
  - python finetune/qlib_data_preprocess.py
- 输出：train/val/test 的 pickle 数据，位于 volumes/data/processed_datasets/

### Step 3 运行微调
- 单卡（示例）：
  - set CUDA_VISIBLE_DEVICES=0
  - python -m torch.distributed.run --nproc_per_node=1 finetune/train_predictor_entry.py
- Checkpoint：volumes/outputs/models/finetune_predictor_demo/checkpoints/best_model

### Step 4 通过回测进行评估
- 命令：python finetune/qlib_test.py --device cuda:0
- 控制台打印详尽指标；生成 figures/backtest_result_example.png，展示相对基准的累计收益曲线

### 在线预测与前端
- app/prediction_service.py 已切换 2k 上下文（Kronos-base + Tokenizer-2k），max_context=2048
- 前端与回测（tests/backtest_direction.py、app/backtesting.py）不受影响，仍可使用

### 备注
- 如需改 benchmark 或标的集合，编辑 finetune/config.py 的 instrument / backtest_benchmark
- 可通过环境变量调整：
  - CALIBRATE_FIRST_STEP（首日标尺校准，默认1开）
  - DAILY_LIMIT_PCT（日内涨跌幅限制，默认0.2）

