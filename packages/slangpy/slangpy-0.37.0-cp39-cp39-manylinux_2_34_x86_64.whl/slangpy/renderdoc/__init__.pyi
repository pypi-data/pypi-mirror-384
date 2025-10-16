from typing import TypedDict, Union
from numpy.typing import NDArray
from typing import Optional

import slangpy


def is_available() -> bool:
    """
    Check if RenderDoc is available.

    This is typically the case when the application is running under the
    RenderDoc.

    Returns:
        True if RenderDoc is available.
    """

def start_frame_capture(device: slangpy.Device, window: Optional[slangpy.Window] = None) -> bool:
    """
    Start capturing a frame in RenderDoc.

    This function will start capturing a frame (or some partial
    compute/graphics workload) in RenderDoc.

    To end the frame capture, call ``end_frame_capture``().

    Parameter ``device``:
        The device to capture the frame for.

    Parameter ``window``:
        The window to capture the frame for (optional).

    Returns:
        True if the frame capture was started successfully.
    """

def end_frame_capture() -> bool:
    """
    End capturing a frame in RenderDoc.

    This function will end capturing a frame (or some partial
    compute/graphics workload) in RenderDoc.

    Returns:
        True if the frame capture was ended successfully.
    """

def is_frame_capturing() -> bool:
    """
    Check if a frame is currently being captured in RenderDoc.

    Returns:
        True if a frame is currently being captured.
    """
