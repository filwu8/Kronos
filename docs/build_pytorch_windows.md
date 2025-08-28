# 在 Windows 上从源码编译 PyTorch（适配 RTX 5090）

本指南帮助你在 Windows 原生环境（非 WSL）从源码编译最新的 PyTorch，以获得对新一代 GPU（如 RTX 5090）的更好/更早支持。

注意：源码编译耗时较长（30–180 分钟，取决于 CPU/磁盘），请耐心等待。推荐优先尝试官方夜版 Wheel（CUDA 12.x），若仍不满足再走源码编译。

---

## 1. 环境准备（Windows 10/11 x64）

必需软件（请保证均为 64 位）：
- Visual Studio 2022（安装“使用 C++ 的桌面开发”工作负载，包含 MSVC v143、Windows SDK）
- Python 3.10 或 3.11（建议 64 位，路径无空格）
- Git（包含 LFS 支持更佳）
- CMake 与 Ninja（可由 pip 安装）
- 最新 NVIDIA 显卡驱动（Studio 或 Game Ready），能驱动 RTX 5090

可选（仅在需要 NVCC/Headers 时）：
- CUDA Toolkit 12.4+/12.6+（与驱动匹配）

---

## 2. 创建专用虚拟环境并安装构建工具

PowerShell 在项目根（Kronos）执行：

```powershell
# 创建并启用 GPU venv（如已存在可跳过创建）
python -m venv .venv-gpu
.\.venv-gpu\Scripts\pip install --upgrade pip

# 安装通用构建工具
.\.venv-gpu\Scripts\pip install cmake ninja setuptools wheel typing_extensions
```

---

## 3. 获取 PyTorch 源码

建议放在与项目同级或任意无空格路径下，例如 D:\src\pytorch：

```powershell
cd D:\src
# 克隆含全部子模块（体积较大，时间较长）
git clone --recursive https://github.com/pytorch/pytorch.git
cd pytorch
# 若未使用 --recursive，可执行：
# git submodule sync --recursive
# git submodule update --init --recursive
```

可选择稳定分支或主分支：
```powershell
# 示例：切换到主分支（最新特性）
git checkout main
```

---

## 4. 安装 PyTorch 源码依赖

```powershell
# 在 pytorch 源码目录下
..\..\Docker-Devops\Aigc\Kronos\.venv-gpu\Scripts\pip install -r .\requirements.txt
```

若下载较慢，可配置国内镜像；但建议对源码依赖保持默认源，避免版本不兼容。

---

## 5. 配置编译环境变量（关键）

在 PowerShell 当前会话设置以下变量（仅对本次会话生效）：

```powershell
# 使用 Ninja 更快
$env:CMAKE_GENERATOR = "Ninja"

# 最大并行编译任务（按你 CPU 调整）
$env:MAX_JOBS = "$( [Environment]::ProcessorCount )"

# 启用 CUDA 构建
$env:USE_CUDA = "1"

# 可选：如果安装了 CUDA Toolkit，指定路径（按你的实际安装路径修改）
# $env:CUDA_HOME = "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.4"

# 针对新架构的前向兼容：包含 PTX，以便对未来/更新架构 JIT
# 对 30/40/数据中心卡普遍有效；若你的工具链已支持更高架构，可将 "9.0+PTX" 改为 "10.0+PTX"
$env:TORCH_CUDA_ARCH_LIST = "8.6;8.9;9.0;9.0+PTX"

# 可选：减少链接内存峰值（内存不足时）
# $env:USE_NINJA = "1"
```

说明：
- RTX 5090（Blackwell）如果你的 CUDA/编译链条已支持 sm_100/10.0，可将上面改为：`8.6;8.9;9.0;10.0;10.0+PTX`。
- 如果不确定，保留 `9.0+PTX` 也能通过 PTX 在新架构上运行（性能可能略低，但可用）。

---

## 6. 开始构建 PyTorch

