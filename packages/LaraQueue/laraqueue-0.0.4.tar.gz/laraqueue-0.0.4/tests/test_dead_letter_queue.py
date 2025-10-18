"""Tests for Dead Letter Queue functionality."""
import pytest
import json
import uuid
import time
from unittest.mock import Mock, patch, call
from lara_queue import Queue


class TestDeadLetterQueueInit:
    """Tests for Dead Letter Queue initialization."""
    
    def test_default_dead_letter_queue_name(self, mock_redis):
        """Test default dead letter queue name."""
        queue = Queue(mock_redis, queue='test_queue')
        
        assert queue.dead_letter_queue == 'test_queue:failed'
        assert queue.max_retries == 3
    
    def test_custom_dead_letter_queue_name(self, mock_redis):
        """Test custom dead letter queue name."""
        queue = Queue(mock_redis, queue='test_queue', dead_letter_queue='custom_failed')
        
        assert queue.dead_letter_queue == 'custom_failed'
        assert queue.max_retries == 3
    
    def test_custom_max_retries(self, mock_redis):
        """Test custom max retries setting."""
        queue = Queue(mock_redis, queue='test_queue', max_retries=5)
        
        assert queue.dead_letter_queue == 'test_queue:failed'
        assert queue.max_retries == 5
    
    def test_retry_count_tracking_initialized(self, mock_redis):
        """Test that retry count tracking is initialized."""
        queue = Queue(mock_redis, queue='test_queue')
        
        assert queue._job_retry_count == {}


class TestDeadLetterQueueHelpers:
    """Tests for Dead Letter Queue helper methods."""
    
    def test_get_job_id_from_uuid(self, mock_redis):
        """Test getting job ID from UUID field."""
        queue = Queue(mock_redis, queue='test')
        job_data = {'uuid': 'test-uuid-123', 'data': {}}
        
        job_id = queue._get_job_id(job_data)
        assert job_id == 'test-uuid-123'
    
    def test_get_job_id_generates_new(self, mock_redis):
        """Test generating new job ID when UUID not present."""
        queue = Queue(mock_redis, queue='test')
        job_data = {'data': {}}
        
        job_id = queue._get_job_id(job_data)
        assert job_id is not None
        assert len(job_id) > 0
    
    def test_increment_retry_count(self, mock_redis):
        """Test incrementing retry count."""
        queue = Queue(mock_redis, queue='test')
        job_id = 'test-job-123'
        
        # First increment
        count = queue._increment_retry_count(job_id)
        assert count == 1
        assert queue._get_retry_count(job_id) == 1
        
        # Second increment
        count = queue._increment_retry_count(job_id)
        assert count == 2
        assert queue._get_retry_count(job_id) == 2
    
    def test_clear_retry_count(self, mock_redis):
        """Test clearing retry count."""
        queue = Queue(mock_redis, queue='test')
        job_id = 'test-job-123'
        
        # Set retry count
        queue._increment_retry_count(job_id)
        assert queue._get_retry_count(job_id) == 1
        
        # Clear retry count
        queue._clear_retry_count(job_id)
        assert queue._get_retry_count(job_id) == 0
    
    def test_should_retry_logic(self, mock_redis):
        """Test retry logic based on max retries."""
        queue = Queue(mock_redis, queue='test', max_retries=2)
        job_id = 'test-job-123'
        
        # Should retry (0 < 2)
        assert queue._should_retry(job_id) is True
        
        # Increment once (1 < 2)
        queue._increment_retry_count(job_id)
        assert queue._should_retry(job_id) is True
        
        # Increment again (2 >= 2)
        queue._increment_retry_count(job_id)
        assert queue._should_retry(job_id) is False


