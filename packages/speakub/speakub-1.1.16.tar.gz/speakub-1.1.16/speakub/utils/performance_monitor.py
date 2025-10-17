
#!/usr/bin/env python3
"""
Performance monitoring utilities for SpeakUB.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    size: int
    max_size: int
    hit_rate: float
    hits: int
    misses: int


@dataclass
class MemoryMetrics:
    """Memory usage metrics."""

    rss_mb: float
    vms_mb: float
    system_total_gb: float
    system_available_gb: float


@dataclass
class PerformanceMetrics:
    """Structured performance metrics."""

    cache: CacheMetrics
    memory: MemoryMetrics
    tts_state: Optional[str] = None


class PerformanceMonitor:
    """Monitor system performance metrics."""

    def __init__(self, app: Any):
        """
        Initialize performance monitor.

        Args:
            app: Application instance
        """
        self.app = app
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Metrics storage
        self.metrics_history: Dict[str, list] = {
            "cache_hit_rate": [],
            "memory_usage_mb": [],
            "tts_state_changes": [],
            "render_time_ms": [],
        }

        # Configuration
        self.monitor_interval = 30  # seconds
        self.max_history_size = 100

    def start_monitoring(self):
        """Start performance monitoring."""
        with self._lock:
            if self._monitoring:
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True, name="PerformanceMonitor"
            )
            self._monitor_thread.start()
            logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring."""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5.0)
            logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._collect_metrics()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(5)  # Brief pause on error

    def _collect_metrics(self):
        """Collect current performance metrics."""
        try:
            # Cache metrics
            if hasattr(self.app, "viewport_content") and self.app.viewport_content:
                cache_stats = self.app.viewport_content.get_cache_stats()
                self._add_metric("cache_hit_rate", cache_stats.get("hit_rate", 0))

            # Memory usage
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self._add_metric("memory_usage_mb", memory_mb)

            # TTS state (if available)
            if hasattr(self.app, "tts_engine") and self.app.tts_engine:
                try:
                    current_state = self.app.tts_engine.get_current_state()
                    self._add_metric("tts_state_changes", hash(current_state))
                except:
                    pass

        except Exception as e:
            logger.debug(f"Failed to collect metrics: {e}")

    def _add_metric(self, name: str, value: Any):
        """Add metric to history."""
        if name not in self.metrics_history:
            self.metrics_history[name] = []

        history = self.metrics_history[name]
        history.append((time.time(), value))

        # Keep history size manageable
        if len(history) > self.max_history_size:
            history.pop(0)

    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics from viewport content."""
        if hasattr(self.app, "viewport_content") and self.app.viewport_content:
            return self.app.viewport_content.get_cache_stats()
        return {}

    def _get_memory_info(self):
        """Get memory information."""
        import psutil

        process = psutil.Process()
        return process.memory_info()

    def _get_system_memory(self):
        """Get system memory information."""
        import psutil

        return psutil.virtual_memory()

    def _get_tts_state(self) -> Optional[str]:
        """Get current TTS state."""
        if hasattr(self.app, "tts_engine") and self.app.tts_engine:
            try:
                return self.app.tts_engine.get_current_state()
            except:
                return "unknown"
        return None

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        metrics = {}

        try:
            # Cache metrics
            cache_stats = self._get_cache_stats()
            if cache_stats:
                metrics.update(
                    {
                        "cache_size": cache_stats.get("size", 0),
                        "cache_max_size": cache_stats.get("max_size", 0),
                        "cache_hit_rate": cache_stats.get("hit_rate", 0),
                        "cache_hits": cache_stats.get("hits", 0),
                        "cache_misses": cache_stats.get("misses", 0),
                    }
                )

            # Memory usage
            memory_info = self._get_memory_info()
            metrics.update(
                {
                    "memory_rss_mb": memory_info.rss / 1024 / 1024,
                    "memory_vms_mb": memory_info.vms / 1024 / 1024,
                }
            )

            # System memory
            system_mem = self._get_system_memory()
            metrics.update(
                {
                    "system_memory_total_gb": system_mem.total / (1024**3),
                    "system_memory_available_gb": system_mem.available / (1024**3),
                    "system_memory_percent": system_mem.percent,
                }
            )

            # TTS metrics
            tts_state = self._get_tts_state()
            if tts_state is not None:
                metrics["tts_current_state"] = tts_state

            if hasattr(self.app, "tts_status"):
                metrics["tts_status"] = self.app.tts_status

        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    def get_structured_metrics(self) -> PerformanceMetrics:
        """Get structured performance metrics with type safety."""
        try:
            # Cache metrics
            cache_stats = self._get_cache_stats()
            cache_metrics = CacheMetrics(
                size=cache_stats.get("size", 0),
                max_size=cache_stats.get("max_size", 0),
                hit_rate=cache_stats.get("hit_rate", 0.0),
                hits=cache_stats.get("hits", 0),
                misses=cache_stats.get("misses", 0),
            )

            # Memory metrics
            memory_info = self._get_memory_info()
            system_mem = self._get_system_memory()

            memory_metrics = MemoryMetrics(
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                system_total_gb=system_mem.total / (1024**3),
                system_available_gb=system_mem.available / (1024**3),
            )

            # TTS state
            tts_state = self._get_tts_state()

            return PerformanceMetrics(
                cache=cache_metrics, memory=memory_metrics, tts_state=tts_state
            )

        except Exception as e:
            logger.error(f"Error getting structured metrics: {e}")
            # Return default/empty metrics on error
            return PerformanceMetrics(
                cache=CacheMetrics(0, 0, 0.0, 0, 0),
                memory=MemoryMetrics(0.0, 0.0, 0.0, 0.0),
                tts_state="error",
            )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        summary = {}

        for metric_name, history in self.metrics_history.items():
            if not history:
                continue

            values = [value for _, value in history]

            if metric_name == "cache_hit_rate":
                summary["avg_cache_hit_rate"] = (
                    sum(values) / len(values) if values else 0
                )
                summary["min_cache_hit_rate"] = min(values) if values else 0
                summary["max_cache_hit_rate"] = max(values) if values else 0
            elif metric_name == "memory_usage_mb":
                summary["avg_memory_mb"] = sum(values) / len(values) if values else 0
                summary["peak_memory_mb"] = max(values) if values else 0
            elif metric_name == "tts_state_changes":
                summary["tts_state_change_count"] = len(set(values))

        # Add current metrics
        summary.update(self.get_current_metrics())

        return summary

    def log_performance_report(self):
        """Log a performance report."""
        try:
            metrics = self.get_metrics_summary()

            logger.info("=== Performance Report ===")
            logger.info(f"Cache hit rate: {metrics.get('avg_cache_hit_rate', 0):.1%}")
            logger.info(f"Memory usage: {metrics.get('avg_memory_mb', 0):.1f} MB")
            logger.info(f"Peak memory: {metrics.get('peak_memory_mb', 0):.1f} MB")
            logger.info(
                f"TTS state changes: {metrics.get('tts_state_change_count', 0)}"
            )

            if "cache_hit_rate" in metrics:
                logger.info(f"Current cache hit rate: {metrics['cache_hit_rate']:.1%}")
            if "memory_rss_mb" in metrics:
                logger.info(f"Current memory: {metrics['memory_rss_mb']:.1f} MB")

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")


def create_performance_monitor(app: Any) -> PerformanceMonitor:
    """Create and return a performance monitor instance."""
    return PerformanceMonitor(app)
