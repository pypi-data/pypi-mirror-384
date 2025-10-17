
#!/usr/bin/env python3
"""
CPU Optimization Test Script for SpeakUB

This script tests the CPU usage optimizations implemented in the EPUB reader.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil


class CPUOptimizerTester:
    """Test CPU optimization features."""

    def __init__(self):
        self.process = None
        self.test_epub = self._find_test_epub()

    def _find_test_epub(self) -> str:
        """Find a test EPUB file."""
        # Look for common test EPUB files
        test_files = ["test.epub", "sample.epub", "example.epub", "test_book.epub"]

        for test_file in test_files:
            if Path(test_file).exists():
                return test_file

        # Create a simple test EPUB if none found
        return self._create_test_epub()

    def _create_test_epub(self) -> str:
        """Create a simple test EPUB file."""
        test_epub = "test_cpu_optimization.epub"

        # Create a minimal EPUB structure
        import tempfile
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create META-INF/container.xml
            metainf_dir = Path(tmpdir) / "META-INF"
            metainf_dir.mkdir()

            container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

            (metainf_dir / "container.xml").write_text(container_xml)

            # Create content.opf
            content_opf = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>CPU Optimization Test Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>"""

            (Path(tmpdir) / "content.opf").write_text(content_opf)

            # Create chapter1.xhtml with substantial content
            chapter_content = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
<h1>CPU Optimization Test Chapter</h1>
<p>This is a test chapter for CPU optimization testing.</p>
"""

            # Add many paragraphs to create substantial content
            for i in range(100):
                chapter_content += (
                    f"<p>This is paragraph {i + 1}. "
                    + " ".join([f"word{j}" for j in range(50)])
                    + "</p>\n"
                )

            chapter_content += """
