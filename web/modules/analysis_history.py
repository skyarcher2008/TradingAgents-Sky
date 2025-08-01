#!/usr/bin/env python3
"""
分析历史记录Web界面
提供历史记录查看、搜索、统计功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 导入历史记录管理器
try:
    from tradingagents.utils.analysis_history import get_history_manager
    HISTORY_AVAILABLE = True
except ImportError as e:
    HISTORY_AVAILABLE = False
    st.error(f"历史记录模块不可用: {e}")

def render_analysis_history():
    """渲染分析历史记录页面"""
    
    st.title("📈 分析历史记录")
    st.markdown("---")
    
    if not HISTORY_AVAILABLE:
        st.error("❌ 历史记录功能不可用")
        st.info("请确保数据库配置正确并且历史记录模块已正确安装。")
        return
    
    # 获取历史记录管理器
    try:
        history_manager = get_history_manager()
    except Exception as e:
        st.error(f"❌ 无法初始化历史记录管理器: {e}")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 记录查看", "📈 统计分析", "🔍 详细搜索", "⚙️ 管理工具"])
    
    with tab1:
        render_records_view(history_manager)
    
    with tab2:
        render_statistics_view(history_manager)
    
    with tab3:
        render_advanced_search(history_manager)
    
    with tab4:
        render_management_tools(history_manager)

def render_records_view(history_manager):
    """渲染记录查看界面"""
    st.subheader("📊 最近的分析记录")
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stock_filter = st.text_input("🔍 股票代码过滤", placeholder="例如: AAPL, 000001")
    
    with col2:
        success_filter = st.selectbox("📊 状态过滤", ["全部", "仅成功", "仅失败"])
    
    with col3:
        limit = st.selectbox("📄 显示条数", [10, 25, 50, 100], index=1)
    
    # 获取记录
    try:
        success_only = success_filter == "仅成功"
        if success_filter == "仅失败":
            # 这需要在history_manager中添加failure_only参数
            records = []  # 暂时为空，可以后续扩展
            st.info("⚠️ '仅失败'过滤功能暂未实现")
        else:
            # 直接获取最新数据，不使用缓存
            records = history_manager.get_analysis_history(
                stock_symbol=stock_filter if stock_filter else None,
                limit=limit,
                success_only=success_only
            )
        
        if not records:
            st.info("� 暂无分析记录")
            st.markdown("""
            **可能的原因：**
            - 还没有进行过股票分析
            - 请先在"股票分析"页面进行一次分析，然后回到这里查看历史记录
            """)
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(records)
        
        # 格式化显示
        display_df = prepare_display_dataframe(df)
        
        # 添加删除功能
        st.markdown("### 🗑️ 记录管理")
        
        # 删除选项
        delete_col1, delete_col2 = st.columns([3, 1])
        
        with delete_col1:
            # 使用多选框让用户选择要删除的记录
            if 'record_id' in df.columns:
                # 创建显示选项，包含股票代码、时间和状态
                delete_options = []
                for _, record in df.iterrows():
                    created_at = record.get('created_at', '')
                    if isinstance(created_at, str):
                        created_at = created_at[:19]  # 截取到秒
                    status = "✅" if record.get('success', False) else "❌"
                    option_text = f"{record.get('stock_symbol', 'N/A')} - {created_at} - {status}"
                    delete_options.append({
                        'text': option_text,
                        'record_id': record.get('record_id'),
                        'index': len(delete_options)
                    })
                
                # 多选组件
                selected_for_deletion = st.multiselect(
                    "选择要删除的记录（可多选）:",
                    options=[opt['index'] for opt in delete_options],
                    format_func=lambda x: delete_options[x]['text'],
                    help="⚠️ 删除操作不可恢复，请谨慎选择"
                )
            else:
                st.warning("⚠️ 记录缺少ID字段，无法执行删除操作")
                selected_for_deletion = []
        
        with delete_col2:
            # 删除按钮
            if selected_for_deletion:
                st.write("")  # 添加一些空间
                st.write("")  # 添加一些空间
                
                # 获取要删除的记录ID
                record_ids_to_delete = [delete_options[idx]['record_id'] for idx in selected_for_deletion]
                
                # 一步确认删除
                if st.button("🗑️ 删除选中记录", type="secondary", help=f"将删除 {len(selected_for_deletion)} 条记录"):
                    with st.spinner("正在删除记录..."):
                        # 立即执行删除
                        deleted_count = history_manager.delete_records_by_ids(record_ids_to_delete)
                        
                        if deleted_count > 0:
                            st.success(f"✅ 成功删除了 {deleted_count} 条记录")
                            
                            # 清除所有session state
                            for key in list(st.session_state.keys()):
                                if 'selected' in key.lower() or 'confirm' in key.lower():
                                    del st.session_state[key]
                            
                            # 等待一点时间确保数据库操作完成
                            import time
                            time.sleep(0.5)
                            
                            # 强制刷新页面
                            st.rerun()
                        else:
                            st.error("❌ 删除失败，请检查记录是否存在")
        
        # 显示记录表格
        st.markdown("### 📊 记录详情")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "状态": st.column_config.TextColumn(
                    "状态",
                    help="分析是否成功完成"
                ),
                "成本": st.column_config.NumberColumn(
                    "成本($)",
                    help="分析总成本",
                    format="%.4f"
                ),
                "耗时": st.column_config.NumberColumn(
                    "耗时(秒)",
                    help="分析总耗时",
                    format="%.2f"
                )
            }
        )
        
        # 选择记录查看详情
        if len(records) > 0:
            st.markdown("### 🔍 查看详细分析结果")
            
            # 创建选择框
            record_options = []
            for i, record in enumerate(records):
                created_at = record.get('created_at', '')
                if isinstance(created_at, str):
                    created_at = created_at[:19]  # 截取到秒
                option = f"{record.get('stock_symbol', 'N/A')} - {created_at} - {record.get('llm_provider', 'N/A')}"
                record_options.append(option)
            
            selected_index = st.selectbox(
                "选择要查看的分析记录:",
                range(len(record_options)),
                format_func=lambda x: record_options[x]
            )
            
            if st.button("📋 查看分析详情", type="primary"):
                show_analysis_details(records[selected_index])
    
    except Exception as e:
        st.error(f"❌ 获取记录失败: {e}")

def prepare_display_dataframe(df):
    """准备显示用的DataFrame"""
    display_df = df.copy()
    
    # 重命名列
    column_mapping = {
        'stock_symbol': '股票代码',
        'created_at': '分析时间',
        'market_type': '市场类型',
        'llm_provider': 'LLM提供商',
        'llm_model': '模型',
        'research_depth': '研究深度',
        'duration': '耗时(秒)',
        'total_cost': '成本($)',
        'success': '状态'
    }
    
    # 选择要显示的列（不包括record_id，但会保留在原始数据中用于删除）
    display_columns = ['stock_symbol', 'created_at', 'market_type', 'llm_provider', 
                      'llm_model', 'research_depth', 'duration', 'total_cost', 'success']
    
    # 过滤存在的列用于显示
    available_display_columns = [col for col in display_columns if col in display_df.columns]
    display_for_table = display_df[available_display_columns].copy()
    
    # 重命名显示列
    display_for_table = display_for_table.rename(columns=column_mapping)
    
    # 格式化数据
    if '分析时间' in display_for_table.columns:
        display_for_table['分析时间'] = pd.to_datetime(display_for_table['分析时间']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    if '状态' in display_for_table.columns:
        display_for_table['状态'] = display_for_table['状态'].map({True: '✅ 成功', False: '❌ 失败'})
    
    if '耗时(秒)' in display_for_table.columns:
        display_for_table['耗时(秒)'] = display_for_table['耗时(秒)'].round(2)
    
    if '成本($)' in display_for_table.columns:
        display_for_table['成本($)'] = display_for_table['成本($)'].round(4)
    
    # 修复研究深度列的数据类型问题，确保Arrow序列化兼容
    if '研究深度' in display_for_table.columns:
        # 将所有研究深度值转换为字符串，避免Arrow类型转换错误
        display_for_table['研究深度'] = display_for_table['研究深度'].astype(str)
        
        # 可选：将数字映射为更友好的描述
        depth_mapping = {
            '1': '1级-快速',
            '2': '2级-基础', 
            '3': '3级-标准',
            '4': '4级-深度',
            '5': '5级-极深'
        }
        display_for_table['研究深度'] = display_for_table['研究深度'].map(lambda x: depth_mapping.get(str(x), str(x)))
    
    return display_for_table

def show_analysis_details(record):
    """显示分析详情"""
    st.markdown("---")
    st.subheader(f"📋 {record.get('stock_symbol', 'N/A')} 分析详情")
    
    # 基本信息
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**基本信息**")
        st.write(f"📊 股票代码: {record.get('stock_symbol', 'N/A')}")
        st.write(f"📅 分析日期: {record.get('analysis_date', 'N/A')}")
        st.write(f"🌐 市场类型: {record.get('market_type', 'N/A')}")
        st.write(f"🔬 研究深度: {record.get('research_depth', 'N/A')}")
    
    with col2:
        st.markdown("**技术信息**")
        st.write(f"🤖 LLM提供商: {record.get('llm_provider', 'N/A')}")
        st.write(f"🧠 模型: {record.get('llm_model', 'N/A')}")
        st.write(f"⏱️ 耗时: {record.get('duration', 0):.2f} 秒")
        st.write(f"💰 成本: ${record.get('total_cost', 0):.4f}")
    
    # 分析师信息
    analysts = record.get('analysts', [])
    if analysts:
        st.markdown("**参与分析师**")
        analyst_cols = st.columns(min(len(analysts), 4))
        for i, analyst in enumerate(analysts):
            with analyst_cols[i % 4]:
                st.badge(analyst)
    
    # 分析结果
    results = record.get('results', {})
    if results:
        st.markdown("**分析结果**")
        
        # 创建展开的分析结果
        for key, value in results.items():
            if key and value:
                with st.expander(f"📄 {key}"):
                    if isinstance(value, dict):
                        st.json(value)
                    else:
                        st.markdown(str(value))
    
    # Token使用情况
    token_usage = record.get('token_usage', {})
    if token_usage:
        st.markdown("**Token使用情况**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("输入Token", token_usage.get('input_tokens', 0))
        with col2:
            st.metric("输出Token", token_usage.get('output_tokens', 0))
        with col3:
            st.metric("总Token", token_usage.get('total_tokens', 0))

def render_statistics_view(history_manager):
    """渲染统计分析界面"""
    st.subheader("📈 分析统计")
    
    try:
        # 获取统计信息
        stats = history_manager.get_analysis_statistics()
        
        if not stats:
            st.info("📭 暂无统计数据")
            return
        
        # 基本统计指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "总分析次数",
                stats.get('total_analyses', 0)
            )
        
        with col2:
            success_rate = 0
            if stats.get('total_analyses', 0) > 0:
                success_rate = (stats.get('successful_analyses', 0) / stats.get('total_analyses', 1)) * 100
            st.metric(
                "成功率",
                f"{success_rate:.1f}%"
            )
        
        with col3:
            st.metric(
                "总成本",
                f"${stats.get('total_cost', 0):.2f}"
            )
        
        with col4:
            st.metric(
                "平均耗时",
                f"{stats.get('avg_duration', 0):.1f}秒"
            )
        
        # 获取详细记录用于图表
        recent_records = history_manager.get_analysis_history(limit=100)
        
        if recent_records:
            render_charts(recent_records)
    
    except Exception as e:
        st.error(f"❌ 获取统计信息失败: {e}")

def render_charts(records):
    """渲染图表"""
    df = pd.DataFrame(records)
    
    if df.empty:
        return
    
    # 时间序列图表
    st.markdown("### 📊 分析趋势")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 分析次数趋势
        if 'created_at' in df.columns:
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            fig = px.line(
                daily_counts, 
                x='date', 
                y='count',
                title="每日分析次数",
                labels={'date': '日期', 'count': '分析次数'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 成功率趋势
        if 'success' in df.columns and 'created_at' in df.columns:
            daily_success = df.groupby('date')['success'].agg(['count', 'sum']).reset_index()
            daily_success['success_rate'] = (daily_success['sum'] / daily_success['count']) * 100
            
            fig = px.bar(
                daily_success,
                x='date',
                y='success_rate',
                title="每日成功率",
                labels={'date': '日期', 'success_rate': '成功率(%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 更多图表
    col3, col4 = st.columns(2)
    
    with col3:
        # LLM提供商分布
        if 'llm_provider' in df.columns:
            provider_counts = df['llm_provider'].value_counts()
            
            fig = px.pie(
                values=provider_counts.values,
                names=provider_counts.index,
                title="LLM提供商分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        # 市场类型分布
        if 'market_type' in df.columns:
            market_counts = df['market_type'].value_counts()
            
            fig = px.pie(
                values=market_counts.values,
                names=market_counts.index,
                title="市场类型分布"
            )
            st.plotly_chart(fig, use_container_width=True)

def render_advanced_search(history_manager):
    """渲染高级搜索界面"""
    st.subheader("🔍 高级搜索")
    
    # 搜索条件
    col1, col2 = st.columns(2)
    
    with col1:
        stock_symbol = st.text_input("股票代码", placeholder="例如: AAPL")
        llm_provider = st.selectbox("LLM提供商", ["全部", "dashscope", "deepseek", "google", "openai"])
        success_status = st.selectbox("分析状态", ["全部", "成功", "失败"])
    
    with col2:
        date_range = st.date_input(
            "日期范围",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
        research_depth = st.selectbox("研究深度", ["全部", "简单", "详细", "深度"])
        sort_by = st.selectbox("排序方式", ["时间(降序)", "时间(升序)", "成本(降序)", "成本(升序)"])
    
    # 搜索按钮
    if st.button("🔍 搜索", type="primary"):
        # 构建搜索参数
        date_from = None
        date_to = None
        
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            date_from = datetime.combine(date_range[0], datetime.min.time())
            date_to = datetime.combine(date_range[1], datetime.max.time())
        
        try:
            records = history_manager.get_analysis_history(
                stock_symbol=stock_symbol if stock_symbol else None,
                limit=100,
                success_only=success_status == "成功",
                date_from=date_from,
                date_to=date_to
            )
            
            # 额外过滤
            if llm_provider != "全部":
                records = [r for r in records if r.get('llm_provider') == llm_provider]
            
            if research_depth != "全部":
                records = [r for r in records if r.get('research_depth') == research_depth]
            
            if success_status == "失败":
                records = [r for r in records if not r.get('success', True)]
            
            # 排序
            if sort_by == "时间(升序)":
                records.sort(key=lambda x: x.get('created_at', ''))
            elif sort_by == "成本(降序)":
                records.sort(key=lambda x: x.get('total_cost', 0), reverse=True)
            elif sort_by == "成本(升序)":
                records.sort(key=lambda x: x.get('total_cost', 0))
            
            # 显示结果
            if records:
                st.success(f"🎯 找到 {len(records)} 条记录")
                
                # 显示结果表格
                df = pd.DataFrame(records)
                display_df = prepare_display_dataframe(df)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("📭 未找到符合条件的记录")
        
        except Exception as e:
            st.error(f"❌ 搜索失败: {e}")

def render_management_tools(history_manager):
    """渲染管理工具界面"""
    st.subheader("⚙️ 管理工具")
    
    # 数据清理
    st.markdown("### 🧹 数据清理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**批量清理**")
        days = st.number_input("清理多少天前的记录", min_value=1, max_value=365, value=30)
        
        if st.button("🗑️ 清理旧记录", type="secondary"):
            try:
                deleted_count = history_manager.delete_old_records(days)
                st.success(f"✅ 已清理 {deleted_count} 条旧记录")
            except Exception as e:
                st.error(f"❌ 清理失败: {e}")
    
    with col2:
        st.markdown("**快速删除**")
        
        # 按股票代码删除
        stock_to_delete = st.text_input("输入要删除的股票代码", placeholder="例如: AAPL")
        
        if st.button("🗑️ 删除指定股票记录", type="secondary"):
            if stock_to_delete:
                try:
                    # 获取该股票的所有记录
                    records_to_delete = history_manager.get_analysis_history(
                        stock_symbol=stock_to_delete,
                        limit=1000
                    )
                    
                    if records_to_delete:
                        record_ids = [r.get('record_id') for r in records_to_delete if r.get('record_id')]
                        deleted_count = history_manager.delete_records_by_ids(record_ids)
                        if deleted_count > 0:
                            st.success(f"✅ 已删除股票 {stock_to_delete} 的 {deleted_count} 条记录")
                            # 标记数据已更新
                            st.session_state['just_deleted'] = True
                        else:
                            st.info(f"📭 未找到股票 {stock_to_delete} 的记录或删除失败")
                    else:
                        st.info(f"📭 未找到股票 {stock_to_delete} 的记录")
                        
                except Exception as e:
                    st.error(f"❌ 删除失败: {e}")
            else:
                st.warning("⚠️ 请输入股票代码")
    
    # 数据导出
    st.markdown("### 📤 数据管理")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        # 数据导出
        if st.button("📤 导出数据", type="secondary"):
            try:
                records = history_manager.get_analysis_history(limit=1000)
                if records:
                    df = pd.DataFrame(records)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="💾 下载CSV文件",
                        data=csv,
                        file_name=f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📭 暂无数据可导出")
            except Exception as e:
                st.error(f"❌ 导出失败: {e}")
    
    with export_col2:
        # 清空所有记录（危险操作）
        st.markdown("**⚠️ 危险操作**")
        if st.button("🚨 清空所有记录", type="secondary"):
            # 需要二次确认
            if st.session_state.get('confirm_clear_all', False):
                try:
                    # 获取所有记录ID
                    all_records = history_manager.get_analysis_history(limit=10000)
                    if all_records:
                        record_ids = [r.get('record_id') for r in all_records if r.get('record_id')]
                        deleted_count = history_manager.delete_records_by_ids(record_ids)
                        if deleted_count > 0:
                            st.success(f"✅ 已清空所有记录，共删除 {deleted_count} 条")
                            # 标记数据已更新
                            st.session_state['just_deleted'] = True
                        else:
                            st.error("❌ 清空操作失败")
                    else:
                        st.info("📭 没有记录需要清空")
                    
                    st.session_state['confirm_clear_all'] = False
                except Exception as e:
                    st.error(f"❌ 清空失败: {e}")
            else:
                st.warning("⚠️ 此操作将删除所有历史记录，不可恢复！")
                clear_col1, clear_col2 = st.columns(2)
                
                with clear_col1:
                    if st.button("✅ 确认清空", type="primary", key="confirm_clear_all_btn"):
                        st.session_state['confirm_clear_all'] = True
                        st.rerun()
                
                with clear_col2:
                    if st.button("❌ 取消", key="cancel_clear_all_btn"):
                        st.session_state['confirm_clear_all'] = False
    
    # 系统信息
    st.markdown("### ℹ️ 系统信息")
    
    try:
        stats = history_manager.get_analysis_statistics()
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.info(f"""
            **数据库状态**
            - MongoDB: {'✅ 可用' if history_manager.mongodb_client else '❌ 不可用'}
            - Redis: {'✅ 可用' if history_manager.redis_client else '❌ 不可用'}
            """)
        
        with info_col2:
            st.info(f"""
            **存储统计**
            - 总记录数: {stats.get('total_analyses', 0)}
            - 成功记录: {stats.get('successful_analyses', 0)}
            - 分析股票数: {stats.get('unique_stocks_count', 0)}
            """)
    
    except Exception as e:
        st.error(f"❌ 获取系统信息失败: {e}")

# 主函数
def main():
    """主函数"""
    render_analysis_history()

if __name__ == "__main__":
    main()
