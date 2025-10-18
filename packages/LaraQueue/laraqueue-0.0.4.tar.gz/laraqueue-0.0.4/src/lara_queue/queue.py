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
from typing import Dict, List, Optional, Union, Any, Callable, Tuple

# Setup logger
logger = logging.getLogger(__name__)

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
                 max_retries: int = 3) -> None:
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
            
            logger.warning(f"Job sent to dead letter queue '{self.dead_letter_queue}' after {retry_count} retries")
            logger.debug(f"Dead letter data: {dead_letter_data}")
            
        except Exception as dlq_error:
            logger.error(f"Failed to send job to dead letter queue: {dlq_error}")
            logger.error(f"Original job data: {job_data}")
    
    def _should_retry(self, job_id: str) -> bool:
        """Check if job should be retried."""
        retry_count = self._get_retry_count(job_id)
        return retry_count < self.max_retries
    
    def _retry_job(self, job_data: Dict[str, Any], delay: int = 5) -> None:
        """Retry a failed job with delay."""
        try:
            # Add delay to job data
            job_data['retry_delay'] = delay
            job_data['retry_attempt'] = self._get_retry_count(self._get_job_id(job_data))
            
            queue_key = f"{self.appname}{self.prefix}queues:{self.queue}"
            self.client.rpush(queue_key, json.dumps(job_data))
            
            logger.info(f"Job retried with {delay}s delay (attempt {self._get_retry_count(self._get_job_id(job_data))})")
            
        except Exception as retry_error:
            logger.error(f"Failed to retry job: {retry_error}")
    
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
                raw = phpserialize.loads(command, object_hook=phpserialize.phpobject)
            except (KeyError, Exception) as e:
                logger.error(f"PHP object deserialization error: {e}")
                logger.debug(f"Object data: {obj}")
                self._processing_job = False
                self.redisPop()
                return

            try:
                self.ee.emit(
                    'queued', {'name': obj['data']['commandName'], 'data': raw._asdict()})
                
                # Job processed successfully, clear retry count
                job_id = self._get_job_id(obj)
                self._clear_retry_count(job_id)
                
            except Exception as e:
                logger.error(f"Error calling event handler: {e}")
                
                # Handle job failure with retry/dead letter queue logic
                job_id = self._get_job_id(obj)
                retry_count = self._increment_retry_count(job_id)
                
                if self._should_retry(job_id):
                    # Retry with exponential backoff
                    delay = min(5 * (2 ** (retry_count - 1)), 60)  # Max 60 seconds
                    logger.warning(f"Job failed, retrying in {delay}s (attempt {retry_count}/{self.max_retries})")
                    self._retry_job(obj, delay)
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
                    "command": command.decode("utf-8"),
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