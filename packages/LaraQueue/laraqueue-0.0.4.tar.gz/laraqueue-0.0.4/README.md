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

#### 🏷️ Type Hints (v0.0.5)

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

### Features

- ✅ **Redis driver support** - Queue communication between Python and Laravel
- ✅ **Bidirectional job processing** - Send and receive jobs in both directions
- ✅ **PHP object serialization** - Compatible with Laravel's job serialization format
- ✅ **Event-driven architecture** - Simple decorator-based job handlers
- ✅ **Automatic reconnection** - Resilient to network issues
- ✅ **Comprehensive error handling** - Detailed logging and error recovery
- ✅ **Graceful shutdown** - Signal handling (SIGINT, SIGTERM) with job completion
- ✅ **Production ready** - Battle-tested with extensive test coverage
- ✅ **Tested** - 40+ unit and integration tests included

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
