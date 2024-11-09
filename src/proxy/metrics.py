from dataclasses import dataclass
from datetime import datetime
import threading
import time
import logging

@dataclass
class ConnectionMetrics:
    total_connections: int = 0
    active_connections: int = 0
    bytes_transferred: int = 0
    start_time: datetime = datetime.now()
    
    def __init__(self):
        self.lock = threading.Lock()
    
    def increment_connection(self):
        with self.lock:
            self.total_connections += 1
            self.active_connections += 1
    
    def decrement_active(self):
        with self.lock:
            self.active_connections -= 1
    
    def add_bytes(self, bytes_count: int):
        with self.lock:
            self.bytes_transferred += bytes_count
    
    def get_stats(self):
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'bytes_transferred': self.bytes_transferred,
            'uptime_seconds': uptime,
            'bytes_per_second': self.bytes_transferred / uptime if uptime > 0 else 0
        }

class MetricsReporter:
    def __init__(self, metrics: ConnectionMetrics, interval: int = 60):
        self.metrics = metrics
        self.interval = interval
        self.thread = threading.Thread(target=self._report_loop, daemon=True)
        
    def start(self):
        self.thread.start()
        
    def _report_loop(self):
        while True:
            stats = self.metrics.get_stats()
            logging.info(f"Performance Metrics: {stats}")
            time.sleep(self.interval)