class TestDeadLetterQueueOperations:
    """Tests for Dead Letter Queue operations."""
    
    def test_send_to_dead_letter_queue(self, mock_redis):
        """Test sending job to dead letter queue."""
        queue = Queue(mock_redis, queue='test', dead_letter_queue='failed')
        job_data = {'uuid': 'test-123', 'data': {'key': 'value'}}
        error = ValueError("Test error")
        
        queue._send_to_dead_letter_queue(job_data, error, 3)
        
        # Verify rpush was called with correct key and data
        assert mock_redis.rpush.called
        call_args = mock_redis.rpush.call_args[0]
        
        # Check queue key
        assert call_args[0] == 'laravel_database_queues:failed'
        
        # Check data structure
        dead_letter_data = json.loads(call_args[1])
        assert dead_letter_data['original_job'] == job_data
        assert dead_letter_data['error']['type'] == 'ValueError'
        assert dead_letter_data['error']['message'] == 'Test error'
        assert dead_letter_data['retry_count'] == 3
        assert dead_letter_data['max_retries'] == 3
        assert dead_letter_data['queue'] == 'test'
        assert 'failed_at' in dead_letter_data
    
    def test_retry_job(self, mock_redis):
        """Test retrying a failed job."""
        queue = Queue(mock_redis, queue='test')
        job_data = {'uuid': 'test-123', 'data': {'key': 'value'}}
        
        # Set up retry count
        queue._increment_retry_count('test-123')
        
        queue._retry_job(job_data, delay=10)
        
        # Verify rpush was called
        assert mock_redis.rpush.called
        call_args = mock_redis.rpush.call_args[0]
        
        # Check queue key
        assert call_args[0] == 'laravel_database_queues:test'
        
        # Check retry data
        retry_data = json.loads(call_args[1])
        assert retry_data['retry_delay'] == 10
        assert retry_data['retry_attempt'] == 1
    
    def test_get_dead_letter_jobs(self, mock_redis):
        """Test getting jobs from dead letter queue."""
        queue = Queue(mock_redis, queue='test', dead_letter_queue='failed')
        
        # Mock Redis response
        mock_job_data = {
            'original_job': {'uuid': 'test-123'},
            'error': {'type': 'ValueError', 'message': 'Test error'}
        }
        mock_redis.lrange.return_value = [json.dumps(mock_job_data)]
        
        jobs = queue.get_dead_letter_jobs(limit=10)
        
        # Verify lrange was called
        assert mock_redis.lrange.called
        call_args = mock_redis.lrange.call_args[0]
        assert call_args[0] == 'laravel_database_queues:failed'
        assert call_args[1] == 0
        assert call_args[2] == 9
        
        # Check returned data
        assert len(jobs) == 1
        assert jobs[0] == mock_job_data
    
    def test_reprocess_dead_letter_job(self, mock_redis):
        """Test reprocessing a dead letter job."""
        queue = Queue(mock_redis, queue='test')
        
        dead_letter_job = {
            'original_job': {'uuid': 'test-123', 'data': {'key': 'value'}},
            'error': {'type': 'ValueError', 'message': 'Test error'}
        }
        
        # Set up retry count
        queue._increment_retry_count('test-123')
        
        result = queue.reprocess_dead_letter_job(dead_letter_job)
        
        assert result is True
        
        # Verify rpush was called
        assert mock_redis.rpush.called
        call_args = mock_redis.rpush.call_args[0]
        assert call_args[0] == 'laravel_database_queues:test'
        
        # Check that retry count was cleared
        assert queue._get_retry_count('test-123') == 0
    
    def test_clear_dead_letter_queue(self, mock_redis):
        """Test clearing dead letter queue."""
        queue = Queue(mock_redis, queue='test', dead_letter_queue='failed')
        
        # Mock Redis response
        mock_redis.llen.return_value = 5
        
        count = queue.clear_dead_letter_queue()
        
        assert count == 5
        
        # Verify Redis operations
        assert mock_redis.llen.called
        assert mock_redis.delete.called
        
        llen_args = mock_redis.llen.call_args[0]
        assert llen_args[0] == 'laravel_database_queues:failed'
        
        delete_args = mock_redis.delete.call_args[0]
        assert delete_args[0] == 'laravel_database_queues:failed'


