#!/usr/bin/env python3
"""
测试历史记录删除功能的验证脚本
"""

import sys
from pathlib import Path
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.analysis_history import get_history_manager
from datetime import datetime, timedelta

def test_delete_with_verification():
    """测试删除功能并验证结果"""
    print("🧪 测试历史记录删除功能（含验证）")
    print("=" * 60)
    
    # 获取历史记录管理器
    history_manager = get_history_manager()
    
    # 1. 查看当前记录数
    print("\n📊 步骤1: 查看当前记录")
    current_records = history_manager.get_analysis_history(limit=100)
    print(f"  📈 当前总记录数: {len(current_records)}")
    
    if len(current_records) == 0:
        print("  📭 没有记录，创建测试记录...")
        # 创建一些测试记录
        for i in range(3):
            record_id = history_manager.save_analysis_record(
                session_id=f"test_delete_session_{i}",
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
                results={"test": f"data_{i}"},
                total_cost=0.01
            )
            print(f"    ✅ 创建测试记录: {record_id}")
        
        # 重新获取记录
        current_records = history_manager.get_analysis_history(limit=100)
        print(f"  📈 创建后记录数: {len(current_records)}")
    
    # 2. 选择要删除的记录
    if len(current_records) > 0:
        # 选择前两条记录进行删除测试
        records_to_delete = current_records[:min(2, len(current_records))]
        record_ids_to_delete = [r.get('record_id') for r in records_to_delete if r.get('record_id')]
        
        print(f"\n🗑️ 步骤2: 删除选中的记录")
        print(f"  📋 准备删除记录数: {len(record_ids_to_delete)}")
        for i, record in enumerate(records_to_delete):
            print(f"    {i+1}. {record.get('stock_symbol', 'N/A')} - {record.get('created_at', 'N/A')[:19]}")
        
        # 3. 执行删除
        print(f"\n⚡ 步骤3: 执行删除操作")
        deleted_count = history_manager.delete_records_by_ids(record_ids_to_delete)
        print(f"  ✅ 删除操作返回结果: {deleted_count} 条记录")
        
        # 4. 验证删除结果
        print(f"\n🔍 步骤4: 验证删除结果")
        time.sleep(1)  # 等待一秒确保操作完成
        
        # 重新获取记录
        updated_records = history_manager.get_analysis_history(limit=100)
        print(f"  📈 删除后记录数: {len(updated_records)}")
        print(f"  📊 预期减少: {len(record_ids_to_delete)} 条")
        print(f"  📊 实际减少: {len(current_records) - len(updated_records)} 条")
        
        # 检查被删除的记录是否还存在
        remaining_ids = [r.get('record_id') for r in updated_records]
        still_exists = [rid for rid in record_ids_to_delete if rid in remaining_ids]
        
        if still_exists:
            print(f"  ❌ 以下记录仍然存在: {still_exists}")
        else:
            print(f"  ✅ 所有目标记录已成功删除")
        
        # 5. 详细验证
        print(f"\n📋 步骤5: 详细验证")
        for record_id in record_ids_to_delete:
            # 尝试查找特定记录
            found = False
            for record in updated_records:
                if record.get('record_id') == record_id:
                    found = True
                    break
            
            status = "❌ 仍存在" if found else "✅ 已删除"
            print(f"  记录 {record_id[:8]}...{record_id[-8:]}: {status}")
    
    else:
        print("  📭 没有记录可供删除测试")
    
    print(f"\n🎉 删除功能验证测试完成！")
    
    # 6. 显示最终状态
    final_records = history_manager.get_analysis_history(limit=10)
    print(f"\n📊 最终状态:")
    print(f"  📈 当前记录数: {len(final_records)}")
    if final_records:
        print(f"  📋 最近的记录:")
        for i, record in enumerate(final_records[:3]):
            print(f"    {i+1}. {record.get('stock_symbol', 'N/A')} - {record.get('created_at', 'N/A')[:19]}")

if __name__ == "__main__":
    test_delete_with_verification()
