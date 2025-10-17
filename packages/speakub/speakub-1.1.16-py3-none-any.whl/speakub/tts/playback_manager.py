
"""
Playback Manager for TTS in SpeakUB.
Handles playback thread lifecycle using a thread pool for efficiency.
"""

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import TYPE_CHECKING, List

from speakub.tts.ui.runners import (
    tts_pre_synthesis_worker,
    tts_runner_parallel,
    tts_runner_serial,
)

if TYPE_CHECKING:
    from speakub.tts.integration import TTSIntegration
    from speakub.tts.playlist_manager import PlaylistManager

logger = logging.getLogger(__name__)


class PlaybackManager:
    """Manages TTS playback thread lifecycle using a ThreadPoolExecutor."""

    def __init__(
        self, tts_integration: "TTSIntegration", playlist_manager: "PlaylistManager"
    ):
        self.tts_integration = tts_integration
        self.app = tts_integration.app
        self.stop_event = tts_integration.tts_stop_requested
        self.playlist_manager = playlist_manager  # Direct reference
        self.lock = tts_integration.tts_lock
        self.executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="TTSWorker"
        )
        self.futures: List[Future] = []

    def _cleanup_futures(self) -> None:
        """Periodically clean completed futures during playback."""
        self.futures = [f for f in self.futures if not f.done()]

    def start_playback(self) -> None:
        """Start TTS playback using the thread pool."""
        self._cleanup_futures()
        if self.is_playing():
            return

        self.stop_event.clear()
        self.app.tts_status = "PLAYING"
        self.tts_integration.tts_thread_active = True

        if self.app.tts_smooth_mode:
            self.futures.append(
                self.executor.submit(tts_runner_parallel, self.tts_integration)
            )
            self.futures.append(
                self.executor.submit(tts_pre_synthesis_worker, self.tts_integration)
            )
        else:
            self.futures.append(
                self.executor.submit(tts_runner_serial, self.tts_integration)
            )

    def stop_playback(self, is_pause: bool = False) -> None:
        """Stop TTS playback."""
        with self.lock:
            if (
                not self.tts_integration.tts_thread_active
                and self.app.tts_status != "PAUSED"
            ):
                if not is_pause:
                    self.app.tts_status = "STOPPED"
                return

            self.stop_event.set()

            if self.app.tts_engine:
                try:
                    # Distinguish between pause and stop operations
                    if is_pause:
                        # For pause, call pause() which only pauses playback without cleanup
                        if hasattr(self.app.tts_engine, "pause"):
                            self.app.tts_engine.pause()
                    else:
                        # For stop, call stop() which stops and cleans up resources
                        if hasattr(self.app.tts_engine, "stop"):
                            self.app.tts_engine.stop()
                except Exception as e:
                    logger.warning(f"Error in TTS engine operation: {e}")

            # Wait for futures to complete with timeout to prevent blocking
            if not is_pause and self.futures:
                for future in self.futures:
                    try:
                        # Wait up to 2 seconds per future
                        future.result(timeout=2.0)
                    except FutureTimeout:
                        logger.warning("TTS future timed out during stop")
                        future.cancel()
                    except Exception as e:
                        logger.error(f"Error waiting for future: {e}")

            self.tts_integration.tts_thread_active = False
            self.app.tts_status = "PAUSED" if is_pause else "STOPPED"

            if not is_pause:
                self.playlist_manager.reset()
                # Clear futures on a full stop
                self.futures = []
                self._cleanup_futures()

    def pause_playback(self) -> None:
        """Pause TTS playback."""
        self.stop_playback(is_pause=True)

    def is_playing(self) -> bool:
        """Check if playback is active by checking the futures."""
        if not self.futures:
            return False

        # Clean up completed futures and check if any are still running.
        active_futures = [f for f in self.futures if not f.done()]
        self.futures = active_futures
        # If the list is not empty after cleanup, it means something is still running.
        return len(self.futures) > 0

    def shutdown(self) -> None:
        """Shutdown the thread pool executor with timeout protection."""
        logger.debug("Shutting down TTS playback manager thread pool.")
        self.stop_event.set()

        try:
            # Attempt graceful shutdown with timeout (Python 3.9+)
            import sys

            if sys.version_info >= (3, 9):
                self.executor.shutdown(wait=True, timeout=5.0)
            else:
                # For older Python versions, use wait=True without timeout
                self.executor.shutdown(wait=True)
            logger.debug("Thread pool shutdown completed successfully.")
        except TimeoutError:
            logger.warning("Thread pool shutdown timed out - forcing cleanup")
            # Force shutdown if graceful shutdown fails
            self.executor.shutdown(wait=False)
            # Give a moment for forced shutdown
            import time

            time.sleep(0.1)
        except TypeError as e:
            # Handle case where timeout parameter is not supported
            if "timeout" in str(e):
                logger.debug(
                    "ThreadPoolExecutor.shutdown() does not support timeout parameter, using basic shutdown"
                )
                try:
                    self.executor.shutdown(wait=True)
                    logger.debug("Thread pool shutdown completed successfully.")
                except Exception as shutdown_error:
                    logger.error(
                        f"Error during basic thread pool shutdown: {shutdown_error}"
                    )
                    self.executor.shutdown(wait=False)
            else:
                raise
        except Exception as e:
            logger.error(f"Error during thread pool shutdown: {e}")
            # Ensure executor is shut down even on error
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass  # Ignore errors during forced shutdown
