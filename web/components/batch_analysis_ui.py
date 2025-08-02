#!/usr/bin/env python3
"""
批量分析管理界面 - 改进版
用于显示和管理批量分析任务的进度，支持自动状态更新
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
    """渲染批量分析监控界面 - 改进版支持自动刷新"""
    
    processor = get_batch_processor()
    status = processor.get_progress_status()
    
    # 初始化状态跟踪
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
    
    # 运行状态与控制
    if status['is_running']:
        st.success("🟢 批量分析正在进行中...")
        
        # 控制面板
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # 自动刷新选项
            auto_refresh = st.checkbox(
                "🔄 自动刷新", 
                value=st.session_state.get('batch_auto_refresh', True), 
                key="auto_refresh_batch",
                help="开启后每5秒自动更新进度状态"
            )
            st.session_state.batch_auto_refresh = auto_refresh
        
        with col2:
            if st.button("🔄 立即刷新", key="manual_refresh"):
                st.rerun()
        
        with col3:
            if st.button("⏸️ 停止任务", type="secondary", key="stop_tasks"):
                processor.stop_all_tasks()
                st.warning("⏸️ 已请求停止所有任务")
                st.rerun()
        
        # 自动刷新实现 - 智能版本基于活动时间判断
        if auto_refresh:
            # 检查是否需要重新刷新
            if 'batch_refresh_timer' not in st.session_state:
                st.session_state.batch_refresh_timer = time.time()
            
            current_time = time.time()
            elapsed = current_time - st.session_state.batch_refresh_timer
            
            # 动态刷新间隔：更频繁的检查
            time_since_activity = status.get('time_since_last_activity')
            
            # 当有任务运行时，每1-2秒检查一次；无活动时每3秒检查
            if status['is_running'] and status['running_tasks'] > 0:
                refresh_interval = 1  # 运行中时更频繁
            elif time_since_activity is not None and time_since_activity < 10:
                refresh_interval = 2  # 最近有活动时适中频率
            else:
                refresh_interval = 3  # 长时间无活动时较低频率
            
            # 检查状态变化
            if elapsed >= refresh_interval:
                st.session_state.batch_refresh_timer = current_time
                
                # 获取最新状态
                latest_status = processor.get_progress_status()
                
                # 智能刷新判断：基于多种条件
                should_refresh = False
                refresh_reason = ""
                
                # 1. 任务完成状态变化
                if latest_status['completed_tasks'] != status['completed_tasks']:
                    should_refresh = True
                    refresh_reason = f"任务完成数变化: {status['completed_tasks']} -> {latest_status['completed_tasks']}"
                
                # 2. 运行状态变化
                elif latest_status['is_running'] != status['is_running']:
                    should_refresh = True
                    refresh_reason = f"运行状态变化: {status['is_running']} -> {latest_status['is_running']}"
                
                # 3. 检测到死线程
                elif latest_status.get('dead_threads_detected', 0) > 0:
                    should_refresh = True
                    refresh_reason = f"检测到{latest_status['dead_threads_detected']}个死线程"
                
                # 4. 强制完成标识
                elif latest_status.get('force_completion', False):
                    should_refresh = True
                    refresh_reason = "强制完成检测触发"
                
                # 5. 运行中任务数变化
                elif latest_status['running_tasks'] != status['running_tasks']:
                    should_refresh = True
                    refresh_reason = f"运行中任务数变化: {status['running_tasks']} -> {latest_status['running_tasks']}"
                
                # 6. 长时间无活动后的确认检查（缩短到8秒）
                elif (latest_status.get('time_since_last_activity') or 0) > 8 and latest_status['completed_tasks'] > 0 and latest_status['is_running']:
                    should_refresh = True
                    time_since = latest_status.get('time_since_last_activity') or 0
                    refresh_reason = f"长时间无活动确认检查: {time_since:.1f}秒"
                
                if should_refresh:
                    logger.info(f"[UI] 触发自动刷新 - {refresh_reason}")
                    st.rerun()
                else:
                    # 显示倒计时和状态信息
                    remaining = refresh_interval - elapsed
                    activity_info = ""
                    if status.get('last_activity_time'):
                        time_since = status.get('time_since_last_activity') or 0
                        activity_info = f" | 最后活动: {status['last_activity_time']} ({time_since:.0f}秒前)"
                    
                    st.info(f"⏱️ {remaining:.1f}秒后检查更新{activity_info}")
                    
                    # 使用客户端定时器
                    st.markdown(f"""
                    <script>
                        setTimeout(function() {{
                            window.parent.postMessage({{
                                type: 'streamlit:rerun'
                            }}, '*');
                        }}, {int(remaining * 1000)});
                    </script>
                    """, unsafe_allow_html=True)
            else:
                # 显示实时状态信息
                remaining = refresh_interval - elapsed
                activity_info = ""
                if status.get('last_activity_time'):
                    time_since = status.get('time_since_last_activity') or 0
                    activity_info = f" | 最后活动: {status['last_activity_time']} ({time_since:.0f}秒前)"
                
                st.info(f"⏱️ {remaining:.1f}秒后检查更新{activity_info}")
    else:
        # 清理自动刷新状态
        if 'batch_refresh_timer' in st.session_state:
            del st.session_state.batch_refresh_timer
        
        # 显示完成状态
        if status['completed_tasks'] > 0:
            st.success(f"✅ 批量分析已完成！共分析了 {status['completed_tasks']} 个股票")
            
            # 显示完成时间和活动信息
            completion_info = []
            if status.get('last_activity_time'):
                completion_info.append(f"最后完成时间: {status['last_activity_time']}")
            time_since = status.get('time_since_last_activity')
            if time_since is not None:
                completion_info.append(f"完成已过: {time_since:.0f}秒")
            
            if completion_info:
                st.info(f"⏰ {' | '.join(completion_info)}")
            
            # 如果刚刚完成，显示庆祝效果
            if st.session_state.get('batch_just_completed', False):
                st.balloons()
                st.success("🎉 所有股票分析已成功完成！")
                st.session_state.batch_just_completed = False
        else:
            st.info("📭 暂无正在运行的分析任务")
    
    # 显示任务详情
    _render_task_details(status)


def _render_task_details(status: Dict):
    """渲染任务详情"""
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
                task_options = {
                    f"{task['symbol']} - {task['task_id'][:8]}": task 
                    for task in completed_tasks
                }
                
                if task_options:
                    selected_task_key = st.selectbox(
                        "选择要查看的分析结果",
                        options=list(task_options.keys()),
                        key="batch_result_selector"
                    )
                    
                    if selected_task_key and st.button("📖 查看详细结果", key="view_batch_result"):
                        selected_task = task_options[selected_task_key]
                        _display_task_result(selected_task)


def _display_task_result(task: Dict):
    """显示单个任务的详细结果"""
    if task.get('result'):
        st.markdown(f"### 📊 {task['symbol']} 详细分析结果")
        
        result = task['result']
        if isinstance(result, dict):
            # 显示格式化的分析结果
            for section, content in result.items():
                if content:
                    st.markdown(f"#### {section}")
                    if isinstance(content, str):
                        st.markdown(content)
                    elif isinstance(content, dict):
                        st.json(content)
                    else:
                        st.write(content)
        else:
            st.markdown(str(result))
    else:
        st.warning("该任务暂无详细结果")


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
            # 初始化自动刷新
            st.session_state.batch_auto_refresh = True
            st.session_state.batch_refresh_time = time.time()
            logger.info(f"启动批量分析: {len(symbols)} 个股票代码")
            return True
        else:
            st.error("❌ 启动批量分析失败")
            return False
            
    except Exception as e:
        st.error(f"❌ 启动批量分析时出错: {e}")
        logger.error(f"批量分析启动失败: {e}")
        return False


def clear_batch_results():
    """清理批量分析结果"""
    st.success("✅ 清理功能暂未实现，请重启应用以清理结果")
    logger.info("批量结果清理请求")


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
        - 🔄 **自动刷新**：页面自动更新分析状态，无需手动刷新
        
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
        - 🔄 启用自动刷新后，页面会每5秒自动更新状态
        
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
