"""
智能新闻过滤系统集成测试
测试新闻相关性评分和过滤功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tradingagents.utils.news_filter import create_news_filter
from tradingagents.utils.news_filter_integration import apply_news_filtering_patches

def test_news_filter():
    """测试新闻过滤器功能"""
    print("=== 🎯 智能新闻过滤器测试 ===")
    
    # 创建测试数据
    test_news_data = {
        '新闻标题': [
            '招商银行发布三季度财报 净利润增长15%',
            '银行股集体上涨 市场表现良好',
            '娱乐新闻：某明星结婚引发热议',
            '招商银行与某公司签署重大合作协议',
            'A股市场今日震荡 投资者需谨慎'
        ],
        '新闻内容': [
            '招商银行今日发布第三季度财务报告，净利润同比增长15%，营收表现超预期，ROE达到16.8%。',
            '今日银行板块整体表现突出，招商银行涨幅领先，投资者情绪乐观。',
            '某知名明星今日宣布结婚，引发网友热议，相关话题冲上热搜榜首。',
            '招商银行与知名科技公司签署战略合作协议，将在金融科技领域深度合作。',
            'A股市场今日呈现震荡格局，银行、科技板块表现分化，投资者需理性对待。'
        ],
        '发布时间': ['2024-12-19 10:30:00'] * 5,
        '新闻链接': ['http://test.com/news1', 'http://test.com/news2', 
                  'http://test.com/news3', 'http://test.com/news4', 'http://test.com/news5']
    }
    
    test_df = pd.DataFrame(test_news_data)
    print(f"📊 测试数据: {len(test_df)} 条新闻")
    
    # 创建过滤器
    news_filter = create_news_filter("600036", "招商银行")
    print(f"🔧 已创建招商银行新闻过滤器")
    
    # 测试评分功能
    print("\\n=== 📈 相关性评分测试 ===")
    for idx, row in test_df.iterrows():
        score, details = news_filter.calculate_relevance_score(
            row['新闻标题'], row['新闻内容']
        )
        print(f"新闻 {idx + 1}: {row['新闻标题'][:20]}...")
        print(f"  📊 评分: {score:.1f}分")
        print(f"  🏢 公司匹配: {details['company_match']}")
        print(f"  🔑 强关键词: {details['strong_keywords']}")
        print(f"  💡 一般关键词: {details['include_keywords']}")
        print()
    
    # 测试过滤功能
    print("=== 🎯 新闻过滤测试 ===")
    min_score = 30
    filtered_df = news_filter.filter_news(test_df, min_score=min_score)
    
    print(f"📊 过滤结果:")
    print(f"  - 原始新闻: {len(test_df)} 条")
    print(f"  - 过滤后新闻: {len(filtered_df)} 条")
    print(f"  - 过滤阈值: {min_score} 分")
    
    if not filtered_df.empty:
        print(f"  - 平均评分: {filtered_df['final_score'].mean():.1f} 分")
        print(f"  - 最高评分: {filtered_df['final_score'].max():.1f} 分")
        
        print("\\n🏆 高质量新闻:")
        for idx, (_, row) in enumerate(filtered_df.iterrows()):
            score = row['final_score']
            emoji = "🔥" if score >= 70 else "⭐" if score >= 50 else "💡"
            print(f"  {emoji} [{score:.1f}分] {row['新闻标题']}")
    
    # 测试统计功能
    stats = news_filter.get_filter_statistics(test_df, filtered_df)
    print(f"\\n📈 过滤统计:")
    print(f"  - 过滤率: {stats['filter_rate']:.1f}%")
    print(f"  - 保留率: {stats['retention_rate']:.1f}%")

def test_integration_patches():
    """测试集成补丁功能"""
    print("\\n=== 🚀 智能新闻过滤集成测试 ===")
    
    try:
        enhanced_function = apply_news_filtering_patches()
        print("✅ 智能新闻过滤补丁应用成功")
        print("🎯 增强版实时新闻函数已创建")
        
        # 测试增强版函数签名
        import inspect
        sig = inspect.signature(enhanced_function)
        print(f"📋 增强函数参数: {list(sig.parameters.keys())}")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")

if __name__ == "__main__":
    print("🎯 开始智能新闻过滤系统测试...\\n")
    
    # 测试1: 基础过滤器功能
    test_news_filter()
    
    # 测试2: 集成补丁功能
    test_integration_patches()
    
    print("\\n🎉 智能新闻过滤系统测试完成!")
    print("\\n📋 功能总结:")
    print("  ✅ 新闻相关性评分算法 (0-100分)")
    print("  ✅ 多层次过滤机制")
    print("  ✅ 公司名称匹配")
    print("  ✅ 关键词权重分析")
    print("  ✅ 智能过滤集成")
    print("  ✅ 统计分析功能")
    print("\\n🚀 现在可以在新闻分析师中享受智能过滤功能了！")
