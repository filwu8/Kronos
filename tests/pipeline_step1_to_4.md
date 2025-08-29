# Kronos 项目四步流水线（Step 1~4）

本说明给出严格对齐 examples/prediction_example.py 的“配置→数据→微调→回测”四步流程，提供可执行的脚本与命令，所有中间产物保存于 volumes/。

- 环境：Windows + .venv
- 数据：volumes/qlib_data/cn_data（Qlib）与 volumes/data/processed_datasets（pickle）
- 模型：默认切换为 2k 上下文（Kronos-base + Kronos-Tokenizer-2k）

## Step 1：配置您的实验（Config）
- 配置文件：finetune/config.py
- 关键项
  - instrument: csi300
  - dataset_begin_time / dataset_end_time
  - lookback_window=90, predict_window=10, max_context=2048（2k）
  - feature_list=['open','high','low','close','vol','amt']
  - 路径：
    - qlib_data_path: ./volumes/qlib_data/cn_data
    - dataset_path: ./volumes/data/processed_datasets
    - save_path: ./volumes/outputs/models
    - backtest_result_path: ./volumes/outputs/backtest_results

## Step 2：准备数据集（Qlib → Pickle）
- 运行：
  - python -m venv .venv
  - .venv\Scripts\activate
  - pip install -r app/requirements.txt
  - python finetune/qlib_data_preprocess.py
- 输出：
  - volumes/data/processed_datasets/train_data.pkl
  - volumes/data/processed_datasets/val_data.pkl
  - volumes/data/processed_datasets/test_data.pkl

## Step 3：运行微调（DDP 可选）
- 单机单卡（示例）：
  - set CUDA_VISIBLE_DEVICES=0
  - python -m torch.distributed.run --nproc_per_node=1 finetune/train_predictor_entry.py
- 说明：
  - 入口脚本会读取 finetune/config.py，并在 volumes/outputs/models 下保存 checkpoint 到 finetune_predictor_demo/checkpoints/best_model

## Step 4：通过回测进行评估（含累计收益曲线）
- 运行：
  - python finetune/qlib_test.py --device cuda:0
- 输出：
  - 控制台打印：基准收益、超额收益（含交易成本）等详尽报告
  - 图片：figures/backtest_result_example.png（累计收益与基准曲线）

## 注意
- 若使用 2k 上下文，确保 app/prediction_service.py 中模型加载与 max_context=2048 已生效（已为你切换）
- 四步流程只影响训练与评估，不影响前端 UI 的在线预测；两者共享 volumes/models 与 outputs
- 如需切换 benchmark/instrument，请修改 finetune/config.py

