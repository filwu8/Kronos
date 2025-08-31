# 清理多余的启动脚本，只保留唯一解决方案

Write-Host "🧹 清理多余的启动脚本..." -ForegroundColor Yellow

# 要删除的文件列表
$filesToRemove = @(
    "quick_start.ps1",
    "stable_start.ps1", 
    "start_services.ps1",
    "diagnose.ps1",
    "fix_timeout.ps1",
    "temp_api_start.py",
    "temp_streamlit_start.py",
    "test_api_400.py",
    "test_quick_ohlc.py"
)

Write-Host "将要删除的文件:" -ForegroundColor Cyan
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Gray
    } else {
        Write-Host "  - $file (不存在)" -ForegroundColor DarkGray
    }
}

$confirm = Read-Host "`n确认删除这些文件? (y/N)"
if ($confirm -eq 'y' -or $confirm -eq 'Y') {
    foreach ($file in $filesToRemove) {
        if (Test-Path $file) {
            try {
                Remove-Item $file -Force
                Write-Host "✅ 已删除: $file" -ForegroundColor Green
            } catch {
                Write-Host "❌ 删除失败: $file" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "`n🎯 现在您只需要使用一个启动脚本:" -ForegroundColor Green
    Write-Host ".\START.ps1" -ForegroundColor Cyan
    
} else {
    Write-Host "取消清理" -ForegroundColor Yellow
}

Write-Host "`n📋 唯一启动解决方案使用说明:" -ForegroundColor Yellow
Write-Host "启动服务: .\START.ps1" -ForegroundColor Gray
Write-Host "重启服务: .\START.ps1 restart" -ForegroundColor Gray  
Write-Host "诊断问题: .\START.ps1 diagnose" -ForegroundColor Gray
Write-Host "停止服务: taskkill /f /im python.exe" -ForegroundColor Gray
