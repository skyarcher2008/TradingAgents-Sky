#!/usr/bin/env python3
"""
测试动态日期计算功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_dynamic_date_calculation():
    """测试动态日期计算"""
    print("🧪 测试动态日期计算功能...")
    
    # 模拟不同的输入日期格式
    test_dates = [
        "2025-07-24",  # 标准格式
        "20250724",    # 紧凑格式
        datetime.now().strftime('%Y-%m-%d'),  # 当前日期
    ]
    
    for current_date in test_dates:
        print(f"\n📅 测试输入日期: {current_date}")
        
        try:
            # 模拟分析师中的日期计算逻辑
            if isinstance(current_date, str):
                if '-' in current_date:
                    current_dt = datetime.strptime(current_date, '%Y-%m-%d')
                else:
                    current_dt = datetime.strptime(current_date, '%Y%m%d')
            else:
                current_dt = datetime.now()
            
            # 计算一年前的日期作为开始日期
            start_dt = current_dt - timedelta(days=365)
            start_date = start_dt.strftime('%Y-%m-%d')
            
            print(f"✅ 计算成功:")
            print(f"   当前日期: {current_dt.strftime('%Y-%m-%d')}")
            print(f"   开始日期: {start_date}")
            print(f"   数据范围: {start_date} 到 {current_dt.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            print(f"❌ 计算失败: {e}")
            # 如果解析失败，使用当前年份的开始
            current_year = datetime.now().year
            start_date = f'{current_year}-01-01'
            print(f"🔄 使用默认范围: {start_date} 到 {datetime.now().strftime('%Y-%m-%d')}")

def test_current_system_date():
    """测试当前系统日期"""
    print(f"\n🕒 当前系统信息:")
    print(f"   系统日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"   系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   当前年份: {datetime.now().year}")
    
    # 计算一年前
    one_year_ago = datetime.now() - timedelta(days=365)
    print(f"   一年前日期: {one_year_ago.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    test_current_system_date()
    test_dynamic_date_calculation()
