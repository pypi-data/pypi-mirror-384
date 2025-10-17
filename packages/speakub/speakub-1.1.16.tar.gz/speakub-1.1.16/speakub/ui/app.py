
#!/usr/bin/env python3
"""
Main SpeakUB Application - Textual UI
"""

# Re-add necessary imports that are actually used
import logging
from typing import Dict, Iterable, Optional

from bs4 import BeautifulSoup
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Tree

from speakub import TTS_AVAILABLE
from speakub.core import ConfigurationError
from speakub.core.progress_tracker import ProgressTracker
from speakub.tts.integration import TTSIntegration
from speakub.ui.actions import SpeakUBActions
from speakub.ui.epub_manager import EPUBManager
from speakub.ui.panel_titles import PanelTitle
from speakub.ui.progress import ProgressManager
from speakub.ui.ui_utils import UIUtils
from speakub.ui.voice_selector_panel import VoiceSelectorPanel
from speakub.ui.widgets.content_widget import ContentDisplay, ViewportContent
from speakub.utils.config import ConfigManager

if TTS_AVAILABLE:
    try:
        from speakub.tts.edge_tts_provider import EdgeTTSProvider
    except Exception:
        EdgeTTSProvider = None  # type: ignore
    try:
        from speakub.ui.widgets.tts_widget import TTSRichWidget  # type: ignore
    except Exception:
        TTSRichWidget = None  # type: ignore


logger = logging.getLogger(__name__)


