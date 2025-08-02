"""
新闻相关性过滤器
基于AI的新闻相关性评分和多层次过滤机制
"""

import pandas as pd
import re
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import requests
import json

logger = logging.getLogger(__name__)

class NewsRelevanceFilter:
    """新闻相关性过滤器"""
    
    def __init__(self, stock_code: str, company_name: str):
        """
        初始化过滤器
        
        Args:
            stock_code: 股票代码
            company_name: 公司名称
        """
        self.stock_code = stock_code
        self.company_name = company_name
        
        # 强相关关键词（高权重）
        self.strong_keywords = [
            '业绩', '财报', '年报', '季报', '营收', '利润', '净利润', '收益',
            '股价', '涨停', '跌停', '涨幅', '跌幅', '成交量', '市值',
            '分红', '送股', '配股', '增发', '回购', '减持', '增持',
            '重组', '并购', '收购', '投资', '合作', '签约', '中标',
            '上市', '退市', '停牌', '复牌', '公告', '披露'
        ]
        
        # 一般相关关键词（中等权重）
        self.include_keywords = [
            '股票', '证券', '投资', '基金', '机构', '券商',
            '行业', '市场', '经济', '政策', '监管', '规划',
            '技术', '创新', '研发', '专利', '产品', '服务',
            '管理', '团队', '董事', '高管', '员工', '人事'
        ]
        
        # 排除关键词（负权重）
        self.exclude_keywords = [
            '娱乐', '体育', '游戏', '影视', '明星', '网红',
            '旅游', '美食', '时尚', '购物', '生活', '健康',
            '天气', '交通', '房产', '教育', '婚恋', '社交',
            '其他公司', '竞争对手', '无关', '广告', '推广'
        ]
        
        # 公司名称相关模式
        self.company_patterns = self._build_company_patterns()
        
        logger.info(f"[新闻过滤器] 初始化完成 - 股票代码: {stock_code}, 公司: {company_name}")
    
    def _build_company_patterns(self) -> List[str]:
        """构建公司名称相关的正则模式"""
        patterns = []
        
        # 基础公司名称
        if self.company_name:
            # 完整公司名称
            patterns.append(re.escape(self.company_name))
            
            # 去掉常见后缀的公司名称
            for suffix in ['股份有限公司', '有限公司', '集团', '控股', '科技', '实业']:
                short_name = self.company_name.replace(suffix, '')
                if len(short_name) >= 2:
                    patterns.append(re.escape(short_name))
        
        # 股票代码
        patterns.append(re.escape(self.stock_code))
        
        return patterns
    
    def calculate_relevance_score(self, title: str, content: str) -> Tuple[float, Dict]:
        """
        计算新闻相关性评分
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            Tuple[float, Dict]: (评分, 详细信息)
        """
        score = 0.0
        details = {
            'company_match': False,
            'strong_keywords': [],
            'include_keywords': [],
            'exclude_keywords': [],
            'title_score': 0.0,
            'content_score': 0.0
        }
        
        # 合并标题和内容进行分析
        full_text = f"{title} {content}"
        title_lower = title.lower() if title else ""
        content_lower = content.lower() if content else ""
        full_text_lower = full_text.lower()
        
        # 1. 公司名称和股票代码匹配（高权重）
        company_score = 0
        for pattern in self.company_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                company_score += 30
                details['company_match'] = True
                break
        
        # 标题中包含公司信息额外加分
        for pattern in self.company_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                company_score += 20
                break
        
        score += min(company_score, 50)  # 公司相关性最高50分
        
        # 2. 强相关关键词匹配
        strong_score = 0
        for keyword in self.strong_keywords:
            if keyword in full_text_lower:
                strong_score += 15
                details['strong_keywords'].append(keyword)
                
                # 标题中出现强关键词额外加分
                if keyword in title_lower:
                    strong_score += 10
        
        score += min(strong_score, 30)  # 强关键词最高30分
        
        # 3. 一般关键词匹配
        include_score = 0
        for keyword in self.include_keywords:
            if keyword in full_text_lower:
                include_score += 5
                details['include_keywords'].append(keyword)
        
        score += min(include_score, 15)  # 一般关键词最高15分
        
        # 4. 排除关键词惩罚
        exclude_penalty = 0
        for keyword in self.exclude_keywords:
            if keyword in full_text_lower:
                exclude_penalty += 10
                details['exclude_keywords'].append(keyword)
        
        score -= min(exclude_penalty, 20)  # 排除关键词最多扣20分
        
        # 5. 内容长度和质量评估
        if content:
            content_length = len(content)
            if content_length > 200:
                score += 5  # 内容丰富加分
            if content_length < 50:
                score -= 5  # 内容过短扣分
        
        # 6. 标题质量评估
        if title:
            # 标题包含数字（可能是财务数据）
            if re.search(r'\d+', title):
                score += 3
            
            # 标题长度适中
            if 10 <= len(title) <= 50:
                score += 2
        
        # 确保分数在0-100范围内
        score = max(0, min(score, 100))
        
        details['title_score'] = score * 0.7 if details['company_match'] else score * 0.3
        details['content_score'] = score * 0.3 if details['company_match'] else score * 0.7
        
        return score, details
    
    def filter_news(self, news_df: pd.DataFrame, min_score: float = 30) -> pd.DataFrame:
        """
        过滤新闻DataFrame
        
        Args:
            news_df: 新闻数据
            min_score: 最低评分阈值
            
        Returns:
            pd.DataFrame: 过滤后的新闻数据
        """
        if news_df.empty:
            logger.warning("[新闻过滤器] 输入的新闻数据为空")
            return news_df
        
        logger.info(f"[新闻过滤器] 开始过滤新闻，输入 {len(news_df)} 条，阈值: {min_score}")
        
        # 准备结果列表
        filtered_rows = []
        score_details = []
        
        for idx, row in news_df.iterrows():
            # 提取标题和内容
            title = str(row.get('新闻标题', '')) if pd.notna(row.get('新闻标题', '')) else ''
            content = str(row.get('新闻内容', '')) if pd.notna(row.get('新闻内容', '')) else ''
            
            # 计算相关性评分
            score, details = self.calculate_relevance_score(title, content)
            
            # 如果评分达到阈值，保留该条新闻
            if score >= min_score:
                # 创建新行，添加评分信息
                new_row = row.copy()
                new_row['relevance_score'] = score
                new_row['filter_details'] = json.dumps(details, ensure_ascii=False)
                new_row['final_score'] = score
                
                filtered_rows.append(new_row)
                score_details.append(details)
        
        # 创建过滤后的DataFrame
        if filtered_rows:
            filtered_df = pd.DataFrame(filtered_rows)
            
            # 按评分排序
            filtered_df = filtered_df.sort_values('final_score', ascending=False).reset_index(drop=True)
            
            logger.info(f"[新闻过滤器] 过滤完成，保留 {len(filtered_df)} 条新闻")
            
            if len(filtered_df) > 0:
                avg_score = filtered_df['final_score'].mean()
                max_score = filtered_df['final_score'].max()
                logger.info(f"[新闻过滤器] 平均评分: {avg_score:.1f}, 最高评分: {max_score:.1f}")
        else:
            filtered_df = pd.DataFrame()
            logger.warning(f"[新闻过滤器] 没有新闻达到评分阈值 {min_score}")
        
        return filtered_df
    
    def get_filter_statistics(self, original_df: pd.DataFrame, filtered_df: pd.DataFrame) -> Dict:
        """
        获取过滤统计信息
        
        Args:
            original_df: 原始新闻数据
            filtered_df: 过滤后新闻数据
            
        Returns:
            Dict: 统计信息
        """
        original_count = len(original_df)
        filtered_count = len(filtered_df)
        
        stats = {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': original_count - filtered_count,
            'filter_rate': (original_count - filtered_count) / original_count * 100 if original_count > 0 else 0,
            'retention_rate': filtered_count / original_count * 100 if original_count > 0 else 0
        }
        
        if filtered_count > 0 and 'final_score' in filtered_df.columns:
            stats.update({
                'avg_score': filtered_df['final_score'].mean(),
                'max_score': filtered_df['final_score'].max(),
                'min_score': filtered_df['final_score'].min(),
                'score_std': filtered_df['final_score'].std()
            })
        
        return stats


