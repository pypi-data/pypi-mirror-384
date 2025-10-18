#!/usr/bin/env python3
"""
Type Hints Example

This example demonstrates how to use LaraQueue with proper type hints
for better IDE support, code completion, and type safety.
"""

import logging
from typing import Dict, List, Any, Optional
from redis import Redis
from lara_queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Main function demonstrating type hints usage."""
    
    # Connect to Redis with type hints
    redis_client: Redis = Redis(host='localhost', port=6379, db=0)
    
    # Create queue with type hints
    queue: Queue = Queue(
        client=redis_client,
        queue='typed_worker',
        dead_letter_queue='typed_failed',
        max_retries=3
    )
    
    print("✅ Queue created with type hints")
    print(f"📧 Queue: {queue.queue}")
    print(f"💀 Dead Letter Queue: {queue.dead_letter_queue}")
    print(f"🔄 Max Retries: {queue.max_retries}")
    
    # Register typed handler
    @queue.handler
    def process_email(data: Dict[str, Any]) -> None:
        """Typed email handler with proper type annotations."""
        email_type: str = data.get('type', 'unknown')
        recipient: str = data.get('recipient', 'unknown')
        subject: Optional[str] = data.get('subject')
        
        print(f"\n📨 Processing email: {email_type} to {recipient}")
        
        if subject:
            print(f"   Subject: {subject}")
        
        # Type-safe data processing
        if 'invalid' in recipient.lower():
            raise ValueError(f"Invalid email address: {recipient}")
        
        print(f"   ✅ Email sent successfully to {recipient}")
    
    # Function to demonstrate typed DLQ operations
    def demonstrate_typed_dlq_operations() -> None:
        """Demonstrate Dead Letter Queue operations with type hints."""
        print("\n" + "="*60)
        print("🔍 TYPED DEAD LETTER QUEUE OPERATIONS")
        print("="*60)
        
        # Get failed jobs with type hints
        failed_jobs: List[Dict[str, Any]] = queue.get_dead_letter_jobs(limit=10)
        print(f"\n📋 Found {len(failed_jobs)} failed jobs in DLQ:")
        
        for i, job in enumerate(failed_jobs, 1):
            original_job: Dict[str, Any] = job.get('original_job', {})
            error_info: Dict[str, Any] = job.get('error', {})
            retry_count: int = job.get('retry_count', 0)
            
            print(f"\n   {i}. Job ID: {original_job.get('uuid', 'unknown')}")
            print(f"      Error: {error_info.get('type', 'unknown')} - {error_info.get('message', 'no message')}")
            print(f"      Retries: {retry_count}/{job.get('max_retries', 0)}")
        
        # Demonstrate reprocessing with type hints
        if failed_jobs:
            print(f"\n🔄 Reprocessing first failed job...")
            success: bool = queue.reprocess_dead_letter_job(failed_jobs[0])
            if success:
                print("   ✅ Job reprocessed successfully")
            else:
                print("   ❌ Failed to reprocess job")
        
        # Clear DLQ with type hints
        if failed_jobs:
            cleared_count: int = queue.clear_dead_letter_queue()
            print(f"   ✅ Cleared {cleared_count} jobs from DLQ")
    
    # Function to push typed test jobs
    def push_typed_test_jobs() -> None:
        """Push various test jobs with proper type annotations."""
        print("\n" + "="*60)
        print("📤 PUSHING TYPED TEST JOBS")
        print("="*60)
        
        # Define typed job data
        test_jobs: List[Dict[str, Any]] = [
            {
                'type': 'welcome',
                'recipient': 'user@example.com',
                'subject': 'Welcome to our service!'
            },
            {
                'type': 'invalid',
                'recipient': 'invalid-email',  # Will fail
                'subject': 'This will fail'
            },
            {
                'type': 'newsletter',
                'recipient': 'user2@example.com',
                'subject': 'Weekly Newsletter'
            },
            {
                'type': 'notification',
                'recipient': 'user3@example.com',
                'subject': None  # Optional subject
            }
        ]
        
        for job in test_jobs:
            try:
                queue.push('SendEmail', job)
                print(f"   📤 Pushed: {job['type']} to {job['recipient']}")
            except Exception as e:
                print(f"   ❌ Failed to push job: {e}")
    
    # Function to demonstrate type-safe job processing
    def demonstrate_type_safety() -> None:
        """Demonstrate type safety features."""
        print("\n" + "="*60)
        print("🛡️ TYPE SAFETY DEMONSTRATION")
        print("="*60)
        
        # Type-safe job data creation
        job_data: Dict[str, Any] = {
            'type': 'test',
            'recipient': 'test@example.com',
            'subject': 'Test Email',
            'metadata': {
                'priority': 'high',
                'tags': ['test', 'example']
            }
        }
        
        # Type-safe method calls
        job_id: str = queue._get_job_id(job_data)
        retry_count: int = queue._increment_retry_count(job_id)
        should_retry: bool = queue._should_retry(job_id)
        
        print(f"   Job ID: {job_id}")
        print(f"   Retry Count: {retry_count}")
        print(f"   Should Retry: {should_retry}")
        
        # Type-safe DLQ operations
        failed_jobs: List[Dict[str, Any]] = queue.get_dead_letter_jobs(limit=5)
        cleared_count: int = queue.clear_dead_letter_queue()
        
        print(f"   Failed Jobs Count: {len(failed_jobs)}")
        print(f"   Cleared Count: {cleared_count}")
    
    # Main execution with type hints
    try:
        # Demonstrate type safety
        demonstrate_type_safety()
        
        # Push typed test jobs
        push_typed_test_jobs()
        
        print(f"\n🎧 Starting to listen to queue '{queue.queue}'...")
        print("   Jobs will be processed with full type safety")
        print("   Press Ctrl+C to stop and view DLQ operations\n")
        
        # Start listening (this will process jobs)
        queue.listen()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping worker...")
        
        # Demonstrate typed DLQ operations after stopping
        demonstrate_typed_dlq_operations()
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        demonstrate_typed_dlq_operations()

def demonstrate_advanced_type_hints() -> None:
    """Demonstrate advanced type hints usage patterns."""
    print("\n" + "="*60)
    print("🚀 ADVANCED TYPE HINTS PATTERNS")
    print("="*60)
    
    # Type aliases for better readability
    JobData = Dict[str, Any]
    JobList = List[JobData]
    ErrorInfo = Dict[str, Any]
    
    # Typed function signatures
    def process_job_batch(jobs: JobList) -> List[bool]:
        """Process a batch of jobs with type hints."""
        results: List[bool] = []
        
        for job in jobs:
            try:
                # Type-safe job processing
                job_type: str = job.get('type', 'unknown')
                recipient: str = job.get('recipient', 'unknown')
                
                print(f"   Processing: {job_type} to {recipient}")
                results.append(True)
                
            except Exception as e:
                print(f"   Failed: {e}")
                results.append(False)
        
        return results
    
    def analyze_errors(failed_jobs: JobList) -> Dict[str, int]:
        """Analyze error patterns with type hints."""
        error_counts: Dict[str, int] = {}
        
        for job in failed_jobs:
            error_info: ErrorInfo = job.get('error', {})
            error_type: str = error_info.get('type', 'unknown')
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return error_counts
    
    # Example usage
    sample_jobs: JobList = [
        {'type': 'email', 'recipient': 'user1@example.com'},
        {'type': 'sms', 'recipient': '+1234567890'},
        {'type': 'push', 'recipient': 'device123'}
    ]
    
    results: List[bool] = process_job_batch(sample_jobs)
    print(f"   Batch processing results: {results}")
    
    # Simulate failed jobs analysis
    failed_jobs: JobList = [
        {'error': {'type': 'ValueError', 'message': 'Invalid email'}},
        {'error': {'type': 'TimeoutError', 'message': 'Connection timeout'}},
        {'error': {'type': 'ValueError', 'message': 'Invalid phone number'}}
    ]
    
    error_analysis: Dict[str, int] = analyze_errors(failed_jobs)
    print(f"   Error analysis: {error_analysis}")

if __name__ == '__main__':
    main()
    demonstrate_advanced_type_hints()