class EPUBReaderApp(App):
    """Main SpeakUB Application using Textual UI.

    This class implements the AppInterface protocol.
    """

    CSS = """
    #app-container {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }

    #main-app-column {
        layout: vertical;
        width: 100fr;
    }

    #voice-panel {
        width: 60;
        border-left: solid $accent;
        layout: vertical;
    }
    #voice-panel.hidden {
        display: none;
    }
    #voice-table {
        height: 1fr;
        margin: 1 0;
    }

    .main-container {
        layout: horizontal;
        height: 1fr;
    }

    .toc-panel {
        width: 24fr;
        border: solid $primary;
        padding: 0 0;
        margin: 0 0;
    }
    .content-panel {
        width: 76fr;
        border: solid $secondary;
        padding: 0 0;
        margin: 0 0;
    }
    #content-container { height: 100%; overflow: hidden; }
    #content-display { height: 100%; padding: 1; overflow: hidden; }
    .toc-panel.focused { border: solid $accent; }
    .content-panel.focused { border: solid $accent; }
    #voice-panel.focused { border-left: solid $warning; }

    #tts-footer {
        height: auto;
        min-height: 1;
        max-height: 3;
        padding: 0 1;
        margin: 0 0;
        background: $surface;
        border: solid $accent;
    }
    #tts-footer > #tts-status { text-align: left; width: 1fr; }
    #tts-footer > #tts-controls { text-align: center; width: 2fr; }
    #tts-footer > #tts-page { text-align: right; width: 1fr; }
    .panel-title { background: $boost; padding: 0 1; height: 1; }
    Tree { padding: 0 0; margin: 0 0; }
    Input { margin: 0 1; padding: 0 1; width: 6; }
    Static { margin: 0 1; padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "⏻"),
        Binding("tab", "switch_focus", "Switch Focus"),
        Binding("f1", "toggle_toc", "⇄ TOC"),
        Binding("f2", "toggle_tts", "⇄ TTS"),
        Binding("v", "toggle_voice_panel", "⇄ Voices"),
        Binding("m", "toggle_smooth_tts", "⇄ Smooth TTS"),
        Binding("space", "tts_play_pause", "▶ ❚❚ "),
        Binding("s", "tts_stop", "🚫 TTS"),
        Binding("+", "increase_volume", "🔊 "),
        Binding("=", "increase_volume", "Vol Up", show=False),
        Binding("-", "decrease_volume", "🔉 "),
        Binding("]", "increase_speed", "🗲 Up"),
        Binding("[", "decrease_speed", "🗲 Down"),
        Binding("p", "increase_pitch", "🎼 Up"),
        Binding("o", "decrease_pitch", "🎼 Down"),
    ]

    # ... (rest of __init__ and compose methods remain unchanged) ...
    def __init__(
        self,
        epub_path: str,
        debug: bool = False,
        log_file: Optional[str] = None,
        fallback_viewport_height: int = 25,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.epub_path = epub_path
        self.log_file = log_file
        self._debug = bool(debug)
        self.fallback_viewport_height = fallback_viewport_height

        self.current_focus = "toc"
        self.toc_visible = True
        self.tts_visible = True
        self.toc_data: Optional[Dict] = None
        self.current_chapter: Optional[Dict] = None
        self.current_chapter_soup: Optional[BeautifulSoup] = None
        self.viewport_content: Optional[ViewportContent] = None
        self.current_viewport_height = fallback_viewport_height
        self._widgets_ready = False

        # Refactored to use private attributes with properties to match AppInterface
        self._tts_engine: Optional["EdgeTTSProvider"] = None
        self.tts_widget: Optional["TTSRichWidget"] = None
        self._tts_status: str = "STOPPED"
        self.now_reading_text = "..."

        # Load TTS configuration from centralized config
        try:
            config_mgr = ConfigManager()
            tts_config = config_mgr.get("tts", {})
            self.tts_rate = tts_config["rate"]
            self.tts_volume = tts_config["volume"]
            self.tts_pitch = tts_config["pitch"]
            self.tts_smooth_mode = tts_config["smooth_mode"]
            logger.debug(f"TTS configuration loaded: {tts_config}")
        except (ConfigurationError, KeyError) as e:
            logger.warning(f"Failed to load TTS config, using defaults: {e}")
            # Fallback to default values
            self.tts_rate = 0
            self.tts_volume = 100
            self.tts_pitch = "+0Hz"
            self.tts_smooth_mode = False
        except Exception as e:
            # Include traceback
            logger.exception("Unexpected error loading TTS config")
            raise  # Re-raise unexpected errors

        self.actions = SpeakUBActions(self)
        self.epub_manager = EPUBManager(self)
        self.progress_manager = ProgressManager(self, self._update_tts_progress)
        self.tts_integration = TTSIntegration(self)
        self.ui_utils = UIUtils(self)
        self.progress_tracker: Optional[ProgressTracker] = None
        self.chapter_manager = None

    # --- Start: Property implementations for AppInterface ---
    @property
    def tts_engine(self) -> Optional["EdgeTTSProvider"]:
        return self._tts_engine

    @tts_engine.setter
    def tts_engine(self, value: Optional["EdgeTTSProvider"]) -> None:
        self._tts_engine = value

    @property
    def tts_status(self) -> str:
        return self._tts_status

    @tts_status.setter
    def tts_status(self, value: str) -> None:
        # Optional: Add validation here in the future
        self._tts_status = value

    # --- End: Property implementations for AppInterface ---

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Horizontal(id="app-container"):
            with Vertical(id="main-app-column"):
                yield Header(show_clock=False)

                with Horizontal(classes="main-container"):
                    with Vertical(classes="toc-panel", id="toc-panel"):
                        yield PanelTitle(
                            "Table of Contents",
                            classes="panel-title",
                            id="toc-panel-title",
                        )
                        yield Tree("Loading...", id="toc-tree")

                    with Vertical(classes="content-panel", id="content-panel"):
                        yield PanelTitle(
                            "Chapter Content",
                            classes="panel-title",
                            id="content-panel-title",
                        )
                        with Container(id="content-container"):
                            yield ContentDisplay(
                                "Select a chapter to begin reading...",
                                id="content-display",
                            )

                with Horizontal(id="tts-footer"):
                    yield Static("TTS: IDLE", id="tts-status")
                    yield Static(
                        "-- | Vol: 70% | Speed: 0% | Pitch: +0Hz",
                        id="tts-controls",
                    )
                    yield Static("", id="tts-page")

                yield Footer()

            yield VoiceSelectorPanel(id="voice-panel", classes="hidden")

    async def on_mount(self) -> None:
        logger.debug("on_mount started")

        # Clean up orphaned temporary files on startup
        if TTS_AVAILABLE:
            try:
                from speakub.tts.edge_tts_provider import cleanup_orphaned_tts_files

                cleaned = cleanup_orphaned_tts_files(max_age_hours=24)
                if cleaned > 0:
                    logger.info(
                        f"Startup cleanup: removed {cleaned} orphaned TTS files"
                    )
            except Exception as e:
                logger.warning(f"Startup cleanup failed: {e}")

        content_display = self.query_one("#content-display", ContentDisplay)
        content_display.app_ref = self
        content_display.can_focus = True
        self._widgets_ready = True
        self.set_timer(0.1, self._delayed_viewport_calculation)
        await self.tts_integration.setup_tts()
        await self.epub_manager.load_epub()
        await self.progress_manager.start_progress_tracking()
        self.ui_utils.update_panel_focus()
        logger.debug("on_mount finished")

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Provide system commands to the command palette."""
        yield from super().get_system_commands(screen)

        yield SystemCommand(
            "Toggle Voice Panel",
            "Show/hide the TTS voice selector",
            self.action_toggle_voice_panel,
        )

    async def _populate_voice_list(self) -> None:
        """Fetch TTS voice list, filter, and populate the voice selector panel."""
        if self.tts_engine and hasattr(self.tts_engine, "get_available_voices"):
            try:
                voices = await self.tts_engine.get_available_voices()
                voice_panel = self.query_one(VoiceSelectorPanel)

                if voices:
                    female_chinese_voices = [
                        voice
                        for voice in voices
                        if voice.get("gender", "").lower() == "female"
                        and voice.get("locale", "").startswith(("zh-CN", "zh-TW"))
                    ]

                    # --- Key modification: Get current voice and pass to panel ---
                    current_voice = self.tts_engine.get_current_voice()

                    if female_chinese_voices:
                        voice_panel.update_voices(female_chinese_voices, current_voice)
                    else:
                        self.notify(
                            "No female Chinese voices found. Displaying all available voices.",
                            severity="warning",
                        )
                        voice_panel.update_voices(voices, current_voice)
                else:
                    self.notify("No TTS voices found.", severity="warning")
            except Exception as e:
                self.notify(f"Error fetching voices: {e}", severity="error")

    # ... (all other methods remain unchanged) ...
    def action_toggle_voice_panel(self) -> None:
        """Toggles the visibility of the voice selector panel."""
        voice_panel = self.query_one(VoiceSelectorPanel)
        panel_is_visible = not voice_panel.has_class("hidden")

        if panel_is_visible:
            voice_panel.add_class("hidden")
            self.query_one("#main-app-column").styles.width = "100fr"
            self.query_one("#content-display").focus()
        else:
            self.run_worker(self._populate_voice_list, exclusive=True)
            self.query_one("#main-app-column").styles.width = "1fr"
            voice_panel.remove_class("hidden")
            voice_panel.focus()

    def _delayed_viewport_calculation(self) -> None:
        self.ui_utils.calculate_viewport_height()

    def on_resize(self, event) -> None:
        self.set_timer(0.05, self.ui_utils.calculate_viewport_height)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.data:
            self.run_worker(self.epub_manager.load_chapter(event.node.data))

    def on_voice_selector_panel_voice_selected(
        self, message: VoiceSelectorPanel.VoiceSelected
    ) -> None:
        """Handles the voice selected event from the panel."""
        if self.tts_engine and hasattr(self.tts_engine, "set_voice"):
            if self.tts_engine.set_voice(message.voice_short_name):
                self.notify(f"TTS voice set to: {message.voice_short_name}")
                self.action_toggle_voice_panel()
            else:
                self.notify(
                    f"Failed to set voice: {message.voice_short_name}", severity="error"
                )

    def action_quit(self) -> None:
        """Quit the application."""
        self.actions.action_quit()

    def action_switch_focus(self) -> None:
        """Switch focus between panels."""
        self.actions.action_switch_focus()

    def action_toggle_smooth_tts(self) -> None:
        """Toggle smooth TTS mode."""
        self.actions.action_toggle_smooth_tts()

    def action_toggle_toc(self) -> None:
        """Toggle table of contents visibility."""
        self.actions.action_toggle_toc()

    def action_toggle_tts(self) -> None:
        """Toggle TTS functionality."""
        self.actions.action_toggle_tts()

    def action_increase_volume(self) -> None:
        self.actions.action_increase_volume()

    def action_decrease_volume(self) -> None:
        self.actions.action_decrease_volume()

    def action_increase_speed(self) -> None:
        self.actions.action_increase_speed()

    def action_decrease_speed(self) -> None:
        self.actions.action_decrease_speed()

    def action_increase_pitch(self) -> None:
        self.actions.action_increase_pitch()

    def action_decrease_pitch(self) -> None:
        self.actions.action_decrease_pitch()

    def action_content_up(self) -> None:
        self.actions.action_content_up()

    def action_content_down(self) -> None:
        self.actions.action_content_down()

    def action_content_page_up(self) -> None:
        self.actions.action_content_page_up()

    def action_content_page_down(self) -> None:
        self.actions.action_content_page_down()

    def action_content_home(self) -> None:
        self.actions.action_content_home()

    def action_content_end(self) -> None:
        self.actions.action_content_end()

    def action_tts_play_pause(self) -> None:
        self.actions.action_tts_play_pause()

    def action_tts_stop(self) -> None:
        self.actions.action_tts_stop()

    def stop_speaking(self, is_pause: bool = False):
        self.tts_integration.stop_speaking(is_pause)

    def _get_line_from_cfi(self, cfi: str) -> int:
        return self.progress_manager.get_line_from_cfi(cfi)

    def _get_cfi_from_line(self, line_num: int) -> str:
        return self.progress_manager.get_cfi_from_line(line_num)

    def _save_progress(self) -> None:
        self.progress_manager.save_progress()

    def _update_user_activity(self) -> None:
        self.progress_manager._update_user_activity()

    def _update_panel_focus(self) -> None:
        self.ui_utils.update_panel_focus()

    def _update_panel_titles(self) -> None:
        self.ui_utils.update_panel_titles()

    def _update_content_display(self) -> None:
        self.ui_utils.update_content_display()

    def _calculate_content_width(self) -> int:
        return self.ui_utils.calculate_content_width()

    async def _update_toc_tree(self, toc_data: dict) -> None:
        await self.ui_utils.update_toc_tree(toc_data)

    async def _update_tts_progress(self) -> None:
        await self.tts_integration.update_tts_progress()

    async def _setup_tts(self) -> None:
        await self.tts_integration.setup_tts()

    def _prepare_tts_playlist(self):
        self.tts_integration.prepare_tts_playlist()

    def _start_tts_thread(self):
        self.tts_integration.start_tts_thread()

    def _speak_with_engine(self, text: str) -> None:
        self.tts_integration.speak_with_engine(text)

    def _find_next_chapter(self) -> Optional[dict]:
        return self.actions.find_next_chapter()

    def _find_prev_chapter(self) -> Optional[dict]:
        return self.actions.find_prev_chapter()

    def _cleanup(self) -> None:
        self.tts_integration.cleanup()
        self.progress_manager.cleanup()
        self.epub_manager.close_epub()
