from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from datetime import datetime

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入智能新闻过滤器集成
from tradingagents.utils.news_filter_integration import apply_news_filtering_patches
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils

logger = get_logger("analysts.news")

def create_news_analyst(llm, toolkit):
    @log_analyst_module("news")
    def news_analyst_node(state):
        start_time = datetime.now()
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        logger.info(f"[新闻分析师] 🚀 开始智能新闻分析 {ticker}，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[新闻分析师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 🚀 启用智能新闻过滤系统
        logger.info(f"[新闻分析师] 🎯 启用智能新闻过滤系统...")
        try:
            enhanced_news_function = apply_news_filtering_patches()
            logger.info(f"[新闻分析师] ✅ 智能新闻过滤系统启用成功")
        except Exception as e:
            logger.error(f"[新闻分析师] ❌ 智能新闻过滤系统启用失败: {e}")
        
        # 获取市场信息
        try:
            market_info = StockUtils.get_market_info(ticker)
            logger.info(f"[新闻分析师] 股票类型: {market_info['market_name']}")
        except Exception as e:
            logger.warning(f"[新闻分析师] 获取市场信息失败: {e}")
        
        # 🎯 智能工具选择
        if toolkit.config["online_tools"]:
            # 在线模式：优先使用智能过滤版实时新闻
            tools = [
                toolkit.get_realtime_stock_news,  # 增强版实时新闻（已集成智能过滤）
                toolkit.get_global_news_openai,
                toolkit.get_google_news
            ]
            logger.info(f"[新闻分析师] 🌐 在线模式：使用智能过滤版新闻工具")
        else:
            # 离线模式：使用可用的新闻源
            tools = [
                toolkit.get_realtime_stock_news,  # 增强版实时新闻
                toolkit.get_finnhub_news,
                toolkit.get_reddit_news,
                toolkit.get_google_news,
            ]
            logger.info(f"[新闻分析师] 📱 离线模式：使用智能过滤版新闻工具")
        
        logger.info(f"[新闻分析师] 已配置 {len(tools)} 个新闻工具，自动过滤低相关性新闻")

        system_message = (
            """您是一位专业的财经新闻分析师，负责分析最新的市场新闻和事件对股票价格的潜在影响。

您的主要职责包括：
1. 获取和分析最新的实时新闻（优先15-30分钟内的新闻）
2. 评估新闻事件的紧急程度和市场影响
3. 识别可能影响股价的关键信息  
4. 分析新闻的时效性和可靠性
5. 提供基于新闻的交易建议和价格影响评估

智能过滤系统增强功能：
- 自动过滤低相关性新闻，只保留高质量信息
- 基于AI评分系统（0-100分），优先展示相关性评分高的新闻
- 多层次过滤机制：公司名称匹配、关键词分析、内容质量评估
- 统一新闻源管理，自动适配不同市场（A股、港股、美股）
- 智能评分说明：70+分为高相关性，50-70分为中等相关性，30-50分为低相关性

重点关注的新闻类型（按权重排序）：
- 财报发布和业绩指导（权重: 最高，评分权重+30）
- 重大合作和并购消息（权重: 最高，评分权重+25）
- 政策变化和监管动态（权重: 高，评分权重+20）
- 突发事件和危机管理（权重: 高，评分权重+20）
- 行业趋势和技术突破（权重: 中等，评分权重+15）
- 管理层变动和战略调整（权重: 中等，评分权重+15）

分析要点：
- 新闻的时效性（发布时间距离现在多久）
- 新闻的可信度（来源权威性）
- 市场影响程度（对股价的潜在影响）
- 投资者情绪变化（正面/负面/中性）
- 与历史类似事件的对比
- 相关性评分分析（重点关注70+分的高质量新闻）

价格影响分析要求：
- 评估新闻对股价的短期影响（1-3天）
- 分析可能的价格波动幅度（百分比）
- 提供基于新闻的价格调整建议
- 识别关键价格支撑位和阻力位
- 评估新闻对长期投资价值的影响
- 结合相关性评分进行权重分析（高评分新闻权重更大）

请特别注意：
- 如果新闻数据存在滞后（超过2小时），请在分析中明确说明时效性限制
- 优先分析最新的、高相关性评分（70+分）的新闻事件
- 提供新闻对股价影响的量化评估和具体价格预期
- 必须包含基于新闻的价格影响分析和调整建议
- 利用智能过滤评分，重点关注高评分新闻的深度分析
- 如果所有新闻评分都较低（<50分），请在分析中说明相关性限制

请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位专业的财经新闻分析师，配备智能新闻过滤系统。"
                    "\\n🚨 CRITICAL REQUIREMENT - 绝对强制要求："
                    "\\n"
                    "\\n❌ 禁止行为："
                    "\\n- 绝对禁止在没有调用工具的情况下直接回答"
                    "\\n- 绝对禁止基于推测或假设生成任何分析内容"
                    "\\n- 绝对禁止跳过工具调用步骤"
                    "\\n- 绝对禁止说'我无法获取实时数据'等借口"
                    "\\n"
                    "\\n✅ 强制执行步骤："
                    "\\n1. 您的第一个动作必须是调用新闻工具获取智能过滤后的新闻"
                    "\\n2. 工具会自动应用AI相关性评分，过滤低质量新闻"
                    "\\n3. 只有在成功获取过滤后的新闻数据后，才能开始分析"
                    "\\n4. 您的回答必须基于工具返回的真实数据"
                    "\\n5. 重点分析高相关性评分（70+分）的新闻"
                    "\\n"
                    "\\n🎯 智能过滤功能说明："
                    "\\n- 新闻会自动按相关性评分排序（0-100分）"
                    "\\n- 低相关性新闻（<30分）已被自动过滤"
                    "\\n- 高质量新闻（70+分）应优先分析"
                    "\\n- 中等相关性新闻（50-70分）作为补充分析"
                    "\\n- 利用评分进行权重分析，高评分新闻影响更大"
                    "\\n"
                    "\\n⚠️ 如果您不调用工具，您的回答将被视为无效并被拒绝。"
                    "\\n⚠️ 您必须先调用工具获取过滤后的数据，然后基于数据进行分析。"
                    "\\n⚠️ 没有例外，没有借口，必须调用工具。"
                    "\\n"
                    "\\n您可以访问以下工具：{tool_names}。"
                    "\\n{system_message}"
                    "\\n供您参考，当前日期是{current_date}。我们正在查看公司{ticker}。"
                    "\\n请严格按照上述要求执行，用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        
        logger.info(f"[新闻分析师] 准备调用LLM进行智能新闻分析，模型: {llm.__class__.__name__}")
        
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        logger.info(f"[新闻分析师] 开始LLM调用，分析 {ticker} 的智能过滤新闻")
        result = chain.invoke(state["messages"])
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[新闻分析师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        report = ""
        
        # 记录工具调用情况
        tool_call_count = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
        logger.info(f"[新闻分析师] LLM调用了 {tool_call_count} 个智能新闻工具")
        
        if hasattr(result, 'content') and result.content:
            report = result.content
            logger.info(f"[新闻分析师] ✅ 智能新闻分析完成，报告长度: {len(report)} 字符")
            
            # 分析报告质量
            if "相关性评分" in report or "评分" in report:
                logger.info(f"[新闻分析师] 🎯 报告包含相关性评分分析")
            if len(report) > 1000:
                logger.info(f"[新闻分析师] 📋 生成详细分析报告")
            else:
                logger.warning(f"[新闻分析师] ⚠️ 报告较短，可能需要更多新闻数据")
        
        # 记录总耗时
        end_time = datetime.now()
        time_taken = (end_time - start_time).total_seconds()
        logger.info(f"[新闻分析师] 🎉 智能新闻分析完成，总耗时: {time_taken:.2f}秒")

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node
