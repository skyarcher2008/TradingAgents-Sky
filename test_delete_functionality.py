#!/usr/bin/env python3
"""
测试历史记录删除功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.analysis_history import get_history_manager
from datetime import datetime, timedelta
import uuid

def test_delete_functionality():
    """测试删除功能"""
    print("🧪 测试历史记录删除功能")
    print("=" * 50)
    
    # 获取历史记录管理器
    history_manager = get_history_manager()
    
    # 创建测试记录
    print("📝 创建测试记录...")
    test_record_ids = []
    
    for i in range(3):
        record_id = history_manager.save_analysis_record(
            session_id=f"test_session_{i}",
            stock_symbol=f"TEST{i:02d}",
            analysis_date="2024-01-01",
            market_type="US",
            analysts=["test_analyst"],
            research_depth="简单",
            llm_provider="test",
            llm_model="test-model",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=10),
            duration=10.0,
            success=True,
            results={"test": "data"},
            total_cost=0.01
        )
        test_record_ids.append(record_id)
        print(f"  ✅ 创建记录: {record_id}")
    
    # 查询记录
    print("\n📊 查询记录...")
    records = history_manager.get_analysis_history(limit=10)
    print(f"  📈 总记录数: {len(records)}")
    
    # 删除单条记录
    print(f"\n🗑️ 删除单条记录: {test_record_ids[0]}")
    success = history_manager.delete_record_by_id(test_record_ids[0])
    print(f"  {'✅ 删除成功' if success else '❌ 删除失败'}")
    
    # 批量删除记录
    print(f"\n🗑️ 批量删除记录: {test_record_ids[1:]}")
    deleted_count = history_manager.delete_records_by_ids(test_record_ids[1:])
    print(f"  ✅ 删除了 {deleted_count} 条记录")
    
    # 再次查询记录
    print("\n📊 删除后查询记录...")
    records_after = history_manager.get_analysis_history(limit=10)
    print(f"  📈 总记录数: {len(records_after)}")
    
    # 验证删除
    remaining_test_records = [r for r in records_after if r.get('stock_symbol', '').startswith('TEST')]
    print(f"  🧪 剩余测试记录: {len(remaining_test_records)}")
    
    if len(remaining_test_records) == 0:
        print("  ✅ 所有测试记录已成功删除")
    else:
        print("  ⚠️ 仍有测试记录存在")
        for record in remaining_test_records:
            print(f"    - {record.get('stock_symbol')} ({record.get('record_id')})")
    
    print("\n🎉 删除功能测试完成！")

if __name__ == "__main__":
    test_delete_functionality()
