# 启动问题排查指南

## 🎯 问题解决

您遇到的"API服务不可用"问题已经解决！

### ✅ 解决方案

**使用新的快速启动脚本**：
```powershell
.\quick_start.ps1
```

### 🔍 问题原因分析

1. **原并行启动问题**：
   - PowerShell后台任务可能因窗口关闭事件异常终止
   - 错误信息：`forrtl: error (200): program aborting due to window-CLOSE event`

2. **端口占用问题**：
   - 之前的进程没有正确清理
   - 端口8000和8501被占用

3. **启动时序问题**：
   - API和Streamlit同时启动可能导致竞争条件

### 🛠️ 修复措施

#### 1. 创建了稳定的启动脚本
- **quick_start.ps1**：顺序启动，健康检查
- **diagnose.ps1**：问题诊断和环境检查

#### 2. 改进的启动流程
```powershell
# 1. 环境检查
✅ 检测虚拟环境
✅ 验证依赖包

# 2. 端口清理  
🛑 停止占用进程
⏳ 等待端口释放

# 3. 顺序启动
📡 先启动API服务
⏳ 等待API健康检查通过
🌐 再启动Streamlit服务
⏳ 等待Streamlit健康检查通过

# 4. 成功确认
🎉 自动打开浏览器
📋 提供管理命令
```

#### 3. 健康检查机制
```powershell
# API健康检查
for ($i = 1; $i -le 15; $i++) {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health"
    if ($response.StatusCode -eq 200) { break }
    Start-Sleep 2
}

# Streamlit健康检查  
for ($i = 1; $i -le 10; $i++) {
    $response = Invoke-WebRequest -Uri "http://localhost:8501"
    if ($response.StatusCode -eq 200) { break }
    Start-Sleep 3
}
```

## 📋 常见问题解决

### 问题1：虚拟环境未激活
**症状**：`❌ 未找到虚拟环境`
**解决**：
```powershell
.venv\Scripts\activate
```

### 问题2：依赖缺失
**症状**：`❌ 缺少必要依赖`
**解决**：
```powershell
pip install -r app/requirements.txt
```

### 问题3：端口被占用
**症状**：`⚠️ 端口 8000 被占用`
**解决**：
```powershell
# 自动解决（脚本已包含）
taskkill /f /im python.exe
```

### 问题4：API启动失败
**症状**：`❌ API服务启动失败`
**解决**：
```powershell
# 手动启动测试
.venv\Scripts\python.exe -m uvicorn app.api:app --host 0.0.0.0 --port 8000
```

### 问题5：Streamlit启动失败
**症状**：`❌ Streamlit服务启动失败`
**解决**：
```powershell
# 手动启动测试
.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

## 🔧 管理命令

### 查看服务状态
```powershell
# 查看Python进程
Get-Process | Where-Object {$_.ProcessName -like '*python*'}

# 查看端口占用
netstat -an | findstr ":8000\|:8501"
```

### 停止服务
```powershell
# 停止所有Python进程
taskkill /f /im python.exe

# 或者更精确地停止
taskkill /f /im python3.11.exe
```

### 查看日志
```powershell
# 实时查看API日志
Get-Content volumes\logs\api.log -Tail 20 -Wait

# 实时查看Streamlit日志  
Get-Content volumes\logs\streamlit.log -Tail 20 -Wait
```

## 🎯 最佳实践

### 1. 启动前检查
```powershell
# 运行诊断
.\diagnose.ps1
```

### 2. 正常启动
```powershell
# 使用快速启动
.\quick_start.ps1
```

### 3. 问题排查
```powershell
# 如果启动失败，检查：
# 1. 虚拟环境是否激活
# 2. 依赖是否完整
# 3. 端口是否被占用
# 4. 查看错误日志
```

### 4. 清理重启
```powershell
# 完全清理后重启
taskkill /f /im python.exe
Start-Sleep 3
.\quick_start.ps1
```

## 📞 技术支持

如果仍然遇到问题：

1. **运行诊断**：`.\diagnose.ps1`
2. **查看日志**：检查 `volumes/logs/` 下的错误日志
3. **手动测试**：分别手动启动API和Streamlit服务
4. **环境重建**：重新创建虚拟环境和安装依赖

## ✅ 验证成功

启动成功后，您应该看到：
- ✅ API服务: http://localhost:8000
- ✅ 前端界面: http://localhost:8501  
- ✅ API文档: http://localhost:8000/docs
- 🌐 浏览器自动打开前端界面

现在您可以正常使用G-Prophet进行股票预测了！🎉