def get_company_name(stock_code: str) -> str:
    """
    根据股票代码获取公司名称
    
    Args:
        stock_code: 股票代码
        
    Returns:
        str: 公司名称
    """
    # 简化的公司名称映射（实际项目中可以从数据库或API获取）
    company_map = {
        '000001': '平安银行',
        '000002': '万科A',
        '600036': '招商银行',
        '600519': '贵州茅台',
        '000858': '五粮液',
        '600276': '恒瑞医药',
        # 可以继续添加更多映射...
    }
    
    # 清理股票代码
    clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.SS', '') \
                          .replace('.XSHE', '').replace('.XSHG', '')
    
    return company_map.get(clean_code, f"股票{clean_code}")


def create_news_filter(stock_code: str, company_name: str = None) -> NewsRelevanceFilter:
    """
    创建新闻相关性过滤器
    
    Args:
        stock_code: 股票代码
        company_name: 公司名称（可选）
        
    Returns:
        NewsRelevanceFilter: 新闻过滤器实例
    """
    if not company_name:
        company_name = get_company_name(stock_code)
    
    return NewsRelevanceFilter(stock_code, company_name)


if __name__ == "__main__":
    # 测试过滤器
    print("=== 测试新闻相关性过滤器 ===")
    
    # 创建测试过滤器
    filter_obj = create_news_filter("600036", "招商银行")
    
    # 测试评分功能
    test_cases = [
        ("招商银行发布三季度财报 净利润增长15%", "招商银行今日发布第三季度财务报告，净利润同比增长15%，营收表现超预期。"),
        ("A股市场整体表现良好", "今日A股市场整体上涨，银行股表现突出。"),
        ("娱乐新闻：某明星结婚", "某知名明星今日宣布结婚，引发网友热议。")
    ]
    
    for title, content in test_cases:
        score, details = filter_obj.calculate_relevance_score(title, content)
        print(f"\n标题: {title}")
        print(f"评分: {score:.1f}")
        print(f"详情: {details}")