在 `pytorch` 源码目录内运行（确保已激活 .venv-gpu 的 pip）：

```powershell
# 开发安装（便于后续更新）
..\..\Docker-Devops\Aigc\Kronos\.venv-gpu\Scripts\pip install -e .
# 或者：
# ..\..\Docker-Devops\Aigc\Kronos\.venv-gpu\Scripts\python setup.py develop
```

构建过程会自动下载/构建部分第三方组件，耗时较长。若构建失败，请查看“故障排查”。

---

## 7. 构建完成后的验证

回到 Kronos 根目录，使用同一解释器执行快速检查：

```powershell
.\.venv-gpu\Scripts\python -c "import torch,os; print('torch=',torch.__version__,'cuda=',torch.version.cuda,'is_available=',torch.cuda.is_available()); print('CUDA_VISIBLE_DEVICES=',os.getenv('CUDA_VISIBLE_DEVICES'))"

# 运行项目的 GPU 冒烟测试
.\.venv-gpu\Scripts\python .\tests\gpu_smoke_test.py
```

期望输出：`is_available=True`，并能成功完成一次极小的 CUDA matmul，同时打印出 GPU 名称与显存信息。

---

## 8. 与 Kronos 项目联动

- 使用 `DEVICE=auto` 启动可在有 GPU 时自动启用 CUDA，避免强制 `cuda` 时因不可用导致启动失败：

```powershell
$env:DEVICE='auto'; $env:FAST_CPU_MODE='0'; $env:CPU_THREADS='24'
.\.venv-gpu\Scripts\python -m uvicorn app.api:app --host 0.0.0.0 --port 8000
```

- 另开终端启动前端：

```powershell
.\.venv-gpu\Scripts\python -m streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

---

## 9. 常见故障排查

1) `cl.exe not found` 或 C++ 编译器报错
- 确认已安装 VS2022 + “使用 C++ 的桌面开发”组件
- 在“开发者命令提示符”或 PowerShell 中重新打开终端以刷新环境变量

2) `ninja: command not found`
- 已通过 pip 安装 `ninja` 但不可用时，重开终端；或直接设置 `$env:CMAKE_GENERATOR="Ninja"`

3) `nvcc fatal: Unsupported gpu architecture 'compute_XX'`
- 你的 CUDA 工具链不支持该架构号。例如设置了 `10.0` 但本地 NVCC 不支持。
- 解决：将 `TORCH_CUDA_ARCH_LIST` 降到工具链支持的最高数值，并保留 `+PTX` 实现前向兼容（如 `9.0;9.0+PTX`）。

4) `torch.cuda.is_available() = False`
- 驱动版本过旧 → 升级 NVIDIA 驱动
- 构建未启用 CUDA → 确认 `$env:USE_CUDA='1'`
- 没有可见 GPU → 笔记本需切换独显直连/禁用节能；台式机检查设备管理器

5) OOM 或链接阶段内存不足
- 降低并行度：`$env:MAX_JOBS='4'`
- 关闭调试符号/减少可选组件（进阶配置）

6) `error: torch/...' file not found` 等头文件缺失
- 确认子模块完整：`git submodule sync --recursive && git submodule update --init --recursive`

---

## 10. 可选：从源码编译 torchvision/torchaudio（如需要）

如果你的项目依赖源码级的 torchvision/torchaudio，新建目录并类似执行：

```powershell
# 以 torchvision 为例
cd D:\src
git clone https://github.com/pytorch/vision.git
cd vision
..\..\Docker-Devops\Aigc\Kronos\.venv-gpu\Scripts\pip install -e .
```

---

## 11. 清理与重建

```powershell
# 在 pytorch 源码目录
python tools\build\clear_caches.py
# 或手动删除 build 目录后重新 pip install -e .
```

---

如需我帮你远程按此步骤逐条执行（并在失败时最小化调整后重试），请告知你当前已安装的软件版本（VS、Python、驱动、是否安装 CUDA Toolkit）。
