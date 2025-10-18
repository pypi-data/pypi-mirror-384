## LaraQueue

Simple and lightweight queue synchronization between Python and Laravel using Redis. Process Laravel jobs in Python and vice versa.

> **Fork Notice:** This package is a fork of the original [python-laravel-queue](https://github.com/sinanbekar/python-laravel-queue) by [@sinanbekar](https://github.com/sinanbekar). This version includes critical bug fixes, comprehensive tests, and updated compatibility with newer dependencies.

**NOTE: This package is in beta and only Redis is supported currently. Production usage is not recommended until stable release.**

### ✨ New Features

#### 🛡️ Robust Error Handling (v0.0.3)

The package now includes a comprehensive error handling system:

- **Automatic reconnection** to Redis when connection is lost
- **Retry logic** with smart delays
- **Detailed logging** of all operations and errors
- **Protection against invalid data** - worker continues running when encountering problematic messages

#### 🔄 Graceful Shutdown (v0.0.3)

Advanced signal handling for clean worker termination:

- **Signal handlers** for SIGINT (Ctrl+C) and SIGTERM (kill)
- **Current job completion** - waits for job to finish before stopping
- **Automatic registration** - handlers are set up when you call `listen()`
- **Manual shutdown** - programmatically trigger shutdown with `queue.shutdown()`
- **No job loss** - ensures current job completes successfully

#### 💀 Dead Letter Queue (v0.0.4)

Advanced job failure handling with retry mechanisms:

- **Automatic retry** with exponential backoff (5s, 10s, 20s, 40s, max 60s)
- **Configurable max retries** (default: 3 attempts)
- **Dead letter queue** for permanently failed jobs
- **Job reprocessing** from dead letter queue
- **Comprehensive failure tracking** with error details and timestamps

#### 🔄 Advanced Retry Mechanism (v0.0.5)

Powerful and flexible retry system with multiple strategies:

- **Multiple retry strategies**: Exponential, Linear, Fixed, Custom
- **Configurable retry parameters**: delays, max attempts, jitter
- **Exception-based retry control**: retry only for specific error types
- **Retry statistics and monitoring**: track success rates and performance
- **Runtime configuration updates**: change retry settings without restart
- **Jitter support**: prevent thundering herd problems

#### 📊 Metrics & Monitoring (v0.0.5)

Comprehensive metrics collection and performance monitoring:

- **Real-time metrics**: track processed, successful, and failed jobs
- **Performance analytics**: average processing time, throughput, min/max times
- **Job type breakdown**: metrics per job type with success rates
- **Error tracking**: detailed error counts and types
- **Historical data**: configurable history size for trend analysis
- **Memory efficient**: automatic cleanup of old metrics data

```python
# Create queue with Dead Letter Queue
queue = Queue(
    redis_client, 
    queue='email_worker',
    dead_letter_queue='email_failed',  # Custom DLQ name
    max_retries=3  # Retry failed jobs 3 times
)

# Get failed jobs
failed_jobs = queue.get_dead_letter_jobs(limit=100)

# Reprocess a failed job
queue.reprocess_dead_letter_job(failed_jobs[0])

# Clear all failed jobs
queue.clear_dead_letter_queue()
```

#### 🔄 Advanced Retry Configuration

```python
from lara_queue import Queue, RetryStrategy

# Exponential backoff strategy (default)
queue_exponential = Queue(
    redis_client,
    queue='email_worker',
    max_retries=5,
    retry_strategy=RetryStrategy.EXPONENTIAL,
    retry_delay=2,                    # Initial delay: 2s
    retry_max_delay=60,               # Max delay: 60s
    retry_backoff_multiplier=2.0,     # Multiply by 2 each time
    retry_jitter=True,                # Add randomness to prevent thundering herd
    retry_exceptions=[ValueError, ConnectionError]  # Only retry these exceptions
)

# Linear retry strategy
queue_linear = Queue(
    redis_client,
    queue='notification_worker',
    max_retries=4,
    retry_strategy=RetryStrategy.LINEAR,
    retry_delay=5,                    # Each retry: 5s, 10s, 15s, 20s
    retry_jitter=False                # No randomness for predictable delays
)

# Fixed delay strategy
queue_fixed = Queue(
    redis_client,
    queue='report_worker',
    max_retries=3,
    retry_strategy=RetryStrategy.FIXED,
    retry_delay=10,                   # Always 10 seconds between retries
    retry_jitter=True                 # Add some randomness
)

# Custom retry function
def fibonacci_retry_delay(attempt: int) -> int:
    """Fibonacci-based retry delay: 1, 1, 2, 3, 5, 8, 13..."""
    if attempt <= 1:
        return 1
    elif attempt == 2:
        return 1
    else:
        a, b = 1, 1
        for _ in range(attempt - 2):
            a, b = b, a + b
        return min(b, 20)  # Cap at 20 seconds

queue_custom = Queue(
    redis_client,
    queue='analytics_worker',
    max_retries=6,
    retry_strategy=RetryStrategy.CUSTOM,
    retry_custom_function=fibonacci_retry_delay,
    retry_exceptions=[Exception]      # Retry for all exceptions
)

# Monitor retry statistics
stats = queue_exponential.get_retry_statistics()
print(f"Total retries: {stats['total_retries']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Dead letter jobs: {stats['dead_letter_jobs']}")

# Update retry configuration at runtime
queue_exponential.update_retry_config(
    max_retries=7,
    retry_delay=1,
    retry_strategy=RetryStrategy.LINEAR
)

# Reset retry statistics
queue_exponential.reset_retry_statistics()
```

#### 📊 Metrics Configuration

```python
from lara_queue import Queue, MetricsCollector

# Create queue with metrics enabled
queue = Queue(
    redis_client,
    queue='monitored_worker',
    enable_metrics=True,              # Enable metrics collection
    metrics_history_size=1000         # Keep last 1000 jobs in history
)

# Get comprehensive metrics
metrics = queue.get_metrics()
print(f"Total processed: {metrics['general']['total_processed']}")
print(f"Success rate: {metrics['general']['success_rate']:.1f}%")
print(f"Throughput: {metrics['performance']['throughput_per_second']:.2f} jobs/sec")
print(f"Avg processing time: {metrics['performance']['avg_processing_time']:.3f}s")

# Get metrics for specific job type
email_metrics = queue.get_job_type_metrics('App\\Jobs\\EmailJob')
if email_metrics:
    print(f"Email jobs: {email_metrics['total']} total, {email_metrics['success_rate']:.1f}% success")

# Get recent job history
recent_jobs = queue.get_recent_jobs(limit=10)
for job in recent_jobs:
    status = "✅" if job['success'] else "❌"
    print(f"{status} {job['name']} - {job['processing_time']:.3f}s")

# Get performance summary
summary = queue.get_performance_summary()
print(f"Uptime: {summary['general']['uptime_seconds']:.1f}s")
print(f"Total retries: {summary['general']['total_retries']}")

# Reset metrics
queue.reset_metrics()

# Disable metrics for better performance
queue_no_metrics = Queue(
    redis_client,
    queue='high_performance_worker',
    enable_metrics=False  # Disable metrics collection
)
```

#### 🏷️ Type Hints (v0.0.4)

Complete type annotations for better IDE support and code safety:

- **Full type coverage** for all methods and parameters
- **IDE autocompletion** and type checking
- **Runtime type safety** with proper annotations
- **Optional parameters** with `Optional[T]` types
- **Generic types** for collections and data structures

```python
from typing import Dict, List, Any, Optional
from lara_queue import Queue

# Typed queue creation
queue: Queue = Queue(
    client=redis_client,
    queue='typed_worker',
    dead_letter_queue='typed_failed',
    max_retries=3
)

# Typed job processing
@queue.handler
def process_email(data: Dict[str, Any]) -> None:
    email_type: str = data.get('type', 'unknown')
    recipient: str = data.get('recipient', 'unknown')
    subject: Optional[str] = data.get('subject')
    
    # Type-safe processing
    if 'invalid' in recipient.lower():
        raise ValueError(f"Invalid email address: {recipient}")
    
    print(f"Email sent to {recipient}")

# Typed DLQ operations
failed_jobs: List[Dict[str, Any]] = queue.get_dead_letter_jobs(limit=100)
success: bool = queue.reprocess_dead_letter_job(failed_jobs[0])
cleared_count: int = queue.clear_dead_letter_queue()
```

```python
import logging

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('lara_queue')
logger.setLevel(logging.DEBUG)
```

### Installation

```bash
pip install LaraQueue
```

### Usage

#### Listen for jobs in Python

```python
from lara_queue import Queue
from redis import Redis

r = Redis(host='localhost', port=6379, db=0)
queue_python = Queue(r, queue='python')

@queue_python.handler
def handle(data):
    name = data['name']  # job name
    job_data = data['data']  # job data
    print('Processing: ' + job_data['a'] + ' ' + job_data['b'] + ' ' + job_data['c'])

queue_python.listen()
```

#### Send jobs from Laravel

```php
<?php
$job = new \App\Jobs\TestJob('hi', 'send to', 'python');
dispatch($job)->onQueue('python');
```

#### Send jobs to Laravel from Python

```python
from lara_queue import Queue
from redis import Redis

r = Redis(host='localhost', port=6379, db=0)
queue_laravel = Queue(r, queue='laravel')
queue_laravel.push('App\\Jobs\\TestJob', {'a': 'hello', 'b': 'send to', 'c': 'laravel'})
```

#### TestJob in Laravel

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

    /**
     * Create a new job instance.
     *
     * @return void
     */
    public function __construct($a, $b, $c)
    {
        $this->a = $a;
        $this->b = $b;
        $this->c = $c;
    }

    /**
     * Execute the job.
     *
     * @return void
     */
    public function handle()
    {
        Log::info('TEST: ' . $this->a . ' ' . $this->b . ' ' . $this->c);
    }
}
```

#### Process jobs in Laravel

You need to `:listen` (or `:work`) the preferred queue name to handle jobs sent from Python in Laravel.

```bash
php artisan queue:listen --queue=laravel
```

### Graceful Shutdown Example

```python
import logging
from lara_queue import Queue
from redis import Redis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = Redis(host='localhost', port=6379, db=0)
queue = Queue(r, queue='python_worker')

