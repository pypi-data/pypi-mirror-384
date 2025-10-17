
#!/usr/bin/env python3
"""
TTS runners and workers for SpeakUB.
"""

import asyncio
import logging
import socket
import time
from typing import TYPE_CHECKING

from speakub.utils.text_utils import correct_chinese_pronunciation

if TYPE_CHECKING:
    from speakub.tts.integration import TTSIntegration

logger = logging.getLogger(__name__)


def tts_runner_serial(tts_integration: "TTSIntegration") -> None:
    """Serial TTS runner."""
    app = tts_integration.app
    playlist_manager = tts_integration.playlist_manager
    with tts_integration.tts_lock:
        tts_integration.tts_thread_active = True
    try:
        while not tts_integration.tts_stop_requested.is_set():
            if app.tts_status != "PLAYING":
                break
            with tts_integration.tts_lock:
                exhausted = playlist_manager.is_exhausted()
            if exhausted:
                try:
                    if not playlist_manager.load_next_chapter():
                        break
                    else:
                        continue
                except Exception as e:
                    logger.error(f"TTS runner failed to load next chapter: {e}")
                    app.call_from_thread(
                        app.notify,
                        f"TTS chapter load failed: {e}",
                        title="TTS Error",
                        severity="error",
                    )
                    break
            with tts_integration.tts_lock:
                current_item = playlist_manager.get_current_item()
                if not current_item:
                    break
                text, line_num = current_item[0], current_item[1]
                if app.viewport_content:
                    page, cursor = divmod(
                        line_num, app.viewport_content.viewport_height
                    )
                    app.viewport_content.current_page = min(
                        page, app.viewport_content.total_pages - 1
                    )
                    lines = len(app.viewport_content.get_current_viewport_lines())
                    app.viewport_content.cursor_in_page = max(0, min(cursor, lines - 1))
                    app.call_from_thread(app._update_content_display)
            if app.tts_engine:
                playback_completed = False
                try:
                    tts_integration.speak_with_engine(text)
                    playback_completed = True  # Only set on successful completion
                except (
                    socket.gaierror,
                    socket.timeout,
                    ConnectionError,
                    OSError,
                ) as e:
                    tts_integration.network_manager.handle_network_error(
                        e, "serial_runner"
                    )
                    break
                except Exception as e:
                    if tts_integration.tts_stop_requested.is_set():
                        break
                    tts_integration.last_tts_error = str(e)
                    error_msg_str = str(e).lower()
                    if (
                        "no audio was received" in error_msg_str
                        or "noaudioreceived" in str(type(e).__name__).lower()
                    ):
                        with tts_integration.tts_lock:
                            playlist_manager.advance_index()
                        continue
                    else:
                        app.call_from_thread(
                            app.notify,
                            f"TTS playback failed: {str(e)}",
                            title="TTS Playback Error",
                            severity="error",
                        )
                        with tts_integration.tts_lock:
                            playlist_manager.advance_index()
                        continue

                # Only advance to next item if playback completed and not paused
                if (
                    playback_completed
                    and not tts_integration.tts_stop_requested.is_set()
                ):
                    with tts_integration.tts_lock:
                        playlist_manager.advance_index()
    finally:
        with tts_integration.tts_lock:
            if app.tts_status == "PLAYING":
                app.tts_status = "STOPPED"


def find_and_play_next_chapter_worker(tts_integration: "TTSIntegration") -> None:
    """Worker to find and play next chapter."""
    app = tts_integration.app
    if tts_integration.playlist_manager.load_next_chapter():
        tts_integration.start_tts_thread()
    else:
        app.call_from_thread(app.notify, "No more content to read.", title="TTS")
        app.tts_status = "STOPPED"


