
#!/usr/bin/env python3
"""
TTS integration for SpeakUB
"""

import functools
import threading
from typing import Optional

# TTS availability check
try:
    import edge_tts  # noqa: F401

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
from speakub.tts.playback_manager import PlaybackManager
from speakub.tts.playlist_manager import PlaylistManager
from speakub.tts.ui.network import NetworkManager
from speakub.tts.ui.runners import find_and_play_next_chapter_worker
from speakub.ui.protocols import AppInterface
from speakub.utils.text_utils import correct_chinese_pronunciation

if TTS_AVAILABLE:
    try:
        from speakub.tts.edge_tts_provider import EdgeTTSProvider
    except Exception:
        EdgeTTSProvider = None


class TTSIntegration:
    """Handles TTS functionality integration."""

    def __init__(self, app: AppInterface):
        self.app = app

        # Runtime check to ensure the app object conforms to the protocol.
        # This will raise an error if EPUBReaderApp does not correctly implement the properties.
        if not isinstance(app, AppInterface):
            raise ValueError(
                "The 'app' object does not conform to AppInterface protocol."
            )

        self.tts_thread: Optional[threading.Thread] = None
        self.tts_pre_synthesis_thread: Optional[threading.Thread] = None
        self.tts_lock = threading.RLock()
        self.tts_stop_requested = threading.Event()
        with self.tts_lock:
            self.tts_thread_active = False
            self.last_tts_error = None

        self.tts_synthesis_ready = threading.Event()
        self.tts_playback_ready = threading.Event()
        self.tts_data_available = threading.Event()

        self.network_manager = NetworkManager(app)

        # Initialize managers
        self.playlist_manager = PlaylistManager(self)
        self.playback_manager = PlaybackManager(self, self.playlist_manager)

        # Backward compatibility properties
        self.network_error_occurred = self.network_manager.network_error_occurred
        self.network_error_notified = self.network_manager.network_error_notified
        self.network_recovery_notified = self.network_manager.network_recovery_notified

    async def setup_tts(self) -> None:
        """Set up TTS engine."""
        if not TTS_AVAILABLE or EdgeTTSProvider is None:
            return
        try:
            self.app.tts_engine = EdgeTTSProvider()
            if hasattr(self.app.tts_engine, "start_async_loop"):
                self.app.tts_engine.start_async_loop()
        except Exception:
            self.app.bell()

    async def update_tts_progress(self) -> None:
        """Update TTS progress display."""
        try:
            from textual.widgets import Static

            status_widget = self.app.query_one("#tts-status", Static)
            status = self.app.tts_status.upper()
            smooth = " (Smooth)" if self.app.tts_smooth_mode else ""
            status_text = f"TTS: {status}{smooth}"
            status_widget.update(status_text)

            controls_widget = self.app.query_one("#tts-controls", Static)
            percent = None
            if status == "PLAYING" and self.playlist_manager.has_items():
                total = self.playlist_manager.get_playlist_length()
                current = self.playlist_manager.get_current_index()
                if total > 0 and current < total:
                    percent = int((current / total) * 100)
            p_disp = f"{percent}%" if percent is not None else "--"
            v_disp = f"{self.app.tts_volume}"
            s_disp = f"{self.app.tts_rate:+}"
            controls_text = f"{p_disp} | Vol: {v_disp}% | Speed: {s_disp}% | Pitch: {self.app.tts_pitch}"
            controls_widget.update(controls_text)

            page_widget = self.app.query_one("#tts-page", Static)
            page_text = ""
            if self.app.viewport_content:
                info = self.app.viewport_content.get_viewport_info()
                page_text = f"Page {info['current_page'] + 1}/{info['total_pages']}"
            page_widget.update(page_text)

            # Add debug info for current audio file
            try:
                if self.app.tts_engine and hasattr(self.app.tts_engine, "audio_player"):
                    audio_status = self.app.tts_engine.audio_player.get_status()
                    current_file = audio_status.get("current_file", "None")
                    if current_file and current_file != "None":
                        # Extract just the filename from the path for display
                        import os

                        filename = os.path.basename(current_file)
                        debug_info = f"File: {filename}"
                        # Update the TTS panel with debug info if it exists
                        try:
                            tts_panel = self.app.query_one(
                                "#tts-panel", type=type(None)
                            )
                            if tts_panel and hasattr(tts_panel, "update_status"):
                                # Get current status and add debug info
                                current_status = status_text
                                tts_panel.update_status(
                                    current_status, debug_info)
                        except Exception:
                            pass  # Ignore if panel doesn't exist or doesn't support debug info
            except Exception:
                pass  # Ignore debug info errors

        except Exception:
            import logging

            logging.exception("Error updating TTS progress display")

    def handle_tts_play_pause(self) -> None:
        """Handle TTS play/pause action."""
        with self.tts_lock:
            if self.app.tts_status == "PLAYING":
                self.playback_manager.stop_playback(is_pause=True)
                self.app.tts_status = "PAUSED"
            elif self.app.tts_status == "PAUSED":
                if self.network_manager.network_error_occurred:
                    self.network_manager.reset_network_error_state()
                    self.app.notify(
                        "Restarting TTS playback...",
                        title="TTS Resume",
                        severity="information",
                    )
                self.playback_manager.start_playback()
            elif self.app.tts_status == "STOPPED":
                if self.network_manager.network_error_occurred:
                    self.network_manager.reset_network_error_state()
                self.playlist_manager.generate_playlist()
                if self.playlist_manager.has_items():
                    self.playback_manager.start_playback()
                else:
                    worker_func = functools.partial(
                        find_and_play_next_chapter_worker, self
                    )
                    self.app.run_worker(
                        worker_func, exclusive=True, thread=True)

    def stop_speaking(self, is_pause: bool = False) -> None:
        """Stop TTS playback."""
        self.playback_manager.stop_playback(is_pause=is_pause)
        if not is_pause:
            self.playlist_manager.reset()
            self.last_tts_error = None

    def start_tts_thread(self) -> None:
        """Start TTS playback thread (backward compatibility)."""
        self.playback_manager.start_playback()

    def prepare_tts_playlist(self) -> None:
        """Prepare TTS playlist (backward compatibility)."""
        self.playlist_manager.generate_playlist()

    def _handle_network_error(self, error: Exception, context: str) -> None:
        """Handle network error (backward compatibility)."""
        self.network_manager.handle_network_error(error, context)

    def reset_network_error_state(self) -> None:
        """Reset network error state (backward compatibility)."""
        self.network_manager.reset_network_error_state()

    def _monitor_network_recovery(self) -> None:
        """Monitor network recovery (backward compatibility)."""
        self.network_manager.monitor_network_recovery()

    def speak_with_engine(self, text: str) -> None:
        """Speak text using TTS engine."""
        if not self.app.tts_engine:
            return
        try:
            corrected_text = correct_chinese_pronunciation(text)
            rate, volume = f"{self.app.tts_rate:+}%", f"{self.app.tts_volume - 100:+}%"
            kwargs = {"rate": rate, "volume": volume,
                      "pitch": self.app.tts_pitch}
            if hasattr(self.app.tts_engine, "speak_text_sync"):
                self.app.tts_engine.speak_text_sync(corrected_text, **kwargs)
        except Exception as e:
            raise e

    def cleanup(self) -> None:
        """Clean up TTS resources."""
        # Shut down the playback manager and its thread pool first
        import logging

        try:
            self.playback_manager.shutdown()
        except Exception as e:
            logging.error(f"Error shutting down playback manager: {e}")

        if self.app.tts_status in ["PLAYING", "PAUSED"]:
            try:
                self.stop_speaking(is_pause=False)
            except Exception as e:
                logging.warning(f"Error during stop_speaking on cleanup: {e}")

        if self.app.tts_widget:
            try:
                self.app.tts_widget.cleanup()
            except Exception as e:
                logging.warning(f"Error cleaning up tts_widget: {e}")

        if self.app.tts_engine and hasattr(self.app.tts_engine, "stop_async_loop"):
            try:
                self.app.tts_engine.stop_async_loop()
            except Exception as e:
                logging.warning(f"Error stopping tts_engine async loop: {e}")
