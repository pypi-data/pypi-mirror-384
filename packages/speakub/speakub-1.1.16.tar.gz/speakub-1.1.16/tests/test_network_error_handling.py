
#!/usr/bin/env python3
"""
Test script for TTS network error handling.
This script simulates network failures and tests edge-tts error handling.
"""

import asyncio
import socket
import subprocess
import sys
import time

import pytest

from speakub.tts.edge_tts_provider import EdgeTTSProvider

# Add the project root to Python path
# Adjust path as needed for your environment
sys.path.insert(0, "/path/to/project/root")


class NetworkErrorSimulator:
    """Simulate various network error conditions."""

    def __init__(self):
        self.original_socket_connect = socket.socket.connect
        self.original_getaddrinfo = socket.getaddrinfo

    def simulate_dns_failure(self):
        """Simulate DNS resolution failure."""

        def mock_getaddrinfo(*args, **kwargs):
            raise socket.gaierror(-3, "Temporary failure in name resolution")

        socket.getaddrinfo = mock_getaddrinfo

    def simulate_connection_timeout(self):
        """Simulate connection timeout."""

        def mock_connect(self, address):
            raise socket.timeout("Connection timed out")

        socket.socket.connect = mock_connect

    def simulate_connection_refused(self):
        """Simulate connection refused."""

        def mock_connect(self, address):
            raise ConnectionError("Connection refused")

    def restore_network(self):
        """Restore normal network functionality."""
        socket.getaddrinfo = self.original_getaddrinfo
        socket.socket.connect = self.original_socket_connect


@pytest.mark.asyncio
async def test_edge_tts_network_errors():
    """Test edge-tts behavior under various network error conditions."""

    print("=== TTS Network Error Handling Test ===\n")

    simulator = NetworkErrorSimulator()
    provider = EdgeTTSProvider()

    test_cases = [
        ("DNS Resolution Failure", simulator.simulate_dns_failure),
        ("Connection Timeout", simulator.simulate_connection_timeout),
        ("Connection Refused", simulator.simulate_connection_refused),
    ]

    for test_name, error_simulator in test_cases:
        print(f"Testing: {test_name}")
        print("-" * 50)

        try:
            # Apply network error simulation
            error_simulator()

            # Test TTS synthesis
            print("Attempting TTS synthesis...")
            start_time = time.time()

            try:
                audio_data = await provider.synthesize(
                    text="This is a test sentence for testing network error handling.",
                    voice="zh-TW-HsiaoChenNeural",
                    rate="+0%",
                    volume="+0%",
                    pitch="+0Hz",
                )
                print(f"❌ UNEXPECTED: Synthesis succeeded despite {test_name}")
                print(
                    f"   Audio data length: {len(audio_data) if audio_data else 0} bytes"
                )

            except Exception as e:
                assert (
                    time.time() - start_time < 1.5
                ), "Timeout should trigger in about 1 second"
                print("✅ EXPECTED: Synthesis failed with network error")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                print(".2f")
                print(f"   Error details: {repr(e)}")

                # Check if it's a network-related error
                error_msg = str(e).lower()
                network_keywords = [
                    "network",
                    "connection",
                    "timeout",
                    "dns",
                    "host",
                    "socket",
                    "url",
                    "getaddrinfo",
                    "unreachable",
                    "nodename",
                    "servname",
                    "http",
                    "request",
                    "temporary failure",
                    "resolution",
                ]

                is_network_error = any(
                    keyword in error_msg for keyword in network_keywords
                )
                print(
                    f"   Is network error: {'✅ Yes' if is_network_error else '❌ No'}"
                )

                if not is_network_error:
                    print(
                        "   ⚠️  WARNING: Error doesn't match expected network error patterns"
                    )

        except Exception as e:
            print(f"❌ TEST ERROR: {type(e).__name__}: {str(e)}")

        finally:
            # Restore network functionality
            simulator.restore_network()
            print("Network functionality restored\n")

    print("=== Test Summary ===")
    print("This test helps identify what errors edge-tts actually throws")
    print("under network failure conditions. Use this information to")
    print("improve the error handling in tts_integration.py")


