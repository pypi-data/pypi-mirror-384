__version__ = "0.0.8"
from .queue import Queue, RetryStrategy, MetricsCollector

__all__ = ['Queue', 'RetryStrategy', 'MetricsCollector', '__version__']