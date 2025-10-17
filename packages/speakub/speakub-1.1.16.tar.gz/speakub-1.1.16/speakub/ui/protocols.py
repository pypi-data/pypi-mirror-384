
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Protocol,
    runtime_checkable,
)

if TYPE_CHECKING:
    pass

    from speakub.tts.edge_tts_provider import EdgeTTSProvider
    from speakub.ui.widgets.content_widget import ViewportContent
    from speakub.ui.widgets.tts_widget import TTSRichWidget


@runtime_checkable
class AppInterface(Protocol):
    """An interface defining the methods and attributes the TTSIntegration expects from the main app."""

    # Properties
    @property
    def tts_engine(self) -> Optional["EdgeTTSProvider"]: ...

    @tts_engine.setter
    def tts_engine(self, value: Optional["EdgeTTSProvider"]) -> None: ...

    @property
    def tts_status(self) -> str: ...

    @tts_status.setter
    def tts_status(self, value: str) -> None: ...

    @property
    def tts_smooth_mode(self) -> bool: ...

    @property
    def tts_volume(self) -> int: ...

    @property
    def tts_rate(self) -> int: ...

    @property
    def tts_pitch(self) -> str: ...

    @property
    def viewport_content(self) -> Optional["ViewportContent"]: ...

    @property
    def tts_widget(self) -> Optional["TTSRichWidget"]: ...

    # Methods
    def query_one(self, selector: str, expected_type: Any) -> Any: ...

    def notify(
        self, message: str, title: str = "", severity: str = "information"
    ) -> None: ...

    def run_worker(
        self,
        worker: Callable,
        *,
        name: Optional[str] = None,
        group: Optional[str] = None,
        exclusive: bool = False,
        thread: bool = False,
    ) -> None: ...

    def bell(self) -> None: ...
