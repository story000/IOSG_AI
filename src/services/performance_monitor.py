"""Performance monitoring and metrics system for deduplication services"""

import time
import json
import os
import sqlite3
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class PerformanceMetric:
    """Individual performance metric record"""
    timestamp: float
    operation_type: str
    algorithm_used: str
    input_size: int
    processing_time: float
    removal_rate: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    error_occurred: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class PerformanceReport:
    """Aggregated performance report"""
    total_operations: int = 0
    avg_processing_time: float = 0.0
    avg_removal_rate: float = 0.0
    total_articles_processed: int = 0
    algorithms_used: Dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0
    performance_trends: Dict[str, List[float]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class PerformanceMonitor:
    """Performance monitoring system for deduplication services"""
    
    def __init__(self, 
                 db_path: str = "performance_metrics.db",
                 max_records: int = 10000,
                 enable_memory_monitoring: bool = True):
        
        self.db_path = db_path
        self.max_records = max_records
        self.enable_memory_monitoring = enable_memory_monitoring
        self._lock = threading.Lock()
        
        # Initialize database
        self._init_database()
        
        # In-memory cache for recent metrics
        self.recent_metrics: List[PerformanceMetric] = []
        self.cache_size = 100
        
        print(f"✅ Performance Monitor initialized")
        print(f"   - Database: {db_path}")
        print(f"   - Max records: {max_records}")
        print(f"   - Memory monitoring: {enable_memory_monitoring}")
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    operation_type TEXT,
                    algorithm_used TEXT,
                    input_size INTEGER,
                    processing_time REAL,
                    removal_rate REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL,
                    error_occurred BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON performance_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_algorithm ON performance_metrics(algorithm_used)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operation ON performance_metrics(operation_type)")
    
    def record_metric(self, 
                     operation_type: str,
                     algorithm_used: str, 
                     input_size: int,
                     processing_time: float,
                     removal_rate: float,
                     error_occurred: bool = False,
                     error_message: Optional[str] = None) -> PerformanceMetric:
        """Record a performance metric"""
        
        # Get system metrics if enabled
        memory_usage = self._get_memory_usage() if self.enable_memory_monitoring else None
        cpu_usage = self._get_cpu_usage() if self.enable_memory_monitoring else None
        
        metric = PerformanceMetric(
            timestamp=time.time(),
            operation_type=operation_type,
            algorithm_used=algorithm_used,
            input_size=input_size,
            processing_time=processing_time,
            removal_rate=removal_rate,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            error_occurred=error_occurred,
            error_message=error_message
        )
        
        # Store in database and cache
        self._store_metric(metric)
        self._update_cache(metric)
        
        return metric
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return None
    
    def _store_metric(self, metric: PerformanceMetric):
        """Store metric in database"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, operation_type, algorithm_used, input_size, processing_time, 
                     removal_rate, memory_usage_mb, cpu_usage_percent, error_occurred, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.timestamp, metric.operation_type, metric.algorithm_used,
                    metric.input_size, metric.processing_time, metric.removal_rate,
                    metric.memory_usage_mb, metric.cpu_usage_percent, 
                    metric.error_occurred, metric.error_message
                ))
                
                # Cleanup old records if needed
                self._cleanup_old_records(conn)
    
    def _cleanup_old_records(self, conn):
        """Remove old records to maintain max_records limit"""
        cursor = conn.execute("SELECT COUNT(*) FROM performance_metrics")
        count = cursor.fetchone()[0]
        
        if count > self.max_records:
            # Delete oldest records
            records_to_delete = count - self.max_records
            conn.execute("""
                DELETE FROM performance_metrics 
                WHERE id IN (
                    SELECT id FROM performance_metrics 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                )
            """, (records_to_delete,))
    
    def _update_cache(self, metric: PerformanceMetric):
        """Update in-memory cache"""
        with self._lock:
            self.recent_metrics.append(metric)
            
            # Keep only recent metrics in cache
            if len(self.recent_metrics) > self.cache_size:
                self.recent_metrics = self.recent_metrics[-self.cache_size:]
    
    def generate_report(self, 
                       hours_back: int = 24,
                       algorithm_filter: Optional[str] = None) -> PerformanceReport:
        """Generate comprehensive performance report"""
        
        # Query metrics from database
        since_timestamp = time.time() - (hours_back * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT * FROM performance_metrics 
                WHERE timestamp > ?
            """
            params = [since_timestamp]
            
            if algorithm_filter:
                query += " AND algorithm_used = ?"
                params.append(algorithm_filter)
            
            query += " ORDER BY timestamp ASC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to metrics
            columns = [desc[0] for desc in cursor.description]
            metrics = []
            for row in rows:
                metric_dict = dict(zip(columns, row))
                # Remove database-specific fields
                metric_dict.pop('id', None)
                metric_dict.pop('created_at', None)
                metrics.append(PerformanceMetric(**metric_dict))
        
        return self._analyze_metrics(metrics)
    
    def _analyze_metrics(self, metrics: List[PerformanceMetric]) -> PerformanceReport:
        """Analyze metrics and generate report"""
        
        if not metrics:
            return PerformanceReport()
        
        # Basic statistics
        total_operations = len(metrics)
        successful_operations = [m for m in metrics if not m.error_occurred]
        
        avg_processing_time = sum(m.processing_time for m in successful_operations) / len(successful_operations) if successful_operations else 0
        avg_removal_rate = sum(m.removal_rate for m in successful_operations) / len(successful_operations) if successful_operations else 0
        total_articles = sum(m.input_size for m in metrics)
        error_rate = (total_operations - len(successful_operations)) / total_operations * 100 if total_operations > 0 else 0
        
        # Algorithm usage
        algorithms_used = defaultdict(int)
        for metric in metrics:
            algorithms_used[metric.algorithm_used] += 1
        
        # Performance trends (last 10 operations)
        recent_metrics = metrics[-10:] if len(metrics) >= 10 else metrics
        performance_trends = {
            'processing_times': [m.processing_time for m in recent_metrics],
            'removal_rates': [m.removal_rate for m in recent_metrics],
            'input_sizes': [m.input_size for m in recent_metrics]
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics)
        
        return PerformanceReport(
            total_operations=total_operations,
            avg_processing_time=avg_processing_time,
            avg_removal_rate=avg_removal_rate,
            total_articles_processed=total_articles,
            algorithms_used=dict(algorithms_used),
            error_rate=error_rate,
            performance_trends=performance_trends,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, metrics: List[PerformanceMetric]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        
        recommendations = []
        
        if not metrics:
            return recommendations
        
        # Analyze algorithm performance
        algorithm_performance = defaultdict(list)
        for metric in metrics:
            if not metric.error_occurred:
                algorithm_performance[metric.algorithm_used].append(metric.processing_time)
        
        # Find best performing algorithm
        if len(algorithm_performance) > 1:
            avg_times = {alg: sum(times)/len(times) for alg, times in algorithm_performance.items()}
            best_algorithm = min(avg_times, key=avg_times.get)
            worst_algorithm = max(avg_times, key=avg_times.get)
            
            if avg_times[worst_algorithm] > avg_times[best_algorithm] * 2:
                recommendations.append(f"Consider using {best_algorithm} instead of {worst_algorithm} for better performance")
        
        # Check error rate
        error_rate = sum(1 for m in metrics if m.error_occurred) / len(metrics) * 100
        if error_rate > 5:
            recommendations.append(f"High error rate ({error_rate:.1f}%) - review error handling and input validation")
        
        # Check memory usage trends
        memory_metrics = [m for m in metrics if m.memory_usage_mb is not None]
        if memory_metrics:
            avg_memory = sum(m.memory_usage_mb for m in memory_metrics) / len(memory_metrics)
            max_memory = max(m.memory_usage_mb for m in memory_metrics)
            
            if max_memory > avg_memory * 2:
                recommendations.append(f"Memory usage spikes detected (max: {max_memory:.1f}MB, avg: {avg_memory:.1f}MB)")
        
        # Check processing time trends
        recent_times = [m.processing_time for m in metrics[-10:]]
        if len(recent_times) >= 5:
            trend = sum(recent_times[-3:]) / 3 - sum(recent_times[:3]) / 3
            if trend > 0.5:  # Processing time increasing
                recommendations.append("Processing time is increasing - consider algorithm optimization or data preprocessing")
        
        return recommendations
    
    def get_algorithm_comparison(self, hours_back: int = 24) -> Dict[str, Dict]:
        """Compare performance across different algorithms"""
        
        report = self.generate_report(hours_back)
        
        # Get detailed metrics for each algorithm
        algorithm_details = {}
        
        since_timestamp = time.time() - (hours_back * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            for algorithm in report.algorithms_used.keys():
                cursor = conn.execute("""
                    SELECT processing_time, removal_rate, input_size, error_occurred
                    FROM performance_metrics 
                    WHERE timestamp > ? AND algorithm_used = ? AND error_occurred = 0
                """, (since_timestamp, algorithm))
                
                rows = cursor.fetchall()
                if rows:
                    times, rates, sizes, _ = zip(*rows)
                    
                    algorithm_details[algorithm] = {
                        'count': len(rows),
                        'avg_time': sum(times) / len(times),
                        'avg_removal_rate': sum(rates) / len(rates),
                        'avg_input_size': sum(sizes) / len(sizes),
                        'min_time': min(times),
                        'max_time': max(times),
                        'efficiency_score': (sum(rates) / len(rates)) / (sum(times) / len(times))  # removal_rate / time
                    }
        
        return algorithm_details
    
    def export_metrics(self, 
                      filename: str,
                      format: str = 'json',
                      hours_back: int = 24) -> str:
        """Export metrics to file"""
        
        since_timestamp = time.time() - (hours_back * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM performance_metrics 
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            """, (since_timestamp,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
        
        if format.lower() == 'json':
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format.lower() == 'csv':
            import csv
            with open(filename, 'w', newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(data)
        
        return filename
    
    def clear_metrics(self, older_than_hours: Optional[int] = None):
        """Clear metrics data"""
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                if older_than_hours is None:
                    # Clear all metrics
                    conn.execute("DELETE FROM performance_metrics")
                    self.recent_metrics.clear()
                    print("All performance metrics cleared")
                else:
                    # Clear metrics older than specified hours
                    cutoff_timestamp = time.time() - (older_than_hours * 3600)
                    conn.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_timestamp,))
                    
                    # Update cache
                    self.recent_metrics = [m for m in self.recent_metrics if m.timestamp >= cutoff_timestamp]
                    print(f"Cleared metrics older than {older_than_hours} hours")
    
    def get_status(self) -> Dict:
        """Get monitoring system status"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM performance_metrics")
            total_records = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM performance_metrics")
            time_range = cursor.fetchone()
            
            oldest_timestamp, newest_timestamp = time_range if time_range[0] else (None, None)
        
        return {
            'total_records': total_records,
            'cache_size': len(self.recent_metrics),
            'oldest_record': datetime.fromtimestamp(oldest_timestamp).isoformat() if oldest_timestamp else None,
            'newest_record': datetime.fromtimestamp(newest_timestamp).isoformat() if newest_timestamp else None,
            'database_path': self.db_path,
            'memory_monitoring_enabled': self.enable_memory_monitoring
        }