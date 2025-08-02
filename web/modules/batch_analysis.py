#!/usr/bin/env python3
"""
批量分析模块 - 调试和测试版本
专门用于测试自动刷新功能的改进
"""

import streamlit as st
import time
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any, Optional

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('batch_analysis')

# 导入必要的组件
from utils.batch_processor import get_batch_processor
from components.batch_analysis_ui import render_batch_analysis_monitor
from utils.analysis_runner import validate_analysis_params


def render_batch_analysis_page():
    """渲染批量分析页面 - 测试版本"""
    
    st.title("📊 批量股票分析 - 改进版")
    st.markdown("支持并发分析多个股票/基金，无需等待上一个完成")
    
    # 获取批量处理器
    processor = get_batch_processor()
    
    # 添加测试状态显示
    with st.expander("🔍 调试信息", expanded=False):
        status = processor.get_progress_status()
        st.json(status)
        st.write(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
        
        # 添加死线程检测显示
        if status.get('dead_threads_detected', 0) > 0:
            st.warning(f"💀 检测到 {status['dead_threads_detected']} 个死线程")
        if status.get('force_completion', False):
            st.info("🤖 强制完成检测已触发")
        
        if st.button("🔄 手动获取状态"):
            st.rerun()
    
    # 创建两列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎯 批量分析设置")
        
        # 股票代码输入
        stock_symbols = st.text_area(
            "请输入股票/基金代码",
            placeholder="例如:\n000001\n000002\n510300\n\n多个代码请用换行或逗号分隔",
            height=120,
            help="支持A股、美股、港股等市场的股票和基金代码"
        )
        
        # LLM配置选择
        llm_provider = st.selectbox(
            "🤖 选择LLM提供商",
            options=["deepseek", "dashscope", "openai"],
            index=0,
            help="选择用于分析的大语言模型提供商"
        )
        
        # 模型选择
        model_options = {
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "dashscope": ["qwen-plus", "qwen-plus-latest", "qwen-max"],
            "openai": ["gpt-4", "gpt-3.5-turbo"]
        }
        
        llm_model = st.selectbox(
            "🔧 选择模型",
            options=model_options.get(llm_provider, ["deepseek-chat"]),
            help="选择具体的模型版本"
        )
        
        # 分析深度
        research_depth = st.selectbox(
            "📊 研究深度",
            options=[1, 2, 3, 4, 5],
            index=2,
            help="数值越高，分析越详细，但耗时也越长"
        )
        
        # 市场类型
        market_type = st.selectbox(
            "🌐 市场类型",
            options=["A股", "美股", "港股", "自动识别"],
            index=3,
            help="选择股票所属市场"
        )
        
        # 启动批量分析按钮
        if st.button("🚀 开始批量分析", type="primary", disabled=not stock_symbols.strip()):
            # 解析股票代码
            symbols = processor.parse_stock_symbols(stock_symbols)
            
            if not symbols:
                st.error("❌ 请输入有效的股票代码")
            elif len(symbols) > 10:
                st.error("❌ 批量分析最多支持10个股票代码")
            else:
                # 构建分析参数
                analysis_params = {
                    'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                    'analysts': ['牛市分析师', '熊市分析师', '交易员', '投资顾问', '风险管理专家'],
                    'research_depth': research_depth,
                    'market_type': market_type,
                    'include_sentiment': True,
                    'include_risk_assessment': True,
                    'custom_prompt': ''
                }
                
                # LLM配置
                llm_config = {
                    'llm_provider': llm_provider,
                    'llm_model': llm_model
                }
                
                # 验证参数
                try:
                    # 直接启动批量分析，验证逻辑在batch_processor中处理
                    task_ids = processor.start_batch_analysis(symbols, analysis_params, llm_config)
                    
                    if task_ids:
                        st.success(f"✅ 已启动 {len(task_ids)} 个分析任务")
                        logger.info(f"[批量分析] 启动了 {len(symbols)} 个任务: {symbols}")
                        st.rerun()  # 立即刷新显示监控界面
                    else:
                        st.error("❌ 启动批量分析失败")
                        
                except Exception as e:
                    st.error(f"❌ 参数验证失败: {str(e)}")
                    logger.error(f"[批量分析] 参数验证失败: {e}")
    
    with col2:
        st.subheader("📈 进度监控")
        
        # 渲染监控界面
        render_batch_analysis_monitor()
    
    # 添加使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 🎯 功能特点
        - **并发分析**: 支持同时分析多个股票，无需等待
        - **智能刷新**: 自动检测分析完成状态，及时更新界面
        - **多模型支持**: 支持DeepSeek、阿里云千问、OpenAI等多种LLM
        - **灵活配置**: 可调整分析深度和市场类型
        
        ### 📝 输入格式
        - 支持多种分隔符：换行、逗号、分号、空格
        - 示例代码：`000001, 000002, 510300`
        - 每次最多支持10个股票代码
        
        ### ⚡ 自动刷新说明
        - 开启自动刷新后，界面会每2-5秒检查一次状态
        - 系统会智能检测分析完成状态，自动更新显示
        - 如果检测到长时间无活动，会自动确认完成状态
        
        ### 🔍 调试功能
        - 点击"调试信息"可查看详细的状态数据
        - 包含最后活动时间、完成任务数等信息
        - 有助于诊断自动刷新问题
        """)


if __name__ == "__main__":
    render_batch_analysis_page()
