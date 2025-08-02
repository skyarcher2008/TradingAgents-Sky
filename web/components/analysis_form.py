"""
分析表单组件
"""

import streamlit as st
import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('web')


def render_analysis_form():
    """渲染股票分析表单"""
    
    st.subheader("📋 分析配置")
    
    # 添加分析模式选择
    analysis_mode = st.radio(
        "选择分析模式 🎯",
        options=["单个分析", "批量分析"],
        horizontal=True,
        help="单个分析：分析一个股票代码；批量分析：同时分析多个股票代码"
    )
    
    # 创建表单
    with st.form("analysis_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 市场选择
            market_type = st.selectbox(
                "选择市场 🌍",
                options=["美股", "A股", "港股"],
                index=1,
                help="选择要分析的股票市场"
            )

            # 根据分析模式显示不同的输入界面
            if analysis_mode == "批量分析":
                # 批量输入界面
                if market_type == "美股":
                    stock_input = st.text_area(
                        "批量股票代码 📈",
                        placeholder="输入多个美股代码，可用逗号、空格或换行分隔\n例如：\nAAPL, TSLA, MSFT\nGOOGL\nAMZN, NVDA",
                        height=100,
                        help="支持多种分隔符：逗号、空格、换行。系统会自动去重并验证代码格式。"
                    )
                elif market_type == "港股":
                    stock_input = st.text_area(
                        "批量股票代码 📈",
                        placeholder="输入多个港股代码，可用逗号、空格或换行分隔\n例如：\n0700.HK, 9988.HK, 3690.HK\n1810.HK\n2318.HK, 0005.HK",
                        height=100,
                        help="支持多种分隔符：逗号、空格、换行。请包含.HK后缀。"
                    )
                else:  # A股
                    stock_input = st.text_area(
                        "批量股票代码 📈",
                        placeholder="输入多个A股代码，可用逗号、空格或换行分隔\n例如：\n000001, 600519, 000002\n002415\n300750, 688981",
                        height=100,
                        help="支持多种分隔符：逗号、空格、换行。系统会自动去重并验证代码格式。"
                    )
                
                # 解析并预览股票代码
                if stock_input:
                    from utils.batch_processor import get_batch_processor
                    processor = get_batch_processor()
                    symbols = processor.parse_stock_symbols(stock_input)
                    
                    if symbols:
                        st.success(f"✅ 已识别 {len(symbols)} 个股票代码")
                        if len(symbols) <= 10:
                            st.info(f"📋 代码列表: {', '.join(symbols)}")
                        else:
                            st.info(f"� 代码列表: {', '.join(symbols[:10])} ... (共{len(symbols)}个)")
                        
                        # 估算分析时间
                        estimated_time = len(symbols) * 12  # 每个股票约12分钟
                        st.warning(f"⏱️ 预估总耗时: {estimated_time // 60}小时{estimated_time % 60}分钟 (可并发分析，实际时间会短一些)")
                    else:
                        st.error("❌ 未识别到有效的股票代码")
                
                stock_symbol = stock_input  # 用于后续处理
                
            else:
                # 单个分析模式（原有逻辑）
                if market_type == "美股":
                    stock_symbol = st.text_input(
                        "股票代码 📈",
                        placeholder="输入美股代码，如 AAPL, TSLA, MSFT，然后按回车确认",
                        help="输入要分析的美股代码，输入完成后请按回车键确认",
                        key="us_stock_input",
                        autocomplete="off"
                    ).upper().strip()
                elif market_type == "港股":
                    stock_symbol = st.text_input(
                        "股票代码 📈",
                        placeholder="输入港股代码，如 0700.HK, 9988.HK, 3690.HK，然后按回车确认",
                        help="输入要分析的港股代码，如 0700.HK(腾讯控股), 9988.HK(阿里巴巴), 3690.HK(美团)，输入完成后请按回车键确认",
                        key="hk_stock_input",
                        autocomplete="off"
                    ).upper().strip()
                else:  # A股
                    stock_symbol = st.text_input(
                        "股票代码 📈",
                        placeholder="输入A股代码，如 000001, 600519，然后按回车确认",
                        help="输入要分析的A股代码，如 000001(平安银行), 600519(贵州茅台)，输入完成后请按回车键确认",
                        key="cn_stock_input",
                        autocomplete="off"
                    ).strip()

            logger.debug(f"🔍 [FORM DEBUG] {market_type}输入返回值: '{stock_symbol}'")
            
            # 分析日期
            analysis_date = st.date_input(
                "分析日期 📅",
                value=datetime.date.today(),
                help="选择分析的基准日期"
            )
        
        with col2:
            # 研究深度
            research_depth = st.select_slider(
                "研究深度 🔍",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {
                    1: "1级 - 快速分析",
                    2: "2级 - 基础分析",
                    3: "3级 - 标准分析",
                    4: "4级 - 深度分析",
                    5: "5级 - 全面分析"
                }[x],
                help="选择分析的深度级别，级别越高分析越详细但耗时更长"
            )
        
        # 分析师团队选择
        st.markdown("### 👥 选择分析师团队")
        
        col1, col2 = st.columns(2)
        
        with col1:
            market_analyst = st.checkbox(
                "📈 市场分析师",
                value=True,
                help="专注于技术面分析、价格趋势、技术指标"
            )
            
            social_analyst = st.checkbox(
                "💭 社交媒体分析师",
                value=False,
                help="分析社交媒体情绪、投资者情绪指标"
            )
        
        with col2:
            news_analyst = st.checkbox(
                "📰 新闻分析师",
                value=False,
                help="分析相关新闻事件、市场动态影响"
            )
            
            fundamentals_analyst = st.checkbox(
                "💰 基本面分析师",
                value=True,
                help="分析财务数据、公司基本面、估值水平"
            )
        
        # 收集选中的分析师
        selected_analysts = []
        if market_analyst:
            selected_analysts.append(("market", "市场分析师"))
        if social_analyst:
            selected_analysts.append(("social", "社交媒体分析师"))
        if news_analyst:
            selected_analysts.append(("news", "新闻分析师"))
        if fundamentals_analyst:
            selected_analysts.append(("fundamentals", "基本面分析师"))
        
        # 显示选择摘要
        if selected_analysts:
            st.success(f"已选择 {len(selected_analysts)} 个分析师: {', '.join([a[1] for a in selected_analysts])}")
        else:
            st.warning("请至少选择一个分析师")
        
        # 高级选项
        with st.expander("🔧 高级选项"):
            include_sentiment = st.checkbox(
                "包含情绪分析",
                value=True,
                help="是否包含市场情绪和投资者情绪分析"
            )
            
            include_risk_assessment = st.checkbox(
                "包含风险评估",
                value=True,
                help="是否包含详细的风险因素评估"
            )
            
            custom_prompt = st.text_area(
                "自定义分析要求",
                placeholder="输入特定的分析要求或关注点...",
                help="可以输入特定的分析要求，AI会在分析中重点关注"
            )

        # 显示输入状态提示
        if analysis_mode == "批量分析":
            if not stock_symbol:
                st.info("💡 请在上方输入多个股票代码，支持逗号、空格或换行分隔")
            else:
                from utils.batch_processor import get_batch_processor
                processor = get_batch_processor()
                symbols = processor.parse_stock_symbols(stock_symbol)
                if symbols:
                    st.success(f"✅ 准备分析 {len(symbols)} 个股票代码")
                else:
                    st.error("❌ 未识别到有效的股票代码")
        else:
            if not stock_symbol:
                st.info("💡 请在上方输入股票代码，输入完成后按回车键确认")
            else:
                st.success(f"✅ 已输入股票代码: {stock_symbol}")

        # 添加JavaScript来改善用户体验
        st.markdown("""
        <script>
        // 监听输入框的变化，提供更好的用户反馈
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input[type="text"], textarea');
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    if (this.value.trim()) {
                        this.style.borderColor = '#00ff00';
                        this.title = '输入已确认';
                    } else {
                        this.style.borderColor = '';
                        this.title = '';
                    }
                });
            });
        });
        </script>
        """, unsafe_allow_html=True)

        # 根据分析模式显示不同的提交按钮
        if analysis_mode == "批量分析":
            submitted = st.form_submit_button(
                "🚀 开始批量分析",
                type="primary",
                use_container_width=True,
                help="开始对所有输入的股票代码进行并发分析"
            )
        else:
            submitted = st.form_submit_button(
                "🚀 开始分析",
                type="primary",
                use_container_width=True
            )

    # 只有在提交时才返回数据
    if submitted and stock_symbol:  # 确保有股票代码才提交
        # 添加详细日志
        logger.debug(f"🔍 [FORM DEBUG] ===== 分析表单提交 =====")
        logger.debug(f"🔍 [FORM DEBUG] 分析模式: '{analysis_mode}'")
        logger.debug(f"🔍 [FORM DEBUG] 用户输入的股票代码: '{stock_symbol}'")
        logger.debug(f"🔍 [FORM DEBUG] 市场类型: '{market_type}'")
        logger.debug(f"🔍 [FORM DEBUG] 分析日期: '{analysis_date}'")
        logger.debug(f"🔍 [FORM DEBUG] 选择的分析师: {[a[0] for a in selected_analysts]}")
        logger.debug(f"🔍 [FORM DEBUG] 研究深度: {research_depth}")

        form_data = {
            'submitted': True,
            'analysis_mode': analysis_mode,
            'stock_symbol': stock_symbol,
            'market_type': market_type,
            'analysis_date': str(analysis_date),
            'analysts': [a[0] for a in selected_analysts],
            'research_depth': research_depth,
            'include_sentiment': include_sentiment,
            'include_risk_assessment': include_risk_assessment,
            'custom_prompt': custom_prompt
        }

        logger.debug(f"🔍 [FORM DEBUG] 返回的表单数据: {form_data}")
        logger.debug(f"🔍 [FORM DEBUG] ===== 表单提交结束 =====")

        return form_data
    elif submitted and not stock_symbol:
        # 用户点击了提交但没有输入股票代码
        logger.error(f"🔍 [FORM DEBUG] 提交失败：股票代码为空")
        st.error("❌ 请输入股票代码后再提交")
        return {'submitted': False}
    else:
        return {'submitted': False}
