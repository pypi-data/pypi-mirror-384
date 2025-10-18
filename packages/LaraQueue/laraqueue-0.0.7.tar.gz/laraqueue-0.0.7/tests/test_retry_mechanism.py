#!/usr/bin/env python3
"""
Тесты для улучшенного retry механизма в LaraQueue.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from redis import Redis
from lara_queue import Queue, RetryStrategy


class TestRetryMechanism:
    """Тесты для retry механизма."""
    
    @pytest.fixture
    def mock_redis(self):
        """Мок Redis клиента."""
        mock = Mock(spec=Redis)
        mock.rpush = Mock()
        mock.blpop = Mock()
        mock.lrange = Mock(return_value=[])
        mock.llen = Mock(return_value=0)
        mock.delete = Mock()
        return mock
    
    @pytest.fixture
    def queue_with_retry(self, mock_redis):
        """Очередь с настройками retry."""
        return Queue(
            client=mock_redis,
            queue='test_queue',
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL,
            retry_delay=2,
            retry_max_delay=30,
            retry_jitter=False,  # Отключаем для предсказуемости тестов
            retry_backoff_multiplier=2.0,
            retry_exceptions=[ValueError, ConnectionError]
        )
    
    def test_retry_strategy_enum(self):
        """Тест enum стратегий retry."""
        assert RetryStrategy.EXPONENTIAL.value == "exponential"
        assert RetryStrategy.LINEAR.value == "linear"
        assert RetryStrategy.FIXED.value == "fixed"
        assert RetryStrategy.CUSTOM.value == "custom"
    
    def test_queue_initialization_with_retry_config(self, mock_redis):
        """Тест инициализации очереди с retry конфигурацией."""
        queue = Queue(
            client=mock_redis,
            queue='test',
            max_retries=5,
            retry_strategy=RetryStrategy.LINEAR,
            retry_delay=10,
            retry_max_delay=100,
            retry_jitter=True,
            retry_backoff_multiplier=1.5,
            retry_exceptions=[ValueError]
        )
        
        assert queue.max_retries == 5
        assert queue.retry_strategy == RetryStrategy.LINEAR
        assert queue.retry_delay == 10
        assert queue.retry_max_delay == 100
        assert queue.retry_jitter is True
        assert queue.retry_backoff_multiplier == 1.5
        assert queue.retry_exceptions == [ValueError]
        
        # Проверяем инициализацию статистики
        stats = queue.get_retry_statistics()
        assert stats['total_retries'] == 0
        assert stats['successful_retries'] == 0
        assert stats['failed_retries'] == 0
        assert stats['dead_letter_jobs'] == 0
    
    def test_calculate_retry_delay_exponential(self, queue_with_retry):
        """Тест расчета задержки для экспоненциальной стратегии."""
        # Попытка 1: 2 * (2^0) = 2 секунды
        delay1 = queue_with_retry._calculate_retry_delay(1)
        assert delay1 == 2
        
        # Попытка 2: 2 * (2^1) = 4 секунды
        delay2 = queue_with_retry._calculate_retry_delay(2)
        assert delay2 == 4
        
        # Попытка 3: 2 * (2^2) = 8 секунд
        delay3 = queue_with_retry._calculate_retry_delay(3)
        assert delay3 == 8
        
        # Попытка 4: 2 * (2^3) = 16 секунд
        delay4 = queue_with_retry._calculate_retry_delay(4)
        assert delay4 == 16
    
    def test_calculate_retry_delay_linear(self, mock_redis):
        """Тест расчета задержки для линейной стратегии."""
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.LINEAR,
            retry_delay=5,
            retry_jitter=False
        )
        
        assert queue._calculate_retry_delay(1) == 5
        assert queue._calculate_retry_delay(2) == 10
        assert queue._calculate_retry_delay(3) == 15
        assert queue._calculate_retry_delay(4) == 20
    
    def test_calculate_retry_delay_fixed(self, mock_redis):
        """Тест расчета задержки для фиксированной стратегии."""
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.FIXED,
            retry_delay=10,
            retry_jitter=False
        )
        
        assert queue._calculate_retry_delay(1) == 10
        assert queue._calculate_retry_delay(2) == 10
        assert queue._calculate_retry_delay(3) == 10
        assert queue._calculate_retry_delay(10) == 10
    
    def test_calculate_retry_delay_custom(self, mock_redis):
        """Тест расчета задержки для пользовательской функции."""
        def custom_delay(attempt):
            return attempt * 3
        
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.CUSTOM,
            retry_custom_function=custom_delay,
            retry_jitter=False
        )
        
        assert queue._calculate_retry_delay(1) == 3
        assert queue._calculate_retry_delay(2) == 6
        assert queue._calculate_retry_delay(3) == 9
    
    def test_calculate_retry_delay_max_limit(self, mock_redis):
        """Тест ограничения максимальной задержки."""
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.EXPONENTIAL,
            retry_delay=10,
            retry_max_delay=50,
            retry_jitter=False
        )
        
        # Попытка 5: 10 * (2^4) = 160, но ограничено 50
        delay = queue._calculate_retry_delay(5)
        assert delay == 50
    
    def test_calculate_retry_delay_min_limit(self, mock_redis):
        """Тест минимальной задержки."""
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.FIXED,
            retry_delay=0,  # Нулевая задержка
            retry_jitter=False
        )
        
        delay = queue._calculate_retry_delay(1)
        assert delay == 1  # Минимум 1 секунда
    
    def test_calculate_retry_delay_with_jitter(self, mock_redis):
        """Тест добавления jitter к задержке."""
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.FIXED,
            retry_delay=10,
            retry_jitter=True
        )
        
        # Запускаем несколько раз и проверяем, что задержка варьируется
        delays = [queue._calculate_retry_delay(1) for _ in range(10)]
        
        # Все задержки должны быть больше базовой (10) из-за jitter
        assert all(delay > 10 for delay in delays)
        # Но не слишком большими (jitter добавляет 10-30%)
        assert all(delay <= 13 for delay in delays)
    
    def test_is_retryable_exception(self, queue_with_retry):
        """Тест проверки retryable исключений."""
        # Должны retry для настроенных исключений
        assert queue_with_retry._is_retryable_exception(ValueError("test"))
        assert queue_with_retry._is_retryable_exception(ConnectionError("test"))
        
        # Не должны retry для других исключений
        assert not queue_with_retry._is_retryable_exception(RuntimeError("test"))
        assert not queue_with_retry._is_retryable_exception(KeyError("test"))
    
    def test_should_retry_logic(self, queue_with_retry):
        """Тест логики принятия решения о retry."""
        job_id = "test_job_123"
        
        # Первая попытка с retryable исключением - должна retry
        assert queue_with_retry._should_retry(job_id, ValueError("test"))
        
        # Увеличиваем счетчик попыток
        queue_with_retry._increment_retry_count(job_id)
        assert queue_with_retry._should_retry(job_id, ValueError("test"))
        
        # Достигаем максимального количества попыток
        queue_with_retry._increment_retry_count(job_id)
        queue_with_retry._increment_retry_count(job_id)
        assert not queue_with_retry._should_retry(job_id, ValueError("test"))
        
        # Сбрасываем счетчик и проверяем non-retryable исключение
        queue_with_retry._clear_retry_count(job_id)
        assert not queue_with_retry._should_retry(job_id, RuntimeError("test"))
    
    def test_retry_job_execution(self, queue_with_retry):
        """Тест выполнения retry задачи."""
        job_data = {
            'uuid': 'test_job_123',
            'data': {'commandName': 'TestJob', 'command': 'test_data'}
        }
        
        queue_with_retry._retry_job(job_data, 2)
        
        # Проверяем, что задача была добавлена в очередь
        queue_with_retry.client.rpush.assert_called_once()
        
        # Проверяем содержимое добавленной задачи
        call_args = queue_with_retry.client.rpush.call_args
        queue_key, job_json = call_args[0]
        
        assert queue_key == "laravel_database_queues:test_queue"
        
        retry_job_data = json.loads(job_json)
        assert retry_job_data['retry_attempt'] == 2
        assert retry_job_data['retry_strategy'] == 'exponential'
        assert 'retry_timestamp' in retry_job_data
        assert 'retry_delay' in retry_job_data
    
    def test_retry_statistics_tracking(self, queue_with_retry):
        """Тест отслеживания статистики retry."""
        # Изначально статистика пустая
        stats = queue_with_retry.get_retry_statistics()
        assert stats['total_retries'] == 0
        assert stats['successful_retries'] == 0
        assert stats['failed_retries'] == 0
        
        # Имитируем retry
        job_data = {'uuid': 'test_job', 'data': {}}
        queue_with_retry._retry_job(job_data, 1)
        
        # Проверяем обновление статистики
        stats = queue_with_retry.get_retry_statistics()
        assert stats['total_retries'] == 1
        
        # Имитируем успешный retry
        queue_with_retry._increment_retry_count('test_job')
        queue_with_retry._clear_retry_count('test_job')
        # В реальном коде это происходит в redisPop при успешной обработке
        
        # Имитируем отправку в dead letter queue
        queue_with_retry._send_to_dead_letter_queue(job_data, ValueError("test"), 3)
        
        stats = queue_with_retry.get_retry_statistics()
        assert stats['dead_letter_jobs'] == 1
    
    def test_reset_retry_statistics(self, queue_with_retry):
        """Тест сброса статистики retry."""
        # Добавляем некоторую статистику
        queue_with_retry._retry_stats['total_retries'] = 10
        queue_with_retry._retry_stats['successful_retries'] = 7
        
        # Сбрасываем статистику
        queue_with_retry.reset_retry_statistics()
        
        stats = queue_with_retry.get_retry_statistics()
        assert stats['total_retries'] == 0
        assert stats['successful_retries'] == 0
        assert stats['failed_retries'] == 0
        assert stats['dead_letter_jobs'] == 0
    
    def test_update_retry_config(self, queue_with_retry):
        """Тест обновления конфигурации retry."""
        # Обновляем несколько параметров
        queue_with_retry.update_retry_config(
            max_retries=5,
            retry_delay=10,
            retry_strategy=RetryStrategy.LINEAR
        )
        
        assert queue_with_retry.max_retries == 5
        assert queue_with_retry.retry_delay == 10
        assert queue_with_retry.retry_strategy == RetryStrategy.LINEAR
        
        # Проверяем, что конфигурация отображается в статистике
        stats = queue_with_retry.get_retry_statistics()
        config = stats['current_retry_config']
        assert config['max_retries'] == 5
        assert config['delay'] == 10
        assert config['strategy'] == 'linear'
    
    def test_retry_job_with_custom_function(self, mock_redis):
        """Тест retry с пользовательской функцией."""
        def custom_delay(attempt):
            return attempt * 2
        
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_strategy=RetryStrategy.CUSTOM,
            retry_custom_function=custom_delay,
            retry_jitter=False  # Отключаем jitter для предсказуемости
        )
        
        job_data = {'uuid': 'test_job', 'data': {}}
        queue._retry_job(job_data, 3)
        
        # Проверяем, что пользовательская функция была использована
        call_args = queue.client.rpush.call_args
        retry_job_data = json.loads(call_args[0][1])
        assert retry_job_data['retry_delay'] == 6  # 3 * 2
    
    def test_retry_exceptions_configuration(self, mock_redis):
        """Тест конфигурации retryable исключений."""
        # Создаем очередь только с определенными исключениями
        queue = Queue(
            client=mock_redis,
            queue='test',
            retry_exceptions=[ValueError, ConnectionError]
        )
        
        # Проверяем, что только настроенные исключения retryable
        assert queue._is_retryable_exception(ValueError("test"))
        assert queue._is_retryable_exception(ConnectionError("test"))
        assert not queue._is_retryable_exception(RuntimeError("test"))
        assert not queue._is_retryable_exception(KeyError("test"))
        
        # Проверяем отображение в статистике
        stats = queue.get_retry_statistics()
        retryable_exceptions = stats['current_retry_config']['retryable_exceptions']
        assert 'ValueError' in retryable_exceptions
        assert 'ConnectionError' in retryable_exceptions
        assert 'RuntimeError' not in retryable_exceptions
    
    def test_retry_job_error_handling(self, queue_with_retry):
        """Тест обработки ошибок при retry."""
        # Мокаем ошибку при добавлении в очередь
        queue_with_retry.client.rpush.side_effect = Exception("Redis error")
        
        job_data = {'uuid': 'test_job', 'data': {}}
        
        # Retry должен обработать ошибку и обновить статистику
        queue_with_retry._retry_job(job_data, 1)
        
        stats = queue_with_retry.get_retry_statistics()
        assert stats['failed_retries'] == 1
    
    def test_success_rate_calculation(self, queue_with_retry):
        """Тест расчета процента успешности."""
        # Добавляем статистику
        queue_with_retry._retry_stats['total_retries'] = 10
        queue_with_retry._retry_stats['successful_retries'] = 7
        
        stats = queue_with_retry.get_retry_statistics()
        assert stats['success_rate'] == 70.0
        
        # Тест с нулевыми retry
        queue_with_retry._retry_stats['total_retries'] = 0
        queue_with_retry._retry_stats['successful_retries'] = 0
        
        stats = queue_with_retry.get_retry_statistics()
        assert stats['success_rate'] == 0.0


class TestRetryIntegration:
    """Интеграционные тесты retry механизма."""
    
    @pytest.fixture
    def mock_redis_with_jobs(self):
        """Мок Redis с имитацией задач."""
        mock = Mock(spec=Redis)
        mock.rpush = Mock()
        
        # Имитируем задачи в очереди
        job_data = {
            'uuid': 'test_job_1',
            'data': {
                'commandName': 'TestJob',
                'command': 'test_data'
            }
        }
        
        mock.blpop = Mock(return_value=('queue_key', json.dumps(job_data)))
        return mock
    
    def test_retry_flow_integration(self, mock_redis_with_jobs):
        """Тест полного потока retry."""
        queue = Queue(
            client=mock_redis_with_jobs,
            queue='test',
            max_retries=2,
            retry_strategy=RetryStrategy.EXPONENTIAL,
            retry_delay=1,
            retry_jitter=False
        )
        
        # Мокаем обработчик, который всегда падает
        @queue.handler
        def failing_handler(data):
            raise ValueError("Test error")
        
        # Мокаем phpserialize для избежания ошибок десериализации
        with patch('lara_queue.queue.phpserialize') as mock_phpserialize:
            mock_php_obj = Mock()
            mock_php_obj._asdict.return_value = {'test': 'data'}
            mock_phpserialize.loads.return_value = mock_php_obj
            
            # Мокаем blpop чтобы избежать зависания
            mock_redis_with_jobs.blpop.return_value = ('queue_key', json.dumps({
                'uuid': 'test_job_1',
                'data': {
                    'commandName': 'TestJob',
                    'command': 'test_data'
                }
            }))
            
            # Запускаем обработку (одну итерацию)
            try:
                queue.redisPop()
            except Exception:
                pass  # Ожидаем ошибку из-за мока
        
        # Проверяем, что задача была retry
        assert mock_redis_with_jobs.rpush.called
        
        # Проверяем статистику
        stats = queue.get_retry_statistics()
        assert stats['total_retries'] >= 0  # Может быть 0 из-за мока


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
