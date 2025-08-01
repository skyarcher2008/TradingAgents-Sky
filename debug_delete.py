#!/usr/bin/env python3
"""
历史记录删除功能调试页面
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tradingagents.utils.analysis_history import get_history_manager
from datetime import datetime

def main():
    st.title("🔍 历史记录删除功能调试")
    st.markdown("---")
    
    try:
        history_manager = get_history_manager()
        
        # 显示当前记录
        st.subheader("📊 当前记录列表")
        records = history_manager.get_analysis_history(limit=20)
        
        st.write(f"总记录数: {len(records)}")
        
        if records:
            # 显示记录表格
            import pandas as pd
            df = pd.DataFrame(records)
            
            # 选择要显示的列
            display_cols = ['record_id', 'stock_symbol', 'created_at', 'success', 'llm_provider']
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                display_df = df[available_cols].copy()
                if 'created_at' in display_df.columns:
                    display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                st.dataframe(display_df, use_container_width=True)
                
                # 删除测试
                st.subheader("🗑️ 删除测试")
                
                if st.button("删除第一条记录（测试）"):
                    if len(records) > 0:
                        record_to_delete = records[0]
                        record_id = record_to_delete.get('record_id')
                        
                        st.write(f"准备删除记录: {record_id}")
                        st.write(f"股票代码: {record_to_delete.get('stock_symbol')}")
                        
                        deleted_count = history_manager.delete_records_by_ids([record_id])
                        st.write(f"删除结果: {deleted_count} 条记录")
                        
                        # 重新获取记录验证
                        updated_records = history_manager.get_analysis_history(limit=20)
                        st.write(f"删除后记录数: {len(updated_records)}")
                        
                        # 检查记录是否还存在
                        still_exists = any(r.get('record_id') == record_id for r in updated_records)
                        if still_exists:
                            st.error("❌ 记录仍然存在！")
                        else:
                            st.success("✅ 记录已成功删除")
                        
                        st.rerun()
            else:
                st.error("数据格式异常，无法显示")
        else:
            st.info("📭 暂无记录")
        
        # 系统信息
        st.subheader("ℹ️ 系统信息")
        st.write(f"MongoDB 可用: {'✅' if history_manager.mongodb_client else '❌'}")
        st.write(f"Redis 可用: {'✅' if history_manager.redis_client else '❌'}")
        st.write(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        st.error(f"❌ 错误: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
