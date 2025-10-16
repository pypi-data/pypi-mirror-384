"""Unit tests for Queue class with mocked Redis."""
import pytest
import json
import uuid
from unittest.mock import Mock, patch, call
from lara_queue import Queue


class TestQueueInit:
    """Test Queue initialization."""
    
    def test_init_with_defaults(self, mock_redis):
        """Test Queue initialization with default parameters."""
        queue = Queue(mock_redis, queue='test')
        
        assert queue.client == mock_redis
        assert queue.queue == 'test'
        assert queue.driver == 'redis'
        assert queue.appname == 'laravel'
        assert queue.prefix == '_database_'
        assert queue.is_queue_notify is True
        assert queue.is_horizon is False
    
    def test_init_with_custom_params(self, mock_redis):
        """Test Queue initialization with custom parameters."""
        queue = Queue(
            mock_redis,
            queue='custom',
            appname='myapp',
            prefix='_custom_',
            is_queue_notify=False,
            is_horizon=True
        )
        
        assert queue.appname == 'myapp'
        assert queue.prefix == '_custom_'
        assert queue.is_queue_notify is False
        assert queue.is_horizon is True


class TestQueuePush:
    """Test Queue.push() method."""
    
    def test_push_calls_redis_rpush(self, mock_redis, sample_job_name, sample_job_data):
        """Test that push() calls Redis rpush with correct queue key."""
        queue = Queue(mock_redis, queue='test_queue')
        queue.push(sample_job_name, sample_job_data)
        
        # Verify rpush was called
        assert mock_redis.rpush.called
        call_args = mock_redis.rpush.call_args[0]
        
        # Check queue key format
        assert call_args[0] == 'laravel_database_queues:test_queue'
    
    def test_push_creates_valid_json_payload(self, mock_redis, sample_job_name, sample_job_data):
        """Test that push() creates valid JSON payload."""
        queue = Queue(mock_redis, queue='test_queue')
        queue.push(sample_job_name, sample_job_data)
        
        call_args = mock_redis.rpush.call_args[0]
        payload = json.loads(call_args[1])
        
        # Verify payload structure
        assert 'uuid' in payload
        assert 'job' in payload
        assert 'data' in payload
        assert 'timeout' in payload
        assert 'attempts' in payload
        
        # Verify job handler
        assert payload['job'] == 'Illuminate\\Queue\\CallQueuedHandler@call'
        
        # Verify data structure
        assert payload['data']['commandName'] == sample_job_name
        assert 'command' in payload['data']
        
        # Verify attempts is 0
        assert payload['attempts'] == 0
    
    def test_push_with_queue_notify_false(self, mock_redis, sample_job_name, sample_job_data):
        """Test push() with is_queue_notify=False changes payload structure."""
        queue = Queue(mock_redis, queue='test_queue', is_queue_notify=False)
        queue.push(sample_job_name, sample_job_data)
        
        call_args = mock_redis.rpush.call_args[0]
        payload = json.loads(call_args[1])
        
        # These fields should not exist when is_queue_notify=False
        assert 'delay' not in payload
        assert 'maxExceptions' not in payload
        
        # These fields should exist
        assert 'displayName' in payload
        assert 'maxTries' in payload
        assert 'timeoutAt' in payload
        assert payload['displayName'] == sample_job_name
    
    def test_push_with_custom_appname_and_prefix(self, mock_redis, sample_job_name, sample_job_data):
        """Test push() respects custom appname and prefix."""
        queue = Queue(
            mock_redis,
            queue='custom',
            appname='myapp',
            prefix='_myprefix_'
        )
        queue.push(sample_job_name, sample_job_data)
        
        call_args = mock_redis.rpush.call_args[0]
        assert call_args[0] == 'myapp_myprefix_queues:custom'


class TestQueueHandler:
    """Test Queue.handler() decorator."""
    
    def test_handler_as_decorator(self, mock_redis):
        """Test handler can be used as decorator."""
        queue = Queue(mock_redis, queue='test')
        
        @queue.handler
        def my_handler(data):
            pass
        
        # Verify handler was registered
        assert 'queued' in queue.ee._events
    
    def test_handler_as_function_call(self, mock_redis):
        """Test handler can be called as function."""
        queue = Queue(mock_redis, queue='test')
        
        def my_handler(data):
            pass
        
        queue.handler(my_handler)
        
        # Verify handler was registered
        assert 'queued' in queue.ee._events
    
    def test_multiple_handlers(self, mock_redis):
        """Test multiple handlers can be registered."""
        queue = Queue(mock_redis, queue='test')
        
        @queue.handler
        def handler1(data):
            pass
        
        @queue.handler
        def handler2(data):
            pass
        
        # Both handlers should be registered
        assert len(queue.ee._events.get('queued', [])) == 2


class TestQueuePop:
    """Test Queue.redisPop() method."""
    
    def test_pop_handles_timeout(self, mock_redis):
        """Test that redisPop handles timeout (None result) correctly."""
        # Setup: first call returns None (timeout), second call stops
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # First call: timeout
            raise KeyboardInterrupt()  # Stop on second call
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        # Run and catch the KeyboardInterrupt
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Should have called blpop at least once
        assert mock_redis.blpop.call_count >= 1
    
    def test_pop_parses_valid_payload(self, mock_redis, sample_job_name):
        """Test that redisPop correctly parses valid Laravel job payload."""
        from lara_queue.module import phpserialize
        
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
        
        # First call returns job, second call raises exception to stop
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', json.dumps(payload).encode())
            raise KeyboardInterrupt()  # Stop recursion
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        handler_called = Mock()
        
        @queue.handler
        def test_handler(data):
            handler_called(data)
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Handler should have been called
        assert handler_called.called
        call_data = handler_called.call_args[0][0]
        assert call_data['name'] == sample_job_name
        assert 'data' in call_data
    
    def test_pop_with_queue_notify(self, mock_redis, sample_job_name):
        """Test that redisPop calls blpop twice when is_queue_notify=True."""
        from lara_queue.module import phpserialize
        
        job_data = {'test': 'data'}
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
        
        # Return job, then notify, then stop
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', json.dumps(payload).encode())
            elif call_count[0] == 2:
                return ('notify_key', b'1')
            raise KeyboardInterrupt()  # Stop after notify
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=True)
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # blpop should be called at least twice: once for job, once for notify
        # (may be called 3 times due to recursive call after notify)
        assert mock_redis.blpop.call_count >= 2


class TestQueueListen:
    """Test Queue.listen() method."""
    
    def test_listen_calls_redis_pop(self, mock_redis):
        """Test that listen() calls redisPop()."""
        queue = Queue(mock_redis, queue='test')
        
        with patch.object(queue, 'redisPop') as mock_pop:
            mock_pop.return_value = None
            queue.listen()
            
            assert mock_pop.called

