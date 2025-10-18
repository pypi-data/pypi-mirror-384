#!/usr/bin/env python3
"""
Пример использования улучшенного retry механизма в LaraQueue.

Этот пример демонстрирует различные стратегии retry и их настройку.
"""

import logging
import time
import random
from redis import Redis
from lara_queue import Queue, RetryStrategy

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция с примерами retry механизма."""
    
    # Подключение к Redis
    redis_client = Redis(host='localhost', port=6379, db=0)
    
    print("🔄 Примеры использования Retry механизма в LaraQueue")
    print("=" * 60)
    
    # Пример 1: Экспоненциальная стратегия retry (по умолчанию)
    print("\n1️⃣ Экспоненциальная стратегия retry")
    print("-" * 40)
    
    queue_exponential = Queue(
        client=redis_client,
        queue='retry_exponential',
        max_retries=3,
        retry_strategy=RetryStrategy.EXPONENTIAL,
        retry_delay=2,  # Начальная задержка 2 секунды
        retry_max_delay=30,  # Максимальная задержка 30 секунд
        retry_jitter=True,  # Добавляем случайность
        retry_backoff_multiplier=2.0,  # Умножаем задержку на 2 каждый раз
        retry_exceptions=[ValueError, ConnectionError]  # Retry только для этих исключений
    )
    
    @queue_exponential.handler
    def handle_exponential_retry(data):
        """Обработчик с имитацией ошибок для демонстрации retry."""
        logger.info(f"Обработка задачи: {data}")
        
        # Имитируем случайные ошибки
        if random.random() < 0.7:  # 70% вероятность ошибки
            raise ValueError("Случайная ошибка для демонстрации retry")
        
        logger.info("✅ Задача успешно обработана!")
    
    # Пример 2: Линейная стратегия retry
    print("\n2️⃣ Линейная стратегия retry")
    print("-" * 40)
    
    queue_linear = Queue(
        client=redis_client,
        queue='retry_linear',
        max_retries=4,
        retry_strategy=RetryStrategy.LINEAR,
        retry_delay=5,  # Каждая попытка будет с задержкой 5, 10, 15, 20 секунд
        retry_jitter=False  # Без jitter для предсказуемости
    )
    
    @queue_linear.handler
    def handle_linear_retry(data):
        """Обработчик с линейной стратегией retry."""
        logger.info(f"Обработка задачи (линейная): {data}")
        
        if random.random() < 0.6:  # 60% вероятность ошибки
            raise ConnectionError("Ошибка соединения")
        
        logger.info("✅ Задача успешно обработана!")
    
    # Пример 3: Фиксированная задержка
    print("\n3️⃣ Фиксированная задержка")
    print("-" * 40)
    
    queue_fixed = Queue(
        client=redis_client,
        queue='retry_fixed',
        max_retries=3,
        retry_strategy=RetryStrategy.FIXED,
        retry_delay=10,  # Всегда 10 секунд задержки
        retry_jitter=True  # Добавляем немного случайности
    )
    
    @queue_fixed.handler
    def handle_fixed_retry(data):
        """Обработчик с фиксированной задержкой."""
        logger.info(f"Обработка задачи (фиксированная): {data}")
        
        if random.random() < 0.5:  # 50% вероятность ошибки
            raise RuntimeError("Временная ошибка")
        
        logger.info("✅ Задача успешно обработана!")
    
    # Пример 4: Пользовательская функция retry
    print("\n4️⃣ Пользовательская функция retry")
    print("-" * 40)
    
    def custom_retry_delay(attempt: int) -> int:
        """Пользовательская функция расчета задержки."""
        # Fibonacci-based delay: 1, 1, 2, 3, 5, 8, 13...
        if attempt <= 1:
            return 1
        elif attempt == 2:
            return 1
        else:
            a, b = 1, 1
            for _ in range(attempt - 2):
                a, b = b, a + b
            return min(b, 20)  # Максимум 20 секунд
    
    queue_custom = Queue(
        client=redis_client,
        queue='retry_custom',
        max_retries=5,
        retry_strategy=RetryStrategy.CUSTOM,
        retry_custom_function=custom_retry_delay,
        retry_exceptions=[Exception]  # Retry для всех исключений
    )
    
    @queue_custom.handler
    def handle_custom_retry(data):
        """Обработчик с пользовательской функцией retry."""
        logger.info(f"Обработка задачи (пользовательская): {data}")
        
        if random.random() < 0.8:  # 80% вероятность ошибки
            raise Exception("Ошибка для демонстрации пользовательского retry")
        
        logger.info("✅ Задача успешно обработана!")
    
    # Пример 5: Демонстрация статистики и управления
    print("\n5️⃣ Статистика и управление retry")
    print("-" * 40)
    
    # Добавляем несколько задач для демонстрации
    test_data = [
        {'task_id': 1, 'type': 'email', 'recipient': 'user1@example.com'},
        {'task_id': 2, 'type': 'notification', 'message': 'Hello World'},
        {'task_id': 3, 'type': 'report', 'data': 'analytics_data'},
    ]
    
    # Отправляем задачи в разные очереди
    for data in test_data:
        queue_exponential.push('TestJob', data)
        queue_linear.push('TestJob', data)
        queue_fixed.push('TestJob', data)
        queue_custom.push('TestJob', data)
    
    print("📊 Статистика retry (до обработки):")
    for name, queue in [
        ("Экспоненциальная", queue_exponential),
        ("Линейная", queue_linear),
        ("Фиксированная", queue_fixed),
        ("Пользовательская", queue_custom)
    ]:
        stats = queue.get_retry_statistics()
        print(f"  {name}: {stats['total_retries']} retry, {stats['success_rate']:.1f}% успех")
    
    # Демонстрация изменения конфигурации во время выполнения
    print("\n🔧 Изменение конфигурации retry во время выполнения:")
    queue_exponential.update_retry_config(
        max_retries=5,
        retry_delay=1,
        retry_max_delay=60
    )
    
    # Показываем обновленную конфигурацию
    updated_stats = queue_exponential.get_retry_statistics()
    print(f"Обновленная конфигурация: {updated_stats['current_retry_config']}")
    
    print("\n📝 Рекомендации по использованию:")
    print("• Экспоненциальная стратегия - для временных сбоев сети/БД")
    print("• Линейная стратегия - для предсказуемых задержек")
    print("• Фиксированная задержка - для простых случаев")
    print("• Пользовательская функция - для сложной логики retry")
    print("• Используйте jitter=True для избежания thundering herd")
    print("• Настройте retry_exceptions для контроля типов ошибок")
    
    print("\n🚀 Запуск обработки задач...")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        # Запускаем обработку (в реальном приложении это будет в отдельных процессах)
        print("Обработка задач в очереди 'retry_exponential'...")
        # queue_exponential.listen()  # Раскомментируйте для реального запуска
        
    except KeyboardInterrupt:
        print("\n⏹️ Остановка обработки...")
        
        # Показываем финальную статистику
        print("\n📊 Финальная статистика retry:")
        for name, queue in [
            ("Экспоненциальная", queue_exponential),
            ("Линейная", queue_linear),
            ("Фиксированная", queue_fixed),
            ("Пользовательская", queue_custom)
        ]:
            stats = queue.get_retry_statistics()
            print(f"  {name}:")
            print(f"    Всего retry: {stats['total_retries']}")
            print(f"    Успешных: {stats['successful_retries']}")
            print(f"    Неудачных: {stats['failed_retries']}")
            print(f"    В dead letter: {stats['dead_letter_jobs']}")
            print(f"    Процент успеха: {stats['success_rate']:.1f}%")

if __name__ == "__main__":
    main()
