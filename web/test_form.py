"""
简化的表单测试页面，用于调试"True"显示问题
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="表单测试",
    page_icon="🧪",
    layout="wide"
)

def simple_form():
    """简化的表单"""
    st.subheader("🧪 简化表单测试")
    
    with st.form("test_form"):
        # 市场选择
        market_type = st.selectbox(
            "选择市场",
            options=["美股", "A股", "港股"],
            index=2  # 默认选择港股
        )
        
        # 股票代码
        if market_type == "港股":
            stock_symbol = st.text_input(
                "股票代码",
                value="0700.HK",
                placeholder="输入港股代码，如 0700.HK"
            ).upper().strip()
        elif market_type == "A股":
            stock_symbol = st.text_input(
                "股票代码", 
                value="000001",
                placeholder="输入A股代码，如 000001"
            ).strip()
        else:
            stock_symbol = st.text_input(
                "股票代码",
                value="AAPL", 
                placeholder="输入美股代码，如 AAPL"
            ).upper().strip()
        
        # 提交按钮
        submitted = st.form_submit_button("🚀 测试提交")
    
    # 返回表单数据
    if submitted:
        return {
            'submitted': True,
            'market_type': market_type,
            'stock_symbol': stock_symbol
        }
    else:
        return {'submitted': False}

def main():
    """主函数"""
    st.title("🧪 表单测试页面")
    st.markdown("用于调试Web界面显示'True'的问题")
    
    # 显示当前状态
    st.info("当前测试：检查表单提交是否会意外显示'True'")
    
    # 渲染表单
    st.markdown("### 📋 测试表单")
    form_data = simple_form()
    
    # 显示表单数据（受控显示）
    st.markdown("### 📊 表单数据")
    
    if form_data.get('submitted', False):
        st.success("✅ 表单已提交")
        
        with st.expander("📋 表单数据详情"):
            st.json(form_data)
        
        # 测试验证功能
        st.markdown("### 🔍 验证测试")
        
        try:
            from web.utils.analysis_runner import validate_analysis_params
            
            errors = validate_analysis_params(
                stock_symbol=form_data['stock_symbol'],
                analysis_date="2025-07-14",
                analysts=["market"],
                research_depth=3,
                market_type=form_data['market_type']
            )
            
            if errors:
                st.error(f"验证失败: {errors}")
            else:
                st.success("✅ 验证通过")
                
        except Exception as e:
            st.error(f"验证异常: {e}")
    
    else:
        st.info("等待表单提交...")
    
    # 调试信息
    st.markdown("### 🐛 调试信息")
    
    with st.expander("🔍 调试详情"):
        st.write("表单数据类型:", type(form_data))
        st.write("表单数据内容:", form_data)
        
        # 检查是否有意外的输出
        if isinstance(form_data, bool):
            st.error("⚠️ 检测到布尔值返回，这可能是问题所在！")
        elif form_data is None:
            st.warning("⚠️ 表单数据为None")
        elif not isinstance(form_data, dict):
            st.error(f"⚠️ 表单数据类型异常: {type(form_data)}")
        else:
            st.success("✅ 表单数据类型正常")

if __name__ == "__main__":
    main()
