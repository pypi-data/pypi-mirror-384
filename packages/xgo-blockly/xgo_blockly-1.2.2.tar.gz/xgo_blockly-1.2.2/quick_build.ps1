#!/usr/bin/env powershell
# 快速构建脚本 - 仅构建不上传
# 使用方法: .\quick_build.ps1

Write-Host "=== 快速构建 XGO Blockly 包 ===" -ForegroundColor Green

# 1. 构建前端
Write-Host "构建前端..." -ForegroundColor Yellow
$currentDir = Get-Location
Set-Location "..\blockly-vue3"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "前端构建失败"
    Set-Location $currentDir
    exit 1
}

# 2. 复制资源
Write-Host "复制资源..." -ForegroundColor Yellow
Remove-Item -Path "..\xgo-blockly-server\xgo_blockly\dist" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path "dist" -Destination "..\xgo-blockly-server\xgo_blockly\" -Recurse -Force

# 3. 构建Python包
Write-Host "构建Python包..." -ForegroundColor Yellow
Set-Location "..\xgo-blockly-server"
Remove-Item -Path "build", "dist", "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue
python -m build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 构建成功！" -ForegroundColor Green
    Write-Host "构建文件位于 dist/ 目录" -ForegroundColor Cyan
    Get-ChildItem -Path "dist" | ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  $($_.Name) (${size} KB)" -ForegroundColor Cyan
    }
} else {
    Write-Error "构建失败"
    Set-Location $currentDir
    exit 1
}

Set-Location $currentDir