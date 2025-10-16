from typing import TypedDict, Union
from numpy.typing import NDArray
from typing import overload

import slangpy


@overload
def show(bitmap: slangpy.Bitmap, name: str = '', host: str = '127.0.0.1', port: int = 14158, max_retries: int = 3) -> bool:
    """
    Show a bitmap in the tev viewer (https://github.com/Tom94/tev).

    This will block until the image is sent over.

    Parameter ``bitmap``:
        Bitmap to show.

    Parameter ``name``:
        Name of the image in tev. If not specified, a unique name will be
        generated.

    Parameter ``host``:
        Host to connect to.

    Parameter ``port``:
        Port to connect to.

    Parameter ``max_retries``:
        Maximum number of retries.

    Returns:
        True if successful.
    """

@overload
def show(texture: slangpy.Texture, name: str = '', host: str = '127.0.0.1', port: int = 14158, max_retries: int = 3) -> bool:
    """
    Show texture in the tev viewer (https://github.com/Tom94/tev).

    This will block until the image is sent over.

    Parameter ``texture``:
        Texture to show.

    Parameter ``name``:
        Name of the image in tev. If not specified, a unique name will be
        generated.

    Parameter ``host``:
        Host to connect to.

    Parameter ``port``:
        Port to connect to.

    Parameter ``max_retries``:
        Maximum number of retries.

    Returns:
        True if successful.
    """

@overload
def show_async(bitmap: slangpy.Bitmap, name: str = '', host: str = '127.0.0.1', port: int = 14158, max_retries: int = 3) -> None:
    """
    Show a bitmap in the tev viewer (https://github.com/Tom94/tev).

    This will return immediately and send the image asynchronously in the
    background.

    Parameter ``bitmap``:
        Bitmap to show.

    Parameter ``name``:
        Name of the image in tev. If not specified, a unique name will be
        generated.

    Parameter ``host``:
        Host to connect to.

    Parameter ``port``:
        Port to connect to.

    Parameter ``max_retries``:
        Maximum number of retries.
    """

@overload
def show_async(texture: slangpy.Texture, name: str = '', host: str = '127.0.0.1', port: int = 14158, max_retries: int = 3) -> None:
    """
    Show a texture in the tev viewer (https://github.com/Tom94/tev).

    This will return immediately and send the image asynchronously in the
    background.

    Parameter ``bitmap``:
        Texture to show.

    Parameter ``name``:
        Name of the image in tev. If not specified, a unique name will be
        generated.

    Parameter ``host``:
        Host to connect to.

    Parameter ``port``:
        Port to connect to.

    Parameter ``max_retries``:
        Maximum number of retries.
    """
