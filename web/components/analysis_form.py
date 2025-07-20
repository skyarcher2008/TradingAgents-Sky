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

            # 根据市场类型显示不同的输入提示
            if market_type == "美股":
                # 不设置默认值，让用户自己输入
                stock_symbol = st.text_input(
                    "股票代码 📈",
                    placeholder="输入美股代码，如 AAPL, TSLA, MSFT，然后按回车确认",
                    help="输入要分析的美股代码，输入完成后请按回车键确认",
                    key="us_stock_input",
                    autocomplete="off"  # 修复autocomplete警告
                ).upper().strip()

                logger.debug(f"🔍 [FORM DEBUG] 美股text_input返回值: '{stock_symbol}'")

            elif market_type == "港股":
                # 应用与美股相同的修复：移除默认值，添加回车提示
                stock_symbol = st.text_input(
                    "股票代码 📈",
                    placeholder="输入港股代码，如 0700.HK, 9988.HK, 3690.HK，然后按回车确认",
                    help="输入要分析的港股代码，如 0700.HK(腾讯控股), 9988.HK(阿里巴巴), 3690.HK(美团)，输入完成后请按回车键确认",
                    key="hk_stock_input",
                    autocomplete="off"  # 修复autocomplete警告
                ).upper().strip()

                logger.debug(f"🔍 [FORM DEBUG] 港股text_input返回值: '{stock_symbol}'")

            else:  # A股
                stock_symbol = st.text_input(
                    "股票代码 📈",
                    placeholder="输入A股代码，如 000001, 600519，然后按回车确认",
                    help="输入要分析的A股代码，如 000001(平安银行), 600519(贵州茅台)，输入完成后请按回车键确认",
                    key="cn_stock_input",
                    autocomplete="off"  # 修复autocomplete警告
                ).strip()

                logger.debug(f"🔍 [FORM DEBUG] A股text_input返回值: '{stock_symbol}'")
            
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
        if not stock_symbol:
            st.info("💡 请在上方输入股票代码，输入完成后按回车键确认")
        else:
            st.success(f"✅ 已输入股票代码: {stock_symbol}")

        # 添加JavaScript来改善用户体验
        st.markdown("""
        <script>
        // 监听输入框的变化，提供更好的用户反馈
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input[type="text"]');
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    if (this.value.trim()) {
                        this.style.borderColor = '#00ff00';
                        this.title = '按回车键确认输入';
                    } else {
                        this.style.borderColor = '';
                        this.title = '';
                    }
                });
            });
        });
        </script>
        """, unsafe_allow_html=True)

        # 提交按钮（不禁用，让用户可以点击）
        submitted = st.form_submit_button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )

    # 只有在提交时才返回数据
    if submitted and stock_symbol:  # 确保有股票代码才提交
        # 添加详细日志
        logger.debug(f"🔍 [FORM DEBUG] ===== 分析表单提交 =====")
        logger.debug(f"🔍 [FORM DEBUG] 用户输入的股票代码: '{stock_symbol}'")
        logger.debug(f"🔍 [FORM DEBUG] 市场类型: '{market_type}'")
        logger.debug(f"🔍 [FORM DEBUG] 分析日期: '{analysis_date}'")
        logger.debug(f"🔍 [FORM DEBUG] 选择的分析师: {[a[0] for a in selected_analysts]}")
        logger.debug(f"🔍 [FORM DEBUG] 研究深度: {research_depth}")

        form_data = {
            'submitted': True,
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
