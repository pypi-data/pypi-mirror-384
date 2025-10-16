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

# Setup logger
logger = logging.getLogger(__name__)

class Queue:

    def __init__(self, client: Redis, 
                 queue: str,
                 driver: str = 'redis',
                 appname: str = 'laravel', prefix: str = '_database_', is_queue_notify: bool = True, is_horizon: bool = False) -> None:
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

    def push(self, name: str, dictObj: dict):
        if self.driver == 'redis':
            self.redisPush(name, dictObj)

    def listen(self):
        if self.driver == 'redis':
            # Register shutdown handlers before starting
            if not self._shutdown_handlers_registered:
                self._register_shutdown_handlers()
            self.redisPop()

    def handler(self, f=None):
        def wrapper(f):
            self.ee._add_event_handler('queued', f, f)
        if f is None:
            return wrapper
        else:
            return wrapper(f)
    
    def _register_shutdown_handlers(self):
        """Register signal handlers for graceful shutdown."""
        def shutdown_handler(signum, frame):
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
    
    def shutdown(self):
        """Trigger graceful shutdown manually."""
        logger.info("Manual shutdown requested")
        self._shutdown = True

    def redisPop(self):
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
            except Exception as e:
                logger.error(f"Error calling event handler: {e}")
                # Continue working even if handler fails

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

    def redisPush(self, name: str, dictObj: dict, timeout: int = None, delay: int = None):
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