def tts_runner_parallel(tts_integration: "TTSIntegration") -> None:
    """Parallel TTS runner."""
    app = tts_integration.app
    playlist_manager = tts_integration.playlist_manager
    with tts_integration.tts_lock:
        tts_integration.tts_thread_active = True
    try:
        while not tts_integration.tts_stop_requested.is_set():
            with tts_integration.tts_lock:
                exhausted = playlist_manager.is_exhausted()
            if exhausted:
                if not playlist_manager.load_next_chapter():
                    break
                else:
                    continue

            with tts_integration.tts_lock:
                if playlist_manager.is_exhausted():
                    break
                current_item = playlist_manager.get_current_item()

            if not current_item:
                break
            if len(current_item) == 3:
                audio = current_item[2]
                if audio == b"FAILED_SYNTHESIS":
                    with tts_integration.tts_lock:
                        playlist_manager.advance_index()
                    continue

                with tts_integration.tts_lock:
                    line_num = current_item[1]
                    if app.viewport_content:
                        page, cursor = divmod(
                            line_num, app.viewport_content.viewport_height
                        )
                        app.viewport_content.current_page = min(
                            page, app.viewport_content.total_pages - 1
                        )
                        lines = len(app.viewport_content.get_current_viewport_lines())
                        app.viewport_content.cursor_in_page = max(
                            0, min(cursor, lines - 1)
                        )
                        app.call_from_thread(app._update_content_display)

                if (
                    app.tts_engine
                    and hasattr(app.tts_engine, "_event_loop")
                    and app.tts_engine._event_loop
                ):
                    playback_completed = False
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            app.tts_engine.play_audio(audio),
                            app.tts_engine._event_loop,
                        )
                        future.result()
                        playback_completed = True  # Only set on successful completion
                    except (
                        socket.gaierror,
                        socket.timeout,
                        ConnectionError,
                        OSError,
                    ) as e:
                        tts_integration.network_manager.handle_network_error(
                            e, "parallel_runner_playback"
                        )
                        break
                    except Exception as e:
                        app.call_from_thread(
                            app.notify,
                            f"TTS playback failed: {str(e)}",
                            title="TTS Playback Error",
                            severity="error",
                        )
                        with tts_integration.tts_lock:
                            playlist_manager.advance_index()
                        continue

                    # Only advance to next item if playback completed and not paused
                    if (
                        playback_completed
                        and not tts_integration.tts_stop_requested.is_set()
                    ):
                        with tts_integration.tts_lock:
                            playlist_manager.advance_index()
            else:
                tts_integration.tts_synthesis_ready.clear()
                synthesis_ready = tts_integration.tts_synthesis_ready.wait(timeout=0.1)
                if not synthesis_ready:
                    time.sleep(0.05)
    finally:
        with tts_integration.tts_lock:
            if app.tts_status == "PLAYING":
                app.tts_status = "STOPPED"


def tts_pre_synthesis_worker(tts_integration: "TTSIntegration") -> None:
    """Worker thread that synthesizes text ahead of time for smooth mode."""
    app = tts_integration.app
    playlist_manager = tts_integration.playlist_manager
    while not tts_integration.tts_stop_requested.is_set():
        try:
            text_to_synthesize = None
            target_index = -1
            with tts_integration.tts_lock:
                current_idx = playlist_manager.get_current_index()
                limit = min(playlist_manager.get_playlist_length(), current_idx + 3)
            for i in range(current_idx, limit):
                with tts_integration.tts_lock:
                    item = playlist_manager.get_item_at(i)
                    if item and len(item) == 2:
                        text_to_synthesize = item[0]
                        target_index = i
                        break
            if (
                text_to_synthesize
                and app.tts_engine
                and hasattr(app.tts_engine, "synthesize")
                and hasattr(app.tts_engine, "_event_loop")
                and app.tts_engine._event_loop
            ):
                audio_data = b"ERROR"
                synthesis_success = False
                try:
                    rate_str = f"{app.tts_rate:+}%"
                    volume_str = f"{app.tts_volume - 100:+}%"
                    corrected_text = correct_chinese_pronunciation(text_to_synthesize)
                    future = asyncio.run_coroutine_threadsafe(
                        app.tts_engine.synthesize(
                            corrected_text,
                            rate=rate_str,
                            volume=volume_str,
                            pitch=app.tts_pitch,
                        ),
                        app.tts_engine._event_loop,
                    )
                    audio_data = future.result(timeout=60)
                    if audio_data is not None and audio_data != b"ERROR":
                        synthesis_success = True
                    else:
                        audio_data = b"FAILED_SYNTHESIS"
                except (
                    socket.gaierror,
                    socket.timeout,
                    ConnectionError,
                    OSError,
                ) as e:
                    tts_integration.network_manager.handle_network_error(
                        e, "synthesis_worker"
                    )
                    break
                except Exception:
                    audio_data = b"FAILED_SYNTHESIS"

                with tts_integration.tts_lock:
                    item = playlist_manager.get_item_at(target_index)
                    if item and len(item) == 2:
                        if synthesis_success:
                            new_item = (item[0], item[1], audio_data)
                        else:
                            new_item = (item[0], item[1], b"FAILED_SYNTHESIS")
                        playlist_manager.update_item_at(target_index, new_item)
                    tts_integration.tts_synthesis_ready.set()
            else:
                tts_integration.tts_data_available.clear()
                data_available = tts_integration.tts_data_available.wait(timeout=0.2)
                if not data_available:
                    time.sleep(0.1)
        except (socket.gaierror, socket.timeout) as e:
            logger.error("Network error in TTS pre-synthesis worker: %s", e)
            time.sleep(1)
        except asyncio.TimeoutError as e:
            logger.error("TTS synthesis timeout in pre-synthesis worker: %s", e)
            time.sleep(1)
        except Exception as e:
            logger.exception("Unexpected error in TTS pre-synthesis worker")
            time.sleep(1)