@pytest.mark.asyncio
async def test_edge_tts_during_operation():
    """Test edge-tts behavior when network fails during operation."""

    print("=== TTS During Operation Network Failure Test ===\n")

    provider = EdgeTTSProvider()
    simulator = NetworkErrorSimulator()

    print("Starting TTS synthesis in background...")

    # Start a synthesis task
    synthesis_task = asyncio.create_task(
        provider.synthesize(
            text="This is a long sentence used to test network disconnection during operation. This sentence takes some time to process, so we can simulate network disconnection in the middle.",
            voice="zh-TW-HsiaoChenNeural",
            rate="+0%",
            volume="+0%",
            pitch="+0Hz",
        )
    )

    # Wait a bit to let synthesis start
    await asyncio.sleep(2)

    print("Simulating network failure during operation...")
    # Apply network error simulation while synthesis is running
    simulator.simulate_dns_failure()

    try:
        # Wait for synthesis to complete or fail
        audio_data = await asyncio.wait_for(synthesis_task, timeout=30)
        print(
            "❌ UNEXPECTED: Synthesis succeeded despite network failure during operation"
        )
        print(f"   Audio data length: {len(audio_data) if audio_data else 0} bytes")

    except asyncio.TimeoutError:
        print("⏰ Synthesis timed out")
        synthesis_task.cancel()

    except Exception as e:
        print("✅ EXPECTED: Synthesis failed due to network error during operation")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print(f"   Error details: {repr(e)}")

        # Check if it's a network-related error
        error_msg = str(e).lower()
        network_keywords = [
            "network",
            "connection",
            "timeout",
            "dns",
            "host",
            "socket",
            "url",
            "getaddrinfo",
            "unreachable",
            "nodename",
            "servname",
            "http",
            "request",
            "temporary failure",
            "resolution",
        ]

        is_network_error = any(keyword in error_msg for keyword in network_keywords)
        print(f"   Is network error: {'✅ Yes' if is_network_error else '❌ No'}")

    finally:
        # Restore network functionality
        simulator.restore_network()
        print("Network functionality restored\n")


def test_command_line_edge_tts():
    """Test edge-tts command line behavior with network errors."""

    print("=== Command Line Edge-TTS Test ===\n")

    # Test with network disconnected
    print("Testing edge-tts command line with network disconnected...")
    print("Make sure to disconnect network before running this test\n")

    test_commands = [
        'edge-tts --text "Test network error" --write-media /tmp/test1.mp3',
        'edge-tts --text "Okay" --write-media /tmp/test2.mp3',
    ]

    for cmd in test_commands:
        print(f"Running: {cmd}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("Command timed out")
        except Exception as e:
            print(f"Error running command: {e}")
        print()


def mock_aiohttp_connector():
    """Mock aiohttp connector to simulate network errors."""

    print("=== Mocked aiohttp Connector Test ===\n")

    # Import here to avoid import errors if aiohttp is not available
    try:
        import aiohttp
        from aiohttp import ClientConnectorError
    except ImportError:
        print("aiohttp not available, skipping mock test")
        return

    async def test_with_mocked_connector():
        provider = EdgeTTSProvider()

        # Mock the connector to raise network errors
        original_init = aiohttp.TCPConnector.__init__

        def mock_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Simulate the error from user's traceback

            async def mock_connect(*args, **kwargs):
                raise ClientConnectorError(
                    connection_key=aiohttp.ClientConnectionKey(
                        host="speech.platform.bing.com",
                        port=443,
                        is_ssl=True,
                        ssl=None,
                        proxy=None,
                        proxy_auth=None,
                        proxy_headers_hash=None,
                    ),
                    exc=Exception("Temporary failure in name resolution"),
                )

            self.connect = mock_connect

        # Apply mock
        aiohttp.TCPConnector.__init__ = mock_init

        try:
            print("Testing with mocked aiohttp connector...")
            await provider.synthesize(
                text="Test simulated network error", voice="zh-TW-HsiaoChenNeural"
            )
            print("❌ UNEXPECTED: Synthesis succeeded with mocked error")
        except Exception as e:
            print("✅ EXPECTED: Synthesis failed with mocked network error")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")

        finally:
            # Restore original
            aiohttp.TCPConnector.__init__ = original_init

    asyncio.run(test_with_mocked_connector())


if __name__ == "__main__":
    print("TTS Network Error Testing Script")
    print("=" * 50)

    if len(sys.argv) > 1:
        test_type = sys.argv[1]

        if test_type == "command":
            test_command_line_edge_tts()
        elif test_type == "mock":
            mock_aiohttp_connector()
        else:
            print("Usage: python test_network_error_handling.py [command|mock]")
            print("  command: Test edge-tts command line")
            print("  mock: Test with mocked aiohttp connector")
    else:
        # Run the main async test
        asyncio.run(test_edge_tts_network_errors())
        asyncio.run(test_edge_tts_during_operation())
