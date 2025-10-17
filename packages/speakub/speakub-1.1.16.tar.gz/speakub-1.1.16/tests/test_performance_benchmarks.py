
#!/usr/bin/env python3
"""
Performance benchmarks for SpeakUB optimizations.
"""

import time
import psutil
from collections import OrderedDict

from speakub.core.content_renderer import AdaptiveCache, ContentRenderer


class LegacyCache:
    """Legacy OrderedDict-based cache for comparison."""

    def __init__(self, max_size: int):
        self._cache: OrderedDict[int, object] = OrderedDict()
        self._max_size = max_size

    def get(self, key):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key, value):
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[key] = value


def benchmark_cache_performance():
    """Benchmark cache performance comparison."""
    print("=== Cache Performance Benchmark ===\n")

    # Test parameters
    cache_sizes = [10, 20, 50]
    operations = 10000
    ttl = 300

    for size in cache_sizes:
        print(f"Testing cache size: {size}")

        # Create caches
        adaptive_cache = AdaptiveCache(max_size=size, ttl=ttl)
        legacy_cache = LegacyCache(max_size=size)

        # Warm up
        for i in range(size):
            adaptive_cache.set(i, f"value_{i}")
            legacy_cache.set(i, f"value_{i}")

        # Benchmark adaptive cache
        start_time = time.time()
        hits = 0
        for i in range(operations):
            key = i % size
            result = adaptive_cache.get(key)
            if result is not None:
                hits += 1
        adaptive_time = time.time() - start_time

        # Benchmark legacy cache
        start_time = time.time()
        for i in range(operations):
            key = i % size
            result = legacy_cache.get(key)
        legacy_time = time.time() - start_time

        # Results
        adaptive_hit_rate = hits / operations
        speedup = legacy_time / adaptive_time if adaptive_time > 0 else float("inf")

        print(".4f")
        print(".4f")
        print(".2f")
        print(".2f")
        print(f"  Hit rate: {adaptive_hit_rate:.1%}")
        print()


def benchmark_memory_usage():
    """Benchmark memory usage."""
    print("=== Memory Usage Benchmark ===\n")

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    print(".1f")

    # Test with different cache sizes
    cache_sizes = [10, 50, 100, 200]

    for size in cache_sizes:
        # Create adaptive cache and fill it
        # Long TTL to prevent expiration
        cache = AdaptiveCache(max_size=size, ttl=3600)

        for i in range(size):
            # Create some EPUBTextRenderer-like objects
            cache.set(
                i, f"test_renderer_{i}_with_longer_content_to_use_more_memory" * 10
            )

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_used = current_memory - initial_memory

        stats = cache.get_stats()
        print("2d")
        print(f"    Cache stats: {stats}")

    print()


def benchmark_content_renderer():
    """Benchmark ContentRenderer with adaptive cache."""
    print("=== ContentRenderer Benchmark ===\n")

    # Create renderer
    renderer = ContentRenderer(content_width=80)

    # Test HTML content
    test_html = """
    <html>
    <body>
    <h1>Test Chapter</h1>
    <p>This is a test paragraph with some content.</p>
    <p>Another paragraph with more text to render.</p>
    <ul>
    <li>List item 1</li>
    <li>List item 2</li>
    </ul>
    </body>
    </html>
    """

    # Benchmark rendering with different widths
    widths = [60, 80, 100, 120]

    print("Rendering performance:")
    for width in widths:
        start_time = time.time()
        lines = renderer.render_chapter(test_html, width=width)
        render_time = time.time() - start_time

        cache_stats = renderer.get_cache_stats()
        print("3d")
        print(f"      Cache: {cache_stats}")

    print()


def run_all_benchmarks():
    """Run all performance benchmarks."""
    print("SpeakUB Performance Benchmarks")
    print("=" * 50)
    print()

    try:
        benchmark_cache_performance()
        benchmark_memory_usage()
        benchmark_content_renderer()

        print("All benchmarks completed successfully!")

    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_benchmarks()
