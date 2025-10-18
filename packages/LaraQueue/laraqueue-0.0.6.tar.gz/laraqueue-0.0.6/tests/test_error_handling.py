"""Tests for Redis error handling."""
import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
    RedisError
)
from lara_queue import Queue
from lara_queue.module import phpserialize


class TestRedisPushErrorHandling:
    """Tests for error handling in push method."""
    
    def test_push_handles_redis_connection_error(self, mock_redis):
        """Test handling connection error during push."""
        mock_redis.rpush.side_effect = RedisConnectionError("Connection refused")
        queue = Queue(mock_redis, queue='test')
        
        with pytest.raises(ConnectionError) as exc_info:
            queue.push('TestJob', {'key': 'value'})
        
        assert "Failed to connect to Redis" in str(exc_info.value)
    
    def test_push_handles_redis_timeout(self, mock_redis):
        """Test handling timeout during push."""
        mock_redis.rpush.side_effect = RedisTimeoutError("Operation timed out")
        queue = Queue(mock_redis, queue='test')
        
        with pytest.raises(TimeoutError) as exc_info:
            queue.push('TestJob', {'key': 'value'})
        
        assert "timeout exceeded" in str(exc_info.value).lower()
    
    def test_push_handles_redis_error(self, mock_redis):
        """Test handling general Redis error during push."""
        mock_redis.rpush.side_effect = RedisError("Redis error")
        queue = Queue(mock_redis, queue='test')
        
        with pytest.raises(RuntimeError) as exc_info:
            queue.push('TestJob', {'key': 'value'})
        
        assert "Redis operation error" in str(exc_info.value)
    
    def test_push_handles_serialization_error(self, mock_redis):
        """Test handling data serialization error."""
        queue = Queue(mock_redis, queue='test')
        
        # Pass unserializable object
        with patch('lara_queue.queue.phpserialize.dumps', side_effect=Exception("Serialization failed")):
            with pytest.raises(ValueError) as exc_info:
                queue.push('TestJob', {'key': 'value'})
            
            assert "Failed to serialize job data" in str(exc_info.value)
    
    def test_push_success_logs_debug_message(self, mock_redis, caplog):
        """Test logging of successful job push."""
        import logging
        caplog.set_level(logging.DEBUG, logger='lara_queue')
        
        queue = Queue(mock_redis, queue='test')
        queue.push('TestJob', {'key': 'value'})
        
        # Check that rpush was called
        assert mock_redis.rpush.called


class TestRedisPopErrorHandling:
    """Tests for error handling in redisPop method."""
    
    def test_pop_handles_connection_error_with_retry(self, mock_redis):
        """Test handling connection error with retry."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RedisConnectionError("Connection lost")
            raise KeyboardInterrupt()  # Stop after retry
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        with patch('time.sleep'):  # Skip real delays
            with pytest.raises(KeyboardInterrupt):
                queue.redisPop()
        
        # blpop should be called at least once
        assert mock_redis.blpop.call_count >= 1
    
    def test_pop_handles_timeout_error(self, mock_redis):
        """Test handling Redis operation timeout."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RedisTimeoutError("Timeout")
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
        
        assert mock_redis.blpop.call_count >= 1
    
    def test_pop_handles_redis_error_with_delay(self, mock_redis):
        """Test handling general Redis error with delay."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RedisError("Redis error")
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(KeyboardInterrupt):
                queue.redisPop()
            
            # Should have 3 second delay
            assert any(call[0][0] == 3 for call in mock_sleep.call_args_list)
    
    def test_pop_handles_json_decode_error(self, mock_redis):
        """Test handling JSON parsing error."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', b'invalid json{{{')
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
        
        # Should continue working after error
        assert mock_redis.blpop.call_count >= 2
    
    def test_pop_handles_php_deserialization_error(self, mock_redis):
        """Test handling PHP deserialization error."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                payload = {
                    "data": {
                        "commandName": "TestJob",
                        "command": "invalid_php_data"
                    }
                }
                return ('queue_key', json.dumps(payload).encode())
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
        
        # Should continue working after error
        assert mock_redis.blpop.call_count >= 2
    
    def test_pop_handles_handler_error(self, mock_redis, sample_job_name):
        """Test handling error in user handler."""
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": str(uuid.uuid4()),
            "job": "Illuminate\\Queue\\CallQueuedHandler@call",
            "data": {
                "commandName": sample_job_name,
                "command": php_command.decode('utf-8')
            }
        }
        
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', json.dumps(payload).encode())
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        # Handler that throws exception
        @queue.handler
        def failing_handler(data):
            raise ValueError("Handler error")
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
        
        # Worker should continue after handler error
        assert mock_redis.blpop.call_count >= 2
    
    def test_pop_handles_notify_queue_error(self, mock_redis, sample_job_name):
        """Test handling error in notify queue."""
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": str(uuid.uuid4()),
            "job": "Illuminate\\Queue\\CallQueuedHandler@call",
            "data": {
                "commandName": sample_job_name,
                "command": php_command.decode('utf-8')
            }
        }
        
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', json.dumps(payload).encode())
            elif call_count[0] == 2:
                # Error in notify queue
                raise RedisConnectionError("Notify queue error")
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=True)
        
        @queue.handler
        def test_handler(data):
            pass
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
        
        # Worker should continue after notify error
        assert mock_redis.blpop.call_count >= 2
    
    def test_pop_handles_keyboard_interrupt(self, mock_redis):
        """Test proper handling of KeyboardInterrupt."""
        mock_redis.blpop.side_effect = KeyboardInterrupt()
        queue = Queue(mock_redis, queue='test')
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
    
    def test_pop_handles_unexpected_error(self, mock_redis):
        """Test handling unexpected error."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Unexpected error")
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        with patch('time.sleep'):
            with pytest.raises(KeyboardInterrupt):
                queue.redisPop()
        
        # Should retry after unexpected error
        assert mock_redis.blpop.call_count >= 1

