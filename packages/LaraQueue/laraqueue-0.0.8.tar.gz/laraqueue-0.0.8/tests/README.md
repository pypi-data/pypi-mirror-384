# Тесты для LaraQueue

## Структура тестов

```
tests/
├── __init__.py              # Инициализация пакета тестов
├── conftest.py              # Фикстуры и конфигурация pytest
├── test_queue_unit.py       # Unit-тесты с моками Redis
├── test_integration.py      # Интеграционные тесты с реальным Redis
├── test_manual.py           # Скрипт для ручного тестирования
└── README.md                # Эта документация
```

## Установка зависимостей

```bash
pip install -e .
pip install -r requirements-dev.txt
```

## Запуск тестов

### Все unit-тесты (без Redis):
```bash
pytest -m "not integration"
```

### Все тесты, включая интеграционные:
```bash
# Убедитесь, что Redis запущен на localhost:6379
redis-server

# Запустите тесты
pytest
```

### Только интеграционные тесты:
```bash
pytest -m integration
```

### С покрытием кода:
```bash
pytest --cov=lara_queue --cov-report=html
```

### Конкретный файл тестов:
```bash
pytest tests/test_queue_unit.py
pytest tests/test_integration.py -v
```

### Конкретный тест:
```bash
pytest tests/test_queue_unit.py::TestQueuePush::test_push_calls_redis_rpush
```

## Ручное тестирование

Для интерактивного тестирования с Laravel:

```bash
python -m tests.test_manual
```

Это запустит интерактивное меню с опциями:
1. Отправить задачу в Laravel очередь
2. Прослушивать Python очередь (получать задачи от Laravel)
3. Проверить содержимое Redis очередей
4. Комбинированный тест

## Требования для интеграционных тестов

- Redis server запущен на `localhost:6379`
- База данных 15 используется для тестов (автоматически очищается)

## Требования для ручного тестирования с Laravel

1. Установите Laravel приложение
2. Настройте Redis драйвер для очередей в `.env`:
   ```
   QUEUE_CONNECTION=redis
   REDIS_HOST=127.0.0.1
   REDIS_PASSWORD=null
   REDIS_PORT=6379
   ```

3. Создайте тестовую задачу в Laravel:

```php
<?php

namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class TestJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $a, $b, $c;

    public function __construct($a, $b, $c)
    {
        $this->a = $a;
        $this->b = $b;
        $this->c = $c;
    }

    public function handle()
    {
        Log::info('TEST: ' . $this->a . ' ' . $this->b . ' ' . $this->c);
    }
}
```

4. Отправьте задачу из Laravel в Python:
```php
dispatch(new TestJob('hello', 'from', 'laravel'))->onQueue('python');
```

5. Запустите Python listener:
```bash
python -m tests.test_manual
# Выберите опцию 2
```

6. Отправьте задачу из Python в Laravel:
```bash
python -m tests.test_manual
# Выберите опцию 1
```

7. Запустите Laravel worker:
```bash
php artisan queue:work --queue=laravel
```

## Отладка

Если тесты падают:

1. Проверьте, что Redis запущен:
   ```bash
   redis-cli ping
   # Должно вернуть: PONG
   ```

2. Проверьте версию Python (требуется >= 3.6):
   ```bash
   python --version
   ```

3. Проверьте установленные пакеты:
   ```bash
   pip list | grep -E "redis|pyee|pytest"
   ```

4. Запустите тесты с подробным выводом:
   ```bash
   pytest -vv -s
   ```

## CI/CD

Для CI/CD окружений рекомендуется:

```bash
# Запуск только unit-тестов (без Redis)
pytest -m "not integration" --tb=short

# Для интеграционных тестов используйте Docker:
docker run -d -p 6379:6379 redis:7-alpine
pytest
```

## Известные проблемы

1. **Интеграционные тесты зависают** - убедитесь, что Redis запущен
2. **Permission denied при подключении к Redis** - проверьте права доступа
3. **Tests не находятся** - убедитесь, что установили пакет: `pip install -e .`

