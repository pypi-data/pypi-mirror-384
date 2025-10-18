"""Tests for Type Hints functionality."""
import pytest
import inspect
from typing import get_type_hints, get_origin, get_args, Dict, List, Optional, Union, Any, Callable, Tuple
from lara_queue import Queue


class TestTypeHints:
    """Tests for type hints coverage and correctness."""
    
    def test_queue_constructor_type_hints(self, mock_redis):
        """Test that Queue constructor has proper type hints."""
        hints = get_type_hints(Queue.__init__)
        
        # Check parameter types
        assert 'client' in hints
        assert 'queue' in hints
        assert 'driver' in hints
        assert 'appname' in hints
        assert 'prefix' in hints
        assert 'is_queue_notify' in hints
        assert 'is_horizon' in hints
        assert 'dead_letter_queue' in hints
        assert 'max_retries' in hints
        
        # Check return type
        assert hints.get('return') is None or hints.get('return') == type(None)
    
    def test_push_method_type_hints(self, mock_redis):
        """Test that push method has proper type hints."""
        hints = get_type_hints(Queue.push)
        
        # Check parameter types
        assert hints.get('name') == str
        assert get_origin(hints.get('dictObj')) is dict
        assert get_args(hints.get('dictObj')) == (str, Any)  # Dict[str, Any]
        
        # Check return type
        assert hints.get('return') is None or hints.get('return') == type(None)
    
    def test_listen_method_type_hints(self, mock_redis):
        """Test that listen method has proper type hints."""
        hints = get_type_hints(Queue.listen)
        
        # Check return type
        assert hints.get('return') is None or hints.get('return') == type(None)
    
    def test_handler_method_type_hints(self, mock_redis):
        """Test that handler method has proper type hints."""
        hints = get_type_hints(Queue.handler)
        
        # Check parameter types
        assert 'f' in hints
        
        # Check return type (should be Union[Callable, Any])
        return_type = hints.get('return')
        assert return_type is not None
    
    def test_shutdown_method_type_hints(self, mock_redis):
        """Test that shutdown method has proper type hints."""
        hints = get_type_hints(Queue.shutdown)
        
        # Check return type
        assert hints.get('return') is None or hints.get('return') == type(None)
    
    def test_dead_letter_queue_methods_type_hints(self, mock_redis):
        """Test that Dead Letter Queue methods have proper type hints."""
        queue = Queue(mock_redis, queue='test')
        
        # Test get_dead_letter_jobs
        hints = get_type_hints(queue.get_dead_letter_jobs)
        assert hints.get('limit') == int
        return_type = hints.get('return')
        assert get_origin(return_type) is list
        assert get_args(return_type) == (Dict[str, Any],)
        
        # Test reprocess_dead_letter_job
        hints = get_type_hints(queue.reprocess_dead_letter_job)
        assert get_origin(hints.get('job_data')) is dict
        assert hints.get('return') == bool
        
        # Test clear_dead_letter_queue
        hints = get_type_hints(queue.clear_dead_letter_queue)
        assert hints.get('return') == int
    
    def test_private_methods_type_hints(self, mock_redis):
        """Test that private methods have proper type hints."""
        queue = Queue(mock_redis, queue='test')
        
        # Test _get_job_id
        hints = get_type_hints(queue._get_job_id)
        assert get_origin(hints.get('job_data')) is dict
        assert hints.get('return') == str
        
        # Test _increment_retry_count
        hints = get_type_hints(queue._increment_retry_count)
        assert hints.get('job_id') == str
        assert hints.get('return') == int
        
        # Test _get_retry_count
        hints = get_type_hints(queue._get_retry_count)
        assert hints.get('job_id') == str
        assert hints.get('return') == int
        
        # Test _clear_retry_count
        hints = get_type_hints(queue._clear_retry_count)
        assert hints.get('job_id') == str
        assert hints.get('return') is None or hints.get('return') == type(None)
        
        # Test _should_retry
        hints = get_type_hints(queue._should_retry)
        assert hints.get('job_id') == str
        assert hints.get('return') == bool
        
        # Test _retry_job
        hints = get_type_hints(queue._retry_job)
        assert get_origin(hints.get('job_data')) is dict
        assert hints.get('delay') == int
        assert hints.get('return') is None or hints.get('return') == type(None)
        
        # Test _send_to_dead_letter_queue
        hints = get_type_hints(queue._send_to_dead_letter_queue)
        assert get_origin(hints.get('job_data')) is dict
        assert hints.get('error') == Exception
        assert hints.get('retry_count') == int
        assert hints.get('return') is None or hints.get('return') == type(None)
    
    def test_redis_methods_type_hints(self, mock_redis):
        """Test that Redis methods have proper type hints."""
        queue = Queue(mock_redis, queue='test')
        
        # Test redisPop
        hints = get_type_hints(queue.redisPop)
        assert hints.get('return') is None or hints.get('return') == type(None)
        
        # Test redisPush
        hints = get_type_hints(queue.redisPush)
        assert hints.get('name') == str
        assert get_origin(hints.get('dictObj')) is dict
        assert get_origin(hints.get('timeout')) is Union  # Optional[int] is Union[int, None]
        assert get_origin(hints.get('delay')) is Union  # Optional[int] is Union[int, None]
        assert hints.get('return') is None or hints.get('return') == type(None)
    
    def test_all_methods_have_type_hints(self, mock_redis):
        """Test that all public methods have type hints."""
        queue = Queue(mock_redis, queue='test')
        
        # Get all methods from the class
        methods = [method for method in dir(queue) 
                  if not method.startswith('__') and callable(getattr(queue, method))]
        
        methods_without_hints = []
        
        for method_name in methods:
            method = getattr(queue, method_name)
            if hasattr(method, '__annotations__'):
                # Check if method has type hints
                if not method.__annotations__:
                    methods_without_hints.append(method_name)
            else:
                methods_without_hints.append(method_name)
        
        # All public methods should have type hints
        assert not methods_without_hints, f"Methods without type hints: {methods_without_hints}"
    
    def test_type_hints_consistency(self, mock_redis):
        """Test that type hints are consistent across similar methods."""
        queue = Queue(mock_redis, queue='test')
        
        # Check that Dict[str, Any] is used consistently for job data
        job_data_methods = [
            '_get_job_id',
            '_retry_job', 
            '_send_to_dead_letter_queue',
            'reprocess_dead_letter_job'
        ]
        
        for method_name in job_data_methods:
            method = getattr(queue, method_name)
            hints = get_type_hints(method)
            
            # Find job_data parameter
            for param_name, param_type in hints.items():
                if 'job_data' in param_name or param_name == 'dictObj':
                    assert get_origin(param_type) is dict, f"{method_name}.{param_name} should be Dict[str, Any]"
                    break
    
    def test_optional_parameters_type_hints(self, mock_redis):
        """Test that optional parameters have correct Optional type hints."""
        queue = Queue(mock_redis, queue='test')
        
        # Test constructor optional parameters
        hints = get_type_hints(Queue.__init__)
        assert get_origin(hints.get('dead_letter_queue')) is Union  # Optional[str] is Union[str, None]
        
        # Test redisPush optional parameters
        hints = get_type_hints(queue.redisPush)
        assert get_origin(hints.get('timeout')) is Union  # Optional[int] is Union[int, None]
        assert get_origin(hints.get('delay')) is Union  # Optional[int] is Union[int, None]
    
    def test_return_type_annotations(self, mock_redis):
        """Test that return types are properly annotated."""
        queue = Queue(mock_redis, queue='test')
        
        # Methods that should return None
        none_return_methods = [
            'push', 'listen', 'shutdown', 'redisPop', 'redisPush',
            '_clear_retry_count', '_retry_job', '_send_to_dead_letter_queue'
        ]
        
        for method_name in none_return_methods:
            method = getattr(queue, method_name)
            hints = get_type_hints(method)
            return_type = hints.get('return')
            assert return_type is None or return_type == type(None), f"{method_name} should return None"
        
        # Methods that should return specific types
        typed_return_methods = {
            '_get_job_id': str,
            '_increment_retry_count': int,
            '_get_retry_count': int,
            '_should_retry': bool,
            'reprocess_dead_letter_job': bool,
            'clear_dead_letter_queue': int
        }
        
        for method_name, expected_type in typed_return_methods.items():
            method = getattr(queue, method_name)
            hints = get_type_hints(method)
            return_type = hints.get('return')
            assert return_type == expected_type, f"{method_name} should return {expected_type}"
    
    def test_type_hints_imports(self):
        """Test that all necessary typing imports are available."""
        from lara_queue.queue import Queue
        
        # Check that typing imports are available in the module
        import lara_queue.queue as queue_module
        
        # These should be available from typing
        typing_imports = ['Dict', 'List', 'Optional', 'Union', 'Any', 'Callable', 'Tuple']
        
        for import_name in typing_imports:
            assert hasattr(queue_module, import_name), f"{import_name} should be imported from typing"
    
    def test_type_hints_with_actual_usage(self, mock_redis):
        """Test that type hints work correctly with actual usage."""
        queue = Queue(mock_redis, queue='test')
        
        # Test with proper types
        job_data: dict = {'key': 'value'}
        job_id: str = queue._get_job_id(job_data)
        retry_count: int = queue._increment_retry_count(job_id)
        should_retry: bool = queue._should_retry(job_id)
        
        # These should not raise type errors
        assert isinstance(job_id, str)
        assert isinstance(retry_count, int)
        assert isinstance(should_retry, bool)
        
        # Test DLQ operations (with proper mock setup)
        mock_redis.lrange.return_value = []  # Mock empty list
        mock_redis.llen.return_value = 0     # Mock count
        mock_redis.delete.return_value = 1   # Mock delete success
        
        failed_jobs: list = queue.get_dead_letter_jobs(limit=10)
        cleared_count: int = queue.clear_dead_letter_queue()
        
        assert isinstance(failed_jobs, list)
        assert isinstance(cleared_count, int)