class TestDeadLetterQueueIntegration:
    """Tests for Dead Letter Queue integration with job processing."""
    
    def test_job_success_clears_retry_count(self, mock_redis, sample_job_name):
        """Test that successful job processing clears retry count."""
        from lara_queue.module import phpserialize
        
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": "test-job-123",
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
        
        # Set up retry count first
        queue._increment_retry_count('test-job-123')
        assert queue._get_retry_count('test-job-123') == 1
        
        @queue.handler
        def test_handler(data):
            pass  # Successful processing
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Retry count should be cleared after successful processing
        assert queue._get_retry_count('test-job-123') == 0
    
    def test_job_failure_retry_logic(self, mock_redis, sample_job_name):
        """Test job failure retry logic."""
        from lara_queue.module import phpserialize
        
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": "test-job-123",
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
        queue = Queue(mock_redis, queue='test', is_queue_notify=False, max_retries=2)
        
        @queue.handler
        def failing_handler(data):
            raise ValueError("Simulated failure")
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Should have incremented retry count
        assert queue._get_retry_count('test-job-123') == 1
        
        # Should have called rpush for retry
        assert mock_redis.rpush.called
        
        # Check retry data
        call_args = mock_redis.rpush.call_args[0]
        retry_data = json.loads(call_args[1])
        assert retry_data['retry_delay'] == 5  # First retry delay
        assert retry_data['retry_attempt'] == 1
    
    def test_job_failure_sends_to_dead_letter_queue(self, mock_redis, sample_job_name):
        """Test that job failure after max retries sends to dead letter queue."""
        from lara_queue.module import phpserialize
        
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": "test-job-123",
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
        queue = Queue(mock_redis, queue='test', is_queue_notify=False, max_retries=1)
        
        # Pre-set retry count to max
        queue._increment_retry_count('test-job-123')
        assert queue._get_retry_count('test-job-123') == 1
        
        @queue.handler
        def failing_handler(data):
            raise ValueError("Simulated failure")
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Should have sent to dead letter queue
        assert mock_redis.rpush.called
        
        # Check dead letter queue data
        call_args = mock_redis.rpush.call_args[0]
        assert 'failed' in call_args[0]  # Dead letter queue key
        
        dead_letter_data = json.loads(call_args[1])
        assert dead_letter_data['original_job'] == payload
        assert dead_letter_data['error']['type'] == 'ValueError'
        assert dead_letter_data['retry_count'] == 2  # 1 + 1 increment
        assert dead_letter_data['max_retries'] == 1
        
        # Retry count should be cleared after sending to DLQ
        assert queue._get_retry_count('test-job-123') == 0
    
    def test_exponential_backoff_delay(self, mock_redis, sample_job_name):
        """Test exponential backoff delay calculation."""
        from lara_queue.module import phpserialize
        
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": "test-job-123",
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
        queue = Queue(mock_redis, queue='test', is_queue_notify=False, max_retries=5)
        
        # Set retry count to 3 (should get 5 * 2^2 = 20 second delay)
        queue._increment_retry_count('test-job-123')
        queue._increment_retry_count('test-job-123')
        queue._increment_retry_count('test-job-123')
        
        @queue.handler
        def failing_handler(data):
            raise ValueError("Simulated failure")
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Check retry data with exponential backoff
        # retry_count = 4 (3 + 1 increment), delay = 5 * 2^(4-1) = 5 * 8 = 40
        call_args = mock_redis.rpush.call_args[0]
        retry_data = json.loads(call_args[1])
        assert retry_data['retry_delay'] == 40  # 5 * 2^3
        assert retry_data['retry_attempt'] == 4
    
    def test_max_delay_cap(self, mock_redis, sample_job_name):
        """Test that delay is capped at maximum value."""
        from lara_queue.module import phpserialize
        
        job_data = {'key': 'value'}
        php_command = phpserialize.dumps(
            phpserialize.phpobject(sample_job_name, job_data)
        )
        
        payload = {
            "uuid": "test-job-123",
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
        queue = Queue(mock_redis, queue='test', is_queue_notify=False, max_retries=11)
        
        # Set retry count to 9 (should get max 60 second delay, but still retry)
        for _ in range(9):
            queue._increment_retry_count('test-job-123')
        
        @queue.handler
        def failing_handler(data):
            raise ValueError("Simulated failure")
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Check retry data with max delay cap
        call_args = mock_redis.rpush.call_args[0]
        retry_data = json.loads(call_args[1])
        assert retry_data['retry_delay'] == 60  # Max delay cap
        assert retry_data['retry_attempt'] == 10


class TestDeadLetterQueueErrorHandling:
    """Tests for Dead Letter Queue error handling."""
    
    def test_dead_letter_queue_send_failure(self, mock_redis):
        """Test handling of dead letter queue send failure."""
        queue = Queue(mock_redis, queue='test')
        job_data = {'uuid': 'test-123', 'data': {'key': 'value'}}
        error = ValueError("Test error")
        
        # Make rpush fail
        mock_redis.rpush.side_effect = Exception("Redis error")
        
        # Should not raise exception
        queue._send_to_dead_letter_queue(job_data, error, 3)
        
        # Should have logged error
        # (We can't easily test logging without more complex mocking)
    
    def test_get_dead_letter_jobs_redis_error(self, mock_redis):
        """Test handling of Redis error when getting dead letter jobs."""
        queue = Queue(mock_redis, queue='test')
        
        # Make lrange fail
        mock_redis.lrange.side_effect = Exception("Redis error")
        
        # Should return empty list
        jobs = queue.get_dead_letter_jobs()
        assert jobs == []
    
    def test_reprocess_dead_letter_job_missing_original(self, mock_redis):
        """Test reprocessing dead letter job with missing original job."""
        queue = Queue(mock_redis, queue='test')
        
        dead_letter_job = {
            'error': {'type': 'ValueError', 'message': 'Test error'}
            # Missing 'original_job'
        }
        
        result = queue.reprocess_dead_letter_job(dead_letter_job)
        assert result is False
    
    def test_clear_dead_letter_queue_redis_error(self, mock_redis):
        """Test handling of Redis error when clearing dead letter queue."""
        queue = Queue(mock_redis, queue='test')
        
        # Make delete fail
        mock_redis.delete.side_effect = Exception("Redis error")
        
        # Should return 0
        count = queue.clear_dead_letter_queue()
        assert count == 0
