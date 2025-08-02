#!/usr/bin/env python3
"""
批量分析处理器
支持多个股票代码的并发分析
"""

import streamlit as st
import threading
import time
import queue
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback
import uuid

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('batch_processor')

# 导入分析运行器
from utils.analysis_runner import run_stock_analysis, validate_analysis_params


class BatchAnalysisProcessor:
    """批量分析处理器"""
    
    def __init__(self):
        self.analysis_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.active_threads = {}
        self.is_running = False
        self.last_activity_time = None  # 记录最后活动时间
        self.completed_tasks_log = []  # 记录完成任务的日志
        self._lock = threading.Lock()  # 线程安全锁
        
    def parse_stock_symbols(self, input_text: str) -> List[str]:
        """解析股票代码输入文本"""
        if not input_text:
            return []
        
        # 支持多种分隔符：换行、逗号、分号、空格
        import re
        symbols = re.split(r'[,;\s\n]+', input_text.strip())
        
        # 清理和验证股票代码
        cleaned_symbols = []
        for symbol in symbols:
            symbol = symbol.strip().upper()
            if symbol:
                cleaned_symbols.append(symbol)
        
        return list(set(cleaned_symbols))  # 去重
    
    def add_analysis_task(self, symbol: str, params: Dict[str, Any], llm_config: Optional[Dict[str, str]] = None) -> str:
        """添加分析任务"""
        task_id = str(uuid.uuid4())[:8]
        task = {
            'task_id': task_id,
            'symbol': symbol,
            'params': params,
            'llm_config': llm_config,
            'status': 'pending',
            'created_at': datetime.now(),
            'start_time': None,
            'end_time': None,
            'result': None,
            'error': None
        }
        
        self.analysis_queue.put(task)
        logger.info(f"添加分析任务: {symbol} (ID: {task_id})")
        return task_id
    
    def run_analysis_worker(self, task: Dict[str, Any]):
        """运行单个分析任务的工作线程"""
        task_id = task['task_id']
        symbol = task['symbol']
        
        try:
            logger.info(f"开始分析任务: {symbol} (ID: {task_id})")
            task['status'] = 'running'
            task['start_time'] = datetime.now()
            
            # 使用传入的LLM配置，如果没有则使用默认配置
            llm_config = task.get('llm_config') or {}
            
            # 从配置中获取LLM设置，如果没有则使用环境变量或默认值
            llm_provider = llm_config.get('llm_provider') or os.getenv('DEFAULT_LLM_PROVIDER', 'deepseek')
            llm_model = llm_config.get('llm_model') or os.getenv('DEFAULT_LLM_MODEL', 'deepseek-chat')
            
            logger.info(f"使用LLM配置: provider={llm_provider}, model={llm_model}")
            
            # 运行分析 - 只传递run_stock_analysis需要的参数
            result = run_stock_analysis(
                stock_symbol=symbol,
                analysis_date=task['params'].get('analysis_date'),
                analysts=task['params'].get('analysts', []),
                research_depth=task['params'].get('research_depth', 3),
                llm_provider=llm_provider,
                llm_model=llm_model,
                market_type=task['params'].get('market_type', '美股'),
                progress_callback=None  # 批量分析不使用进度回调
            )
            
            task['status'] = 'completed'
            task['end_time'] = datetime.now()
            task['result'] = result
            
            # 更新最后活动时间
            self.last_activity_time = datetime.now()
            
            # 记录完成任务日志
            completion_log = {
                'task_id': task_id,
                'symbol': symbol,
                'completed_at': self.last_activity_time,
                'duration': (task['end_time'] - task['start_time']).total_seconds()
            }
            self.completed_tasks_log.append(completion_log)
            
            logger.info(f"完成分析任务: {symbol} (ID: {task_id})")
            
        except Exception as e:
            task['status'] = 'failed'
            task['end_time'] = datetime.now()
            task['error'] = str(e)
            
            # 即使失败也更新活动时间
            self.last_activity_time = datetime.now()
            
            logger.error(f"分析任务失败: {symbol} (ID: {task_id}) - {e}")
            logger.error(traceback.format_exc())
        
        finally:
            # 将结果放入结果队列
            self.results_queue.put(task)
            
            # 从活动线程中移除 - 使用线程安全的方式
            with self._lock:
                if task_id in self.active_threads:
                    del self.active_threads[task_id]
                    logger.info(f"✅ 线程完成并清理: {task_id}")
            
            logger.info(f"📦 任务结果已放入队列: {task_id}")
    
    def start_batch_analysis(self, symbols: List[str], analysis_params: Dict[str, Any], llm_config: Optional[Dict[str, str]] = None) -> List[str]:
        """开始批量分析"""
        if not symbols:
            return []
        
        task_ids = []
        self.is_running = True
        
        logger.info(f"开始批量分析 {len(symbols)} 个股票代码")
        
        for symbol in symbols:
            # 验证参数 - 只传递validate_analysis_params需要的参数
            try:
                validate_analysis_params(
                    stock_symbol=symbol,
                    analysis_date=analysis_params.get('analysis_date'),
                    analysts=analysis_params.get('analysts', []),
                    research_depth=analysis_params.get('research_depth', 3),
                    market_type=analysis_params.get('market_type', '美股')
                )
                
                # 为run_stock_analysis准备完整的参数集
                params = {
                    'analysis_date': analysis_params.get('analysis_date'),
                    'analysts': analysis_params.get('analysts', []),
                    'research_depth': analysis_params.get('research_depth', 3),
                    'market_type': analysis_params.get('market_type', '美股'),
                    'include_sentiment': analysis_params.get('include_sentiment', True),
                    'include_risk_assessment': analysis_params.get('include_risk_assessment', True),
                    'custom_prompt': analysis_params.get('custom_prompt', '')
                }
                
                # 添加任务
                task_id = self.add_analysis_task(symbol, params, llm_config)
                task_ids.append(task_id)
                
                # 启动工作线程
                task = self.analysis_queue.get()
                thread = threading.Thread(
                    target=self.run_analysis_worker,
                    args=(task,),
                    daemon=True
                )
                thread.start()
                
                # 线程安全地添加到活动线程字典
                with self._lock:
                    self.active_threads[task_id] = thread
                
                logger.info(f"🚀 启动分析线程: {symbol} (ID: {task_id})")
                
            except Exception as e:
                logger.error(f"创建任务失败: {symbol} - {e}")
        
        return task_ids
    
    def get_progress_status(self) -> Dict[str, Any]:
        """获取批量分析进度状态 - 改进版本支持更准确的状态检测"""
        completed_results = []
        
        # 收集所有完成的结果
        result_count = 0
        while not self.results_queue.empty():
            try:
                result = self.results_queue.get_nowait()
                completed_results.append(result)
                result_count += 1
            except queue.Empty:
                break
        
        if result_count > 0:
            logger.info(f"📥 从队列中获取了 {result_count} 个完成的结果")
        
        # 清理已完成的线程 - 线程安全 + 死线程检测
        with self._lock:
            finished_threads = []
            dead_threads = []
            for task_id, thread in list(self.active_threads.items()):
                if not thread.is_alive():
                    finished_threads.append(task_id)
                    dead_threads.append(task_id)
                    logger.info(f"💀 检测到死线程: {task_id[:8]} (线程已结束但未清理)")
            
            # 移除已完成的线程
            for task_id in finished_threads:
                if task_id in self.active_threads:
                    del self.active_threads[task_id]
                    logger.info(f"🧹 清理已完成的线程: {task_id[:8]}")
                    
                    # 如果线程死亡但没有结果，创建一个假结果来表示完成
                    if task_id not in [r.get('task_id') for r in completed_results]:
                        fake_result = {
                            'task_id': task_id,
                            'symbol': getattr(thread, 'symbol', 'Unknown'),
                            'success': True,  # 假设成功，因为没有异常
                            'auto_detected': True,
                            'completion_time': datetime.now().strftime("%H:%M:%S")
                        }
                        completed_results.append(fake_result)
                        logger.info(f"🤖 为死线程创建假结果: {task_id[:8]}")
            
            # 统计状态
            running_tasks = len(self.active_threads)
            
        completed_tasks = len(completed_results)
        total_tasks = running_tasks + completed_tasks
        
        logger.debug(f"📊 状态统计: 运行中={running_tasks}, 已完成={completed_tasks}, 总计={total_tasks}, 死线程={len(dead_threads)}")
        
        # 检查是否真的在运行中 - 基于多重条件判断
        is_actually_running = self.is_running and running_tasks > 0
        
        # 智能完成检测：如果没有运行中的任务，且最后活动时间超过5秒，认为已完成
        if self.is_running and running_tasks == 0:
            time_since_activity = (datetime.now() - self.last_activity_time).total_seconds() if self.last_activity_time else 0
            
            if completed_tasks > 0 and time_since_activity > 5:  # 降低到5秒
                self.is_running = False
                is_actually_running = False
                logger.info(f"[进度] ✅ 智能检测：所有任务已完成！总计: {completed_tasks}个，最后活动时间: {time_since_activity:.1f}秒前")
            elif completed_tasks > 0:
                # 短暂等待期间，仍标记为运行中但提示即将完成
                logger.info(f"[进度] 🔄 等待确认完成状态... 已完成: {completed_tasks}个，距离最后活动: {time_since_activity:.1f}秒")
        
        # 如果检测到死线程，立即标记为完成
        if len(dead_threads) > 0 and running_tasks == 0:
            self.is_running = False
            is_actually_running = False
            logger.info(f"[进度] ✅ 基于死线程检测：所有任务已完成！检测到{len(dead_threads)}个死线程")
        
        # 如果没有运行中的任务，标记为停止
        if self.is_running and running_tasks == 0 and completed_tasks > 0:
            time_since_activity = (datetime.now() - self.last_activity_time).total_seconds() if self.last_activity_time else 999
            if time_since_activity > 3:  # 降低到3秒
                self.is_running = False
                is_actually_running = False
                logger.info(f"[进度] ✅ 所有任务已完成！总计: {completed_tasks}个")
        
        status = {
            'total_tasks': total_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'is_running': is_actually_running,
            'completed_results': completed_results,
            'progress_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'last_update_time': datetime.now().strftime("%H:%M:%S"),
            'last_activity_time': self.last_activity_time.strftime("%H:%M:%S") if self.last_activity_time else None,
            'time_since_last_activity': (datetime.now() - self.last_activity_time).total_seconds() if self.last_activity_time else None,
            'completed_tasks_count': len(self.completed_tasks_log),
            'dead_threads_detected': len(dead_threads),
            'force_completion': len(dead_threads) > 0 and running_tasks == 0  # 强制完成标识
        }
        
        # 如果没有运行中的任务，标记为完成
        if running_tasks == 0:
            self.is_running = False
        
        return status
    
    def stop_all_tasks(self):
        """停止所有任务"""
        logger.info("停止所有批量分析任务")
        self.is_running = False
        
        # 清空队列
        while not self.analysis_queue.empty():
            try:
                self.analysis_queue.get_nowait()
            except queue.Empty:
                break
        
        # 等待活动线程完成（设置超时）
        for task_id, thread in list(self.active_threads.items()):
            if thread.is_alive():
                thread.join(timeout=1.0)  # 等待1秒
        
        self.active_threads.clear()


# 全局批量处理器实例
if 'batch_processor' not in st.session_state:
    st.session_state.batch_processor = BatchAnalysisProcessor()


def get_batch_processor() -> BatchAnalysisProcessor:
    """获取批量处理器实例"""
    return st.session_state.batch_processor
