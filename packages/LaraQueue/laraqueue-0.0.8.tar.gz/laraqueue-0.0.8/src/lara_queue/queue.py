from redis import Redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
    RedisError
)
import json
from .module import phpserialize
from pyee.base import EventEmitter
import uuid
import time
import logging
import signal
import sys
import random
import math
from enum import Enum
from collections import defaultdict, deque
from typing import Dict, List, Optional, Union, Any, Callable, Tuple

# Setup logger
logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """Стратегии повторной обработки задач."""
    EXPONENTIAL = "exponential"  # Экспоненциальная задержка
    LINEAR = "linear"           # Линейная задержка
    FIXED = "fixed"            # Фиксированная задержка
    CUSTOM = "custom"          # Пользовательская функция

class MetricsCollector:
    """Сборщик метрик для отслеживания производительности очереди."""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        
        # Общие счетчики
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.total_retries = 0
        
        # Метрики по типам задач
        self.job_type_counts = defaultdict(int)
        self.job_type_success = defaultdict(int)
        self.job_type_failed = defaultdict(int)
        self.job_type_processing_times = defaultdict(list)
        
        # Метрики ошибок
        self.error_counts = defaultdict(int)
        self.error_types = defaultdict(int)
        
        # История обработки (для расчета средних значений)
        self.processing_times = deque(maxlen=max_history_size)
        self.job_history = deque(maxlen=max_history_size)
        
        # Метрики производительности
        self.start_time = time.time()
        self.last_reset_time = time.time()
    
    def record_job_start(self, job_name: str) -> float:
        """Записывает начало обработки задачи и возвращает timestamp."""
        return time.time()
    
    def record_job_success(self, job_name: str, start_time: float, processing_time: float) -> None:
        """Записывает успешную обработку задачи."""
        self.total_processed += 1
        self.total_successful += 1
        self.job_type_counts[job_name] += 1
        self.job_type_success[job_name] += 1
        self.job_type_processing_times[job_name].append(processing_time)
        self.processing_times.append(processing_time)
        self.job_history.append({
            'name': job_name,
            'success': True,
            'processing_time': processing_time,
            'timestamp': start_time
        })
    
    def record_job_failure(self, job_name: str, start_time: float, processing_time: float, error: Exception) -> None:
        """Записывает неудачную обработку задачи."""
        self.total_processed += 1
        self.total_failed += 1
        self.job_type_counts[job_name] += 1
        self.job_type_failed[job_name] += 1
        self.job_type_processing_times[job_name].append(processing_time)
        self.processing_times.append(processing_time)
        self.error_counts[type(error).__name__] += 1
        self.error_types[str(error)] += 1
        self.job_history.append({
            'name': job_name,
            'success': False,
            'processing_time': processing_time,
            'timestamp': start_time,
            'error': type(error).__name__
        })
    
    def record_retry(self, job_name: str) -> None:
        """Записывает retry задачи."""
        self.total_retries += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает полные метрики."""
        current_time = time.time()
        uptime = current_time - self.start_time
        time_since_reset = current_time - self.last_reset_time
        
        # Расчет средних значений
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        min_processing_time = min(self.processing_times) if self.processing_times else 0
        max_processing_time = max(self.processing_times) if self.processing_times else 0
        
        # Throughput (задач в секунду)
        throughput = self.total_processed / time_since_reset if time_since_reset > 0 else 0
        
        # Процент успешности
        success_rate = (self.total_successful / self.total_processed * 100) if self.total_processed > 0 else 0
        
        # Метрики по типам задач
        job_type_metrics = {}
        for job_name in self.job_type_counts:
            total_jobs = self.job_type_counts[job_name]
            successful_jobs = self.job_type_success[job_name]
            failed_jobs = self.job_type_failed[job_name]
            processing_times = self.job_type_processing_times[job_name]
            
            job_type_metrics[job_name] = {
                'total': total_jobs,
                'successful': successful_jobs,
                'failed': failed_jobs,
                'success_rate': (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'min_processing_time': min(processing_times) if processing_times else 0,
                'max_processing_time': max(processing_times) if processing_times else 0
            }
        
        return {
            'general': {
                'total_processed': self.total_processed,
                'total_successful': self.total_successful,
                'total_failed': self.total_failed,
                'total_retries': self.total_retries,
                'success_rate': success_rate,
                'uptime_seconds': uptime,
                'time_since_reset': time_since_reset
            },
            'performance': {
                'avg_processing_time': avg_processing_time,
                'min_processing_time': min_processing_time,
                'max_processing_time': max_processing_time,
                'throughput_per_second': throughput,
                'history_size': len(self.processing_times)
            },
            'job_types': job_type_metrics,
            'errors': {
                'error_counts': dict(self.error_counts),
                'error_types': dict(self.error_types)
            }
        }
    
    def reset_metrics(self) -> None:
        """Сбрасывает все метрики."""
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.total_retries = 0
        
        self.job_type_counts.clear()
        self.job_type_success.clear()
        self.job_type_failed.clear()
        self.job_type_processing_times.clear()
        
        self.error_counts.clear()
        self.error_types.clear()
        
        self.processing_times.clear()
        self.job_history.clear()
        
        self.last_reset_time = time.time()
        logger.info("Metrics reset")
    
    def get_recent_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает последние обработанные задачи."""
        return list(self.job_history)[-limit:]

