
#!/usr/bin/env python3
"""
Test script for TTS integration functionality.
"""

import socket
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from speakub import TTS_AVAILABLE
from speakub.tts.integration import TTSIntegration


class MockApp:
    """Mock application for testing TTS integration."""

    def __init__(self):
        self._tts_engine = None
        self._tts_status = "STOPPED"
        self.tts_smooth_mode = False
        self.tts_volume = 100
        self.tts_rate = 0
        self.tts_pitch = "+0Hz"
        self.viewport_content = None
        self.chapter_manager = None
        self.epub_parser = None
        self.epub_manager = None
        self.content_renderer = None
        self.current_chapter = None
        self.tts_widget = None

    @property
    def tts_engine(self):
        return self._tts_engine

    @tts_engine.setter
    def tts_engine(self, value):
        self._tts_engine = value

    @property
    def tts_status(self):
        return self._tts_status

    @tts_status.setter
    def tts_status(self, value):
        self._tts_status = value

    def notify(self, message, title="", severity="information"):
        """Mock notify method."""
        pass

    def call_from_thread(self, func, *args, **kwargs):
        """Mock call_from_thread method."""
        func(*args, **kwargs)

    def run_worker(self, func, name=None, group=None, exclusive=False, thread=False):
        """Mock run_worker method."""
        if thread:
            thread = threading.Thread(target=func, daemon=True)
            thread.start()
        else:
            func()

    def bell(self):
        """Mock bell method."""
        pass

    def query_one(self, selector: str, expected_type=None):
        """Mock query_one method."""
        # Return a mock widget
        mock_widget = MagicMock()
        return mock_widget

    def _update_tts_progress(self):
        """Mock update progress method."""
        pass

    def _update_content_display(self):
        """Mock update content display method."""
        pass

    def _load_chapter(self, chapter, from_start=False):
        """Mock load chapter method."""
        pass


@pytest.fixture
def mock_app():
    """Fixture providing a mock app instance."""
    return MockApp()


@pytest.fixture
def tts_integration(mock_app):
    """Fixture providing a TTS integration instance."""
    integration = TTSIntegration(mock_app)
    mock_app.tts_integration = integration  # Add reference for compatibility
    return integration


