#!/bin/bash

# Sphinx文档生成脚本 for langmem0项目
# 使用sphinx-autodoc自动生成Python代码文档

set -e  # 遇到错误立即退出

echo "=== 开始生成langmem0项目文档 ==="

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误：未找到Python，请先安装Python"
    exit 1
fi

echo "1. 安装开发依赖..."
# 使用uv安装开发依赖（如果使用uv）
if command -v uv &> /dev/null; then
    uv sync --group dev
else
    # 使用pip安装
    pip install sphinx>=9.1.0 sphinx-autodoc-typehints sphinx-rtd-theme
fi

# 创建docs目录（如果不存在）
mkdir -p docs

# 检查是否已有sphinx配置
if [ ! -f "docs/conf.py" ]; then
    echo "2. 初始化sphinx配置..."
    cd docs
    
    # 快速初始化sphinx配置
    uv run sphinx-quickstart --quiet --project="langmem0" --author="langmem0 developers" \
        --release="0.1.0" --language="en" --extensions="sphinx.ext.autodoc,sphinx.ext.napoleon,sphinx.ext.viewcode,sphinx_autodoc_typehints" \
        --makefile --batchfile
    
    cd ..
else
    echo "2. 使用现有的sphinx配置..."
fi

# 配置sphinx以包含Python模块
echo "3. 配置sphinx以包含Python模块..."

# 更新conf.py文件以包含项目路径和配置
cat > docs/conf.py << 'EOF'
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'langmem0'
copyright = '2024, langmem0 developers'
author = 'langmem0 developers'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

html_theme = 'alabaster'
html_static_path = ['_static']
EOF

# 创建主要的文档索引
echo "4. 创建文档索引..."

cat > docs/index.rst << 'EOF'
langmem0 Documentation
=======================

langmem0 is a Python package providing Mem0 middleware for LangGraph applications.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
EOF

# 创建模块文档
echo "5. 生成模块文档..."

cat > docs/modules.rst << 'EOF'
langmem0 Modules
================

.. automodule:: langmem0
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: langmem0.middleware
   :members:
   :undoc-members:
   :show-inheritance:
EOF

echo "6. 生成HTML文档..."
cd docs && make html

cd ..

echo ""
echo "=== 文档生成完成 ==="
echo "HTML文档已生成到: docs/_build/html/"
echo "打开 docs/_build/html/index.html 查看文档"
echo ""
echo "要重新生成文档，只需再次运行此脚本:"
echo "./generate_docs.sh"
