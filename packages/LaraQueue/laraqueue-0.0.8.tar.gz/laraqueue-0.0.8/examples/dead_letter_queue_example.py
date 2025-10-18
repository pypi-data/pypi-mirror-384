#!/usr/bin/env python3
"""
Dead Letter Queue Example

This example demonstrates how to use the Dead Letter Queue functionality
in LaraQueue for handling failed jobs with retry logic.
"""

import logging
import time
from redis import Redis
from lara_queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function demonstrating Dead Letter Queue usage."""
    
    # Connect to Redis
    try:
        r = Redis(host='localhost', port=6379, db=0)
        r.ping()  # Check connection
        print("✅ Redis connection successful")
    except ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("   Make sure Redis is running: redis-server")
        return
    
    # Create queue with Dead Letter Queue configuration
    queue = Queue(
        r, 
        queue='email_worker',
        dead_letter_queue='email_failed',  # Custom DLQ name
        max_retries=3  # Retry failed jobs 3 times
    )
    
    print(f"📧 Email queue configured with DLQ: {queue.dead_letter_queue}")
    print(f"🔄 Max retries: {queue.max_retries}")
    
    # Register email handler with simulated failures
    @queue.handler
    def send_email(data):
        """Email handler that simulates various failure scenarios."""
        email_type = data.get('type', 'unknown')
        recipient = data.get('recipient', 'unknown')
        
        print(f"\n📨 Processing email: {email_type} to {recipient}")
        
        # Simulate different failure scenarios
        if 'invalid' in recipient.lower():
            raise ValueError(f"Invalid email address: {recipient}")
        elif 'timeout' in email_type.lower():
            raise TimeoutError("Email service timeout")
        elif 'spam' in email_type.lower():
            raise RuntimeError("Email marked as spam")
        elif 'success' in email_type.lower():
            print(f"   ✅ Email sent successfully to {recipient}")
            return
        
        # Default success
        print(f"   ✅ Email sent successfully to {recipient}")
    
    # Function to demonstrate DLQ operations
    def demonstrate_dlq_operations():
        """Demonstrate Dead Letter Queue operations."""
        print("\n" + "="*60)
        print("🔍 DEAD LETTER QUEUE OPERATIONS")
        print("="*60)
        
        # Get failed jobs from DLQ
        failed_jobs = queue.get_dead_letter_jobs(limit=10)
        print(f"\n📋 Found {len(failed_jobs)} failed jobs in DLQ:")
        
        for i, job in enumerate(failed_jobs, 1):
            original_job = job.get('original_job', {})
            error_info = job.get('error', {})
            retry_count = job.get('retry_count', 0)
            
            print(f"\n   {i}. Job ID: {original_job.get('uuid', 'unknown')}")
            print(f"      Error: {error_info.get('type', 'unknown')} - {error_info.get('message', 'no message')}")
            print(f"      Retries: {retry_count}/{job.get('max_retries', 0)}")
            print(f"      Failed at: {time.ctime(job.get('failed_at', 0))}")
        
        # Demonstrate reprocessing a failed job
        if failed_jobs:
            print(f"\n🔄 Reprocessing first failed job...")
            success = queue.reprocess_dead_letter_job(failed_jobs[0])
            if success:
                print("   ✅ Job reprocessed successfully")
            else:
                print("   ❌ Failed to reprocess job")
        
        # Clear DLQ (optional)
        if failed_jobs:
            response = input(f"\n🗑️  Clear all {len(failed_jobs)} failed jobs from DLQ? (y/N): ")
            if response.lower() == 'y':
                cleared = queue.clear_dead_letter_queue()
                print(f"   ✅ Cleared {cleared} jobs from DLQ")
    
    # Function to push test jobs
    def push_test_jobs():
        """Push various test jobs to demonstrate retry and DLQ behavior."""
        print("\n" + "="*60)
        print("📤 PUSHING TEST JOBS")
        print("="*60)
        
        test_jobs = [
            {'type': 'welcome', 'recipient': 'user@example.com'},
            {'type': 'invalid', 'recipient': 'invalid-email'},  # Will fail
            {'type': 'timeout', 'recipient': 'user2@example.com'},  # Will fail
            {'type': 'spam', 'recipient': 'user3@example.com'},  # Will fail
            {'type': 'success', 'recipient': 'user4@example.com'},  # Will succeed
            {'type': 'newsletter', 'recipient': 'user5@example.com'},
        ]
        
        for job in test_jobs:
            try:
                queue.push('SendEmail', job)
                print(f"   📤 Pushed: {job['type']} to {job['recipient']}")
            except Exception as e:
                print(f"   ❌ Failed to push job: {e}")
    
    # Main execution
    try:
        # Push test jobs
        push_test_jobs()
        
        print(f"\n🎧 Starting to listen to queue '{queue.queue}'...")
        print("   Jobs will be processed with retry logic and DLQ handling")
        print("   Press Ctrl+C to stop and view DLQ operations\n")
        
        # Start listening (this will process jobs)
        queue.listen()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping worker...")
        
        # Demonstrate DLQ operations after stopping
        demonstrate_dlq_operations()
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        demonstrate_dlq_operations()

if __name__ == '__main__':
    main()