class TestTTSIntegration:
    """Test cases for TTS integration."""

    def test_initialization(self, tts_integration, mock_app):
        """Test TTS integration initialization."""
        assert tts_integration.app == mock_app
        assert tts_integration.tts_thread is None
        assert tts_integration.playlist_manager.playlist == []
        assert tts_integration.playlist_manager.current_index == 0
        assert mock_app.tts_status == "STOPPED"
        assert not tts_integration.network_error_occurred

    @pytest.mark.asyncio
    async def test_setup_tts_success(self, tts_integration, mock_app):
        """Test successful TTS setup."""
        if not TTS_AVAILABLE:
            pytest.skip("TTS not available")

        await tts_integration.setup_tts()
        assert mock_app.tts_engine is not None

    @pytest.mark.asyncio
    async def test_setup_tts_failure(self, tts_integration, mock_app):
        """Test TTS setup failure."""
        with patch("speakub.tts.integration.TTS_AVAILABLE", False):
            await tts_integration.setup_tts()
            assert mock_app.tts_engine is None

    def test_prepare_tts_playlist_no_content(self, tts_integration, mock_app):
        """Test playlist preparation with no content."""
        mock_app.viewport_content = None
        tts_integration.prepare_tts_playlist()
        assert tts_integration.playlist_manager.playlist == []

    def test_prepare_tts_playlist_with_content(self, tts_integration, mock_app):
        """Test playlist preparation with content."""
        # Mock viewport content
        mock_viewport = MagicMock()
        mock_viewport.get_cursor_global_position.return_value = 0
        mock_viewport.line_to_paragraph_map = {0: {"index": 0}}
        mock_viewport.paragraphs = [{"start": 0, "end": 10}, {"start": 10, "end": 20}]
        mock_viewport.get_paragraph_text.side_effect = ["Text 1", "Text 2"]

        mock_app.viewport_content = mock_viewport
        tts_integration.prepare_tts_playlist()

        assert len(tts_integration.playlist_manager.playlist) == 2
        assert tts_integration.playlist_manager.playlist[0] == ("Text 1", 0)
        assert tts_integration.playlist_manager.playlist[1] == ("Text 2", 10)

    def test_handle_tts_play_pause_from_stopped(self, tts_integration, mock_app):
        """Test play/pause handling from stopped state."""
        mock_app.tts_status = "STOPPED"
        mock_app.viewport_content = MagicMock()
        mock_app.viewport_content.get_cursor_global_position.return_value = 0
        mock_app.viewport_content.line_to_paragraph_map = {0: {"index": 0}}
        mock_app.viewport_content.paragraphs = [{"start": 0, "end": 10}]
        mock_app.viewport_content.get_paragraph_text.return_value = "Test text"

        with patch.object(
            tts_integration.playlist_manager, "has_items", return_value=False
        ), patch.object(tts_integration, "start_tts_thread") as mock_start:
            tts_integration.handle_tts_play_pause()
            mock_start.assert_called_once()

    def test_handle_tts_play_pause_from_playing(self, tts_integration, mock_app):
        """Test play/pause handling from playing state."""
        mock_app.tts_status = "PLAYING"

        with patch.object(
            tts_integration.playback_manager, "stop_playback"
        ) as mock_stop:
            tts_integration.handle_tts_play_pause()
            mock_stop.assert_called_once_with(is_pause=True)
            assert mock_app.tts_status == "PAUSED"

    def test_stop_speaking_not_active(self, tts_integration, mock_app):
        """Test stopping when not active."""
        mock_app.tts_status = "STOPPED"
        tts_integration.tts_thread_active = False

        tts_integration.stop_speaking()
        assert mock_app.tts_status == "STOPPED"

    def test_start_tts_thread_already_running(self, tts_integration, mock_app):
        """Test starting thread when already running."""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        tts_integration.tts_thread = mock_thread

        # Should not create a new thread when one is already running
        original_thread = tts_integration.tts_thread
        tts_integration.start_tts_thread()
        assert tts_integration.tts_thread == original_thread

    def test_speak_with_engine_no_engine(self, tts_integration, mock_app):
        """Test speaking with no TTS engine."""
        mock_app.tts_engine = None
        tts_integration.speak_with_engine("Test text")
        # Should not raise exception

    def test_speak_with_engine_with_engine(self, tts_integration, mock_app):
        """Test speaking with TTS engine."""
        mock_engine = MagicMock()
        mock_app.tts_engine = mock_engine

        tts_integration.speak_with_engine("Test text")

        mock_engine.speak_text_sync.assert_called_once()
        call_args = mock_engine.speak_text_sync.call_args
        assert "Test text" in call_args[0]
        assert "rate" in call_args[1]
        assert "volume" in call_args[1]
        assert "pitch" in call_args[1]

    def test_cleanup(self, tts_integration, mock_app):
        """Test cleanup functionality."""
        mock_app.tts_status = "PLAYING"
        mock_engine = MagicMock()
        mock_app.tts_engine = mock_engine
        mock_widget = MagicMock()
        mock_app.tts_widget = mock_widget

        with patch.object(tts_integration, "stop_speaking") as mock_stop:
            tts_integration.cleanup()
            mock_stop.assert_called_once_with(is_pause=False)
            mock_engine.stop_async_loop.assert_called_once()
            mock_widget.cleanup.assert_called_once()

    def test_handle_network_error(self, tts_integration, mock_app):
        """Test network error handling."""
        test_error = Exception("Network error")

        # Mock call_from_thread to prevent actual execution
        with patch.object(mock_app, "call_from_thread") as mock_call:
            tts_integration._handle_network_error(test_error, "test")

            # Check that network error occurred flag was set
            assert tts_integration.network_error_occurred
            assert tts_integration.last_tts_error == "Network error"
            # call_from_thread should have been called multiple times
            assert mock_call.call_count >= 3  # At least 3 calls in handle_network_error

    def test_reset_network_error_state(self, tts_integration, mock_app):
        """Test resetting network error state."""
        tts_integration.network_manager.network_error_occurred = True
        tts_integration.network_manager.network_error_notified = True
        tts_integration.network_manager.network_recovery_notified = True

        tts_integration.reset_network_error_state()

        assert not tts_integration.network_error_occurred
        assert not tts_integration.network_error_notified
        assert not tts_integration.network_recovery_notified

    def test_monitor_network_recovery_success(self, tts_integration, mock_app):
        """Test network recovery monitoring success."""
        tts_integration.network_manager.network_error_occurred = True
        tts_integration.network_manager.network_recovery_notified = False
        # Ensure tts_stop_requested is not set
        tts_integration.tts_stop_requested.clear()

        with patch("socket.create_connection") as mock_socket:
            with patch.object(mock_app, "call_from_thread") as mock_call:
                # Mock successful connection
                mock_socket.return_value.__enter__.return_value = None

                tts_integration._monitor_network_recovery()

                assert not tts_integration.network_error_occurred
                assert tts_integration.network_recovery_notified
                mock_call.assert_called()

    def test_monitor_network_recovery_failure(self, tts_integration, mock_app):
        """Test network recovery monitoring failure."""
        tts_integration.network_manager.network_error_occurred = True
        # Don't set tts_stop_requested so the loop runs

        with patch(
            "socket.create_connection", side_effect=OSError("Connection failed")
        ):
            with patch("time.sleep") as mock_sleep:
                # Mock the method to exit after one failed attempt
                def mock_monitor():
                    # Simulate one iteration of the monitoring loop
                    try:
                        socket.create_connection(("8.8.8.8", 53), timeout=5)
                    except OSError:
                        time.sleep(10)
                    # Exit the loop by setting network_error_occurred to False
                    tts_integration.network_manager.network_error_occurred = False

                tts_integration._monitor_network_recovery = mock_monitor
                tts_integration._monitor_network_recovery()
                mock_sleep.assert_called_with(10)

    @pytest.mark.asyncio
    async def test_update_tts_progress(self, tts_integration, mock_app):
        """Test TTS progress update."""
        mock_app.tts_status = "PLAYING"
        tts_integration.playlist_manager.playlist = [("text1", 0), ("text2", 10)]
        tts_integration.playlist_manager.current_index = 0

        # Mock the Static widget and query_one method
        mock_static = MagicMock()
        mock_app.query_one = MagicMock(return_value=mock_static)

        await tts_integration.update_tts_progress()

        # Verify widgets were updated
        assert mock_static.update.called

    @pytest.mark.asyncio
    async def test_update_tts_progress_with_viewport(self, tts_integration, mock_app):
        """Test TTS progress update with viewport content."""
        mock_app.tts_status = "PLAYING"
        tts_integration.playlist_manager.playlist = [("text1", 0)]
        tts_integration.playlist_manager.current_index = 0

        # Mock viewport content
        mock_viewport = MagicMock()
        mock_viewport.get_viewport_info.return_value = {
            "current_page": 1,
            "total_pages": 10,
        }
        mock_app.viewport_content = mock_viewport

        # Mock the Static widget and query_one method
        mock_static = MagicMock()
        mock_app.query_one = MagicMock(return_value=mock_static)

        await tts_integration.update_tts_progress()

        # Verify page info was updated
        page_calls = [
            call for call in mock_static.update.call_args_list if "Page" in str(call)
        ]
        assert len(page_calls) > 0
