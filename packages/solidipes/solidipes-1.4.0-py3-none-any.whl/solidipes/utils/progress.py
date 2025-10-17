from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from datasize import DataSize
from rich.live import Live
from rich.progress import BarColumn, FileSizeColumn
from rich.progress import Progress as RichProgress
from rich.progress import TextColumn, TimeRemainingColumn
from rich.spinner import Spinner as RichSpinner

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator


_streamlit_layout: Optional["DeltaGenerator"] = None


def set_streamlit_layout(layout: "DeltaGenerator") -> None:
    global _streamlit_layout
    _streamlit_layout = layout


def get_streamlit_layout() -> "DeltaGenerator":
    global _streamlit_layout

    if _streamlit_layout is None:
        import streamlit as st

        _streamlit_layout = st

    return _streamlit_layout


class ProgressDisplay(ABC):
    def __init__(self, description: str) -> None:
        """Generic progress display interface. Can be used as a context manager."""
        self.description = description

    def __enter__(self) -> "ProgressDisplay":
        self.reset()
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def reset(self) -> None:
        """Reset the progress display to its initial state."""

    def start(self) -> None:
        """Open the progress display context."""

    def close(self) -> None:
        """Close the progress display context."""


class Spinner(ProgressDisplay):
    """Generic spinner interface. Can be used as a context manager."""


class TextSpinner(Spinner):
    def __init__(self, description: str) -> None:
        """Spinner using the rich library, for CLI and Jupyter notebooks."""
        super().__init__(description)
        self.spinner = RichSpinner("dots", text=description)
        self.live = None

    def start(self) -> None:
        self.live = Live(self.spinner)
        self.live.__enter__()

    def __exit__(self, type, value, traceback):
        if self.live is not None:
            self.live.__exit__(type, value, traceback)
            self.live = None


class StreamlitSpinner(Spinner):
    def __init__(self, description: str, layout: Optional["DeltaGenerator"] = None) -> None:
        """Streamlit spinner."""
        super().__init__(description)

        if layout is None:
            layout = get_streamlit_layout()

        self.layout = layout

    def start(self) -> None:
        import streamlit as st

        with self.layout:
            self.spinner = st.spinner(text=self.description)
            self.spinner.__enter__()

    def __exit__(self, type, value, traceback):
        self.spinner.__exit__(type, value, traceback)


class ProgressBar(ProgressDisplay):
    def __init__(self, description: str, total: float = 100, show_datasize: bool = False) -> None:
        """Generic progress bar interface. Can be used as a context manager."""
        super().__init__(description)
        self.total = total
        self.show_datasize = show_datasize

    @abstractmethod
    def update(self, advance: float = 0, text: Optional[str] = None) -> None:
        """Update the progress bar."""


class TextProgressBar(ProgressBar):
    def __init__(self, *args, **kwargs) -> None:
        """Progress bar using the rich library, for CLI and Jupyter notebooks."""
        super().__init__(*args, **kwargs)

        self.description_style = "[bold blue]"
        self.progress_style = "[blue]"
        self.text_style = "[white]"

        columns = [
            BarColumn(),
            TimeRemainingColumn(),
            TextColumn("{task.description}"),
        ]

        if self.show_datasize:
            columns.insert(1, FileSizeColumn())

        self.bar = RichProgress(*columns)
        self.task = self.bar.add_task(self.description, total=self.total)

    def reset(self) -> None:
        self.bar.reset(self.task)

    def start(self) -> None:
        self.bar.start()

    def _set_display_info(self, text: Optional[str] = None) -> None:
        """Set the display info (description, progress, text)."""
        full_text = f"{self.description_style}{self.description}"

        if not self.show_datasize:
            full_text += f"{self.progress_style}({self.bar.tasks[self.task].completed}/{self.total})"

        if text is not None:
            full_text += f" {self.text_style}{text}"

        self.bar.update(self.task, description=full_text)

    def update(self, advance: float = 0, text: Optional[str] = None) -> None:
        self.bar.update(self.task, advance=advance)
        self._set_display_info(text)

    def close(self) -> None:
        self._set_display_info()
        self.bar.stop()


class StreamlitProgressBar(ProgressBar):
    def __init__(self, *args, layout: Optional["DeltaGenerator"] = None, **kwargs) -> None:
        """Progress bar for Streamlit."""
        super().__init__(*args, **kwargs)

        if layout is None:
            layout = get_streamlit_layout()

        self.bar = layout.progress(0, text=self.description)
        self.current = 0

    def reset(self) -> None:
        self.current = 0

    def update(self, advance: float = 0, text: Optional[str] = None) -> None:
        self.current += advance

        full_text = f"**{self.description}**"

        if self.show_datasize:
            full_text += f" ({DataSize(self.current):.1a}/{DataSize(self.total):.1a})"
        else:
            full_text += f" ({self.current}/{self.total})"

        if text is not None:
            full_text += f" {text}"
        self.bar.progress(100 * self.current // self.total, text=full_text)

    def close(self) -> None:
        self.bar.empty()


def get_spinner(
    description: str,
    backend: Optional[str] = None,
    streamlit_layout: Optional["DeltaGenerator"] = None,
) -> Spinner:
    from ..viewers import backends

    if backend is None:
        backend = backends.current_backend

    if backend == "streamlit":
        return StreamlitSpinner(description, layout=streamlit_layout)

    if backend == "python" or backend == "jupyter notebook":
        return TextSpinner(description)

    raise ValueError(f"Backend {backend} not supported")


def get_progress_bar(
    description: str,
    total: float = 100,
    show_datasize: bool = False,
    backend: Optional[str] = None,
    streamlit_layout: Optional["DeltaGenerator"] = None,
) -> ProgressBar:
    from ..viewers import backends

    if backend is None:
        backend = backends.current_backend

    if backend == "streamlit":
        return StreamlitProgressBar(description, total=total, show_datasize=show_datasize, layout=streamlit_layout)

    if backend == "python" or backend == "jupyter notebook":
        return TextProgressBar(description, total=total, show_datasize=show_datasize)

    raise ValueError(f"Backend {backend} not supported")
