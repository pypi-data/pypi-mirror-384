#!/usr/bin/env powershell
# XGO Blockly 构建和上传脚本
# 使用方法: .\build_and_upload.ps1

Write-Host "=== XGO Blockly 包构建和上传 ===" -ForegroundColor Green

# 检查并复制.pypirc配置文件
Write-Host "检查PyPI配置..." -ForegroundColor Yellow
$pypircPath = Join-Path $env:USERPROFILE ".pypirc"
if (!(Test-Path $pypircPath)) {
    if (Test-Path ".pypirc") {
        Write-Host "复制.pypirc到用户目录..." -ForegroundColor Yellow
        Copy-Item ".pypirc" $pypircPath -Force
        Write-Host "✓ .pypirc配置已复制到 $pypircPath" -ForegroundColor Green
    } else {
        Write-Host "⚠ 未找到.pypirc配置文件" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ 找到.pypirc配置文件" -ForegroundColor Green
}

# 检查必要工具
Write-Host "检查必要工具..." -ForegroundColor Yellow
$tools = @("python", "npm", "pip")
foreach ($tool in $tools) {
    try {
        & $tool --version | Out-Null
        Write-Host "✓ $tool 已安装" -ForegroundColor Green
    } catch {
        Write-Error "✗ $tool 未找到，请先安装"
        exit 1
    }
}

# 检查构建工具
Write-Host "检查Python构建工具..." -ForegroundColor Yellow
try {
    python -m build --help | Out-Null
    python -m twine --help | Out-Null
    Write-Host "✓ build 和 twine 已安装" -ForegroundColor Green
} catch {
    Write-Host "安装构建工具..." -ForegroundColor Yellow
    pip install --upgrade build twine setuptools wheel
}

# 1. 构建前端
Write-Host "1. 构建前端项目..." -ForegroundColor Yellow
$currentDir = Get-Location
Set-Location "..\blockly-vue3"

# 检查前端依赖
if (!(Test-Path "node_modules")) {
    Write-Host "安装前端依赖..." -ForegroundColor Yellow
    npm install
}

# 构建前端
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "前端构建失败"
    Set-Location $currentDir
    exit 1
}

Write-Host "✓ 前端构建成功" -ForegroundColor Green

# 2. 复制前端资源
Write-Host "2. 复制前端资源..." -ForegroundColor Yellow
if (Test-Path "..\xgo-blockly-server\xgo_blockly\dist") {
    Remove-Item -Path "..\xgo-blockly-server\xgo_blockly\dist" -Recurse -Force
}
Copy-Item -Path "dist" -Destination "..\xgo-blockly-server\xgo_blockly\" -Recurse -Force
Write-Host "✓ 前端资源复制完成" -ForegroundColor Green

# 3. 回到Python包目录
Set-Location "..\xgo-blockly-server"

# 4. 清理旧构建
Write-Host "3. 清理旧构建文件..." -ForegroundColor Yellow
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✓ 清理完成" -ForegroundColor Green

# 5. 构建包
Write-Host "4. 构建Python包..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Error "包构建失败"
    Set-Location $currentDir
    exit 1
}
Write-Host "✓ 包构建成功" -ForegroundColor Green

# 6. 检查包
Write-Host "5. 检查包质量..." -ForegroundColor Yellow
python -m twine check dist/*
if ($LASTEXITCODE -ne 0) {
    Write-Error "包检查失败"
    Set-Location $currentDir
    exit 1
}
Write-Host "✓ 包检查通过" -ForegroundColor Green

# 7. 显示构建结果
Write-Host "6. 构建结果:" -ForegroundColor Yellow
Get-ChildItem -Path "dist" | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 2)
    Write-Host "  $($_.Name) (${size} KB)" -ForegroundColor Cyan
}

# 8. 询问是否上传到测试PyPI
Write-Host "`n是否先上传到测试PyPI进行验证？(推荐)" -ForegroundColor Green
$testUpload = Read-Host "(y/n)"
if ($testUpload -eq "y" -or $testUpload -eq "Y") {
    Write-Host "上传到测试PyPI..." -ForegroundColor Yellow
    python -m twine upload --repository testpypi dist/*
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 测试PyPI上传成功！" -ForegroundColor Green
        Write-Host "测试安装命令: pip install --index-url https://test.pypi.org/simple/ xgo-blockly" -ForegroundColor Cyan
        
        # 询问是否继续上传到正式PyPI
        Write-Host "`n是否继续上传到正式PyPI？" -ForegroundColor Green
        $prodUpload = Read-Host "(y/n)"
        if ($prodUpload -eq "y" -or $prodUpload -eq "Y") {
            Write-Host "上传到正式PyPI..." -ForegroundColor Yellow
            python -m twine upload dist/*
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ 正式PyPI上传成功！" -ForegroundColor Green
                Write-Host "安装命令: pip install xgo-blockly" -ForegroundColor Cyan
            } else {
                Write-Error "正式PyPI上传失败"
                Set-Location $currentDir
                exit 1
            }
        }
    } else {
        Write-Error "测试PyPI上传失败"
        Set-Location $currentDir
        exit 1
    }
} else {
    # 直接询问是否上传到正式PyPI
    Write-Host "是否上传到正式PyPI？" -ForegroundColor Green
    $upload = Read-Host "(y/n)"
    if ($upload -eq "y" -or $upload -eq "Y") {
        Write-Host "上传到正式PyPI..." -ForegroundColor Yellow
        python -m twine upload dist/*
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 上传成功！" -ForegroundColor Green
            Write-Host "安装命令: pip install xgo-blockly" -ForegroundColor Cyan
        } else {
            Write-Error "上传失败"
            Set-Location $currentDir
            exit 1
        }
    } else {
        Write-Host "包已构建完成！" -ForegroundColor Green
        Write-Host "手动上传命令:" -ForegroundColor Cyan
        Write-Host "  测试PyPI: python -m twine upload --repository testpypi dist/*" -ForegroundColor Cyan
        Write-Host "  正式PyPI: python -m twine upload dist/*" -ForegroundColor Cyan
    }
}

Set-Location $currentDir
Write-Host "`n=== 完成 ===" -ForegroundColor Green