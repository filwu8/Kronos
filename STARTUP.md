# Kronos 启动与目录说明

本文件说明如何启动项目、目录规范，以及数据与测试的组织方式。

## 目录规范（本次已整理建议）

- tests/               所有测试与验证脚本（根目录的 test_*.py 等已迁移至此）
- volumes/             所有外部数据、模型、日志等
  - volumes/data/      外部数据（akshare、tushare、qlib 等）
  - volumes/models/    模型文件（Kronos-* 等）
  - volumes/logs/      运行日志
- scripts/             脚本
  - scripts/local/     本地辅助脚本（organize_repo.py 可再次执行目录整理）
  - scripts/docker/    Docker 相关脚本
- app/                 应用代码（前后端）
- static/              静态资源（CSS/JS/图片）

> 如果你看到根目录仍有 data/ logs/ models/，可以运行 `python scripts/local/organize_repo.py` 自动迁移到 volumes/ 下。

## 启动方式

### 方式一：本地直接运行（开发调试推荐）

1. 安装依赖

```bash
pip install -r app/requirements.txt
```

2. 启动后端 API（终端1）：

```bash
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

3. 启动前端（终端2）：

```bash
python -m streamlit run app/streamlit_app.py --server.port 8501
```

访问：
- 前端：http://localhost:8501
- API文档：http://localhost:8000/docs

### 方式二：Docker

```bash
./manage.sh start
# 或
docker-compose up -d
```

访问：
- 主界面：http://localhost
- 健康检查：http://localhost/health

## 测试

所有测试均在 tests/ 目录。

示例：

```bash
pytest -q tests
# 或单文件
python tests/final_system_verification.py
```

## 目录整理脚本

如果你在根目录新增了测试脚本或外部数据，可随时再次执行：

```bash
python scripts/local/organize_repo.py
```

该脚本会：
- 把根目录下的 test_*.py、final_*.py、quick_test.py 移动到 tests/
- 把 data/、logs/、models/ 合并到 volumes/ 对应目录
- 更新 tests/verify_models.py 的模型路径为 volumes/models
- 移除 *.backup 等冗余文件

## 注意

- 目录整理脚本是幂等的，可以多次运行
- 不会覆盖已有数据（如遇同名文件则合并/拷贝策略处理）

