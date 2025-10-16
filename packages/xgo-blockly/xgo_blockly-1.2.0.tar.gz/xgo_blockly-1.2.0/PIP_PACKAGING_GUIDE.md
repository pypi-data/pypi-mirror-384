# XGO Blockly 手动打包和上传 PyPI 指南

本文档详细说明如何手动构建和上传 `xgo-blockly` 包到 PyPI。

## 📋 前置要求

```bash
# 安装必要的构建工具
pip install --upgrade pip
pip install --upgrade build          # Python包构建工具
pip install --upgrade twine          # PyPI上传工具
pip install --upgrade setuptools     # 安装工具
pip install --upgrade wheel          # wheel格式支持
```

## 🏗️ 第一步：准备项目环境

### 1.1 确保前端资源已构建
```bash
# 切换到前端目录
cd ..\blockly-vue3

# 安装前端依赖（如果还没有安装）
npm install

# 构建前端项目（生成dist目录）
npm run build

# 将构建好的前端资源复制到Python包中
# Windows PowerShell:
Copy-Item -Path "dist" -Destination "..\xgo-blockly-server\xgo_blockly\" -Recurse -Force

# Linux/macOS:
# cp -r dist ../xgo-blockly-server/xgo_blockly/
```

### 1.2 回到Python包目录
```bash
cd ..\xgo-blockly-server
```

### 1.3 验证项目结构
确保目录结构如下：
```
xgo-blockly-server/
├── xgo_blockly/           # 主包目录
│   ├── dist/             # 前端构建资源（重要！）
│   │   ├── index.html
│   │   └── assets/
│   ├── routes/
│   ├── services/
│   ├── __init__.py
│   ├── app.py
│   ├── cli.py
│   └── config.py
├── setup.py              # 安装配置文件
├── pyproject.toml        # 现代Python包配置
├── requirements.txt      # 依赖列表
├── README.md            # 项目说明
└── MANIFEST.in          # 额外文件包含规则
```

## 🔧 第二步：检查和更新版本号

### 2.1 更新版本号
根据语义化版本规范更新版本号：
- **修复bug**: 1.0.0 → 1.0.1
- **新功能**: 1.0.0 → 1.1.0  
- **破坏性更改**: 1.0.0 → 2.0.0

```bash
# 编辑 setup.py 中的 version
# 编辑 pyproject.toml 中的 version
# 确保两个文件中的版本号一致
```

### 2.2 验证配置文件
检查 `setup.py` 和 `pyproject.toml` 中的关键配置：
- **name**: "xgo-blockly"
- **version**: 确保版本号正确
- **author**: "XGO Team"
- **description**: 项目描述
- **dependencies**: 依赖列表

## 🏗️ 第三步：清理旧构建文件

```bash
# Windows PowerShell:
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue

# Linux/macOS:
# rm -rf build/ dist/ *.egg-info/
```

## 📦 第四步：构建包

### 4.1 构建源码分发包和wheel包
```bash
# 使用现代build工具构建
python -m build

# 或者使用传统方式（不推荐）
# python setup.py sdist bdist_wheel
```

### 4.2 验证构建结果
构建完成后，`dist/` 目录应包含：
```
dist/
├── xgo_blockly-1.0.0.tar.gz     # 源码包
└── xgo_blockly-1.0.0-py3-none-any.whl  # wheel包
```

### 4.3 检查包内容
```bash
# 检查源码包内容
tar -tzf dist/xgo-blockly-1.0.0.tar.gz | head -20

# 检查wheel包内容  
python -m zipfile -l dist/xgo_blockly-1.0.0-py3-none-any.whl
```

## ✅ 第五步：本地测试

### 5.1 创建测试环境
```bash
# 创建虚拟环境进行测试
python -m venv test_env

# 激活虚拟环境
# Windows:
test_env\Scripts\activate
# Linux/macOS:  
# source test_env/bin/activate
```