class Queue:

    def __init__(self, 
                 client: Redis, 
                 queue: str,
                 driver: str = 'redis',
                 appname: str = 'laravel', 
                 prefix: str = '_database_', 
                 is_queue_notify: bool = True, 
                 is_horizon: bool = False,
                 dead_letter_queue: Optional[str] = None, 
                 max_retries: int = 3,
                 retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                 retry_delay: int = 5,
                 retry_max_delay: int = 300,
                 retry_jitter: bool = True,
                 retry_backoff_multiplier: float = 2.0,
                 retry_custom_function: Optional[Callable[[int], int]] = None,
                 retry_exceptions: Optional[List[type]] = None,
                 enable_metrics: bool = True,
                 metrics_history_size: int = 1000) -> None:
        self.driver = driver
        self.client = client
        self.queue = queue
        self.appname = appname
        self.prefix = prefix
        self.is_queue_notify = is_queue_notify
        self.is_horizon = is_horizon
        self.ee = EventEmitter()
        
        # Graceful shutdown flags
        self._shutdown = False
        self._processing_job = False
        self._shutdown_handlers_registered = False
        
        # Dead letter queue configuration
        self.dead_letter_queue = dead_letter_queue or f"{queue}:failed"
        self.max_retries = max_retries
        self._job_retry_count = {}  # Track retry count per job
        
        # Retry configuration
        self.retry_strategy = retry_strategy
        self.retry_delay = retry_delay
        self.retry_max_delay = retry_max_delay
        self.retry_jitter = retry_jitter
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.retry_custom_function = retry_custom_function
        self.retry_exceptions = retry_exceptions or [Exception]  # По умолчанию retry для всех исключений
        
        # Retry statistics
        self._retry_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'dead_letter_jobs': 0
        }
        
        # Metrics configuration
        self.enable_metrics = enable_metrics
        self.metrics = MetricsCollector(max_history_size=metrics_history_size) if enable_metrics else None

    def push(self, name: str, dictObj: Dict[str, Any]) -> None:
        if self.driver == 'redis':
            self.redisPush(name, dictObj)

    def listen(self) -> None:
        if self.driver == 'redis':
            # Register shutdown handlers before starting
            if not self._shutdown_handlers_registered:
                self._register_shutdown_handlers()
            self.redisPop()

    def handler(self, f: Optional[Callable] = None) -> Union[Callable, Any]:
        def wrapper(f):
            self.ee._add_event_handler('queued', f, f)
        if f is None:
            return wrapper
        else:
            return wrapper(f)
    
    def _register_shutdown_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        def shutdown_handler(signum: int, frame: Any) -> None:
            signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else signum
            logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
            self._shutdown = True
            
            if self._processing_job:
                logger.info("Waiting for current job to finish...")
            else:
                logger.info("No job in progress, shutting down immediately")
        
        # Register handlers for SIGTERM and SIGINT
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        self._shutdown_handlers_registered = True
        logger.debug("Shutdown signal handlers registered (SIGINT, SIGTERM)")
    
    def shutdown(self) -> None:
        """Trigger graceful shutdown manually."""
        logger.info("Manual shutdown requested")
        self._shutdown = True
    
    def _get_job_id(self, job_data: Dict[str, Any]) -> str:
        """Generate or extract job ID for retry tracking."""
        return job_data.get('uuid', str(uuid.uuid4()))
    
    def _increment_retry_count(self, job_id: str) -> int:
        """Increment retry count for a job."""
        if job_id not in self._job_retry_count:
            self._job_retry_count[job_id] = 0
        self._job_retry_count[job_id] += 1
        return self._job_retry_count[job_id]
    
    def _get_retry_count(self, job_id: str) -> int:
        """Get current retry count for a job."""
        return self._job_retry_count.get(job_id, 0)
    
    def _clear_retry_count(self, job_id: str) -> None:
        """Clear retry count for a job (on success)."""
        if job_id in self._job_retry_count:
            del self._job_retry_count[job_id]
    
    def _send_to_dead_letter_queue(self, job_data: Dict[str, Any], error: Exception, retry_count: int) -> None:
        """Send failed job to dead letter queue."""
        try:
            dead_letter_data = {
                'original_job': job_data,
                'error': {
                    'type': type(error).__name__,
                    'message': str(error),
                    'timestamp': time.time()
                },
                'retry_count': retry_count,
                'max_retries': self.max_retries,
                'failed_at': time.time(),
                'queue': self.queue
            }
            
            dead_letter_key = f"{self.appname}{self.prefix}queues:{self.dead_letter_queue}"
            self.client.rpush(dead_letter_key, json.dumps(dead_letter_data))
            
            # Update statistics
            self._retry_stats['dead_letter_jobs'] += 1
            
            logger.warning(f"Job sent to dead letter queue '{self.dead_letter_queue}' after {retry_count} retries")
            logger.debug(f"Dead letter data: {dead_letter_data}")
            
        except Exception as dlq_error:
            logger.error(f"Failed to send job to dead letter queue: {dlq_error}")
            logger.error(f"Original job data: {job_data}")
    
    def _should_retry(self, job_id: str, exception: Exception) -> bool:
        """Check if job should be retried based on retry count and exception type."""
        retry_count = self._get_retry_count(job_id)
        
        # Проверяем количество попыток
        if retry_count >= self.max_retries:
            return False
        
        # Проверяем тип исключения
        if not self._is_retryable_exception(exception):
            return False
        
        return True
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Check if exception type is retryable."""
        return any(isinstance(exception, exc_type) for exc_type in self.retry_exceptions)
    
    def _calculate_retry_delay(self, retry_count: int) -> int:
        """Calculate delay for retry based on strategy."""
        if self.retry_strategy == RetryStrategy.CUSTOM and self.retry_custom_function:
            delay = self.retry_custom_function(retry_count)
        elif self.retry_strategy == RetryStrategy.EXPONENTIAL:
            delay = int(self.retry_delay * (self.retry_backoff_multiplier ** (retry_count - 1)))
        elif self.retry_strategy == RetryStrategy.LINEAR:
            delay = self.retry_delay * retry_count
        elif self.retry_strategy == RetryStrategy.FIXED:
            delay = self.retry_delay
        else:
            delay = self.retry_delay
        
        # Ограничиваем максимальной задержкой
        delay = min(delay, self.retry_max_delay)
        
        # Добавляем jitter для избежания thundering herd
        if self.retry_jitter:
            jitter = random.uniform(0.1, 0.3) * delay
            delay = int(delay + jitter)
        
        return max(1, delay)  # Минимум 1 секунда
    
    def _retry_job(self, job_data: Dict[str, Any], retry_count: int) -> None:
        """Retry a failed job with calculated delay."""
        try:
            # Calculate delay based on retry strategy
            delay = self._calculate_retry_delay(retry_count)
            
            # Add retry metadata to job data
            job_data['retry_delay'] = delay
            job_data['retry_attempt'] = retry_count
            job_data['retry_strategy'] = self.retry_strategy.value
            job_data['retry_timestamp'] = time.time()
            
            queue_key = f"{self.appname}{self.prefix}queues:{self.queue}"
            self.client.rpush(queue_key, json.dumps(job_data))
            
            # Update statistics
            self._retry_stats['total_retries'] += 1
            
            # Record retry in metrics
            if self.metrics:
                job_name = job_data.get('data', {}).get('commandName', 'UnknownJob')
                self.metrics.record_retry(job_name)
            
            logger.info(f"Job retried with {delay}s delay (attempt {retry_count}/{self.max_retries}, strategy: {self.retry_strategy.value})")
            
        except Exception as retry_error:
            logger.error(f"Failed to retry job: {retry_error}")
            self._retry_stats['failed_retries'] += 1
    
    def get_dead_letter_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs from dead letter queue."""
        try:
            dead_letter_key = f"{self.appname}{self.prefix}queues:{self.dead_letter_queue}"
            jobs = self.client.lrange(dead_letter_key, 0, limit - 1)
            
            result = []
            for job in jobs:
                try:
                    job_data = json.loads(job)
                    result.append(job_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse dead letter job: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get dead letter jobs: {e}")
            return []
    
    def reprocess_dead_letter_job(self, job_data: Dict[str, Any]) -> bool:
        """Reprocess a job from dead letter queue."""
        try:
            original_job = job_data.get('original_job', {})
            if not original_job:
                logger.error("No original job data found in dead letter job")
                return False
            
            # Clear retry count for reprocessing
            job_id = self._get_job_id(original_job)
            self._clear_retry_count(job_id)
            
            # Send back to main queue
            queue_key = f"{self.appname}{self.prefix}queues:{self.queue}"
            self.client.rpush(queue_key, json.dumps(original_job))
            
            logger.info(f"Dead letter job reprocessed: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reprocess dead letter job: {e}")
            return False
    
    def clear_dead_letter_queue(self) -> int:
        """Clear all jobs from dead letter queue."""
        try:
            dead_letter_key = f"{self.appname}{self.prefix}queues:{self.dead_letter_queue}"
            count = self.client.llen(dead_letter_key)
            self.client.delete(dead_letter_key)
            
            logger.info(f"Cleared {count} jobs from dead letter queue")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear dead letter queue: {e}")
            return 0
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics."""
        return {
            'total_retries': self._retry_stats['total_retries'],
            'successful_retries': self._retry_stats['successful_retries'],
            'failed_retries': self._retry_stats['failed_retries'],
            'dead_letter_jobs': self._retry_stats['dead_letter_jobs'],
            'success_rate': (
                self._retry_stats['successful_retries'] / max(1, self._retry_stats['total_retries'])
            ) * 100,
            'current_retry_config': {
                'strategy': self.retry_strategy.value,
                'max_retries': self.max_retries,
                'delay': self.retry_delay,
                'max_delay': self.retry_max_delay,
                'jitter': self.retry_jitter,
                'backoff_multiplier': self.retry_backoff_multiplier,
                'retryable_exceptions': [exc.__name__ for exc in self.retry_exceptions]
            }
        }
    
    def reset_retry_statistics(self) -> None:
        """Reset retry statistics."""
        self._retry_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'dead_letter_jobs': 0
        }
        logger.info("Retry statistics reset")
    
    def update_retry_config(self, 
                           max_retries: Optional[int] = None,
                           retry_strategy: Optional[RetryStrategy] = None,
                           retry_delay: Optional[int] = None,
                           retry_max_delay: Optional[int] = None,
                           retry_jitter: Optional[bool] = None,
                           retry_backoff_multiplier: Optional[float] = None,
                           retry_custom_function: Optional[Callable[[int], int]] = None,
                           retry_exceptions: Optional[List[type]] = None) -> None:
        """Update retry configuration at runtime."""
        if max_retries is not None:
            self.max_retries = max_retries
        if retry_strategy is not None:
            self.retry_strategy = retry_strategy
        if retry_delay is not None:
            self.retry_delay = retry_delay
        if retry_max_delay is not None:
            self.retry_max_delay = retry_max_delay
        if retry_jitter is not None:
            self.retry_jitter = retry_jitter
        if retry_backoff_multiplier is not None:
            self.retry_backoff_multiplier = retry_backoff_multiplier
        if retry_custom_function is not None:
            self.retry_custom_function = retry_custom_function
        if retry_exceptions is not None:
            self.retry_exceptions = retry_exceptions
        
        logger.info(f"Retry configuration updated: {self.get_retry_statistics()['current_retry_config']}")
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive metrics."""
        if not self.metrics:
            return None
        return self.metrics.get_metrics()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        if self.metrics:
            self.metrics.reset_metrics()
    
    def get_recent_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent job history."""
        if not self.metrics:
            return []
        return self.metrics.get_recent_jobs(limit)
    
    def get_job_type_metrics(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for specific job type."""
        if not self.metrics:
            return None
        
        metrics = self.metrics.get_metrics()
        return metrics.get('job_types', {}).get(job_name)
    
    def get_performance_summary(self) -> Optional[Dict[str, Any]]:
        """Get performance summary."""
        if not self.metrics:
            return None
        
        metrics = self.metrics.get_metrics()
        return {
            'general': metrics.get('general', {}),
            'performance': metrics.get('performance', {})
        }

    def redisPop(self) -> None:
        # Check if shutdown was requested
        if self._shutdown:
            logger.info("Shutdown requested, stopping worker loop")
            return
        
        try:
            result = self.client.blpop(
                self.appname + self.prefix + 'queues:' + self.queue, 60)
            
            if result is None:
                # Timeout occurred, check shutdown flag before retrying
                if self._shutdown:
                    logger.info("Shutdown requested during timeout, stopping worker")
                    return
                logger.debug(f"Timeout waiting for job in queue '{self.queue}', retrying...")
                self.redisPop()
                return
                
            key, data = result
            
            # Mark that we're processing a job
            self._processing_job = True
            
            try:
                obj = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error from queue '{self.queue}': {e}")
                logger.debug(f"Invalid data: {data}")
                self._processing_job = False
                self.redisPop()
                return
            
            try:
                command = obj['data']['command']
                # Handle both string and bytes for phpserialize.loads()
                if isinstance(command, str):
                    command = command.encode('utf-8')
                elif isinstance(command, bytes):
                    pass  # Already bytes
                else:
                    logger.error(f"Unexpected command type: {type(command)}")
                    self._processing_job = False
                    self.redisPop()
                    return
                    
                raw = phpserialize.loads(command, object_hook=phpserialize.phpobject)
            except (KeyError, Exception) as e:
                logger.error(f"PHP object deserialization error: {e}")
                logger.error(f"Command type: {type(command)}")
                logger.error(f"Command content: {command[:100] if len(str(command)) > 100 else command}")
                logger.debug(f"Object data: {obj}")
                self._processing_job = False
                self.redisPop()
                return

            # Record job start time for metrics
            job_name = obj['data']['commandName']
            start_time = time.time()
            if self.metrics:
                start_time = self.metrics.record_job_start(job_name)
            
            try:
                self.ee.emit(
                    'queued', {'name': job_name, 'data': raw._asdict()})
                
                # Job processed successfully, clear retry count and update stats
                job_id = self._get_job_id(obj)
                retry_count = self._get_retry_count(job_id)
                if retry_count > 0:
                    self._retry_stats['successful_retries'] += 1
                self._clear_retry_count(job_id)
                
                # Record successful job in metrics
                if self.metrics:
                    processing_time = time.time() - start_time
                    self.metrics.record_job_success(job_name, start_time, processing_time)
                
            except Exception as e:
                logger.error(f"Error calling event handler: {e}")
                
                # Record failed job in metrics
                if self.metrics:
                    processing_time = time.time() - start_time
                    self.metrics.record_job_failure(job_name, start_time, processing_time, e)
                
                # Handle job failure with retry/dead letter queue logic
                job_id = self._get_job_id(obj)
                retry_count = self._increment_retry_count(job_id)
                
                if self._should_retry(job_id, e):
                    # Retry with calculated delay based on strategy
                    logger.warning(f"Job failed, retrying (attempt {retry_count}/{self.max_retries}, exception: {type(e).__name__})")
                    self._retry_job(obj, retry_count)
                else:
                    # Send to dead letter queue
                    logger.error(f"Job failed after {retry_count} attempts, sending to dead letter queue")
                    self._send_to_dead_letter_queue(obj, e, retry_count)
                    self._clear_retry_count(job_id)

            if self.is_horizon: # TODO
                pass 
            
            if self.is_queue_notify:
                try:
                    self.client.blpop(
                        self.appname + self.prefix + 'queues:' + self.queue + ':notify', 60)
                except (RedisConnectionError, RedisTimeoutError, RedisError) as e:
                    logger.warning(f"Error reading notify queue: {e}")
                    # Continue working, notify is not critical

            # Job processing completed
            self._processing_job = False
            
            # Check if shutdown was requested while processing
            if self._shutdown:
                logger.info("Shutdown requested, current job completed successfully")
                return
            
            self.redisPop()
            
        except RedisConnectionError as e:
            self._processing_job = False
            logger.error(f"Redis connection error: {e}")
            
            if self._shutdown:
                logger.info("Shutdown requested, not attempting reconnection")
                return
                
            logger.info("Waiting 5 seconds before reconnecting...")
            time.sleep(5)
            
            if self._shutdown:
                logger.info("Shutdown requested during reconnection wait")
                return
            
            try:
                self.redisPop()
            except Exception as retry_error:
                logger.critical(f"Failed to reconnect to Redis: {retry_error}")
                raise
                
        except RedisTimeoutError as e:
            self._processing_job = False
            logger.warning(f"Redis operation timeout: {e}")
            
            if not self._shutdown:
                self.redisPop()
            
        except RedisError as e:
            self._processing_job = False
            logger.error(f"Redis error: {e}")
            
            if self._shutdown:
                logger.info("Shutdown requested, not retrying after Redis error")
                return
                
            logger.info("Waiting 3 seconds before retry...")
            time.sleep(3)
            
            if not self._shutdown:
                self.redisPop()
            
        except KeyboardInterrupt:
            self._processing_job = False
            logger.info("Received interrupt signal, stopping worker...")
            self._shutdown = True
            raise
            
        except Exception as e:
            self._processing_job = False
            logger.error(f"Unexpected error processing queue: {e}", exc_info=True)
            
            if self._shutdown:
                logger.info("Shutdown requested, not retrying after unexpected error")
                return
                
            time.sleep(2)
            
            if not self._shutdown:
                self.redisPop()

    def redisPush(self, name: str, dictObj: Dict[str, Any], timeout: Optional[int] = None, delay: Optional[int] = None) -> None:
        try:
            # Serialize PHP object
            try:
                command = phpserialize.dumps(phpserialize.phpobject(name, dictObj))
            except Exception as e:
                logger.error(f"PHP object serialization error '{name}': {e}")
                raise ValueError(f"Failed to serialize job data: {e}") from e
            
            # Prepare job data
            data = {
                "uuid": str(uuid.uuid4()),
                "job": 'Illuminate\\Queue\\CallQueuedHandler@call',
                "data": {
                    "commandName": name,
                    "command": command.decode("utf-8"),  # Decode for JSON
                },
                "timeout": timeout,
                "id": str(time.time()),
                "attempts": 0,
                "delay": delay,
                "maxExceptions": None,
            }
            
            if self.is_queue_notify == False:
                del data['delay']
                del data['maxExceptions']
                data.update({'displayName': name, 'maxTries': None, 'timeoutAt': None})
            
            # Serialize to JSON
            try:
                json_data = json.dumps(data)
            except (TypeError, ValueError) as e:
                logger.error(f"JSON serialization error: {e}")
                raise ValueError(f"Failed to create JSON payload: {e}") from e
            
            # Send to Redis
            queue_key = self.appname + self.prefix + 'queues:' + self.queue
            try:
                self.client.rpush(queue_key, json_data)
                logger.debug(f"Job '{name}' successfully added to queue '{self.queue}'")
            except RedisConnectionError as e:
                logger.error(f"Redis connection error while pushing job: {e}")
                raise ConnectionError(f"Failed to connect to Redis: {e}") from e
            except RedisTimeoutError as e:
                logger.error(f"Timeout while pushing job to Redis: {e}")
                raise TimeoutError(f"Redis operation timeout exceeded: {e}") from e
            except RedisError as e:
                logger.error(f"Redis error while pushing job '{name}': {e}")
                raise RuntimeError(f"Redis operation error: {e}") from e
                
        except (ConnectionError, TimeoutError, ValueError, RuntimeError) as e:
            # Re-raise already handled errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error while pushing job '{name}': {e}", exc_info=True)
            raise RuntimeError(f"Failed to add job to queue: {e}") from e