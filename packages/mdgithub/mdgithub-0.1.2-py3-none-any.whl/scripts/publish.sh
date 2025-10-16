#!/bin/bash
set -e

echo "🚀 mdgithub - Publishing Script"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查版本
VERSION=$(grep "^version" pixi.toml | head -1 | cut -d'"' -f2)
echo -e "${BLUE}📦 Version: $VERSION${NC}"

# 1. 清理旧构建
# echo -e "\n${BLUE}🧹 Cleaning old builds...${NC}"
# pixi run clean

# 2. 安装 dev 环境
echo -e "\n${BLUE}📥 Installing dev environment...${NC}"
pixi install -e dev

# 3. 运行测试（如果有测试文件）
if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
    echo -e "\n${BLUE}🧪 Running tests...${NC}"
    pixi run -e dev test || {
        echo -e "${RED}❌ Tests failed!${NC}"
        exit 1
    }
else
    echo -e "\n${YELLOW}⚠️  No tests found, skipping...${NC}"
fi

# 4. 代码检查（如果需要）
if command -v ruff &> /dev/null; then
    echo -e "\n${BLUE}🔍 Linting code...${NC}"
    pixi run -e dev lint || echo -e "${YELLOW}⚠️  Linting warnings found${NC}"
fi

# 5. 构建包
echo -e "\n${BLUE}🏗️  Building package...${NC}"
pixi run -e dev build

# 6. 检查构建产物
echo -e "\n${BLUE}📋 Build artifacts:${NC}"
ls -lh dist/

# 7. 选择发布目标
echo -e "\n${BLUE}🎯 Select publish target:${NC}"
echo "1) PyPI (production)"
echo "2) TestPyPI (testing)"
echo "3) prefix.dev (conda)"
echo "4) PyPI + prefix.dev"
echo "5) Skip publishing (only build)"
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo -e "\n${BLUE}📤 Publishing to PyPI...${NC}"
        pixi run -e dev publish-pypi
        echo -e "${GREEN}✅ Published to PyPI${NC}"
        ;;
    2)
        echo -e "\n${BLUE}📤 Publishing to TestPyPI...${NC}"
        pixi run -e dev publish-test
        echo -e "${GREEN}✅ Published to TestPyPI${NC}"
        echo -e "${YELLOW}Test installation: pip install -i https://test.pypi.org/simple/ mdgithub${NC}"
        ;;
    3)
        echo -e "\n${BLUE}📤 Publishing to prefix.dev...${NC}"
        pixi install -e conda
        pixi run -e conda publish-conda
        echo -e "${GREEN}✅ Published to prefix.dev${NC}"
        ;;
    4)
        echo -e "\n${BLUE}📤 Publishing to PyPI...${NC}"
        pixi run -e dev publish-pypi
        echo -e "\n${BLUE}📤 Publishing to prefix.dev...${NC}"
        pixi install -e conda
        pixi run -e conda publish-conda
        echo -e "${GREEN}✅ Published to all platforms${NC}"
        ;;
    5)
        echo -e "\n${BLUE}⏭️  Skipping publishing${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# 8. 创建 Git tag
echo -e "\n${BLUE}🏷️  Git tagging${NC}"
read -p "Create git tag v$VERSION? (y/n): " create_tag
if [ "$create_tag" = "y" ]; then
    git tag -a "v$VERSION" -m "Release v$VERSION"
    git push origin "v$VERSION"
    echo -e "${GREEN}✅ Tag v$VERSION created and pushed${NC}"
fi

echo -e "\n${GREEN}🎉 Publishing complete!${NC}"
echo -e "${BLUE}📝 Next steps:${NC}"
echo "   1. Create GitHub release: https://github.com/llango/mdgithub/releases/new?tag=v$VERSION"
echo "   2. Install and test: pip install mdgithub"
echo "   3. Or with pixi: pixi global install mdgithub"