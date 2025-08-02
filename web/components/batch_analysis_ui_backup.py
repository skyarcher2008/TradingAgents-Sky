#!/usr/bin/env python3
"""
批量分析管理界面
用于显示和管理批量分析任务的进度
"""

import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any, Optional

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('batch_ui')

from utils.batch_processor import get_batch_processor


def render_batch_analysis_monitor():
    """渲染批量分析监控界面"""
    
    processor = get_batch_processor()
    status = processor.get_progress_status()
    
    # 检查是否是批量分析刚完成的情况
    if 'last_batch_status' not in st.session_state:
        st.session_state.last_batch_status = {'is_running': False, 'completed_tasks': 0}
    
    # 检测状态变化 - 从运行中变为完成
    if (st.session_state.last_batch_status['is_running'] and not status['is_running'] 
        and status['completed_tasks'] > st.session_state.last_batch_status['completed_tasks']):
        st.session_state.batch_just_completed = True
    
    # 更新状态记录
    st.session_state.last_batch_status = {
        'is_running': status['is_running'], 
        'completed_tasks': status['completed_tasks']
    }
    
    if not status['total_tasks'] and not status['is_running']:
        st.info("📭 暂无批量分析任务正在运行")
        return
    
    st.subheader("📊 批量分析进度监控")
    
    # 总体进度显示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总任务数", status['total_tasks'])
    
    with col2:
        st.metric("运行中", status['running_tasks'], delta=None if status['running_tasks'] == 0 else "🔄")
    
    with col3:
        st.metric("已完成", status['completed_tasks'])
    
    with col4:
        progress_pct = status['progress_percentage']
        st.metric("完成率", f"{progress_pct:.1f}%")
    
    # 进度条
    progress_bar = st.progress(progress_pct / 100.0)
    
    # 运行状态
    if status['is_running']:
        st.success("🟢 批量分析正在进行中...")
        
        # 显示刷新选项
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            auto_refresh = st.checkbox("� 自动刷新 (每3秒)", value=True, key="auto_refresh_batch")
        with col2:
            if st.button("🔄 立即刷新", key="manual_refresh"):
                st.rerun()
        with col3:
            if st.button("⏸️ 停止", type="secondary", key="stop_tasks"):
                processor.stop_all_tasks()
                st.warning("⏸️ 已请求停止所有任务")
                time.sleep(1)
                st.rerun()
        
        # 自动刷新逻辑
        if auto_refresh:
            import asyncio
            import threading
            
            # 使用session state跟踪刷新状态
            if 'auto_refresh_enabled' not in st.session_state:
                st.session_state.auto_refresh_enabled = True
            
            if st.session_state.auto_refresh_enabled:
                # 创建一个占位符显示倒计时
                placeholder = st.empty()
                for i in range(3, 0, -1):
                    placeholder.info(f"⏱️ {i}秒后自动刷新...")
                    time.sleep(1)
                
                placeholder.empty()
                st.rerun()
            
    else:
        # 分析完成或未运行
        if 'auto_refresh_enabled' in st.session_state:
            del st.session_state.auto_refresh_enabled
            
        if status['completed_tasks'] > 0:
            st.success("✅ 批量分析已完成！")
            
            # 如果刚刚完成，显示庆祝动画
            if st.session_state.get('batch_just_completed', False):
                st.balloons()
                st.session_state.batch_just_completed = False
        else:
            st.info("📭 暂无正在运行的分析任务")
        
    # 已完成任务的结果显示
    if status['completed_results']:
        st.markdown("---")
        st.subheader("📋 分析结果")
        
        # 创建结果表格
        results_data = []
        for task in status['completed_results']:
            duration = ""
            if task['start_time'] and task['end_time']:
                delta = task['end_time'] - task['start_time']
                duration = f"{delta.total_seconds():.1f}秒"
            
            results_data.append({
                "股票代码": task['symbol'],
                "状态": "✅ 成功" if task['status'] == 'completed' else "❌ 失败",
                "开始时间": task['start_time'].strftime("%H:%M:%S") if task['start_time'] else "-",
                "耗时": duration,
                "任务ID": task['task_id']
            })
        
        if results_data:
            df = pd.DataFrame(results_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 查看详细结果
            st.markdown("### 🔍 查看详细分析结果")
            
            completed_tasks = [t for t in status['completed_results'] if t['status'] == 'completed']
            if completed_tasks:
                # 创建选择选项
                task_options = {}
                for task in completed_tasks:
                    display_text = f"{task['symbol']} - {task['end_time'].strftime('%H:%M:%S')}"
                    task_options[display_text] = task
                
                selected_task_display = st.selectbox(
                    "选择要查看的分析结果",
                    options=list(task_options.keys()),
                    help="选择一个已完成的分析任务查看详细结果"
                )
                
                if selected_task_display:
                    selected_task = task_options[selected_task_display]
                    
                    if st.button(f"📖 查看 {selected_task['symbol']} 的分析报告"):
                        # 将结果存储到session state中供结果显示组件使用
                        st.session_state.analysis_results = selected_task['result']
                        st.session_state.current_symbol = selected_task['symbol']
                        st.success(f"✅ 已加载 {selected_task['symbol']} 的分析结果，请查看下方的详细报告")
                        
                        # 触发页面刷新以显示结果
                        st.rerun()
            
            # 导出结果选项
            if len(completed_tasks) > 1:
                st.markdown("### 📤 批量导出")
                if st.button("💾 导出所有分析结果", help="将所有完成的分析结果导出为文件"):
                    # 这里可以实现批量导出功能
                    st.info("💡 批量导出功能正在开发中...")


def start_batch_analysis(symbols: List[str], analysis_params: Dict[str, Any], llm_config: Optional[Dict[str, str]] = None) -> bool:
    """启动批量分析"""
    try:
        processor = get_batch_processor()
        
        # 清理参数，移除不需要的字段
        clean_params = {
            'market_type': analysis_params.get('market_type'),
            'analysis_date': analysis_params.get('analysis_date'),
            'analysts': analysis_params.get('analysts', []),
            'research_depth': analysis_params.get('research_depth', 3),
            'include_sentiment': analysis_params.get('include_sentiment', True),
            'include_risk_assessment': analysis_params.get('include_risk_assessment', True),
            'custom_prompt': analysis_params.get('custom_prompt', '')
        }
        
        # 显示使用的LLM配置信息
        if llm_config:
            st.info(f"📋 批量分析将使用: {llm_config.get('llm_provider', 'deepseek')} - {llm_config.get('llm_model', 'deepseek-chat')}")
        else:
            st.warning("⚠️ 未获取到LLM配置，使用默认配置: DeepSeek")
        
        # 启动批量分析，传递llm_config
        task_ids = processor.start_batch_analysis(symbols, clean_params, llm_config)
        
        if task_ids:
            st.success(f"✅ 成功启动 {len(task_ids)} 个分析任务")
            logger.info(f"启动批量分析: {len(symbols)} 个股票代码")
            return True
        else:
            st.error("❌ 启动批量分析失败")
            return False
            
    except Exception as e:
        st.error(f"❌ 启动批量分析时出错: {e}")
        logger.error(f"批量分析启动失败: {e}")
        return False


def render_batch_analysis_help():
    """渲染批量分析帮助信息"""
    with st.expander("ℹ️ 批量分析使用说明"):
        st.markdown("""
        ### 📚 批量分析功能说明
        
        **功能特点：**
        - 🔄 **并发处理**：多个股票代码同时分析，节省等待时间
        - 📊 **实时监控**：实时查看分析进度和状态
        - 💾 **结果管理**：分析完成后可逐个查看详细报告
        - ⏸️ **任务控制**：可随时停止运行中的任务
        
        **使用步骤：**
        1. 选择"批量分析"模式
        2. 在文本框中输入多个股票代码（支持逗号、空格、换行分隔）
        3. 配置分析参数（市场类型、分析师团队、研究深度等）
        4. 点击"开始批量分析"
        5. 在监控界面查看进度和结果
        
        **注意事项：**
        - ⏱️ 每个股票分析约需10-15分钟，批量分析会并发处理以节省时间
        - 🔋 建议分批处理大量股票代码，避免系统负载过高
        - 💰 批量分析会消耗更多API调用次数，请注意额度管理
        - 📱 分析过程中可以关闭浏览器，稍后回来查看结果
        
        **支持的输入格式：**
        ```
        # 逗号分隔
        AAPL, TSLA, MSFT, GOOGL
        
        # 空格分隔
        AAPL TSLA MSFT GOOGL
        
        # 换行分隔
        AAPL
        TSLA
        MSFT
        GOOGL
        
        # 混合格式
        AAPL, TSLA
        MSFT GOOGL
        NVDA
        ```
        """)
