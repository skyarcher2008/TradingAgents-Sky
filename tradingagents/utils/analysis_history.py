#!/usr/bin/env python3
"""
分析历史记录管理器
负责保存、查询和管理股票分析历史记录
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid

@dataclass
class AnalysisRecord:
    """分析记录数据类"""
    record_id: str
    session_id: str
    stock_symbol: str
    analysis_date: str
    market_type: str
    analysts: List[str]
    research_depth: str
    llm_provider: str
    llm_model: str
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    created_at: datetime
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
    total_cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 转换datetime对象为ISO格式字符串
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisRecord':
        """从字典创建实例"""
        # 转换时间字符串为datetime对象
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class AnalysisHistoryManager:
    """分析历史记录管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.collection_name = "analysis_history"
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化数据库连接"""
        # 初始化默认值
        self.collection = None
        self.mongodb_client = None
        self.mongodb_db = None
        self.redis_client = None
        self._use_file_storage = False
        
        try:
            from tradingagents.config.database_manager import get_database_manager
            db_manager = get_database_manager()
            
            if db_manager.mongodb_available:
                self.mongodb_client = db_manager.mongodb_client
                self.mongodb_db = self.mongodb_client[db_manager.mongodb_config["database"]]
                self.collection = self.mongodb_db[self.collection_name]
                
                # 创建索引
                self._create_indexes()
                self.logger.info("✅ MongoDB历史记录管理器初始化成功")
            
            if db_manager.redis_available:
                self.redis_client = db_manager.redis_client
                self.logger.info("✅ Redis历史记录缓存初始化成功")
                
        except Exception as e:
            self.logger.warning(f"⚠️ 数据库连接失败，使用文件存储: {e}")
            # 确保使用文件存储
            self.collection = None
            self.mongodb_client = None
            self.mongodb_db = None
            self.redis_client = None
            self._use_file_storage = True
    
    def _create_indexes(self):
        """创建MongoDB索引"""
        if self.collection is not None:
            try:
                # 创建复合索引
                self.collection.create_index([
                    ("stock_symbol", 1),
                    ("created_at", -1)
                ])
                # 创建单字段索引
                self.collection.create_index([("created_at", -1)])
                self.collection.create_index([("success", 1)])
                self.collection.create_index([("llm_provider", 1)])
                self.logger.info("✅ 历史记录索引创建完成")
            except Exception as e:
                self.logger.warning(f"⚠️ 索引创建失败: {e}")
    
    def save_analysis_record(self, 
                           session_id: str,
                           stock_symbol: str,
                           analysis_date: str,
                           market_type: str,
                           analysts: List[str],
                           research_depth: str,
                           llm_provider: str,
                           llm_model: str,
                           start_time: datetime,
                           end_time: datetime,
                           duration: float,
                           success: bool,
                           results: Optional[Dict[str, Any]] = None,
                           error_message: Optional[str] = None,
                           token_usage: Optional[Dict[str, Any]] = None,
                           total_cost: float = 0.0) -> str:
        """保存分析记录"""
        
        try:
            # 创建记录ID
            record_id = str(uuid.uuid4())
            
            # 创建记录对象
            record = AnalysisRecord(
                record_id=record_id,
                session_id=session_id,
                stock_symbol=stock_symbol.upper(),
                analysis_date=analysis_date,
                market_type=market_type,
                analysts=analysts,
                research_depth=research_depth,
                llm_provider=llm_provider,
                llm_model=llm_model,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                created_at=datetime.now(),
                results=results,
                error_message=error_message,
                token_usage=token_usage,
                total_cost=total_cost
            )
            
            if hasattr(self, 'collection') and self.collection is not None:
                # 保存到MongoDB
                self.collection.insert_one(record.to_dict())
                self.logger.info(f"✅ 分析记录已保存到MongoDB: {record_id}")
            else:
                # 保存到文件
                self._save_to_file(record)
                self.logger.info(f"✅ 分析记录已保存到文件: {record_id}")
            
            # 缓存到Redis（如果可用）
            if hasattr(self, 'redis_client') and self.redis_client is not None:
                self._cache_to_redis(record)
                
            return record_id
            
        except Exception as e:
            self.logger.error(f"❌ 保存分析记录失败: {e}")
            # 降级到文件存储
            try:
                self._save_to_file(record)
                return record_id
            except:
                return record_id
    
    def _save_to_file(self, record: AnalysisRecord):
        """保存记录到文件"""
        import os
        from pathlib import Path
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        
        # 确保目录存在
        history_dir = project_root / "data" / "analysis_history"
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # 按日期组织文件
        date_str = record.created_at.strftime("%Y-%m-%d")
        file_path = history_dir / f"analysis_{date_str}.jsonl"
        
        # 追加记录到文件
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
    
    def _cache_to_redis(self, record: AnalysisRecord):
        """缓存记录到Redis"""
        try:
            # 缓存最近的记录，设置过期时间为7天
            key = f"analysis_history:{record.record_id}"
            self.redis_client.setex(
                key, 
                int(timedelta(days=7).total_seconds()),
                json.dumps(record.to_dict(), ensure_ascii=False)
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Redis缓存失败: {e}")
    
    def get_analysis_history(self, 
                           stock_symbol: Optional[str] = None,
                           limit: int = 50,
                           offset: int = 0,
                           success_only: bool = False,
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取分析历史记录"""
        
        try:
            if hasattr(self, 'collection') and self.collection is not None:
                return self._get_from_mongodb(stock_symbol, limit, offset, success_only, date_from, date_to)
            else:
                return self._get_from_files(stock_symbol, limit, offset, success_only, date_from, date_to)
        except Exception as e:
            self.logger.error(f"❌ 获取历史记录失败: {e}")
            return []
    
    def _get_from_mongodb(self, stock_symbol, limit, offset, success_only, date_from, date_to):
        """从MongoDB获取记录"""
        if self.collection is None:
            return []
            
        query = {}
        
        # 构建查询条件
        if stock_symbol:
            query["stock_symbol"] = stock_symbol.upper()
        
        if success_only:
            query["success"] = True
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            if date_query:
                query["created_at"] = date_query
        
        # 执行查询
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        records = list(cursor)
        
        # 移除MongoDB的_id字段
        for record in records:
            if '_id' in record:
                del record['_id']
        
        return records
    
    def _get_from_files(self, stock_symbol, limit, offset, success_only, date_from, date_to):
        """从文件获取记录"""
        import os
        from pathlib import Path
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        history_dir = project_root / "data" / "analysis_history"
        
        if not history_dir.exists():
            return []
        
        records = []
        
        # 读取所有历史文件，按日期倒序
        for file_path in sorted(history_dir.glob("analysis_*.jsonl"), reverse=True):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line.strip())
                            
                            # 应用过滤条件
                            if stock_symbol and record.get("stock_symbol", "").upper() != stock_symbol.upper():
                                continue
                            
                            if success_only and not record.get("success", False):
                                continue
                            
                            # 日期过滤
                            created_at = datetime.fromisoformat(record["created_at"])
                            if date_from and created_at < date_from:
                                continue
                            if date_to and created_at > date_to:
                                continue
                            
                            records.append(record)
                            
                            # 检查是否已达到限制
                            if len(records) >= limit + offset:
                                break
                
                # 如果已达到限制，停止读取更多文件
                if len(records) >= limit + offset:
                    break
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 读取历史文件失败: {file_path}: {e}")
                continue
        
        # 应用偏移和限制
        return records[offset:offset + limit]
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        try:
            if hasattr(self, 'collection') and self.collection is not None:
                return self._get_stats_from_mongodb()
            else:
                return self._get_stats_from_files()
        except Exception as e:
            self.logger.error(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def _get_stats_from_mongodb(self):
        """从MongoDB获取统计信息"""
        if self.collection is None:
            return {}
            
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_analyses": {"$sum": 1},
                    "successful_analyses": {
                        "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                    },
                    "total_cost": {"$sum": "$total_cost"},
                    "avg_duration": {"$avg": "$duration"},
                    "unique_stocks": {"$addToSet": "$stock_symbol"}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            stats["unique_stocks_count"] = len(stats["unique_stocks"])
            stats.pop("unique_stocks")
            stats.pop("_id")
            return stats
        
        return {}
    
    def _get_stats_from_files(self):
        """从文件获取统计信息"""
        import os
        from pathlib import Path
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        history_dir = project_root / "data" / "analysis_history"
        
        if not history_dir.exists():
            return {}
        
        total_analyses = 0
        successful_analyses = 0
        total_cost = 0.0
        total_duration = 0.0
        unique_stocks = set()
        
        for file_path in history_dir.glob("analysis_*.jsonl"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line.strip())
                            total_analyses += 1
                            
                            if record.get("success", False):
                                successful_analyses += 1
                            
                            total_cost += record.get("total_cost", 0.0)
                            total_duration += record.get("duration", 0.0)
                            unique_stocks.add(record.get("stock_symbol", ""))
                            
            except Exception as e:
                self.logger.warning(f"⚠️ 读取统计文件失败: {file_path}: {e}")
                continue
        
        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "total_cost": total_cost,
            "avg_duration": total_duration / total_analyses if total_analyses > 0 else 0.0,
            "unique_stocks_count": len(unique_stocks)
        }
    
    def delete_old_records(self, days: int = 30):
        """删除旧的分析记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            if self.collection is not None:
                result = self.collection.delete_many({"created_at": {"$lt": cutoff_date}})
                self.logger.info(f"✅ 删除了 {result.deleted_count} 条旧记录")
                return result.deleted_count
        except Exception as e:
            self.logger.error(f"❌ 删除旧记录失败: {e}")
            return 0

# 全局实例
_history_manager = None

def get_history_manager():
    """获取历史记录管理器实例"""
    global _history_manager
    if _history_manager is None:
        _history_manager = AnalysisHistoryManager()
    return _history_manager
