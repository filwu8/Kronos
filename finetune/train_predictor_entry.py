#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入口脚本：读取 Config，加载 2k 上下文的 Kronos-base/Kronos-Tokenizer-2k，运行 finetune/train_predictor.py
产物保存在 volumes/outputs/models/ 下
"""
import os
import torch

from config import Config
from train_predictor import main as train_main
from model.kronos import KronosTokenizer, Kronos


def build_train_config(cfg: Config) -> dict:
    return {
        'seed': cfg.seed,
        'batch_size': cfg.batch_size,
        'epochs': cfg.epochs,
        'log_interval': cfg.log_interval,
        'predictor_learning_rate': cfg.predictor_learning_rate,
        'adam_beta1': cfg.adam_beta1,
        'adam_beta2': cfg.adam_beta2,
        'adam_weight_decay': cfg.adam_weight_decay,
        'accumulation_steps': cfg.accumulation_steps,
        'save_path': cfg.save_path,
        'predictor_save_folder_name': cfg.predictor_save_folder_name,
        'use_comet': cfg.use_comet,
        'num_workers': max(2, os.cpu_count()//2),
    }


if __name__ == '__main__':
    os.environ.setdefault('TOKENIZER_MODEL_ID', 'NeoQuasar/Kronos-Tokenizer-2k')
    os.environ.setdefault('PREDICTOR_MODEL_ID', 'NeoQuasar/Kronos-base')

    cfg = Config()
    # 在 volumes/models 下准备预训练模型（可选）
    os.makedirs('./volumes/models', exist_ok=True)

    # 仅检查是否可从HF下载（训练过程中会按需要加载）
    try:
        _ = KronosTokenizer.from_pretrained(os.getenv('TOKENIZER_MODEL_ID'))
        _ = Kronos.from_pretrained(os.getenv('PREDICTOR_MODEL_ID'))
        print('✅ 2k 上下文预训练模型可用')
    except Exception as e:
        print(f'⚠️ 预训练模型检查失败: {e}')

    train_cfg = build_train_config(cfg)
    train_main(train_cfg)

