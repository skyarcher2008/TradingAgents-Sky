#!/usr/bin/env python3
"""
项目清理脚本 - 清理临时文件和未使用的文件
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_project():
    """清理项目临时文件和未使用文件"""
    print("🧹 开始清理TradingAgents项目...")
    
    project_root = Path(__file__).parent
    cleaned_files = []
    cleaned_dirs = []
    
    # 1. 清理Python缓存文件
    print("\n1. 🗑️ 清理Python缓存文件...")
    pycache_dirs = list(project_root.rglob("__pycache__"))
    for cache_dir in pycache_dirs:
        try:
            shutil.rmtree(cache_dir)
            cleaned_dirs.append(str(cache_dir))
            print(f"   ✅ 删除: {cache_dir}")
        except Exception as e:
            print(f"   ❌ 删除失败: {cache_dir} - {e}")
    
    # 清理.pyc文件
    pyc_files = list(project_root.rglob("*.pyc"))
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
            cleaned_files.append(str(pyc_file))
            print(f"   ✅ 删除: {pyc_file}")
        except Exception as e:
            print(f"   ❌ 删除失败: {pyc_file} - {e}")
    
    # 2. 清理日志文件（保留最新的）
    print("\n2. 📝 清理日志文件...")
    logs_dir = project_root / "logs"
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        if len(log_files) > 1:
            # 按修改时间排序，保留最新的
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            for old_log in log_files[1:]:  # 保留第一个（最新的）
                try:
                    old_log.unlink()
                    cleaned_files.append(str(old_log))
                    print(f"   ✅ 删除旧日志: {old_log}")
                except Exception as e:
                    print(f"   ❌ 删除失败: {old_log} - {e}")
    
    # 3. 清理重复的测试文件
    print("\n3. 🧪 清理重复和临时测试文件...")
    temp_test_files = [
        "test_akshare_dates.py",
        "test_akshare_notfound.py", 
        "test_date_fix.py",
        "test_date_flow.py",
        "test_etf.py",
        "test_retry_fix.py",
        "check_dates.py",
        "diagnose_date_issue.py",
        "fix_data_source.py"
    ]
    
    for test_file in temp_test_files:
        file_path = project_root / test_file
        if file_path.exists():
            try:
                file_path.unlink()
                cleaned_files.append(str(file_path))
                print(f"   ✅ 删除临时测试文件: {test_file}")
            except Exception as e:
                print(f"   ❌ 删除失败: {test_file} - {e}")
    
    # 4. 清理重复的演示文件
    print("\n4. 📁 清理重复文件...")
    # 保留examples目录中的版本，删除根目录的重复文件
    duplicate_files = [
        "etf_analysis_demo.py"  # 根目录的重复文件
    ]
    
    for dup_file in duplicate_files:
        file_path = project_root / dup_file
        if file_path.exists():
            try:
                file_path.unlink()
                cleaned_files.append(str(file_path))
                print(f"   ✅ 删除重复文件: {dup_file}")
            except Exception as e:
                print(f"   ❌ 删除失败: {dup_file} - {e}")
    
    # 5. 清理临时下载文件
    print("\n5. 📦 清理临时下载文件...")
    temp_downloads = [
        "pandoc-3.7.0.2-windows-x86_64.msi",
        "AKShare 公募基金数据 — AKShare 1.17.26 文档.mhtml"
    ]
    
    for temp_file in temp_downloads:
        file_path = project_root / temp_file
        if file_path.exists():
            try:
                file_path.unlink()
                cleaned_files.append(str(file_path))
                print(f"   ✅ 删除临时下载: {temp_file}")
            except Exception as e:
                print(f"   ❌ 删除失败: {temp_file} - {e}")
    
    # 6. 清理空目录
    print("\n6. 📂 清理空目录...")
    for dirpath, dirnames, filenames in os.walk(project_root, topdown=False):
        if not dirnames and not filenames:
            dir_path = Path(dirpath)
            # 不删除重要的目录
            if dir_path.name not in ['.git', '.venv', 'node_modules']:
                try:
                    dir_path.rmdir()
                    cleaned_dirs.append(str(dir_path))
                    print(f"   ✅ 删除空目录: {dir_path}")
                except Exception as e:
                    print(f"   ❌ 删除失败: {dir_path} - {e}")
    
    # 7. 清理.DS_Store文件（macOS）
    print("\n7. 🍎 清理系统文件...")
    ds_store_files = list(project_root.rglob(".DS_Store"))
    for ds_file in ds_store_files:
        try:
            ds_file.unlink()
            cleaned_files.append(str(ds_file))
            print(f"   ✅ 删除: {ds_file}")
        except Exception as e:
            print(f"   ❌ 删除失败: {ds_file} - {e}")
    
    # 8. 清理备份文件
    print("\n8. 💾 清理备份文件...")
    backup_patterns = ["*.bak", "*.backup", "*~"]
    for pattern in backup_patterns:
        backup_files = list(project_root.rglob(pattern))
        for backup_file in backup_files:
            try:
                backup_file.unlink()
                cleaned_files.append(str(backup_file))
                print(f"   ✅ 删除备份文件: {backup_file}")
            except Exception as e:
                print(f"   ❌ 删除失败: {backup_file} - {e}")
    
    # 统计结果
    print(f"\n✅ 清理完成!")
    print(f"📁 清理的目录数量: {len(cleaned_dirs)}")
    print(f"📄 清理的文件数量: {len(cleaned_files)}")
    
    if cleaned_files or cleaned_dirs:
        print(f"\n📋 清理详情:")
        if cleaned_dirs:
            print(f"🗂️ 清理的目录: {len(cleaned_dirs)} 个")
        if cleaned_files:
            print(f"📄 清理的文件: {len(cleaned_files)} 个")
            
        # 计算节省的空间（估算）
        print(f"\n💾 预计节省磁盘空间，提升项目整洁度")
    else:
        print(f"\n🎉 项目已经很干净了！没有找到需要清理的文件。")

if __name__ == "__main__":
    cleanup_project()
