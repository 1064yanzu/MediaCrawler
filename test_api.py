#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 服务器测试脚本
"""

import asyncio
import sys
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import api_server
        print("  ✓ api_server 模块导入成功")
    except Exception as e:
        print(f"  ✗ api_server 模块导入失败: {e}")
        return False
    
    try:
        import checkpoint_manager
        print("  ✓ checkpoint_manager 模块导入成功")
    except Exception as e:
        print(f"  ✗ checkpoint_manager 模块导入失败: {e}")
        return False
    
    return True

def test_checkpoint_manager():
    """测试检查点管理器"""
    print("\n🔍 测试检查点管理器...")
    
    try:
        from checkpoint_manager import CheckpointManager, CrawlProgress
        
        manager = CheckpointManager(checkpoint_dir="./test_checkpoint")
        print("  ✓ 检查点管理器创建成功")
        
        # 创建检查点
        progress = manager.create_checkpoint("test", "search", "测试关键词")
        print(f"  ✓ 创建检查点成功: {progress.checkpoint_id}")
        
        # 更新进度
        manager.update_progress(note_id="test123", notes_count=1, comments_count=5)
        print("  ✓ 更新进度成功")
        
        # 保存检查点
        manager.save_checkpoint()
        print("  ✓ 保存检查点成功")
        
        # 列出检查点
        checkpoints = manager.list_checkpoints()
        print(f"  ✓ 列出检查点成功，找到 {len(checkpoints)} 个")
        
        # 清理测试数据
        import shutil
        test_dir = Path("./test_checkpoint")
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("  ✓ 清理测试数据成功")
        
        return True
    except Exception as e:
        print(f"  ✗ 检查点管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """测试API端点定义"""
    print("\n🔍 测试API端点...")
    
    try:
        from api_server import app
        
        routes = [route.path for route in app.routes]
        print(f"  ✓ API应用创建成功，共 {len(routes)} 个路由")
        
        required_routes = [
            "/api/health",
            "/api/platforms",
            "/api/config",
            "/api/crawler/start",
            "/api/crawler/stop",
            "/api/crawler/status",
            "/api/checkpoints",
            "/api/stats",
            "/api/presets"
        ]
        
        missing_routes = [r for r in required_routes if r not in routes]
        if missing_routes:
            print(f"  ✗ 缺少以下路由: {missing_routes}")
            return False
        
        print("  ✓ 所有必要的路由都已定义")
        return True
    except Exception as e:
        print(f"  ✗ API端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n🔍 测试文件结构...")
    
    required_files = [
        "api_server.py",
        "checkpoint_manager.py",
        "web_ui/index.html",
        "web_ui/static/styles.css",
        "web_ui/static/main.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"  ✗ 文件不存在: {file_path}")
        else:
            print(f"  ✓ 文件存在: {file_path}")
    
    if missing_files:
        print(f"\n  ✗ 缺少 {len(missing_files)} 个文件")
        return False
    
    print("  ✓ 所有必要的文件都存在")
    return True

def main():
    print("=" * 60)
    print("MediaCrawler API 测试")
    print("=" * 60)
    print()
    
    tests = [
        ("文件结构", test_file_structure),
        ("模块导入", test_imports),
        ("检查点管理器", test_checkpoint_manager),
        ("API端点", test_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试出错: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
