"""
Example of graceful shutdown with signal handling
"""

import logging
import time
import signal
from lara_queue import Queue
from redis import Redis
from redis.exceptions import ConnectionError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Worker with graceful shutdown handling."""
    
    # Connect to Redis
    try:
        r = Redis(host='localhost', port=6379, db=0)
        r.ping()
        logger.info("✅ Connected to Redis successfully")
    except ConnectionError as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        logger.info("   Make sure Redis is running: redis-server")
        return
    
    # Create queue
    queue = Queue(r, queue='python_worker')
    
    # Register job handler
    @queue.handler
    def handle_job(data):
        """Process jobs with simulated work."""
        job_name = data.get('name', 'Unknown')
        job_data = data.get('data', {})
        
        logger.info(f"📨 Processing job: {job_name}")
        logger.debug(f"   Job data: {job_data}")
        
        try:
            # Simulate some work
            work_duration = job_data.get('duration', 2)
            logger.info(f"   Working for {work_duration} seconds...")
            time.sleep(work_duration)
            
            # Process the job
            result = f"{job_data.get('a', '')} {job_data.get('b', '')} {job_data.get('c', '')}"
            logger.info(f"   ✅ Job completed: {result}")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing job: {e}")
    
    logger.info("🚀 Starting worker with graceful shutdown support...")
    logger.info("   Signal handlers: SIGINT (Ctrl+C), SIGTERM (kill)")
    logger.info("   Current jobs will complete before shutdown")
    logger.info("")
    
    try:
        # Start listening - signal handlers are automatically registered
        queue.listen()
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker crashed: {e}")


def manual_shutdown_example():
    """Example of programmatic shutdown."""
    
    r = Redis(host='localhost', port=6379, db=0)
    queue = Queue(r, queue='python_worker')
    
    @queue.handler
    def handle_job(data):
        logger.info(f"Processing: {data['name']}")
        
        # Trigger shutdown after processing this job
        queue.shutdown()
    
    logger.info("Worker will stop after processing one job")
    queue.listen()


def graceful_vs_immediate_example():
    """Demonstrate graceful vs immediate shutdown."""
    
    r = Redis(host='localhost', port=6379, db=0)
    queue = Queue(r, queue='test_shutdown')
    
    @queue.handler
    def long_running_job(data):
        logger.info("Starting long-running job (10 seconds)...")
        for i in range(10):
            time.sleep(1)
            logger.info(f"  Progress: {i+1}/10 seconds")
        logger.info("Long-running job completed!")
    
    logger.info("Starting worker...")
    logger.info("Try pressing Ctrl+C during job processing")
    logger.info("The worker will wait for the current job to finish")
    logger.info("")
    
    try:
        queue.listen()
    except KeyboardInterrupt:
        logger.info("Shutdown complete")


def production_worker_example():
    """Production-ready worker with all features."""
    
    # Setup logging for production
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(process)d] %(message)s',
        handlers=[
            logging.FileHandler('worker.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Connect to Redis
    try:
        r = Redis(
            host='localhost',
            port=6379,
            db=0,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        r.ping()
        logger.info("Worker started successfully")
    except ConnectionError as e:
        logger.critical(f"Cannot connect to Redis: {e}")
        return 1
    
    # Create queue
    queue = Queue(r, queue='production_queue')
    
    # Job counters
    stats = {'processed': 0, 'failed': 0}
    
    @queue.handler
    def process_job(data):
        """Production job handler with error tracking."""
        try:
            job_name = data['name']
            logger.info(f"Processing job: {job_name}")
            
            # Your business logic here
            # ...
            
            stats['processed'] += 1
            logger.info(f"Job completed. Total processed: {stats['processed']}")
            
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"Job failed: {e}", exc_info=True)
            # Could send to dead letter queue here
    
    # Register custom shutdown handler
    def custom_shutdown_handler(signum, frame):
        logger.info("Received shutdown signal")
        logger.info(f"Statistics: {stats['processed']} processed, {stats['failed']} failed")
        queue.shutdown()
    
    # Override default handlers if needed
    signal.signal(signal.SIGTERM, custom_shutdown_handler)
    
    logger.info("Worker is ready to process jobs")
    
    try:
        queue.listen()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.critical(f"Worker crashed: {e}", exc_info=True)
        return 1
    finally:
        logger.info(f"Final statistics: {stats['processed']} processed, {stats['failed']} failed")
    
    return 0


if __name__ == '__main__':
    # Run basic example
    main()
    
    # Or try other examples:
    # manual_shutdown_example()
    # graceful_vs_immediate_example()
    # production_worker_example()