@queue.handler
def handle_job(data):
    logger.info(f"Processing job: {data['name']}")
    # Simulate some work
    import time
    time.sleep(5)
    logger.info("Job completed!")

logger.info("Worker starting...")
logger.info("Press Ctrl+C to trigger graceful shutdown")
logger.info("Current job will complete before stopping")

try:
    queue.listen()  # Signal handlers auto-registered
except KeyboardInterrupt:
    logger.info("Worker stopped gracefully")
```

### Manual Shutdown Example

```python
queue = Queue(r, queue='test')

@queue.handler
def handle_job(data):
    # Process job
    process_data(data)
    
    # Trigger shutdown programmatically
    if should_stop():
        queue.shutdown()

queue.listen()
```

### Error Handling Example

```python
from lara_queue import Queue
from redis import Redis
from redis.exceptions import ConnectionError

try:
    r = Redis(host='localhost', port=6379, db=0)
    queue = Queue(r, queue='python_worker')
    
    @queue.handler
    def handle_job(data):
        print(f"Processing job: {data['name']}")
    
    queue.listen()  # Worker is now resilient to Redis errors!
    
except ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")
except KeyboardInterrupt:
    print("Worker stopped gracefully")
```

### Retry Strategy Recommendations

| Strategy | Use Case | Example |
|----------|----------|---------|
| **Exponential** | Network/DB temporary failures | API calls, database connections |
| **Linear** | Predictable resource limits | Rate-limited APIs, queue backpressure |
| **Fixed** | Simple retry scenarios | File processing, simple validations |
| **Custom** | Complex business logic | Fibonacci delays, circuit breaker patterns |

**Best Practices:**
- Use **jitter=True** to prevent thundering herd problems
- Set **retry_exceptions** to only retry recoverable errors
- Monitor **retry statistics** to optimize your retry strategy
- Use **dead letter queues** for permanently failed jobs
- Consider **max_delay** limits to prevent excessive wait times

### Features

- ✅ **Redis driver support** - Queue communication between Python and Laravel
- ✅ **Bidirectional job processing** - Send and receive jobs in both directions
- ✅ **PHP object serialization** - Compatible with Laravel's job serialization format
- ✅ **Event-driven architecture** - Simple decorator-based job handlers
- ✅ **Automatic reconnection** - Resilient to network issues
- ✅ **Comprehensive error handling** - Detailed logging and error recovery
- ✅ **Graceful shutdown** - Signal handling (SIGINT, SIGTERM) with job completion
- ✅ **Advanced retry mechanisms** - Multiple strategies with full configurability
- ✅ **Retry statistics and monitoring** - Track performance and success rates
- ✅ **Comprehensive metrics collection** - Real-time performance monitoring
- ✅ **Production ready** - Battle-tested with extensive test coverage
- ✅ **Tested** - 70+ unit and integration tests included

### Requirements

- Python 3.7+
- Redis 4.0+
- Laravel 8+ (for Laravel side)

### Development

```bash
# Install development dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_error_handling.py -v
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

MIT License - see LICENSE file for details.

### Credits

- Original package: [python-laravel-queue](https://github.com/sinanbekar/python-laravel-queue) by [@sinanbekar](https://github.com/sinanbekar)
- This fork maintained with critical bug fixes and improvements
