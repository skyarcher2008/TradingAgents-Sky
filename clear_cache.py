#!/usr/bin/env python3
"""
清理系统缓存以解决日期问题
"""

import os
import shutil
import sys

def clear_data_cache():
    """清理数据缓存目录"""
    cache_dirs = [
        "d:/github/TradingAgents-Sky/data/cache",
        "d:/github/TradingAgents-Sky/cache",
        "d:/github/TradingAgents-Sky/data/finnhub_data",
    ]
    
    total_cleared = 0
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                file_count = len(os.listdir(cache_dir))
                if file_count > 0:
                    print(f"🗑️  清理缓存目录: {cache_dir}")
                    print(f"   发现 {file_count} 个缓存文件")
                    
                    for filename in os.listdir(cache_dir):
                        file_path = os.path.join(cache_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                                total_cleared += 1
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                total_cleared += 1
                        except Exception as e:
                            print(f"   ⚠️  无法删除 {filename}: {e}")
                    
                    print(f"   ✅ 清理完成")
                else:
                    print(f"📂 缓存目录为空: {cache_dir}")
            except Exception as e:
                print(f"❌ 清理缓存目录失败 {cache_dir}: {e}")
        else:
            print(f"📂 缓存目录不存在: {cache_dir}")
    
    return total_cleared

def clear_python_cache():
    """清理Python缓存"""
    print(f"\n🐍 清理Python缓存...")
    
    project_root = "d:/github/TradingAgents-Sky"
    pycache_count = 0
    
    for root, dirs, files in os.walk(project_root):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                pycache_count += 1
                print(f"   🗑️  删除: {pycache_path}")
            except Exception as e:
                print(f"   ⚠️  无法删除 {pycache_path}: {e}")
    
    print(f"   ✅ 清理了 {pycache_count} 个 __pycache__ 目录")

def show_current_status():
    """显示当前缓存状态"""
    print(f"📊 当前缓存状态检查:")
    
    cache_paths = [
        "d:/github/TradingAgents-Sky/data/cache",
        "d:/github/TradingAgents-Sky/cache", 
        "d:/github/TradingAgents-Sky/data/finnhub_data",
    ]
    
    for path in cache_paths:
        if os.path.exists(path):
            file_count = len(os.listdir(path))
            print(f"   📁 {path}: {file_count} 个文件")
        else:
            print(f"   📁 {path}: 不存在")

if __name__ == "__main__":
    print("🧹 开始清理缓存以解决日期问题...")
    
    # 显示清理前状态
    show_current_status()
    
    # 清理数据缓存
    print(f"\n🗑️  开始清理数据缓存...")
    cleared_files = clear_data_cache()
    
    # 清理Python缓存
    clear_python_cache()
    
    # 显示清理后状态
    print(f"\n📊 清理完成后的状态:")
    show_current_status()
    
    print(f"\n✅ 缓存清理完成!")
    print(f"   📄 清理了 {cleared_files} 个数据缓存文件")
    print(f"   🐍 清理了Python __pycache__ 目录")
    print(f"\n💡 建议：重启Web应用以确保使用最新的日期计算逻辑")
