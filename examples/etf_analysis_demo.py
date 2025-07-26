#!/usr/bin/env python3
"""
ETF基金分析演示

演示如何使用TradingAgents-CN项目进行ETF基金分析
"""

import os
import sys

# 添加项目根目录到路径，避免导入冲突
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def demo_etf_analysis():
    """演示ETF分析功能"""
    print("🎯 TradingAgents-CN ETF基金分析演示\n")
    
    # 热门ETF代码
    popular_etfs = {
        "510050": "50ETF",
        "510300": "沪深300ETF", 
        "159919": "300ETF嘉实",
        "512000": "券商ETF",
        "515050": "5G ETF",
        "513100": "纳斯达克100"
    }
    
    try:
        from tradingagents.dataflows.interface import get_stock_data_by_market
        
        for etf_code, etf_name in popular_etfs.items():
            print(f"📊 分析 {etf_code} ({etf_name})")
            print("=" * 50)
            
            try:
                # 获取ETF数据
                etf_data = get_stock_data_by_market(etf_code, "2025-01-01", "2025-01-20")
                
                # 显示数据概况
                if etf_data and "❌" not in etf_data:
                    data_length = len(etf_data)
                    print(f"✅ 数据获取成功: {data_length} 字符")
                    
                    # 显示数据片段（前500字符）
                    preview = etf_data[:500] + "..." if len(etf_data) > 500 else etf_data
                    print(f"📋 数据预览:\n{preview}")
                else:
                    print(f"❌ {etf_code} 数据获取失败")
                    
            except Exception as e:
                print(f"❌ {etf_code} 分析异常: {e}")
            
            print("\n" + "=" * 50 + "\n")
            
        print("✅ ETF分析演示完成！")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保项目环境已正确配置")

if __name__ == "__main__":
    demo_etf_analysis()
