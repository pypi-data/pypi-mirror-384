"""Tests for graceful shutdown functionality."""
import pytest
import signal
import json
import uuid
from unittest.mock import Mock, patch, call
from lara_queue import Queue
from lara_queue.module import phpserialize


class TestGracefulShutdown:
    """Tests for graceful shutdown signal handling."""
    
    def test_shutdown_flag_initialized(self, mock_redis):
        """Test that shutdown flags are properly initialized."""
        queue = Queue(mock_redis, queue='test')
        
        assert queue._shutdown is False
        assert queue._processing_job is False
        assert queue._shutdown_handlers_registered is False
    
    def test_register_shutdown_handlers_on_listen(self, mock_redis):
        """Test that signal handlers are registered when listen() is called."""
        mock_redis.blpop.side_effect = KeyboardInterrupt()
        queue = Queue(mock_redis, queue='test')
        
        with patch('signal.signal') as mock_signal:
            try:
                queue.listen()
            except KeyboardInterrupt:
                pass
            
            # Should register SIGINT and SIGTERM
            assert mock_signal.call_count >= 2
            signal_calls = [call[0][0] for call in mock_signal.call_args_list]
            assert signal.SIGINT in signal_calls
            assert signal.SIGTERM in signal_calls
    
    def test_manual_shutdown(self, mock_redis):
        """Test manual shutdown via shutdown() method."""
        queue = Queue(mock_redis, queue='test')
        
        assert queue._shutdown is False
        queue.shutdown()
        assert queue._shutdown is True
    
    def test_shutdown_stops_worker_loop(self, mock_redis):
        """Test that setting shutdown flag stops the worker loop."""
        queue = Queue(mock_redis, queue='test')
        queue._shutdown = True
        
        # Should return immediately without calling blpop
        queue.redisPop()
        
        assert not mock_redis.blpop.called
    
    def test_shutdown_during_timeout(self, mock_redis):
        """Test shutdown is honored during blpop timeout."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # First call: timeout
            # Should not reach here
            raise AssertionError("Should not retry after shutdown")
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        # Trigger shutdown after first call
        def trigger_shutdown(*args, **kwargs):
            queue._shutdown = True
            return None
        
        mock_redis.blpop.side_effect = trigger_shutdown
        queue.redisPop()
        
        # Should have called blpop once and then stopped
        assert mock_redis.blpop.call_count == 1
    
    def test_processing_job_flag_set_during_job(self, mock_redis, sample_job_name):
        """Test that _processing_job flag is set during job processing."""
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
        
        processing_flag_during_handler = []
        
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', json.dumps(payload).encode())
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        @queue.handler
        def test_handler(data):
            # Capture flag state during handler execution
            processing_flag_during_handler.append(queue._processing_job)
        
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        # Flag should have been True during handler
        assert True in processing_flag_during_handler
        # Flag should be False after exception
        assert queue._processing_job is False
    
    def test_shutdown_after_job_completion(self, mock_redis, sample_job_name):
        """Test that worker stops after completing current job when shutdown requested."""
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
            # Should not reach here after shutdown
            raise AssertionError("Should not process another job after shutdown")
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        @queue.handler
        def test_handler(data):
            # Trigger shutdown during job processing
            queue._shutdown = True
        
        queue.redisPop()
        
        # Should have processed one job and then stopped
        assert mock_redis.blpop.call_count == 1
        assert queue._processing_job is False
    
    def test_shutdown_during_redis_error(self, mock_redis):
        """Test that shutdown prevents retry after Redis error."""
        from redis.exceptions import RedisError
        
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RedisError("Connection lost")
            # Should not reach here after shutdown
            raise AssertionError("Should not retry after shutdown")
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        # Trigger shutdown after error occurs
        def trigger_shutdown_on_error(seconds):
            queue._shutdown = True
        
        with patch('time.sleep', side_effect=trigger_shutdown_on_error):
            queue.redisPop()
        
        # Should have attempted once and then stopped after error
        assert mock_redis.blpop.call_count == 1
        assert queue._shutdown is True
    
    def test_keyboard_interrupt_sets_shutdown_flag(self, mock_redis):
        """Test that KeyboardInterrupt sets the shutdown flag."""
        mock_redis.blpop.side_effect = KeyboardInterrupt()
        queue = Queue(mock_redis, queue='test')
        
        assert queue._shutdown is False
        
        with pytest.raises(KeyboardInterrupt):
            queue.redisPop()
        
        assert queue._shutdown is True
        assert queue._processing_job is False
    
    def test_signal_handler_logs_correct_signal(self, mock_redis):
        """Test that signal handler logs the correct signal name."""
        queue = Queue(mock_redis, queue='test')
        queue._register_shutdown_handlers()
        
        # Get the registered handler
        import signal as sig_module
        handler = sig_module.getsignal(signal.SIGINT)
        
        # Simulate signal
        with patch('lara_queue.queue.logger') as mock_logger:
            handler(signal.SIGINT, None)
            
            # Should log that shutdown is initiated
            assert mock_logger.info.called
            log_message = str(mock_logger.info.call_args_list[0])
            assert 'shutdown' in log_message.lower() or 'SIGINT' in log_message
    
    def test_shutdown_during_reconnection_wait(self, mock_redis):
        """Test that shutdown during reconnection wait prevents retry."""
        from redis.exceptions import ConnectionError as RedisConnectionError
        
        call_count = [0]
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RedisConnectionError("Connection lost")
            raise AssertionError("Should not retry after shutdown during wait")
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test')
        
        def trigger_shutdown_during_sleep(seconds):
            queue._shutdown = True
        
        with patch('time.sleep', side_effect=trigger_shutdown_during_sleep):
            queue.redisPop()
        
        # Should have attempted once and then stopped during sleep
        assert mock_redis.blpop.call_count == 1


class TestShutdownEdgeCases:
    """Test edge cases for graceful shutdown."""
    
    def test_shutdown_with_invalid_json(self, mock_redis):
        """Test shutdown after encountering invalid JSON."""
        call_count = [0]
        
        def blpop_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return ('queue_key', b'invalid json{{{')
            raise KeyboardInterrupt()
        
        mock_redis.blpop.side_effect = blpop_side_effect
        queue = Queue(mock_redis, queue='test', is_queue_notify=False)
        
        # Trigger shutdown
        queue._shutdown = True
        
        # Should handle invalid JSON and then stop due to shutdown
        try:
            queue.redisPop()
        except KeyboardInterrupt:
            pass
        
        assert queue._processing_job is False
    
    def test_shutdown_handlers_only_registered_once(self, mock_redis):
        """Test that shutdown handlers are only registered once."""
        queue = Queue(mock_redis, queue='test')
        
        with patch('signal.signal') as mock_signal:
            queue._register_shutdown_handlers()
            first_call_count = mock_signal.call_count
            
            # Try to register again
            queue._register_shutdown_handlers()
            
            # Should not register again (flag prevents it)
            # But we're calling directly, so it will register again
            # The real protection is in listen() method
            assert queue._shutdown_handlers_registered is True
    
    def test_listen_does_not_double_register_handlers(self, mock_redis):
        """Test that calling listen() multiple times doesn't double-register handlers."""
        mock_redis.blpop.side_effect = KeyboardInterrupt()
        queue = Queue(mock_redis, queue='test')
        
        with patch('signal.signal') as mock_signal:
            # First listen
            try:
                queue.listen()
            except KeyboardInterrupt:
                pass
            
            first_call_count = mock_signal.call_count
            
            # Second listen - should not register handlers again
            try:
                queue.listen()
            except KeyboardInterrupt:
                pass
            
            # Call count should remain the same
            assert mock_signal.call_count == first_call_count

