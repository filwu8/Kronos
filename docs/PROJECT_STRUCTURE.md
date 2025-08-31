# 项目结构与最小运行集说明

本项目包含前端（Streamlit）与后端（FastAPI）两部分，支持 Windows 本地开发与 Docker 运行；数据/模型/日志统一存放于 volumes。

## 最小运行集（本地与 Docker 通用）
- app/: 前端与后端核心代码
  - api.py, streamlit_app.py, prediction_service.py, data_fetcher.py
  - akshare_adapter.py, qlib_adapter.py, static_manager.py, chinese_menu.py
  - static/: 前端静态资源
- model/: Kronos 模型实现（被 prediction_service 直接引用）
- volumes/: 数据/模型/日志/qlib 数据等持久化路径
  - data/, models/, logs/, qlib_data/, nginx_logs/ 等
- run.py: 本地一键启动（读取 APP_DEBUG/LOG_LEVEL；日志写 volumes/logs）
- docker-compose.yml, nginx.conf, logo.png
- tests/: 测试与验证脚本（建议运行）

## 脚本与工具
- scripts/
  - data/download_5year_data.py（数据下载服务，compose 使用）
  - tools/convert_data_format.py, tools/integrate_real_models.py
  - qlib/setup_qlib_data.py

## 依赖与环境
- 统一使用 app/requirements.txt
- Windows 本地：建议 .venv 虚拟环境
- Docker：compose 绑定 volumes/*，日志与数据持久化

## 调试与日志
- 环境变量 APP_DEBUG（0/1），LOG_LEVEL（DEBUG/INFO/WARNING/ERROR）
- API 额外写入 volumes/logs/api_server.log

## 入口
- 本地：python run.py
- Docker：docker compose up -d（需要时启用 profile data-download）

