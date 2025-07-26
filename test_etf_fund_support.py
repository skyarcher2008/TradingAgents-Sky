#!/usr/bin/env python3
"""
测试当前项目对ETF基金代码的支持
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_etf_code_recognition():
    """测试ETF代码识别"""
    print("🧪 测试ETF基金代码识别...")
    
    # 常见ETF基金代码
    etf_codes = [
        "159919",  # 沪深300ETF
        "159915",  # 创业板ETF
        "510050",  # 上证50ETF
        "510300",  # 沪深300ETF
        "159001",  # 易方达创业板ETF
        "513100",  # 纳斯达克100ETF
        "515050",  # 5G ETF
        "512000",  # 军工ETF
        "512890",  # 红利ETF (用户提到的代码)
        "161720",  # 招商沪深300ETF联接A (LOF)
        "000478",  # 建信中证500指数增强A
    ]
    
    try:
        from tradingagents.utils.stock_utils import StockUtils
        
        for code in etf_codes:
            market_info = StockUtils.get_market_info(code)
            print(f"  {code}: {market_info}")
            
    except Exception as e:
        print(f"❌ StockUtils测试失败: {e}")
        
    # 测试AKShare识别
    try:
        from tradingagents.dataflows.akshare_utils import AKShareProvider
        provider = AKShareProvider()
        
        for code in etf_codes:
            is_valid = provider._validate_stock_code(code)
            print(f"  AKShare验证 {code}: {'✅ 有效' if is_valid else '❌ 无效'}")
            
    except Exception as e:
        print(f"❌ AKShare验证测试失败: {e}")

def test_akshare_etf_apis():
    """测试AKShare ETF相关API"""
    print("\n🧪 测试AKShare ETF数据获取...")
    
    try:
        import akshare as ak
        
        # 测试ETF实时行情
        print("  📊 测试ETF实时行情...")
        etf_data = ak.fund_etf_spot_em()
        if etf_data is not None and len(etf_data) > 0:
            print(f"    ✅ 获取到 {len(etf_data)} 只ETF基金")
            print(f"    前5只ETF: {etf_data.head()['名称'].tolist()}")
        else:
            print("    ❌ ETF实时行情获取失败")
            
        # 测试单只ETF历史数据
        print("  📈 测试单只ETF历史数据...")
        hist_data = ak.fund_etf_hist_em(
            symbol="159919", 
            period="daily", 
            start_date="20241201", 
            end_date="20241220"
        )
        if hist_data is not None and len(hist_data) > 0:
            print(f"    ✅ 获取到159919历史数据: {len(hist_data)} 条")
        else:
            print("    ❌ ETF历史数据获取失败")
            
        # 测试基金列表
        print("  📋 测试基金名称列表...")
        fund_names = ak.fund_name_em()
        if fund_names is not None and len(fund_names) > 0:
            print(f"    ✅ 获取到基金列表: {len(fund_names)} 只")
            # 查找ETF相关基金
            etf_funds = fund_names[fund_names['基金简称'].str.contains('ETF', na=False)]
            print(f"    ETF基金数量: {len(etf_funds)} 只")
        else:
            print("    ❌ 基金列表获取失败")
            
    except Exception as e:
        print(f"❌ AKShare ETF API测试失败: {e}")

def test_specific_etf_code():
    """测试特定ETF代码512890的识别"""
    print("\n🧪 测试特定ETF代码512890...")
    
    code = "512890"
    
    try:
        # 测试ETF识别函数
        from tradingagents.dataflows.etf_fund_provider import is_etf_fund_code
        is_etf = is_etf_fund_code(code)
        print(f"  ETF识别结果: {code} -> {'✅ 是ETF' if is_etf else '❌ 不是ETF'}")
        
        # 测试AKShare ETF验证
        from tradingagents.dataflows.akshare_utils import AKShareProvider
        provider = AKShareProvider()
        is_valid_akshare = provider._validate_stock_code(code)
        print(f"  AKShare验证: {code} -> {'✅ 有效' if is_valid_akshare else '❌ 无效'}")
        
        # 测试实际数据获取
        from tradingagents.dataflows.interface import get_stock_data_by_market
        print(f"  尝试获取 {code} 数据...")
        data = get_stock_data_by_market(code, "2025-01-01", "2025-01-20")
        if data and "❌" not in data:
            print(f"    ✅ {code} 数据获取成功: {len(data)} 字符")
            # 显示前200字符
            preview = data[:200] + "..." if len(data) > 200 else data
            print(f"    📋 数据预览: {preview}")
        else:
            print(f"    ❌ {code} 数据获取失败: {data}")
            
    except Exception as e:
        print(f"❌ 测试512890失败: {e}")

def test_project_etf_integration():
    """测试项目ETF集成"""
    print("\n🧪 测试项目ETF集成...")
    
    # 测试项目是否支持ETF代码分析
    test_etf_codes = ["159919", "510050", "512000", "512890"]
    
    try:
        from tradingagents.dataflows.interface import get_stock_data_by_market
        
        for code in test_etf_codes:
            print(f"  测试 {code} 数据获取...")
            try:
                data = get_stock_data_by_market(code)
                if data and "❌" not in data:
                    print(f"    ✅ {code} 数据获取成功")
                else:
                    print(f"    ❌ {code} 数据获取失败")
            except Exception as e:
                print(f"    ❌ {code} 数据获取异常: {e}")
                
    except Exception as e:
        print(f"❌ 项目ETF集成测试失败: {e}")

def suggest_etf_improvements():
    """建议ETF功能改进"""
    print("\n💡 ETF功能改进建议:")
    print("1. 📊 集成AKShare ETF专用API")
    print("   - fund_etf_spot_em(): ETF实时行情")
    print("   - fund_etf_hist_em(): ETF历史数据")
    print("   - fund_etf_category_sina(): ETF分类数据")
    
    print("\n2. 🔍 增强ETF代码识别")
    print("   - 支持15xxxx系列ETF代码")
    print("   - 支持51xxxx系列ETF代码")
    print("   - 支持LOF基金代码")
    
    print("\n3. 📈 ETF专门分析")
    print("   - ETF跟踪误差分析")
    print("   - ETF申赎数据分析")
    print("   - ETF折溢价分析")
    print("   - ETF成分股分析")
    
    print("\n4. 🤖 智能体专门功能")
    print("   - ETF基本面分析师")
    print("   - ETF跟踪指数分析")
    print("   - ETF费率对比分析")

if __name__ == "__main__":
    print("🎯 测试TradingAgents-CN项目对ETF基金代码的支持\n")
    
    test_etf_code_recognition()
    test_specific_etf_code()
    test_akshare_etf_apis()
    test_project_etf_integration()
    suggest_etf_improvements()
    
    print("\n✅ 测试完成")
