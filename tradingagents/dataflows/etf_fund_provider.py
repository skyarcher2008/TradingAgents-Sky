#!/usr/bin/env python3
"""
ETF基金数据获取模块
基于AKShare提供ETF专门的数据获取和分析功能
"""

import pandas as pd
from typing import Optional, Dict, Any, List
import warnings
from datetime import datetime, timedelta

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')

class ETFFundProvider:
    """ETF基金数据提供器"""

    def __init__(self):
        """初始化ETF基金提供器"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True
            logger.info(f"✅ ETF基金数据提供器初始化成功")
        except ImportError:
            self.ak = None
            self.connected = False
            logger.error(f"❌ AKShare未安装，ETF功能不可用")

    def is_etf_code(self, symbol: str) -> bool:
        """
        判断代码是否为ETF基金代码
        
        Args:
            symbol: 股票/基金代码
            
        Returns:
            bool: 是否为ETF基金代码
        """
        if not symbol or len(symbol) != 6 or not symbol.isdigit():
            return False
            
        # ETF基金代码规则
        etf_prefixes = [
            '159',  # 深交所ETF
            '510', '511', '512', '513', '514', '515', '516', '517', '518', '519',  # 上交所ETF
            '160', '161', '162', '163', '164', '165', '166', '167', '168', '169',  # LOF和其他ETF
            '180', '184',  # 债券ETF
            '150', '151',  # 分级基金
            '501', '502', '503', '504', '505', '506', '507', '508', '509',  # 场内基金
        ]
        
        return any(symbol.startswith(prefix) for prefix in etf_prefixes)

    def get_etf_list(self) -> Optional[pd.DataFrame]:
        """
        获取ETF基金列表
        
        Returns:
            DataFrame: ETF基金列表，包含代码、名称等信息
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取ETF列表")
            return None
            
        try:
            # 获取ETF实时行情数据，包含所有ETF
            etf_data = self.ak.fund_etf_spot_em()
            
            if etf_data is not None and len(etf_data) > 0:
                # 重命名列名为中文
                etf_list = etf_data[['代码', '名称']].copy()
                etf_list.columns = ['代码', '基金名称']
                
                logger.info(f"✅ 获取ETF列表成功: {len(etf_list)} 只ETF基金")
                return etf_list
            else:
                logger.error(f"❌ ETF列表数据为空")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取ETF列表失败: {e}")
            return None

    def get_etf_realtime_data(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """
        获取ETF实时行情数据
        
        Args:
            symbol: ETF代码，如果为None则获取所有ETF
            
        Returns:
            DataFrame: ETF实时行情数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取ETF实时数据")
            return None
            
        try:
            # 获取所有ETF实时数据
            etf_data = self.ak.fund_etf_spot_em()
            
            if etf_data is not None and len(etf_data) > 0:
                if symbol:
                    # 过滤特定ETF
                    etf_data = etf_data[etf_data['代码'] == symbol]
                    if len(etf_data) == 0:
                        logger.warning(f"⚠️ 未找到ETF代码: {symbol}")
                        return None
                        
                logger.info(f"✅ 获取ETF实时数据成功: {len(etf_data)} 条记录")
                return etf_data
            else:
                logger.error(f"❌ ETF实时数据为空")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取ETF实时数据失败: {e}")
            return None

    def get_etf_history_data(self, symbol: str, 
                           start_date: str = None, 
                           end_date: str = None,
                           period: str = "daily") -> Optional[pd.DataFrame]:
        """
        获取ETF历史数据
        
        Args:
            symbol: ETF代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 数据周期 ('daily', 'weekly', 'monthly')
            
        Returns:
            DataFrame: ETF历史数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取ETF历史数据")
            return None
            
        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
        try:
            # 获取ETF历史数据
            hist_data = self.ak.fund_etf_hist_em(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            if hist_data is not None and len(hist_data) > 0:
                logger.info(f"✅ 获取ETF历史数据成功: {symbol}, {len(hist_data)} 条记录")
                return hist_data
            else:
                logger.warning(f"⚠️ ETF历史数据为空: {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取ETF历史数据失败: {symbol}, {e}")
            return None

    def get_etf_basic_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取ETF基本信息
        
        Args:
            symbol: ETF代码
            
        Returns:
            dict: ETF基本信息
        """
        if not self.connected:
            return {}
            
        try:
            # 从实时数据中获取基本信息
            realtime_data = self.get_etf_realtime_data(symbol)
            
            if realtime_data is not None and len(realtime_data) > 0:
                row = realtime_data.iloc[0]
                
                basic_info = {
                    '基金代码': row.get('代码', symbol),
                    '基金名称': row.get('名称', ''),
                    '最新价格': row.get('最新价', 0),
                    '涨跌幅': row.get('涨跌幅', 0),
                    '涨跌额': row.get('涨跌额', 0),
                    '成交量': row.get('成交量', 0),
                    '成交额': row.get('成交额', 0),
                    '换手率': row.get('换手率', 0),
                    '市净率': row.get('市净率', 0),
                    '数据时间': row.get('数据日期', ''),
                }
                
                logger.info(f"✅ 获取ETF基本信息成功: {symbol}")
                return basic_info
            else:
                logger.warning(f"⚠️ 未找到ETF基本信息: {symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ 获取ETF基本信息失败: {symbol}, {e}")
            return {}

    def search_etf_by_name(self, keyword: str) -> List[Dict[str, str]]:
        """
        根据名称关键词搜索ETF
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            list: 匹配的ETF列表
        """
        if not self.connected:
            return []
            
        try:
            etf_list = self.get_etf_list()
            
            if etf_list is not None:
                # 模糊搜索
                matches = etf_list[etf_list['基金名称'].str.contains(keyword, na=False)]
                
                result = []
                for _, row in matches.iterrows():
                    result.append({
                        '代码': row['代码'],
                        '名称': row['基金名称']
                    })
                    
                logger.info(f"✅ ETF搜索完成: 关键词'{keyword}', 找到{len(result)}个结果")
                return result
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ ETF搜索失败: {keyword}, {e}")
            return []

    def format_etf_analysis_report(self, symbol: str) -> str:
        """
        生成ETF分析报告
        
        Args:
            symbol: ETF代码
            
        Returns:
            str: 格式化的ETF分析报告
        """
        if not self.connected:
            return f"❌ AKShare未连接，无法分析ETF {symbol}"
            
        try:
            # 获取基本信息
            basic_info = self.get_etf_basic_info(symbol)
            if not basic_info:
                return f"❌ 无法获取ETF {symbol} 的基本信息"
                
            # 获取历史数据
            hist_data = self.get_etf_history_data(symbol, period="daily")
            
            # 生成报告
            report = f"""
## ETF基金分析报告

### 📊 基本信息
- **基金代码**: {basic_info.get('基金代码', symbol)}
- **基金名称**: {basic_info.get('基金名称', '未知')}
- **最新价格**: ¥{basic_info.get('最新价格', 0):.3f}
- **涨跌幅**: {basic_info.get('涨跌幅', 0):.2f}%
- **涨跌额**: ¥{basic_info.get('涨跌额', 0):.3f}

### 📈 交易数据
- **成交量**: {basic_info.get('成交量', 0):,} 手
- **成交额**: ¥{basic_info.get('成交额', 0):,.0f}
- **换手率**: {basic_info.get('换手率', 0):.2f}%
- **市净率**: {basic_info.get('市净率', 0):.2f}

### 📅 数据时间
- **最后更新**: {basic_info.get('数据时间', '未知')}
"""

            # 添加历史数据统计
            if hist_data is not None and len(hist_data) > 0:
                recent_data = hist_data.tail(30)  # 最近30天
                
                if '收盘' in recent_data.columns:
                    price_change_30d = ((recent_data['收盘'].iloc[-1] / recent_data['收盘'].iloc[0]) - 1) * 100
                    max_price_30d = recent_data['收盘'].max()
                    min_price_30d = recent_data['收盘'].min()
                    avg_volume_30d = recent_data.get('成交量', pd.Series([0])).mean()
                    
                    report += f"""
### 📊 近30日表现
- **30日涨跌幅**: {price_change_30d:.2f}%
- **30日最高价**: ¥{max_price_30d:.3f}
- **30日最低价**: ¥{min_price_30d:.3f}
- **30日平均成交量**: {avg_volume_30d:,.0f} 手
"""

            report += f"""
### ⚠️ 风险提示
- ETF基金存在跟踪误差风险
- 基金净值会根据标的指数波动
- 投资有风险，入市需谨慎
- 本分析仅供参考，不构成投资建议

---
*数据来源: AKShare*
*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            logger.info(f"✅ ETF分析报告生成成功: {symbol}")
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成ETF分析报告失败: {symbol}, {e}")
            return f"❌ 生成ETF {symbol} 分析报告时出错: {e}"

def get_etf_data_unified(symbol: str, start_date: str = None, end_date: str = None) -> str:
    """
    统一的ETF数据获取接口
    
    Args:
        symbol: ETF代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        str: 格式化的ETF数据报告
    """
    provider = ETFFundProvider()
    
    if not provider.connected:
        return f"❌ ETF数据服务不可用，请确保已安装AKShare"
    
    # 验证是否为ETF代码
    if not provider.is_etf_code(symbol):
        return f"⚠️ {symbol} 不是有效的ETF基金代码"
    
    # 生成完整报告
    return provider.format_etf_analysis_report(symbol)

# 便捷函数
def search_etf(keyword: str) -> List[Dict[str, str]]:
    """搜索ETF基金"""
    provider = ETFFundProvider()
    return provider.search_etf_by_name(keyword)

def is_etf_fund_code(symbol: str) -> bool:
    """判断是否为ETF基金代码"""
    provider = ETFFundProvider()
    return provider.is_etf_code(symbol)
