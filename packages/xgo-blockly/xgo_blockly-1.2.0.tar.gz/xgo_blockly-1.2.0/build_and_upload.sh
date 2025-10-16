#!/bin/bash
# XGO Blockly 构建和上传脚本
# 使用方法: chmod +x build_and_upload.sh && ./build_and_upload.sh

set -e  # 遇到错误时退出

echo "=== XGO Blockly 包构建和上传 ==="

# 检查并复制.pypirc配置文件
echo -e "${YELLOW}检查PyPI配置...${NC}"
PYPIRC_PATH="$HOME/.pypirc"
if [ ! -f "$PYPIRC_PATH" ]; then
    if [ -f ".pypirc" ]; then
        echo -e "${YELLOW}复制.pypirc到用户目录...${NC}"
        cp ".pypirc" "$PYPIRC_PATH"
        chmod 600 "$PYPIRC_PATH"
        echo -e "${GREEN}✓ .pypirc配置已复制到 $PYPIRC_PATH${NC}"
    else
        echo -e "${YELLOW}⚠ 未找到.pypirc配置文件${NC}"
    fi
else
    echo -e "${GREEN}✓ 找到.pypirc配置文件${NC}"
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查必要工具
echo -e "${YELLOW}检查必要工具...${NC}"
for tool in python npm pip; do
    if command -v $tool >/dev/null 2>&1; then
        echo -e "${GREEN}✓ $tool 已安装${NC}"
    else
        echo -e "${RED}✗ $tool 未找到，请先安装${NC}"
        exit 1
    fi
done

# 检查构建工具
echo -e "${YELLOW}检查Python构建工具...${NC}"
if ! python -m build --help >/dev/null 2>&1 || ! python -m twine --help >/dev/null 2>&1; then
    echo -e "${YELLOW}安装构建工具...${NC}"
    pip install --upgrade build twine setuptools wheel
fi
echo -e "${GREEN}✓ build 和 twine 已安装${NC}"

# 保存当前目录
CURRENT_DIR=$(pwd)

# 1. 构建前端
echo -e "${YELLOW}1. 构建前端项目...${NC}"
cd ../blockly-vue3

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
fi

# 构建前端
npm run build
echo -e "${GREEN}✓ 前端构建成功${NC}"

# 2. 复制前端资源
echo -e "${YELLOW}2. 复制前端资源...${NC}"
if [ -d "../xgo-blockly-server/xgo_blockly/dist" ]; then
    rm -rf "../xgo-blockly-server/xgo_blockly/dist"
fi
cp -r dist ../xgo-blockly-server/xgo_blockly/
echo -e "${GREEN}✓ 前端资源复制完成${NC}"

# 3. 回到Python包目录
cd ../xgo-blockly-server

# 4. 清理旧构建
echo -e "${YELLOW}3. 清理旧构建文件...${NC}"
rm -rf build/ dist/ *.egg-info/
echo -e "${GREEN}✓ 清理完成${NC}"

# 5. 构建包
echo -e "${YELLOW}4. 构建Python包...${NC}"
python -m build
echo -e "${GREEN}✓ 包构建成功${NC}"

# 6. 检查包
echo -e "${YELLOW}5. 检查包质量...${NC}"
python -m twine check dist/*
echo -e "${GREEN}✓ 包检查通过${NC}"

# 7. 显示构建结果
echo -e "${YELLOW}6. 构建结果:${NC}"
for file in dist/*; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        filename=$(basename "$file")
        echo -e "${CYAN}  $filename ($size)${NC}"
    fi
done

# 8. 询问是否上传到测试PyPI
echo ""
echo -e "${GREEN}是否先上传到测试PyPI进行验证？(推荐)${NC}"
read -p "(y/n): " test_upload
if [ "$test_upload" = "y" ] || [ "$test_upload" = "Y" ]; then
    echo -e "${YELLOW}上传到测试PyPI...${NC}"
    python -m twine upload --repository testpypi dist/*
    echo -e "${GREEN}✓ 测试PyPI上传成功！${NC}"
    echo -e "${CYAN}测试安装命令: pip install --index-url https://test.pypi.org/simple/ xgo-blockly${NC}"
    
    # 询问是否继续上传到正式PyPI
    echo ""
    echo -e "${GREEN}是否继续上传到正式PyPI？${NC}"
    read -p "(y/n): " prod_upload
    if [ "$prod_upload" = "y" ] || [ "$prod_upload" = "Y" ]; then
        echo -e "${YELLOW}上传到正式PyPI...${NC}"
        python -m twine upload dist/*
        echo -e "${GREEN}✓ 正式PyPI上传成功！${NC}"
        echo -e "${CYAN}安装命令: pip install xgo-blockly${NC}"
    fi
else
    # 直接询问是否上传到正式PyPI
    echo -e "${GREEN}是否上传到正式PyPI？${NC}"
    read -p "(y/n): " upload
    if [ "$upload" = "y" ] || [ "$upload" = "Y" ]; then
        echo -e "${YELLOW}上传到正式PyPI...${NC}"
        python -m twine upload dist/*
        echo -e "${GREEN}✓ 上传成功！${NC}"
        echo -e "${CYAN}安装命令: pip install xgo-blockly${NC}"
    else
        echo -e "${GREEN}包已构建完成！${NC}"
        echo -e "${CYAN}手动上传命令:${NC}"
        echo -e "${CYAN}  测试PyPI: python -m twine upload --repository testpypi dist/*${NC}"
        echo -e "${CYAN}  正式PyPI: python -m twine upload dist/*${NC}"
    fi
fi

cd "$CURRENT_DIR"
echo ""
echo -e "${GREEN}=== 完成 ===${NC}"