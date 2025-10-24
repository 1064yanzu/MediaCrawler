#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediaCrawler 安装验证脚本
Verify MediaCrawler Installation
"""

import sys

def check_imports():
    """检查必要的模块是否可以导入"""
    print("🔍 正在检查必要的模块...")
    
    required_modules = [
        ('playwright', 'Playwright'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('httpx', 'HTTPX'),
        ('pydantic', 'Pydantic'),
        ('aiofiles', 'aiofiles'),
    ]
    
    missing_modules = []
    
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name} - 已安装")
        except ImportError:
            print(f"  ✗ {display_name} - 未安装")
            missing_modules.append(display_name)
    
    if missing_modules:
        print(f"\n❌ 缺少以下模块: {', '.join(missing_modules)}")
        print("请运行: uv sync 或 pip install -r requirements.txt")
        return False
    
    print("\n✓ 所有必要的模块都已安装\n")
    return True

def check_project_files():
    """检查项目关键文件是否存在"""
    print("📁 正在检查项目文件...")
    
    from pathlib import Path
    
    required_files = [
        'main.py',
        'api_server.py',
        'checkpoint_manager.py',
        'config/base_config.py',
        'web_ui/index.html',
        'web_ui/static/styles.css',
        'web_ui/static/main.js',
    ]
    
    missing_files = []
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - 缺失")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ 缺少以下文件: {', '.join(missing_files)}")
        return False
    
    print("\n✓ 所有必要的文件都存在\n")
    return True

def check_directories():
    """检查并创建必要的目录"""
    print("📂 正在检查/创建必要的目录...")
    
    from pathlib import Path
    
    required_dirs = [
        'data',
        'checkpoint',
        'cache',
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ 创建目录: {dir_path}")
        else:
            print(f"  ✓ 目录已存在: {dir_path}")
    
    print("\n✓ 所有必要的目录都已准备好\n")
    return True

def main():
    print("=" * 60)
    print("MediaCrawler 安装验证")
    print("MediaCrawler Installation Verification")
    print("=" * 60)
    print()
    
    # 检查 Python 版本
    print(f"🐍 Python 版本: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 版本过低，请使用 Python 3.8 或更高版本")
        return False
    print("✓ Python 版本符合要求\n")
    
    # 执行各项检查
    checks = [
        check_imports(),
        check_project_files(),
        check_directories(),
    ]
    
    print("=" * 60)
    if all(checks):
        print("✅ 所有检查通过！MediaCrawler 已准备就绪")
        print()
        print("🚀 快速开始:")
        print("  - 命令行模式: uv run main.py --platform xhs --lt qrcode --type search")
        print("  - Web UI 模式: uv run python api_server.py")
        print("  - 访问控制面板: http://localhost:8000")
        print()
        return True
    else:
        print("❌ 部分检查未通过，请按照上述提示修复问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
