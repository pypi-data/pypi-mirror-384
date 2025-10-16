from collections.abc import Sequence
import pathlib
from typing import TypedDict, Union
from numpy.typing import NDArray
from typing import Optional, overload


class FileDialogFilter:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, name: str, pattern: str) -> None: ...

    @overload
    def __init__(self, arg: tuple[str, str], /) -> None: ...

    @property
    def name(self) -> str:
        """Readable name (e.g. "JPEG")."""

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def pattern(self) -> str:
        """File extension pattern (e.g. "*.jpg" or "*.jpg,*.jpeg")."""

    @pattern.setter
    def pattern(self, arg: str, /) -> None: ...

def open_file_dialog(filters: Sequence[FileDialogFilter] = []) -> Optional[pathlib.Path]:
    """
    Show a file open dialog.

    Parameter ``filters``:
        List of file filters.

    Returns:
        The selected file path or nothing if the dialog was cancelled.
    """

def save_file_dialog(filters: Sequence[FileDialogFilter] = []) -> Optional[pathlib.Path]:
    """
    Show a file save dialog.

    Parameter ``filters``:
        List of file filters.

    Returns:
        The selected file path or nothing if the dialog was cancelled.
    """

def choose_folder_dialog() -> Optional[pathlib.Path]:
    """
    Show a folder selection dialog.

    Returns:
        The selected folder path or nothing if the dialog was cancelled.
    """

def display_scale_factor() -> float:
    """The pixel scale factor of the primary display."""

def executable_path() -> pathlib.Path:
    """The full path to the current executable."""

def executable_directory() -> pathlib.Path:
    """The current executable directory."""

def executable_name() -> str:
    """The current executable name."""

def app_data_directory() -> pathlib.Path:
    """The application data directory."""

def home_directory() -> pathlib.Path:
    """The home directory."""

def project_directory() -> pathlib.Path:
    """
    The project source directory. Note that this is only valid during
    development.
    """

def runtime_directory() -> pathlib.Path:
    """
    The runtime directory. This is the path where the sgl runtime library
    (sgl.dll, libsgl.so or libsgl.dynlib) resides.
    """

page_size: int = 16384

class MemoryStats:
    @property
    def rss(self) -> int:
        """Current resident/working set size in bytes."""

    @property
    def peak_rss(self) -> int:
        """Peak resident/working set size in bytes."""

def memory_stats() -> MemoryStats:
    """Get the current memory stats."""
