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
        
        # 自动刷新实现
        if auto_refresh:
            # 初始化自动刷新计时器
            if 'batch_refresh_time' not in st.session_state:
                st.session_state.batch_refresh_time = time.time()
            
            current_time = time.time()
            elapsed = current_time - st.session_state.batch_refresh_time
            
            # 每5秒自动刷新一次
            if elapsed >= 5:
                st.session_state.batch_refresh_time = current_time
                # 短暂延迟后刷新
                with st.empty():
                    st.info("🔄 正在更新状态...")
                time.sleep(0.5)
                st.rerun()
            else:
                # 显示倒计时
                remaining = 5 - elapsed
                st.info(f"⏱️ {remaining:.1f}秒后自动刷新")
                
                # 使用JavaScript实现客户端定时刷新
                st.markdown(f"""
                <script>
                    setTimeout(function() {{
                        location.reload();
                    }}, {int(remaining * 1000)});
                </script>
                """, unsafe_allow_html=True)
    else:
        # 清理自动刷新状态
        if 'batch_refresh_time' in st.session_state:
            del st.session_state.batch_refresh_time
        
        # 显示完成状态
        if status['completed_tasks'] > 0:
            st.success("✅ 批量分析已完成！")
            
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
    try:
        processor = get_batch_processor()
        processor.clear_completed_tasks()
        st.success("✅ 已清理完成的任务结果")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 清理结果时出错: {e}")
        logger.error(f"清理批量结果失败: {e}")
