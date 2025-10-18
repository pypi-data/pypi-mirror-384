"""
Example of LaraQueue usage with error handling
"""

import logging
from lara_queue import Queue
from redis import Redis
from redis.exceptions import ConnectionError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Detailed logging for lara_queue
logger = logging.getLogger('lara_queue')
logger.setLevel(logging.DEBUG)

def main():
    """Main function with error handling examples"""
    
    # Connect to Redis
    try:
        r = Redis(host='localhost', port=6379, db=0)
        r.ping()  # Check connection
        print("✅ Redis connection successful")
    except ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("   Make sure Redis is running: redis-server")
        return
    
    # Create queue
    queue = Queue(r, queue='python_worker')
    
    # Register handler
    @queue.handler
    def handle_job(data):
        """Job handler with its own error handling"""
        job_name = data.get('name', 'Unknown')
        job_data = data.get('data', {})
        
        print(f"\n📨 Received job: {job_name}")
        print(f"   Data: {job_data}")
        
        try:
            # Your business logic here
            if 'error' in job_data:
                raise ValueError("Simulated handler error")
            
            # Process data
            result = job_data.get('a', '') + ' ' + job_data.get('b', '') + ' ' + job_data.get('c', '')
            print(f"   ✅ Result: {result}")
            
        except Exception as e:
            print(f"   ❌ Handler error: {e}")
            # Here you can add retry logic or send to dead letter queue
    
    print("\n🎧 Starting to listen to queue 'python_worker'...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        # Start listening
        queue.listen()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping worker...")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")


def push_example():
    """Example of pushing jobs with error handling"""
    
    try:
        r = Redis(host='localhost', port=6379, db=0)
        queue = Queue(r, queue='laravel')
        
        # Successful push
        try:
            queue.push('App\\Jobs\\TestJob', {
                'a': 'hello',
                'b': 'from',
                'c': 'python'
            })
            print("✅ Job successfully sent to Laravel")
        except ConnectionError as e:
            print(f"❌ Connection error while pushing: {e}")
        except TimeoutError as e:
            print(f"❌ Timeout while pushing: {e}")
        except ValueError as e:
            print(f"❌ Data validation error: {e}")
        except RuntimeError as e:
            print(f"❌ Redis error: {e}")
            
    except Exception as e:
        print(f"❌ Failed to create queue: {e}")


if __name__ == '__main__':
    # Run worker
    main()
    
    # Or push a job
    # push_example()

