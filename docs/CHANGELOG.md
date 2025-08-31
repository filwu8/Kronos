# CHANGELOG (整理与小优化)

本页记录本轮目录整理、小优化与验证结果，便于快速了解变更与操作方法。

## 2025-08-31 整理清单

### 目录与脚本迁移
- data 下载脚本迁移并保留服务：
  - download_5year_data.py → scripts/data/download_5year_data.py
  - docker-compose.yml: 新增挂载 ./scripts:/app/scripts；命令改为 python scripts/data/download_5year_data.py
- 归档脚本：
  - convert_data_format.py → scripts/tools/convert_data_format.py
  - integrate_real_models.py → scripts/tools/integrate_real_models.py
  - setup_qlib_data.py → scripts/qlib/setup_qlib_data.py
- 本地/工具脚本集中化：
  - manage.bat → scripts/local/manage.bat
  - manage.sh → scripts/local/manage.sh
  - start.sh → scripts/local/start.sh
  - download_data.sh → scripts/tools/download_data.sh
  - download_models.sh → scripts/tools/download_models.sh
- 调试脚本：
  - debug_test.py → tests/debug_test.py
- 删除与清理：
  - 移除根目录 requirements.txt（统一使用 app/requirements.txt）
  - 删除 chart_verification.html、debug_chart.html、out_gpu_check.txt
  - 清理全部 __pycache__

### 调试与日志统一
- run.py：支持 APP_DEBUG、LOG_LEVEL；uvicorn/streamlit 日志级别与 reload 跟随；日志输出 volumes/logs
- app/api.py：按 LOG_LEVEL 初始化 logging，并追加 FileHandler 到 volumes/logs/api_server.log
- docs/PROJECT_STRUCTURE.md：新增项目结构与最小运行集说明

## 使用指南（简版）

### 本地（Windows）
1. 创建/激活虚拟环境（.venv）并安装依赖
   - python -m venv .venv
   - .\.venv\Scripts\activate
   - pip install -r app/requirements.txt
2. 启动
   - 可选：设置调试与日志级别（默认 INFO）
     - $env:APP_DEBUG='1'; $env:LOG_LEVEL='DEBUG'
   - python run.py
3. 访问
   - 前端 http://localhost:8501/
   - 健康检查 http://localhost:8000/health
4. 日志在 volumes/logs/ 下

### Docker
1. 启动
   - docker compose up -d
2. 数据下载服务（可选）
   - docker compose up data-downloader
3. 日志
   - volumes/logs/ 与 volumes/nginx_logs/

## 验证结果（本次）
- 导入烟雾测试：OK（tests/smoke_imports.py）
- 本地运行建议手动验证：
  - 设置 APP_DEBUG/LOG_LEVEL 后 python run.py
  - 浏览器访问 8000/health 与 8501 页面
- 如需要，我可执行更多单元/集成测试并反馈

---

如需回滚或进一步归档/删除脚本，请先与我确认，以确保不影响部署/运行。