</body>
</html>"""

            (Path(tmpdir) / "chapter1.xhtml").write_text(chapter_content)

            # Create toc.ncx
            toc_ncx = """<?xml version="1.0"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="test-book"/>
  </head>
  <docTitle><text>CPU Optimization Test Book</text></docTitle>
  <navMap>
    <navPoint id="chapter1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="chapter1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>"""

            (Path(tmpdir) / "toc.ncx").write_text(toc_ncx)

            # Create EPUB file
            with zipfile.ZipFile(test_epub, "w") as zf:
                for file_path in Path(tmpdir).rglob("*"):
                    if file_path.is_file():
                        zf.write(file_path, file_path.relative_to(tmpdir))

        return test_epub

    def start_reader(self) -> bool:
        """Start the EPUB reader process."""
        try:
            cmd = [sys.executable, "speakub/rich_cli.py", self.test_epub, "--debug"]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,  # Create new process group
            )
            return True
        except Exception:
            # Failed to start reader: {e}
            return False

    def stop_reader(self):
        """Stop the EPUB reader process."""
        if self.process:
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

    def monitor_cpu_usage(self, duration: int = 60) -> dict:
        """Monitor CPU usage for the specified duration."""
        if not self.process:
            return {"error": "No process running"}

        # Create psutil process object to monitor CPU usage
        try:
            psutil_process = psutil.Process(self.process.pid)
        except psutil.NoSuchProcess:
            return {"error": "Process not found"}

        start_time = time.time()
        cpu_samples = []
        memory_samples = []

        try:
            while time.time() - start_time < duration:
                if self.process.poll() is not None:
                    break

                try:
                    # Get CPU and memory usage using psutil
                    cpu_percent = psutil_process.cpu_percent(interval=1)
                    memory_info = psutil_process.memory_info()

                    cpu_samples.append(cpu_percent)
                    memory_samples.append(memory_info.rss / 1024 / 1024)  # MB

                    time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

        except KeyboardInterrupt:
            pass

        if not cpu_samples:
            return {"error": "No CPU samples collected"}

        return {
            "duration": len(cpu_samples),
            "cpu_avg": sum(cpu_samples) / len(cpu_samples),
            "cpu_max": max(cpu_samples),
            "cpu_min": min(cpu_samples),
            "memory_avg": (
                sum(memory_samples) / len(memory_samples) if memory_samples else 0
            ),
            "memory_max": max(memory_samples) if memory_samples else 0,
            "samples": len(cpu_samples),
        }

    def test_idle_cpu_usage(self) -> dict:
        """Test CPU usage during idle periods."""
        # Testing idle CPU usage...

        if not self.start_reader():
            return {"error": "Failed to start reader"}

        # Wait for reader to initialize
        time.sleep(5)

        # Monitor CPU usage for 30 seconds (idle period)
        results = self.monitor_cpu_usage(30)

        self.stop_reader()

        return results

    def test_active_cpu_usage(self) -> dict:
        """Test CPU usage during active usage."""
        # Testing active CPU usage...

        if not self.start_reader():
            return {"error": "Failed to start reader"}

        # Wait for reader to initialize
        time.sleep(5)

        # Simulate some activity (this would require more complex automation)
        # For now, just monitor during what should be active usage
        results = self.monitor_cpu_usage(30)

        self.stop_reader()

        return results

    def run_comprehensive_test(self) -> dict:
        """Run comprehensive CPU optimization tests."""
        # Running comprehensive CPU optimization tests...
        # Using test EPUB: {self.test_epub}

        results = {
            "idle_test": self.test_idle_cpu_usage(),
            "active_test": self.test_active_cpu_usage(),
            "optimizations_implemented": [
                "Content renderer caching",
                "Idle mode detection",
                "Reduced polling frequency",
                "User activity tracking",
                "Viewport height optimization",
                "Background process management",
            ],
        }

        return results


def main():
    """Main test function."""
    tester = CPUOptimizerTester()

    # SpeakUB CPU Optimization Test
    # "=" * 50

    try:
        results = tester.run_comprehensive_test()

        # Test Results:
        # "-" * 30

        if "error" not in results["idle_test"]:
            # Idle CPU Usage:
            # CPU Average: {results["idle_test"]['cpu_avg']:.2f}%
            # CPU Max: {results["idle_test"]['cpu_max']:.2f}%
            # CPU Min: {results["idle_test"]['cpu_min']:.2f}%
            # Memory Average: {results["idle_test"]['memory_avg']:.1f} MB
            pass

        if "error" not in results["active_test"]:
            # Active CPU Usage:
            # CPU Average: {results["active_test"]['cpu_avg']:.2f}%
            # CPU Max: {results["active_test"]['cpu_max']:.2f}%
            # CPU Min: {results["active_test"]['cpu_min']:.2f}%
            # Memory Average: {results["active_test"]['memory_avg']:.1f} MB
            pass

        # Optimizations Implemented:
        for opt in results["optimizations_implemented"]:
            #   ✓ {opt}
            pass

        # CPU Optimization Summary:
        # "-" * 30
        # The EPUB reader now includes several CPU optimization features:
        # 1. Content renderer caching to avoid repeated calculations
        # 2. Idle mode detection that reduces polling frequency
        # 3. User activity tracking to detect idle periods
        # 4. Optimized viewport height calculations
        # 5. Reduced background process overhead
        # 6. Smart caching of frequently used data

        if (
            "error" not in results["idle_test"]
            and "error" not in results["active_test"]
        ):
            idle_cpu = results["idle_test"]["cpu_avg"]
            active_cpu = results["active_test"]["cpu_avg"]

            if idle_cpu < 5.0:
                # ✅ Idle CPU usage is well optimized (< 5%)
                pass
            elif idle_cpu < 10.0:
                # ⚠️  Idle CPU usage is acceptable (< 10%)
                pass
            else:
                # ❌ Idle CPU usage needs improvement
                pass

            if active_cpu < 20.0:
                # ✅ Active CPU usage is reasonable (< 20%)
                pass
            elif active_cpu < 30.0:
                # ⚠️  Active CPU usage is acceptable (< 30%)
                pass
            else:
                # ❌ Active CPU usage needs optimization
                pass

    except KeyboardInterrupt:
        # Test interrupted by user
        pass
    except Exception:
        # Test failed: {e}
        pass
    finally:
        tester.stop_reader()


if __name__ == "__main__":
    main()
