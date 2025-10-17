
#!/usr/bin/env python3
"""
Network handling for TTS integration.
"""

import logging
import socket
import threading
import time
from typing import TYPE_CHECKING

from speakub.utils.config import get_network_config

if TYPE_CHECKING:
    from speakub.ui.app import EPUBReaderApp

logger = logging.getLogger(__name__)


class NetworkManager:
    def __init__(self, app: "EPUBReaderApp"):
        self.app = app
        self.network_error_occurred = False
        self.network_error_notified = False
        self.network_recovery_notified = False
        self._lock = threading.Lock()

    def handle_network_error(self, error: Exception, context: str = "") -> None:
        """Handle network error by pausing TTS and monitoring network recovery."""
        self.app.tts_integration.last_tts_error = str(error)

        with self._lock:
            # Set network error flags if not already set
            if not self.network_error_occurred:
                self.network_error_occurred = True
                self.network_error_notified = False
                self.network_recovery_notified = False

                # Start network monitoring in background
                self.app.call_from_thread(
                    self.app.run_worker,
                    self.monitor_network_recovery,
                    exclusive=True,
                    thread=True,
                )

        # Pause TTS playback and update status
        self.app.call_from_thread(self.app.tts_integration.stop_speaking, is_pause=True)
        self.app.tts_status = "PAUSED"
        self.app.call_from_thread(self.app.tts_integration.update_tts_progress)

        with self._lock:
            # Notify user of network error (only once)
            if not self.network_error_notified:
                error_msg = "Network connection interrupted, TTS paused. Press Space to continue after network recovery."
                self.app.call_from_thread(
                    self.app.notify,
                    error_msg,
                    title="Network Error",
                    severity="warning",
                )
                self.network_error_notified = True

    def monitor_network_recovery(self) -> None:
        """Monitor network recovery and notify user when connection is restored."""
        logger.debug("_monitor_network_recovery started")

        # Get network configuration
        network_config = get_network_config()
        max_retries = (
            network_config["recovery_timeout_minutes"] * 60
        ) // network_config["recovery_check_interval"]
        check_interval = network_config["recovery_check_interval"]
        test_host = network_config["connectivity_test_host"]
        test_port = network_config["connectivity_test_port"]
        test_timeout = network_config["connectivity_test_timeout"]

        retries = 0

        is_monitoring = True
        while is_monitoring:
            with self._lock:
                is_monitoring = (
                    self.network_error_occurred
                    and not self.app.tts_integration.tts_stop_requested.is_set()
                    and retries < max_retries
                )
            logger.debug("Checking network connectivity...")
            try:
                # Test network connectivity by trying to connect to configured host
                socket.create_connection((test_host, test_port), timeout=test_timeout)
                # If we get here, network is back
                logger.debug("Network connection successful!")
                with self._lock:
                    if not self.network_recovery_notified:
                        logger.debug("Sending network recovery notification")
                        self.app.call_from_thread(
                            self.app.notify,
                            "Network connection restored! Press Space to continue TTS playback.",
                            title="Network Recovery",
                            severity="information",
                        )
                        self.network_recovery_notified = True
                        self.network_error_occurred = False
                break
            except (socket.timeout, socket.error) as e:
                # Network still down, wait and try again
                logger.debug(
                    f"Network check failed: {str(e)}, waiting {check_interval} seconds..."
                )
                retries += 1
                if is_monitoring:
                    # Check every configured interval
                    time.sleep(check_interval)

        with self._lock:
            if retries >= max_retries and self.network_error_occurred:
                timeout_minutes = network_config["recovery_timeout_minutes"]
                logger.warning(
                    f"Network recovery monitoring timed out after {timeout_minutes} minutes."
                )
                self.app.call_from_thread(
                    self.app.notify,
                    f"Network recovery check timed out after {timeout_minutes} minutes. TTS remains paused. Please check your connection and restart TTS manually.",
                    title="Network Timeout",
                    severity="warning",
                )
                self.network_error_occurred = False  # Stop further monitoring

        logger.debug("_monitor_network_recovery finished")

    def reset_network_error_state(self) -> None:
        """Reset network error state when user resumes TTS."""
        with self._lock:
            self.network_error_occurred = False
            self.network_error_notified = False
            self.network_recovery_notified = False
