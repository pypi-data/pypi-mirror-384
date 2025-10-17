
import logging
from typing import TYPE_CHECKING, List, Tuple, Union

if TYPE_CHECKING:
    from speakub.tts.playlist_manager import PlaylistManager

logger = logging.getLogger(__name__)


def prepare_tts_playlist(playlist_manager: "PlaylistManager") -> None:
    """Prepare TTS playlist from current content."""
    app = playlist_manager.app
    if not app.viewport_content:
        return

    with playlist_manager.tts_integration.tts_lock:
        playlist_manager.reset()
        cursor_idx = app.viewport_content.get_cursor_global_position()
        para_info = app.viewport_content.line_to_paragraph_map.get(cursor_idx)
        if not para_info:
            for i in range(cursor_idx, len(app.viewport_content.content_lines)):
                if app.viewport_content._is_content_line(
                    app.viewport_content.content_lines[i]
                ):
                    para_info = app.viewport_content.line_to_paragraph_map.get(i)
                    break
            if not para_info:
                return
        start_idx = para_info["index"]
        for p_info in app.viewport_content.paragraphs[start_idx:]:
            text = app.viewport_content.get_paragraph_text(p_info)
            if text.strip():
                playlist_manager.playlist.append((text, p_info["start"]))


def tts_load_next_chapter(playlist_manager: "PlaylistManager") -> bool:
    """Load next chapter for TTS."""
    app = playlist_manager.app
    if not app.epub_manager:
        return False

    with playlist_manager.tts_integration.tts_lock:
        try:
            # Use the new facade method to get next chapter and its content
            result = app.epub_manager.get_next_chapter_content_lines()
            if result:
                next_chapter, lines = result
                if app.viewport_content:
                    temp_vp = app.viewport_content.__class__(
                        lines, app.current_viewport_height
                    )
                    new_playlist: List[
                        Union[Tuple[str, int], Tuple[str, int, Union[bytes, str]]]
                    ] = []
                    for p in temp_vp.paragraphs:
                        text = temp_vp.get_paragraph_text(p)
                        if text.strip():
                            new_playlist.append((text, p["start"]))
                else:
                    new_playlist = []

                if new_playlist:
                    playlist_manager.playlist, playlist_manager.current_index = (
                        new_playlist,
                        0,
                    )
                    app.call_from_thread(
                        app.run_worker,
                        app.epub_manager.load_chapter(next_chapter, from_start=True),
                    )
                    return True
        except Exception:
            return False
    return False