### 5.2 安装测试
```bash
# 从wheel包安装
pip install dist/xgo_blockly-1.0.0-py3-none-any.whl

# 测试命令行工具
xgo-blockly --help

# 测试模块导入
python -c "import xgo_blockly; print('Import successful!')"

# 退出测试环境
deactivate
```

## 🔍 第六步：包质量检查

### 6.1 使用twine检查包
```bash
# 检查构建好的包
python -m twine check dist/*
```

### 6.2 修复常见问题
如果检查失败，常见问题和解决方案：

**问题1**: `long_description_content_type` 缺失
```python
# 在setup.py中确保有：
long_description_content_type="text/markdown"
```

**问题2**: README.md文件缺失
```bash
# 确保README.md存在且内容完整
```

**问题3**: 静态文件缺失
```bash
# 检查MANIFEST.in文件，确保包含：
# include README.md
# recursive-include xgo_blockly/dist *
```

## 🚀 第七步：上传到PyPI

### 7.1 配置PyPI凭据

#### 方法1: 使用API Token（推荐）
1. 登录 [PyPI](https://pypi.org/) 
2. 进入 Account settings → API tokens
3. 创建新token，权限设为 "Entire account" 或指定项目
4. 保存token（只显示一次！）

#### 方法2: 配置.pypirc文件
```bash
# 创建 ~/.pypirc 文件
# Windows: C:\Users\<username>\.pypirc
# Linux/macOS: ~/.pypirc

[distutils]
index-servers = pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 你的API token
```

### 7.2 测试上传（推荐）
先上传到测试PyPI验证：
```bash
# 上传到测试PyPI
python -m twine upload --repository testpypi dist/*

# 或者指定测试PyPI URL
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# 从测试PyPI安装验证
pip install --index-url https://test.pypi.org/simple/ xgo-blockly
```

### 7.3 正式上传
```bash
# 上传到正式PyPI
python -m twine upload dist/*

# 如果配置了.pypirc，twine会自动使用配置
# 如果没有配置，会提示输入用户名和密码
```

### 7.4 交互式上传
如果没有配置.pypirc，twine会提示：
```
Enter your username: __token__
Enter your password: [输入你的API token]
```

## 🎉 第八步：验证发布

### 8.1 检查PyPI页面
访问包页面确认上传成功：
- https://pypi.org/project/xgo-blockly/

### 8.2 安装测试
```bash
# 从PyPI安装
pip install xgo-blockly

# 测试功能
xgo-blockly --help
```

## 🛠️ 故障排除

### 常见错误和解决方案

**错误1**: `HTTP 403: Invalid or non-existent authentication information`
- **原因**: API token错误或权限不足
- **解决**: 检查token是否正确，确保token有上传权限

**错误2**: `HTTP 400: File already exists`  
- **原因**: 相同版本已经存在
- **解决**: 更新版本号后重新构建

**错误3**: `README.md not found`
- **原因**: README.md文件路径错误
- **解决**: 确保README.md在项目根目录

**错误4**: 静态文件缺失
- **原因**: MANIFEST.in配置不正确或前端资源未复制
- **解决**: 检查前端dist目录是否存在并正确复制

**错误5**: `Module not found` 导入错误
- **原因**: 包结构问题或__init__.py缺失
- **解决**: 检查包目录结构和__init__.py文件

## 📝 自动化脚本

为了简化流程，可以创建自动化脚本：

### Windows PowerShell脚本 (build_and_upload.ps1)
```powershell
#!/usr/bin/env powershell
# XGO Blockly 构建和上传脚本

Write-Host "=== XGO Blockly 包构建和上传 ===" -ForegroundColor Green

# 1. 构建前端
Write-Host "1. 构建前端项目..." -ForegroundColor Yellow
Set-Location "..\blockly-vue3"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "前端构建失败"
    exit 1
}

# 2. 复制前端资源
Write-Host "2. 复制前端资源..." -ForegroundColor Yellow
Copy-Item -Path "dist" -Destination "..\xgo-blockly-server\xgo_blockly\" -Recurse -Force

# 3. 回到Python包目录
Set-Location "..\xgo-blockly-server"

# 4. 清理旧构建
Write-Host "3. 清理旧构建文件..." -ForegroundColor Yellow
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue

# 5. 构建包
Write-Host "4. 构建Python包..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Error "包构建失败"
    exit 1
}

# 6. 检查包
Write-Host "5. 检查包质量..." -ForegroundColor Yellow
python -m twine check dist/*
if ($LASTEXITCODE -ne 0) {
    Write-Error "包检查失败"
    exit 1
}

# 7. 询问是否上传
Write-Host "6. 包构建完成！是否上传到PyPI？" -ForegroundColor Green
$upload = Read-Host "(y/n)"
if ($upload -eq "y" -or $upload -eq "Y") {
    Write-Host "上传到PyPI..." -ForegroundColor Yellow
    python -m twine upload dist/*
    if ($LASTEXITCODE -eq 0) {
        Write-Host "上传成功！" -ForegroundColor Green
    } else {
        Write-Error "上传失败"
        exit 1
    }
} else {
    Write-Host "包已构建，可以手动上传：python -m twine upload dist/*" -ForegroundColor Cyan
}

Write-Host "=== 完成 ===" -ForegroundColor Green
```

### Linux/macOS脚本 (build_and_upload.sh)
```bash
#!/bin/bash
# XGO Blockly 构建和上传脚本

echo "=== XGO Blockly 包构建和上传 ==="

# 1. 构建前端
echo "1. 构建前端项目..."
cd ../blockly-vue3
npm run build
if [ $? -ne 0 ]; then
    echo "错误: 前端构建失败"
    exit 1
fi

# 2. 复制前端资源
echo "2. 复制前端资源..."
cp -r dist ../xgo-blockly-server/xgo_blockly/

# 3. 回到Python包目录
cd ../xgo-blockly-server

# 4. 清理旧构建
echo "3. 清理旧构建文件..."
rm -rf build/ dist/ *.egg-info/

# 5. 构建包
echo "4. 构建Python包..."
python -m build
if [ $? -ne 0 ]; then
    echo "错误: 包构建失败"
    exit 1
fi

# 6. 检查包
echo "5. 检查包质量..."
python -m twine check dist/*
if [ $? -ne 0 ]; then
    echo "错误: 包检查失败"
    exit 1
fi

# 7. 询问是否上传
echo "6. 包构建完成！是否上传到PyPI？(y/n)"
read upload
if [ "$upload" = "y" ] || [ "$upload" = "Y" ]; then
    echo "上传到PyPI..."
    python -m twine upload dist/*
    if [ $? -eq 0 ]; then
        echo "上传成功！"
    else
        echo "错误: 上传失败"
        exit 1
    fi
else
    echo "包已构建，可以手动上传：python -m twine upload dist/*"
fi

echo "=== 完成 ==="
```

## 📋 检查清单

发布前请确认以下项目：

- [ ] 前端项目已构建（dist目录存在）
- [ ] 前端资源已复制到Python包中
- [ ] 版本号已更新
- [ ] README.md内容完整
- [ ] 依赖列表正确
- [ ] setup.py和pyproject.toml配置一致
- [ ] 本地安装测试通过
- [ ] twine检查通过
- [ ] PyPI凭据配置正确

## 🔗 相关链接

- [PyPI官网](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
- [Python包构建文档](https://packaging.python.org/)
- [Twine文档](https://twine.readthedocs.io/)
- [语义化版本规范](https://semver.org/)

---

**注意**: 
1. API token只显示一次，请务必保存好
2. 每次发布前建议先上传到TestPyPI测试
3. 发布后的版本无法删除，只能发布新版本
4. 确保版本号遵循语义化版本规范