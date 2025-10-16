from collections.abc import Callable, Mapping, Sequence
import enum
import os
import pathlib
from typing import TypedDict, Union
from numpy.typing import NDArray
from typing import Annotated, Optional, Union, overload

from numpy.typing import ArrayLike
from typing_extensions import TypeAlias

from . import (
    bindings as bindings,
    builtin as builtin,
    core as core,
    experimental as experimental,
    math as math,
    platform as platform,
    reflection as reflection,
    renderdoc as renderdoc,
    slangpy as slangpy,
    slangpy_ext as slangpy_ext,
    tev as tev,
    thread as thread,
    torchintegration as torchintegration,
    types as types,
    ui as ui
)
from .core.calldata import (
    set_dump_generated_shaders as set_dump_generated_shaders,
    set_dump_slang_intermediates as set_dump_slang_intermediates,
    set_print_generated_shaders as set_print_generated_shaders
)
from .core.function import Function as Function
from .core.instance import (
    InstanceBuffer as InstanceBuffer,
    InstanceList as InstanceList
)
from .core.module import Module as Module
from .core.packedarg import pack as pack
from .core.struct import Struct as Struct
from .core.utils import (
    create_device as create_device,
    create_torch_device as create_torch_device
)
from .experimental.gridarg import grid as grid
from .math import (
    bool1 as bool1,
    bool2 as bool2,
    bool3 as bool3,
    bool4 as bool4,
    float1 as float1,
    float16_t as float16_t,
    float16_t1 as float16_t1,
    float16_t2 as float16_t2,
    float16_t3 as float16_t3,
    float16_t4 as float16_t4,
    float2 as float2,
    float2x2 as float2x2,
    float2x3 as float2x3,
    float2x4 as float2x4,
    float3 as float3,
    float3x2 as float3x2,
    float3x3 as float3x3,
    float3x4 as float3x4,
    float4 as float4,
    float4x2 as float4x2,
    float4x3 as float4x3,
    float4x4 as float4x4,
    int1 as int1,
    int2 as int2,
    int3 as int3,
    int4 as int4,
    quatf as quatf,
    uint1 as uint1,
    uint2 as uint2,
    uint3 as uint3,
    uint4 as uint4
)
from .types.buffer import NDBuffer as NDBuffer
from .types.callidarg import (
    CallIdArg as CallIdArg,
    call_id as call_id
)
from .types.diffpair import (
    DiffPair as DiffPair,
    diffPair as diffPair,
    floatDiffPair as floatDiffPair
)
from .types.randfloatarg import (
    RandFloatArg as RandFloatArg,
    rand_float as rand_float
)
from .types.tensor import Tensor as Tensor
from .types.threadidarg import (
    ThreadIdArg as ThreadIdArg,
    thread_id as thread_id
)
from .types.valueref import (
    ValueRef as ValueRef,
    floatRef as floatRef,
    intRef as intRef
)
from .types.wanghasharg import (
    WangHashArg as WangHashArg,
    wang_hash as wang_hash
)


package_dir: str = 'D:\\a\\slangpy\\slangpy\\slangpy'

__warningregistry__: dict = {'version' : 0}

build_dir: str = 'D:/a/slangpy/slangpy/build/pip/RelWithDebInfo'

SGL_VERSION_MAJOR: int = 0

SGL_VERSION_MINOR: int = 37

SGL_VERSION_PATCH: int = 0

SGL_VERSION: str = '0.37.0'

SGL_GIT_VERSION: str = 'commit: f0083d8 / branch: unknown'

SGL_BUILD_TYPE: str = 'RelWithDebInfo'

SLANG_BUILD_TAG: str = '2025.19'
bool1param = Union[math.bool1, Sequence[bool]]
bool2param = Union[math.bool2, Sequence[bool]]
bool3param = Union[math.bool3, Sequence[bool]]
bool4param = Union[math.bool4, Sequence[bool]]
float1param = Union[math.float1, Sequence[float]]
float16_tparam = Union[math.float16_t, float]
float16_t1param = Union[math.float16_t1, Sequence[float16_t]]
float16_t2param = Union[math.float16_t2, Sequence[float16_t]]
float16_t3param = Union[math.float16_t3, Sequence[float16_t]]
float16_t4param = Union[math.float16_t4, Sequence[float16_t]]
float2param = Union[math.float2, Sequence[float]]
float2x2param = Union[math.float2x2, Sequence[float]]
float2x3param = Union[math.float2x3, Sequence[float]]
float2x4param = Union[math.float2x4, Sequence[float]]
float3param = Union[math.float3, Sequence[float]]
float3x2param = Union[math.float3x2, Sequence[float]]
float3x3param = Union[math.float3x3, Sequence[float]]
float3x4param = Union[math.float3x4, Sequence[float]]
float4param = Union[math.float4, Sequence[float]]
float4x2param = Union[math.float4x2, Sequence[float]]
float4x3param = Union[math.float4x3, Sequence[float]]
float4x4param = Union[math.float4x4, Sequence[float]]
int1param = Union[math.int1, Sequence[int]]
int2param = Union[math.int2, Sequence[int]]
int3param = Union[math.int3, Sequence[int]]
int4param = Union[math.int4, Sequence[int]]
quatfparam = Union[math.quatf, Sequence[float]]
uint1param = Union[math.uint1, Sequence[int]]
uint2param = Union[math.uint2, Sequence[int]]
uint3param = Union[math.uint3, Sequence[int]]
uint4param = Union[math.uint4, Sequence[int]]

class Object:
    """Base class for all reference counted objects."""

    def __repr__(self) -> str: ...

class WindowHandle:
    """Native window handle."""

    def __init__(self, hwnd: int) -> None: ...

class CursorMode(enum.Enum):
    """Mouse cursor modes."""

    _member_names_: list = ['normal', 'hidden', 'disabled']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    normal = 0

    hidden = 1

    disabled = 2

class MouseButton(enum.Enum):
    """Mouse buttons."""

    _member_names_: list = ['left', 'middle', 'right', 'unknown']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    left = 0

    middle = 1

    right = 2

    unknown = 3

class KeyModifierFlags(enum.Enum):
    """Keyboard modifier flags."""

    _member_names_: list = ['none', 'shift', 'ctrl', 'alt']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    shift = 1

    ctrl = 2

    alt = 4

class KeyModifier(enum.Enum):
    """Keyboard modifiers."""

    _member_names_: list = ['shift', 'ctrl', 'alt']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    shift = 1

    ctrl = 2

    alt = 4

class KeyCode(enum.Enum):
    """Keyboard key codes."""

    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    space = 32

    apostrophe = 39

    comma = 44

    minus = 45

    period = 46

    slash = 47

    key0 = 48

    key1 = 49

    key2 = 50

    key3 = 51

    key4 = 52

    key5 = 53

    key6 = 54

    key7 = 55

    key8 = 56

    key9 = 57

    semicolon = 59

    equal = 61

    a = 65

    b = 66

    c = 67

    d = 68

    e = 69

    f = 70

    g = 71

    h = 72

    i = 73

    j = 74

    k = 75

    l = 76

    m = 77

    n = 78

    o = 79

    p = 80

    q = 81

    r = 82

    s = 83

    t = 84

    u = 85

    v = 86

    w = 87

    x = 88

    y = 89

    z = 90

    left_bracket = 91

    backslash = 92

    right_bracket = 93

    grave_accent = 96

    escape = 256

    tab = 257

    enter = 258

    backspace = 259

    insert = 260

    delete = 261

    right = 262

    left = 263

    down = 264

    up = 265

    page_up = 266

    page_down = 267

    home = 268

    end = 269

    caps_lock = 270

    scroll_lock = 271

    num_lock = 272

    print_screen = 273

    pause = 274

    f1 = 275

    f2 = 276

    f3 = 277

    f4 = 278

    f5 = 279

    f6 = 280

    f7 = 281

    f8 = 282

    f9 = 283

    f10 = 284

    f11 = 285

    f12 = 286

    keypad0 = 287

    keypad1 = 288

    keypad2 = 289

    keypad3 = 290

    keypad4 = 291

    keypad5 = 292

    keypad6 = 293

    keypad7 = 294

    keypad8 = 295

    keypad9 = 296

    keypad_del = 297

    keypad_divide = 298

    keypad_multiply = 299

    keypad_subtract = 300

    keypad_add = 301

    keypad_enter = 302

    keypad_equal = 303

    left_shift = 304

    left_control = 305

    left_alt = 306

    left_super = 307

    right_shift = 308

    right_control = 309

    right_alt = 310

    right_super = 311

    menu = 312

    unknown = 313

class KeyboardEventType(enum.Enum):
    """Keyboard event types."""

    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    key_press = 0

    key_release = 1

    key_repeat = 2

    input = 3

class KeyboardEvent:
    @property
    def type(self) -> KeyboardEventType:
        """The event type."""

    @property
    def key(self) -> KeyCode:
        """The key that was pressed/released/repeated."""

    @property
    def mods(self) -> KeyModifierFlags:
        """Keyboard modifier flags."""

    @property
    def codepoint(self) -> int:
        """UTF-32 codepoint for input events."""

    def is_key_press(self) -> bool:
        """Returns true if this event is a key press event."""

    def is_key_release(self) -> bool:
        """Returns true if this event is a key release event."""

    def is_key_repeat(self) -> bool:
        """Returns true if this event is a key repeat event."""

    def is_input(self) -> bool:
        """Returns true if this event is an input event."""

    def has_modifier(self, arg: KeyModifier, /) -> bool:
        """Returns true if the specified modifier is set."""

    def __repr__(self) -> str: ...

class MouseEventType(enum.Enum):
    """Mouse event types."""

    _member_names_: list = ['button_down', 'button_up', 'move', 'scroll']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    button_down = 0

    button_up = 1

    move = 2

    scroll = 3

class MouseEvent:
    @property
    def type(self) -> MouseEventType:
        """The event type."""

    @property
    def pos(self) -> math.float2:
        """The mouse position."""

    @property
    def scroll(self) -> math.float2:
        """The scroll offset."""

    @property
    def button(self) -> MouseButton:
        """The mouse button that was pressed/released."""

    @property
    def mods(self) -> KeyModifierFlags:
        """Keyboard modifier flags."""

    def is_button_down(self) -> bool:
        """Returns true if this event is a mouse button down event."""

    def is_button_up(self) -> bool:
        """Returns true if this event is a mouse button up event."""

    def is_move(self) -> bool:
        """Returns true if this event is a mouse move event."""

    def is_scroll(self) -> bool:
        """Returns true if this event is a mouse scroll event."""

    def has_modifier(self, arg: KeyModifier, /) -> bool:
        """Returns true if the specified modifier is set."""

    def __repr__(self) -> str: ...

class GamepadEventType(enum.Enum):
    """Gamepad event types."""

    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    button_down = 0

    button_up = 1

    connect = 2

    disconnect = 3

class GamepadButton(enum.Enum):
    """Gamepad buttons."""

    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    a = 0

    b = 1

    x = 2

    y = 3

    left_bumper = 4

    right_bumper = 5

    back = 6

    start = 7

    guide = 8

    left_thumb = 9

    right_thumb = 10

    up = 11

    right = 12

    down = 13

    left = 14

class GamepadEvent:
    @property
    def type(self) -> GamepadEventType:
        """The event type."""

    @property
    def button(self) -> GamepadButton:
        """The gamepad button that was pressed/released."""

    def is_button_down(self) -> bool:
        """Returns true if this event is a gamepad button down event."""

    def is_button_up(self) -> bool:
        """Returns true if this event is a gamepad button up event."""

    def is_connect(self) -> bool:
        """Returns true if this event is a gamepad connect event."""

    def is_disconnect(self) -> bool:
        """Returns true if this event is a gamepad disconnect event."""

    def __repr__(self) -> str: ...

class GamepadState:
    @property
    def left_x(self) -> float:
        """X-axis of the left analog stick."""

    @property
    def left_y(self) -> float:
        """Y-axis of the left analog stick."""

    @property
    def right_x(self) -> float:
        """X-axis of the right analog stick."""

    @property
    def right_y(self) -> float:
        """Y-axis of the right analog stick."""

    @property
    def left_trigger(self) -> float:
        """Value of the left analog trigger."""

    @property
    def right_trigger(self) -> float:
        """Value of the right analog trigger."""

    @property
    def buttons(self) -> int:
        """Bitfield of gamepad buttons (see GamepadButton)."""

    def is_button_down(self, arg: GamepadButton, /) -> bool:
        """Returns true if the specified button is down."""

    def __repr__(self) -> str: ...

class LogLevel(enum.IntEnum):
    """Log level."""

    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    debug = 1

    info = 2

    warn = 3

    error = 4

    fatal = 5

class LogFrequency(enum.Enum):
    """Log frequency."""

    _member_names_: list = ['always', 'once']

    _member_map_: dict = ...

    _value2member_map_: dict = {0 : LogFrequency.always, 1 : LogFrequency.once}

    always = 0
    """Log the message every time."""

    once = 1
    """Log the message only once."""

class LoggerOutput(Object):
    def __init__(self) -> None: ...

    def write(self, level: LogLevel, name: str, msg: str) -> None:
        """
        Write a log message.

        Parameter ``level``:
            The log level.

        Parameter ``module``:
            The module name.

        Parameter ``msg``:
            The message.
        """

class ConsoleLoggerOutput(LoggerOutput):
    def __init__(self, colored: bool = True) -> None: ...

    IGNORE_PRINT_EXCEPTION: bool = ...
    """(arg: object, /) -> bool"""

class FileLoggerOutput(LoggerOutput):
    def __init__(self, path: str | os.PathLike) -> None: ...

class DebugConsoleLoggerOutput(LoggerOutput):
    def __init__(self) -> None: ...

class Logger(Object):
    def __init__(self, level: LogLevel = LogLevel.info, name: str = '', use_default_outputs: bool = True) -> None:
        """
        Constructor.

        Parameter ``level``:
            The log level to use (messages with level >= this will be logged).

        Parameter ``name``:
            The name of the logger.

        Parameter ``use_default_outputs``:
            Whether to use the default outputs (console + debug console on
            windows).
        """

    @property
    def level(self) -> LogLevel:
        """The log level."""

    @level.setter
    def level(self, arg: LogLevel, /) -> None: ...

    @property
    def name(self) -> str:
        """The name of the logger."""

    @name.setter
    def name(self, arg: str, /) -> None: ...

    def add_console_output(self, colored: bool = True) -> LoggerOutput:
        """
        Add a console logger output.

        Parameter ``colored``:
            Whether to use colored output.

        Returns:
            The created logger output.
        """

    def add_file_output(self, path: str | os.PathLike) -> LoggerOutput:
        """
        Add a file logger output.

        Parameter ``path``:
            The path to the log file.

        Returns:
            The created logger output.
        """

    def add_debug_console_output(self) -> LoggerOutput:
        """
        Add a debug console logger output (Windows only).

        Returns:
            The created logger output.
        """

    def add_output(self, output: LoggerOutput) -> None:
        """
        Add a logger output.

        Parameter ``output``:
            The logger output to add.
        """

    def use_same_outputs(self, other: Logger) -> None:
        """
        Use the same outputs as the given logger.

        Parameter ``other``:
            Logger to copy outputs from.
        """

    def remove_output(self, output: LoggerOutput) -> None:
        """
        Remove a logger output.

        Parameter ``output``:
            The logger output to remove.
        """

    def remove_all_outputs(self) -> None:
        """Remove all logger outputs."""

    def log(self, level: LogLevel, msg: str, frequency: LogFrequency = LogFrequency.always) -> None:
        """
        Log a message.

        Parameter ``level``:
            The log level.

        Parameter ``msg``:
            The message.

        Parameter ``frequency``:
            The log frequency.
        """

    def debug(self, msg: str) -> None: ...

    def info(self, msg: str) -> None: ...

    def warn(self, msg: str) -> None: ...

    def error(self, msg: str) -> None: ...

    def fatal(self, msg: str) -> None: ...

    def debug_once(self, msg: str) -> None: ...

    def info_once(self, msg: str) -> None: ...

    def warn_once(self, msg: str) -> None: ...

    def error_once(self, msg: str) -> None: ...

    def fatal_once(self, msg: str) -> None: ...

    @staticmethod
    def get() -> Logger:
        """Returns the global logger instance."""

def log(level: LogLevel, msg: str, frequency: LogFrequency = LogFrequency.always) -> None:
    """
    Log a message.

    Parameter ``level``:
        The log level.

    Parameter ``msg``:
        The message.

    Parameter ``frequency``:
        The log frequency.
    """

def log_debug(msg: str) -> None: ...

def log_debug_once(msg: str) -> None: ...

def log_info(msg: str) -> None: ...

def log_info_once(msg: str) -> None: ...

def log_warn(msg: str) -> None: ...

def log_warn_once(msg: str) -> None: ...

def log_error(msg: str) -> None: ...

def log_error_once(msg: str) -> None: ...

def log_fatal(msg: str) -> None: ...

def log_fatal_once(msg: str) -> None: ...

class Timer:
    def __init__(self) -> None: ...

    def reset(self) -> None:
        """Reset the timer."""

    def elapsed_s(self) -> float:
        """Elapsed seconds since last reset."""

    def elapsed_ms(self) -> float:
        """Elapsed milliseconds since last reset."""

    def elapsed_us(self) -> float:
        """Elapsed microseconds since last reset."""

    def elapsed_ns(self) -> float:
        """Elapsed nanoseconds since last reset."""

    @staticmethod
    def delta_s(start: int, end: int) -> float:
        """Compute elapsed seconds between two time points."""

    @staticmethod
    def delta_ms(start: int, end: int) -> float:
        """Compute elapsed milliseconds between two time points."""

    @staticmethod
    def delta_us(start: int, end: int) -> float:
        """Compute elapsed microseconds between two time points."""

    @staticmethod
    def delta_ns(start: int, end: int) -> float:
        """Compute elapsed nanoseconds between two time points."""

    @staticmethod
    def now() -> int:
        """Current time point in nanoseconds since epoch."""

class WindowMode(enum.Enum):
    """Window modes."""

    _member_names_: list = ['normal', 'minimized', 'fullscreen']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    normal = 0

    minimized = 1

    fullscreen = 2

class Window(Object):
    def __init__(self, width: int = 1024, height: int = 1024, title: str = 'slangpy', mode: WindowMode = WindowMode.normal, resizable: bool = True) -> None:
        """
        Constructor.

        Parameter ``width``:
            Width of the window in pixels.

        Parameter ``height``:
            Height of the window in pixels.

        Parameter ``title``:
            Title of the window.

        Parameter ``mode``:
            Window mode.

        Parameter ``resizable``:
            Whether the window is resizable.
        """

    @property
    def width(self) -> int:
        """The width of the window in pixels."""

    @property
    def height(self) -> int:
        """The height of the window in pixels."""

    def resize(self, width: int, height: int) -> None:
        """
        Resize the window.

        Parameter ``width``:
            The new width of the window in pixels.

        Parameter ``height``:
            The new height of the window in pixels.
        """

    @property
    def title(self) -> str:
        """The title of the window."""

    @title.setter
    def title(self, arg: str, /) -> None: ...

    def close(self) -> None:
        """Close the window."""

    def should_close(self) -> bool:
        """True if the window should be closed."""

    def process_events(self) -> None:
        """Process any pending events."""

    def set_clipboard(self, text: str) -> None:
        """Set the clipboard content."""

    def get_clipboard(self) -> Optional[str]:
        """Get the clipboard content."""

    @property
    def cursor_mode(self) -> CursorMode:
        """The mouse cursor mode."""

    @cursor_mode.setter
    def cursor_mode(self, arg: CursorMode, /) -> None: ...

    @property
    def on_resize(self) -> Callable[[int, int], None]:
        """Event handler to be called when the window is resized."""

    @on_resize.setter
    def on_resize(self, arg: Optional[Callable[[int, int], None]]) -> None: ...

    @property
    def on_keyboard_event(self) -> Callable[[KeyboardEvent], None]:
        """Event handler to be called when a keyboard event occurs."""

    @on_keyboard_event.setter
    def on_keyboard_event(self, arg: Optional[Callable[[KeyboardEvent], None]]) -> None: ...

    @property
    def on_mouse_event(self) -> Callable[[MouseEvent], None]:
        """Event handler to be called when a mouse event occurs."""

    @on_mouse_event.setter
    def on_mouse_event(self, arg: Optional[Callable[[MouseEvent], None]]) -> None: ...

    @property
    def on_gamepad_event(self) -> Callable[[GamepadEvent], None]:
        """Event handler to be called when a gamepad event occurs."""

    @on_gamepad_event.setter
    def on_gamepad_event(self, arg: Optional[Callable[[GamepadEvent], None]]) -> None: ...

    @property
    def on_gamepad_state(self) -> Callable[[GamepadState], None]:
        """Event handler to be called when the gamepad state changes."""

    @on_gamepad_state.setter
    def on_gamepad_state(self, arg: Optional[Callable[[GamepadState], None]]) -> None: ...

    @property
    def on_drop_files(self) -> Callable[[list[str]], None]:
        """Event handler to be called when files are dropped onto the window."""

    @on_drop_files.setter
    def on_drop_files(self, arg: Optional[Callable[[Sequence[str]], None]]) -> None: ...

class DataStruct(Object):
    """
    Structured data definition.

    This class is used to describe a structured data type layout. It is
    used by the DataStructConverter class to convert between different
    layouts.
    """

    def __init__(self, pack: bool = False, byte_order: DataStruct.ByteOrder = DataStruct.ByteOrder.host) -> None:
        """
        Constructor.

        Parameter ``pack``:
            If true, the struct will be packed.

        Parameter ``byte_order``:
            Byte order of the struct.
        """

    class Type(enum.Enum):
        """Struct field type."""

        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        int8 = 0

        int16 = 1

        int32 = 2

        int64 = 3

        uint8 = 4

        uint16 = 5

        uint32 = 6

        uint64 = 7

        float16 = 8

        float32 = 9

        float64 = 10

    class Flags(enum.IntFlag):
        """Struct field flags."""

        _member_names_: list = ['none', 'normalized', 'srgb_gamma', 'default']

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        none = 0

        normalized = 1

        srgb_gamma = 2

        default = 4

    class ByteOrder(enum.Enum):
        """Byte order."""

        _member_names_: list = ['little_endian', 'big_endian', 'host']

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        little_endian = 0

        big_endian = 1

        host = 2

    class Field:
        """Struct field."""

        @property
        def name(self) -> str:
            """Name of the field."""

        @name.setter
        def name(self, arg: str, /) -> None: ...

        @property
        def type(self) -> DataStruct.Type:
            """Type of the field."""

        @type.setter
        def type(self, arg: DataStruct.Type, /) -> None: ...

        @property
        def flags(self) -> DataStruct.Flags:
            """Field flags."""

        @flags.setter
        def flags(self, arg: DataStruct.Flags, /) -> None: ...

        @property
        def size(self) -> int:
            """Size of the field in bytes."""

        @size.setter
        def size(self, arg: int, /) -> None: ...

        @property
        def offset(self) -> int:
            """Offset of the field in bytes."""

        @offset.setter
        def offset(self, arg: int, /) -> None: ...

        @property
        def default_value(self) -> float:
            """Default value."""

        @default_value.setter
        def default_value(self, arg: float, /) -> None: ...

        def is_integer(self) -> bool:
            """Check if the field is an integer type."""

        def is_unsigned(self) -> bool:
            """Check if the field is an unsigned type."""

        def is_signed(self) -> bool:
            """Check if the field is a signed type."""

        def is_float(self) -> bool:
            """Check if the field is a floating point type."""

        def __eq__(self, arg: DataStruct.Field, /) -> bool: ...

        def __ne__(self, arg: DataStruct.Field, /) -> bool: ...

        def __repr__(self) -> str: ...

    @overload
    def append(self, field: DataStruct.Field) -> DataStruct:
        """Append a field to the struct."""

    @overload
    def append(self, name: str, type: DataStruct.Type, flags: DataStruct.Flags = Flags.none, default_value: float = 0.0, blend: Sequence[tuple[float, str]] = []) -> DataStruct:
        """
        Append a field to the struct.

        Parameter ``name``:
            Name of the field.

        Parameter ``type``:
            Type of the field.

        Parameter ``flags``:
            Field flags.

        Parameter ``default_value``:
            Default value.

        Parameter ``blend``:
            List of blend weights/names.

        Returns:
            Reference to the struct.
        """

    def has_field(self, name: str) -> bool:
        """Check if a field with the specified name exists."""

    def field(self, name: str) -> DataStruct.Field:
        """Access field by name. Throws if field is not found."""

    def __getitem__(self, arg: int, /) -> DataStruct.Field: ...

    def __len__(self) -> int: ...

    def __eq__(self, arg: DataStruct, /) -> bool: ...

    def __ne__(self, arg: DataStruct, /) -> bool: ...

    @property
    def size(self) -> int:
        """The size of the struct in bytes (with padding)."""

    @property
    def alignment(self) -> int:
        """The alignment of the struct in bytes."""

    @property
    def byte_order(self) -> DataStruct.ByteOrder:
        """The byte order of the struct."""

    @staticmethod
    def type_size(arg: DataStruct.Type, /) -> int:
        """Get the size of a type in bytes."""

    @staticmethod
    def type_range(arg: DataStruct.Type, /) -> tuple[float, float]:
        """Get the numeric range of a type."""

    @staticmethod
    def is_integer(arg: DataStruct.Type, /) -> bool:
        """Check if ``type`` is an integer type."""

    @staticmethod
    def is_unsigned(arg: DataStruct.Type, /) -> bool:
        """Check if ``type`` is an unsigned type."""

    @staticmethod
    def is_signed(arg: DataStruct.Type, /) -> bool:
        """Check if ``type`` is a signed type."""

    @staticmethod
    def is_float(arg: DataStruct.Type, /) -> bool:
        """Check if ``type`` is a floating point type."""

class DataStructConverter(Object):
    """
    Data struct converter.

    This helper class can be used to convert between structs with
    different layouts.
    """

    def __init__(self, src: DataStruct, dst: DataStruct) -> None:
        """
        Constructor.

        Parameter ``src``:
            Source struct definition.

        Parameter ``dst``:
            Destination struct definition.
        """

    @property
    def src(self) -> DataStruct:
        """The source struct definition."""

    @property
    def dst(self) -> DataStruct:
        """The destination struct definition."""

    def convert(self, input: bytes) -> bytes: ...

class Bitmap(Object):
    @overload
    def __init__(self, pixel_format: Bitmap.PixelFormat, component_type: DataStruct.Type, width: int, height: int, channel_count: int = 0, channel_names: Sequence[str] = [], srgb_gamma: Optional[bool] = None) -> None: ...

    @overload
    def __init__(self, data: Annotated[ArrayLike, dict(device='cpu')], pixel_format: Optional[Bitmap.PixelFormat] = None, channel_names: Optional[Sequence[str]] = None, srgb_gamma: Optional[bool] = None) -> None: ...

    @overload
    def __init__(self, path: str | os.PathLike) -> None: ...

    class PixelFormat(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        y = 0

        ya = 1

        r = 2

        rg = 3

        rgb = 4

        rgba = 5

        multi_channel = 6

    ComponentType: TypeAlias = DataStruct.Type

    class FileFormat(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        unknown = 0

        auto = 1

        png = 2

        jpg = 3

        bmp = 4

        tga = 5

        hdr = 6

        exr = 7

    @staticmethod
    def load_from_file(path: str | os.PathLike) -> Bitmap:
        """N/A"""

    @staticmethod
    def load_from_numpy(data: Annotated[ArrayLike, dict(device='cpu')]) -> Bitmap:
        """N/A"""

    @property
    def pixel_format(self) -> Bitmap.PixelFormat:
        """The pixel format."""

    @property
    def component_type(self) -> DataStruct.Type:
        """The component type."""

    @property
    def pixel_struct(self) -> DataStruct:
        """DataStruct describing the pixel layout."""

    @property
    def width(self) -> int:
        """The width of the bitmap in pixels."""

    @property
    def height(self) -> int:
        """The height of the bitmap in pixels."""

    @property
    def pixel_count(self) -> int:
        """The total number of pixels in the bitmap."""

    @property
    def channel_count(self) -> int:
        """The number of channels in the bitmap."""

    @property
    def channel_names(self) -> list[str]:
        """The names of the channels in the bitmap."""

    @property
    def srgb_gamma(self) -> bool:
        """True if the bitmap is in sRGB gamma space."""

    @srgb_gamma.setter
    def srgb_gamma(self, arg: bool, /) -> None: ...

    def has_alpha(self) -> bool:
        """Returns true if the bitmap has an alpha channel."""

    @property
    def bytes_per_pixel(self) -> int:
        """The number of bytes per pixel."""

    @property
    def buffer_size(self) -> int:
        """The total size of the bitmap in bytes."""

    def empty(self) -> bool:
        """True if bitmap is empty."""

    def clear(self) -> None:
        """Clears the bitmap to zeros."""

    def vflip(self) -> None:
        """Vertically flip the bitmap."""

    def split(self) -> list[tuple[str, Bitmap]]:
        """
        Split bitmap into multiple bitmaps, each containing the channels with
        the same prefix.

        For example, if the bitmap has channels `albedo.R`, `albedo.G`,
        `albedo.B`, `normal.R`, `normal.G`, `normal.B`, this function will
        return two bitmaps, one containing the channels `albedo.R`,
        `albedo.G`, `albedo.B` and the other containing the channels
        `normal.R`, `normal.G`, `normal.B`.

        Common pixel formats (e.g. `y`, `rgb`, `rgba`) are automatically
        detected and used for the split bitmaps.

        Any channels that do not have a prefix will be returned in the bitmap
        with the empty prefix.

        Returns:
            Returns a list of (prefix, bitmap) pairs.
        """

    def convert(self, pixel_format: Optional[Bitmap.PixelFormat] = None, component_type: Optional[DataStruct.Type] = None, srgb_gamma: Optional[bool] = None) -> Bitmap: ...

    def write(self, path: str | os.PathLike, format: Bitmap.FileFormat = Bitmap.FileFormat.auto, quality: int = -1) -> None: ...

    def write_async(self, path: str | os.PathLike, format: Bitmap.FileFormat = Bitmap.FileFormat.auto, quality: int = -1) -> None: ...

    @staticmethod
    def read_multiple(paths: Sequence[str | os.PathLike], format: Bitmap.FileFormat = Bitmap.FileFormat.auto) -> list[Bitmap]:
        """
        Load a list of bitmaps from multiple paths. Uses multi-threading to
        load bitmaps in parallel.
        """

    def __eq__(self, arg: Bitmap, /) -> bool: ...

    def __ne__(self, arg: Bitmap, /) -> bool: ...

    @property
    def __array_interface__(self) -> object: ...

    def _repr_html_(self) -> object: ...

class SHA1:
    """Helper to compute SHA-1 hash."""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, data: bytes) -> None: ...

    @overload
    def __init__(self, str: str) -> None: ...

    @overload
    def update(self, data: bytes) -> SHA1:
        """
        Update hash by adding the given data.

        Parameter ``data``:
            Data to hash.

        Parameter ``len``:
            Length of data in bytes.
        """

    @overload
    def update(self, str: str) -> SHA1:
        """
        Update hash by adding the given string.

        Parameter ``str``:
            String to hash.
        """

    def digest(self) -> bytes:
        """Return the message digest."""

    def hex_digest(self) -> str:
        """Return the message digest as a hex string."""

class DataType(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    void = 0

    bool = 1

    int8 = 2

    int16 = 3

    int32 = 4

    int64 = 5

    uint8 = 6

    uint16 = 7

    uint32 = 8

    uint64 = 9

    float16 = 10

    float32 = 11

    float64 = 12

class NativeHandleType(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    undefined = 0

    win32 = 1

    file_descriptor = 2

    D3D12Device = 131073

    D3D12CommandQueue = 131074

    D3D12GraphicsCommandList = 131075

    D3D12Resource = 131076

    D3D12PipelineState = 131077

    D3D12StateObject = 131078

    D3D12CpuDescriptorHandle = 131079

    D3D12Fence = 131080

    D3D12DeviceAddress = 131081

    VkDevice = 196609

    VkPhysicalDevice = 196610

    VkInstance = 196611

    VkQueue = 196612

    VkCommandBuffer = 196613

    VkBuffer = 196614

    VkImage = 196615

    VkImageView = 196616

    VkAccelerationStructureKHR = 196617

    VkSampler = 196618

    VkPipeline = 196619

    VkSemaphore = 196620

    MTLDevice = 262145

    MTLCommandQueue = 262146

    MTLCommandBuffer = 262147

    MTLTexture = 262148

    MTLBuffer = 262149

    MTLComputePipelineState = 262150

    MTLRenderPipelineState = 262151

    MTLSharedEvent = 262152

    MTLSamplerState = 262153

    MTLAccelerationStructure = 262154

    CUdevice = 327681

    CUdeviceptr = 327682

    CUtexObject = 327687

    CUstream = 327683

    CUcontext = 327689

    OptixDeviceContext = 393217

    OptixTraversableHandle = 393218

    WGPUDevice = 458753

    WGPUBuffer = 458754

    WGPUTexture = 458755

    WGPUSampler = 458756

    WGPURenderPipeline = 458757

    WGPUComputePipeline = 458758

    WGPUQueue = 458759

    WGPUCommandBuffer = 458760

    WGPUTextureView = 458761

    WGPUCommandEncoder = 458762

class NativeHandle:
    """N/A"""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg0: NativeHandleType, arg1: int, /) -> None: ...

    @property
    def type(self) -> NativeHandleType:
        """N/A"""

    @property
    def value(self) -> int:
        """N/A"""

    def __bool__(self) -> bool: ...

    def __repr__(self) -> str: ...

    def __hash__(self) -> int: ...

    def __eq__(self, arg: NativeHandle, /) -> bool: ...

    def __ne__(self, arg: NativeHandle, /) -> bool: ...

    @staticmethod
    def from_cuda_stream(stream: int) -> NativeHandle:
        """N/A"""

class Format(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    undefined = 0

    r8_uint = 1

    r8_sint = 2

    r8_unorm = 3

    r8_snorm = 4

    rg8_uint = 5

    rg8_sint = 6

    rg8_unorm = 7

    rg8_snorm = 8

    rgba8_uint = 9

    rgba8_sint = 10

    rgba8_unorm = 11

    rgba8_unorm_srgb = 12

    rgba8_snorm = 13

    bgra8_unorm = 14

    bgra8_unorm_srgb = 15

    bgrx8_unorm = 16

    bgrx8_unorm_srgb = 17

    r16_uint = 18

    r16_sint = 19

    r16_unorm = 20

    r16_snorm = 21

    r16_float = 22

    rg16_uint = 23

    rg16_sint = 24

    rg16_unorm = 25

    rg16_snorm = 26

    rg16_float = 27

    rgba16_uint = 28

    rgba16_sint = 29

    rgba16_unorm = 30

    rgba16_snorm = 31

    rgba16_float = 32

    r32_uint = 33

    r32_sint = 34

    r32_float = 35

    rg32_uint = 36

    rg32_sint = 37

    rg32_float = 38

    rgb32_uint = 39

    rgb32_sint = 40

    rgb32_float = 41

    rgba32_uint = 42

    rgba32_sint = 43

    rgba32_float = 44

    r64_uint = 45

    r64_sint = 46

    bgra4_unorm = 47

    b5g6r5_unorm = 48

    bgr5a1_unorm = 49

    rgb9e5_ufloat = 50

    rgb10a2_uint = 51

    rgb10a2_unorm = 52

    r11g11b10_float = 53

    d32_float = 54

    d16_unorm = 55

    d32_float_s8_uint = 56

    bc1_unorm = 57

    bc1_unorm_srgb = 58

    bc2_unorm = 59

    bc2_unorm_srgb = 60

    bc3_unorm = 61

    bc3_unorm_srgb = 62

    bc4_unorm = 63

    bc4_snorm = 64

    bc5_unorm = 65

    bc5_snorm = 66

    bc6h_ufloat = 67

    bc6h_sfloat = 68

    bc7_unorm = 69

    bc7_unorm_srgb = 70

class FormatType(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    unknown = 0

    float = 1

    unorm = 2

    unorm_srgb = 3

    snorm = 4

    uint = 5

    sint = 6

class FormatChannels(enum.IntFlag):
    _member_names_: list = ['none', 'r', 'g', 'b', 'a', 'rg', 'rgb', 'rgba']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    r = 1

    g = 2

    b = 4

    a = 8

    rg = 3

    rgb = 7

    rgba = 15

class FormatSupport(enum.IntFlag):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    copy_source = 1

    copy_destination = 2

    texture = 4

    depth_stencil = 8

    render_target = 16

    blendable = 32

    multisampling = 64

    resolvable = 128

    shader_load = 256

    shader_sample = 512

    shader_uav_load = 1024

    shader_uav_store = 2048

    shader_atomic = 4096

    buffer = 8192

    index_buffer = 16384

    vertex_buffer = 32768

class FormatInfo:
    """Resource format information."""

    @property
    def format(self) -> Format:
        """Resource format."""

    @property
    def name(self) -> str:
        """Format name."""

    @property
    def bytes_per_block(self) -> int:
        """Number of bytes per block (compressed) or pixel (uncompressed)."""

    @property
    def channel_count(self) -> int:
        """Number of channels."""

    @property
    def type(self) -> FormatType:
        """Format type (typeless, float, unorm, unorm_srgb, snorm, uint, sint)."""

    @property
    def is_depth(self) -> bool:
        """True if format has a depth component."""

    @property
    def is_stencil(self) -> bool:
        """True if format has a stencil component."""

    @property
    def is_compressed(self) -> bool:
        """True if format is compressed."""

    @property
    def block_width(self) -> int:
        """Block width for compressed formats (1 for uncompressed formats)."""

    @property
    def block_height(self) -> int:
        """Block height for compressed formats (1 for uncompressed formats)."""

    @property
    def channel_bit_count(self) -> list[int]:
        """Number of bits per channel."""

    @property
    def dxgi_format(self) -> int:
        """DXGI format."""

    @property
    def vk_format(self) -> int:
        """Vulkan format."""

    def is_depth_stencil(self) -> bool:
        """True if format has a depth or stencil component."""

    def is_float_format(self) -> bool:
        """True if format is floating point."""

    def is_integer_format(self) -> bool:
        """True if format is integer."""

    def is_normalized_format(self) -> bool:
        """True if format is normalized."""

    def is_srgb_format(self) -> bool:
        """True if format is sRGB."""

    def get_channels(self) -> FormatChannels:
        """Get the channels for the format (only for color formats)."""

    def get_channel_bits(self, arg: FormatChannels, /) -> int:
        """Get the number of bits for the specified channels."""

    def has_equal_channel_bits(self) -> bool:
        """Check if all channels have the same number of bits."""

    def __repr__(self) -> str: ...

def get_format_info(arg: Format, /) -> FormatInfo: ...

class CommandQueueType(enum.Enum):
    _member_names_: list = ['graphics']

    _member_map_: dict = {'graphics' : CommandQueueType.graphics}

    _value2member_map_: dict = {0 : CommandQueueType.graphics}

    graphics = 0

class Feature(enum.IntEnum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    hardware_device = 0

    software_device = 1

    parameter_block = 2

    bindless = 3

    surface = 4

    pipeline_cache = 5

    rasterization = 6

    barycentrics = 7

    multi_view = 8

    rasterizer_ordered_views = 9

    conservative_rasterization = 10

    custom_border_color = 11

    fragment_shading_rate = 12

    sampler_feedback = 13

    acceleration_structure = 14

    acceleration_structure_spheres = 15

    acceleration_structure_linear_swept_spheres = 16

    ray_tracing = 17

    ray_query = 18

    shader_execution_reordering = 19

    ray_tracing_validation = 20

    timestamp_query = 21

    realtime_clock = 22

    cooperative_vector = 23

    cooperative_matrix = 24

    sm_5_1 = 25

    sm_6_0 = 26

    sm_6_1 = 27

    sm_6_2 = 28

    sm_6_3 = 29

    sm_6_4 = 30

    sm_6_5 = 31

    sm_6_6 = 32

    sm_6_7 = 33

    sm_6_8 = 34

    sm_6_9 = 35

    half = 36

    double_ = 37

    int16 = 38

    int64 = 39

    atomic_float = 40

    atomic_half = 41

    atomic_int64 = 42

    wave_ops = 43

    mesh_shader = 44

    pointer = 45

    conservative_rasterization1 = 46

    conservative_rasterization2 = 47

    conservative_rasterization3 = 48

    programmable_sample_positions1 = 49

    programmable_sample_positions2 = 50

    shader_resource_min_lod = 51

    argument_buffer_tier2 = 52

class DescriptorHandleType(enum.IntEnum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    undefined = 0

    buffer = 1

    rw_buffer = 2

    texture = 3

    rw_texture = 4

    sampler = 5

    acceleration_structure = 6

class DescriptorHandle:
    @property
    def type(self) -> DescriptorHandleType: ...

    @property
    def value(self) -> int: ...

    def __bool__(self) -> bool: ...

    def __repr__(self) -> str: ...

class ShaderModel(enum.IntEnum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    unknown = 0

    sm_6_0 = 60

    sm_6_1 = 61

    sm_6_2 = 62

    sm_6_3 = 63

    sm_6_4 = 64

    sm_6_5 = 65

    sm_6_6 = 66

    sm_6_7 = 67

class ShaderStage(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    vertex = 1

    hull = 2

    domain = 3

    geometry = 4

    fragment = 5

    compute = 6

    ray_generation = 7

    intersection = 8

    any_hit = 9

    closest_hit = 10

    miss = 11

    callable = 12

    mesh = 13

    amplification = 14

class ComparisonFunc(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    never = 0

    less = 1

    equal = 2

    less_equal = 3

    greater = 4

    not_equal = 5

    greater_equal = 6

    always = 7

class TextureFilteringMode(enum.Enum):
    _member_names_: list = ['point', 'linear']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    point = 0

    linear = 1

class TextureAddressingMode(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    wrap = 0

    clamp_to_edge = 1

    clamp_to_border = 2

    mirror_repeat = 3

    mirror_once = 4

class TextureReductionOp(enum.Enum):
    _member_names_: list = ['average', 'comparison', 'minimum', 'maximum']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    average = 0

    comparison = 1

    minimum = 2

    maximum = 3

class DrawArguments:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def vertex_count(self) -> int: ...

    @vertex_count.setter
    def vertex_count(self, arg: int, /) -> None: ...

    @property
    def instance_count(self) -> int: ...

    @instance_count.setter
    def instance_count(self, arg: int, /) -> None: ...

    @property
    def start_vertex_location(self) -> int: ...

    @start_vertex_location.setter
    def start_vertex_location(self, arg: int, /) -> None: ...

    @property
    def start_instance_location(self) -> int: ...

    @start_instance_location.setter
    def start_instance_location(self, arg: int, /) -> None: ...

    @property
    def start_index_location(self) -> int: ...

    @start_index_location.setter
    def start_index_location(self, arg: int, /) -> None: ...

DrawArgumentsDict = TypedDict("DrawArgumentsDict", {
    "vertex_count": int,
    "instance_count": int,
    "start_vertex_location": int,
    "start_instance_location": int,
    "start_index_location": int
}, total = False)

DrawArgumentsParam = Union[DrawArguments, DrawArgumentsDict]

class Viewport:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @staticmethod
    def from_size(width: float, height: float) -> Viewport: ...

    @property
    def x(self) -> float: ...

    @x.setter
    def x(self, arg: float, /) -> None: ...

    @property
    def y(self) -> float: ...

    @y.setter
    def y(self, arg: float, /) -> None: ...

    @property
    def width(self) -> float: ...

    @width.setter
    def width(self, arg: float, /) -> None: ...

    @property
    def height(self) -> float: ...

    @height.setter
    def height(self, arg: float, /) -> None: ...

    @property
    def min_depth(self) -> float: ...

    @min_depth.setter
    def min_depth(self, arg: float, /) -> None: ...

    @property
    def max_depth(self) -> float: ...

    @max_depth.setter
    def max_depth(self, arg: float, /) -> None: ...

    def __repr__(self) -> str: ...

ViewportDict = TypedDict("ViewportDict", {
    "x": float,
    "y": float,
    "width": float,
    "height": float,
    "min_depth": float,
    "max_depth": float
}, total = False)

ViewportParam = Union[Viewport, ViewportDict]

class ScissorRect:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @staticmethod
    def from_size(width: int, height: int) -> ScissorRect: ...

    @property
    def min_x(self) -> int: ...

    @min_x.setter
    def min_x(self, arg: int, /) -> None: ...

    @property
    def min_y(self) -> int: ...

    @min_y.setter
    def min_y(self, arg: int, /) -> None: ...

    @property
    def max_x(self) -> int: ...

    @max_x.setter
    def max_x(self, arg: int, /) -> None: ...

    @property
    def max_y(self) -> int: ...

    @max_y.setter
    def max_y(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

ScissorRectDict = TypedDict("ScissorRectDict", {
    "min_x": int,
    "min_y": int,
    "max_x": int,
    "max_y": int
}, total = False)

ScissorRectParam = Union[ScissorRect, ScissorRectDict]

class IndexFormat(enum.Enum):
    _member_names_: list = ['uint16', 'uint32']

    _member_map_: dict = ...

    _value2member_map_: dict = {0 : IndexFormat.uint16, 1 : IndexFormat.uint32}

    uint16 = 0

    uint32 = 1

class PrimitiveTopology(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    point_list = 0

    line_list = 1

    line_strip = 2

    triangle_list = 3

    triangle_strip = 4

    patch_list = 5

class LoadOp(enum.Enum):
    _member_names_: list = ['load', 'clear', 'dont_care']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    load = 0

    clear = 1

    dont_care = 2

class StoreOp(enum.Enum):
    _member_names_: list = ['store', 'dont_care']

    _member_map_: dict = ...

    _value2member_map_: dict = {0 : StoreOp.store, 1 : StoreOp.dont_care}

    store = 0

    dont_care = 1

class StencilOp(enum.Enum):
    _member_names_: list = ['keep']

    _member_map_: dict = ...

    _value2member_map_: dict = {0 : StencilOp.keep}

    keep = 0

    zero = 0

    replace = 0

    increment_saturate = 0

    decrement_saturate = 0

    invert = 0

    increment_wrap = 0

    decrement_wrap = 0

class FillMode(enum.Enum):
    _member_names_: list = ['solid', 'wireframe']

    _member_map_: dict = ...

    _value2member_map_: dict = {0 : FillMode.solid, 1 : FillMode.wireframe}

    solid = 0

    wireframe = 1

class CullMode(enum.Enum):
    _member_names_: list = ['none', 'front', 'back']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    front = 1

    back = 2

class FrontFaceMode(enum.Enum):
    _member_names_: list = ['counter_clockwise', 'clockwise']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    counter_clockwise = 0

    clockwise = 1

class LogicOp(enum.Enum):
    _member_names_: list = ['no_op']

    _member_map_: dict = {'no_op' : LogicOp.no_op}

    _value2member_map_: dict = {0 : LogicOp.no_op}

    no_op = 0

class BlendOp(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    add = 0

    subtract = 1

    reverse_subtract = 2

    min = 3

    max = 4

class BlendFactor(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    zero = 0

    one = 1

    src_color = 2

    inv_src_color = 3

    src_alpha = 4

    inv_src_alpha = 5

    dest_alpha = 6

    inv_dest_alpha = 7

    dest_color = 8

    inv_dest_color = 9

    src_alpha_saturate = 10

    blend_color = 11

    inv_blend_color = 12

    secondary_src_color = 13

    inv_secondary_src_color = 14

    secondary_src_alpha = 15

    inv_secondary_src_alpha = 16

class RenderTargetWriteMask(enum.IntFlag):
    _member_names_: list = ['none', 'red', 'green', 'blue', 'alpha', 'all']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    red = 1

    green = 2

    blue = 4

    alpha = 8

    all = 15

class AspectBlendDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def src_factor(self) -> BlendFactor: ...

    @src_factor.setter
    def src_factor(self, arg: BlendFactor, /) -> None: ...

    @property
    def dst_factor(self) -> BlendFactor: ...

    @dst_factor.setter
    def dst_factor(self, arg: BlendFactor, /) -> None: ...

    @property
    def op(self) -> BlendOp: ...

    @op.setter
    def op(self, arg: BlendOp, /) -> None: ...

AspectBlendDescDict = TypedDict("AspectBlendDescDict", {
    "src_factor": BlendFactor,
    "dst_factor": BlendFactor,
    "op": BlendOp
}, total = False)

AspectBlendDescParam = Union[AspectBlendDesc, AspectBlendDescDict]

class ColorTargetDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def format(self) -> Format: ...

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def color(self) -> AspectBlendDesc: ...

    @color.setter
    def color(self, arg: AspectBlendDescParam, /) -> None: ...

    @property
    def alpha(self) -> AspectBlendDesc: ...

    @alpha.setter
    def alpha(self, arg: AspectBlendDescParam, /) -> None: ...

    @property
    def write_mask(self) -> RenderTargetWriteMask: ...

    @write_mask.setter
    def write_mask(self, arg: RenderTargetWriteMask, /) -> None: ...

    @property
    def enable_blend(self) -> bool: ...

    @enable_blend.setter
    def enable_blend(self, arg: bool, /) -> None: ...

    @property
    def logic_op(self) -> LogicOp: ...

    @logic_op.setter
    def logic_op(self, arg: LogicOp, /) -> None: ...

ColorTargetDescDict = TypedDict("ColorTargetDescDict", {
    "format": Format,
    "color": AspectBlendDescParam,
    "alpha": AspectBlendDescParam,
    "write_mask": RenderTargetWriteMask,
    "enable_blend": bool,
    "logic_op": LogicOp
}, total = False)

ColorTargetDescParam = Union[ColorTargetDesc, ColorTargetDescDict]

class MultisampleDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def sample_count(self) -> int: ...

    @sample_count.setter
    def sample_count(self, arg: int, /) -> None: ...

    @property
    def sample_mask(self) -> int: ...

    @sample_mask.setter
    def sample_mask(self, arg: int, /) -> None: ...

    @property
    def alpha_to_coverage_enable(self) -> bool: ...

    @alpha_to_coverage_enable.setter
    def alpha_to_coverage_enable(self, arg: bool, /) -> None: ...

    @property
    def alpha_to_one_enable(self) -> bool: ...

    @alpha_to_one_enable.setter
    def alpha_to_one_enable(self, arg: bool, /) -> None: ...

MultisampleDescDict = TypedDict("MultisampleDescDict", {
    "sample_count": int,
    "sample_mask": int,
    "alpha_to_coverage_enable": bool,
    "alpha_to_one_enable": bool
}, total = False)

MultisampleDescParam = Union[MultisampleDesc, MultisampleDescDict]

class DepthStencilOpDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def stencil_fail_op(self) -> StencilOp: ...

    @stencil_fail_op.setter
    def stencil_fail_op(self, arg: StencilOp, /) -> None: ...

    @property
    def stencil_depth_fail_op(self) -> StencilOp: ...

    @stencil_depth_fail_op.setter
    def stencil_depth_fail_op(self, arg: StencilOp, /) -> None: ...

    @property
    def stencil_pass_op(self) -> StencilOp: ...

    @stencil_pass_op.setter
    def stencil_pass_op(self, arg: StencilOp, /) -> None: ...

    @property
    def stencil_func(self) -> ComparisonFunc: ...

    @stencil_func.setter
    def stencil_func(self, arg: ComparisonFunc, /) -> None: ...

DepthStencilOpDescDict = TypedDict("DepthStencilOpDescDict", {
    "stencil_fail_op": StencilOp,
    "stencil_depth_fail_op": StencilOp,
    "stencil_pass_op": StencilOp,
    "stencil_func": ComparisonFunc
}, total = False)

DepthStencilOpDescParam = Union[DepthStencilOpDesc, DepthStencilOpDescDict]

class DepthStencilDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def format(self) -> Format: ...

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def depth_test_enable(self) -> bool: ...

    @depth_test_enable.setter
    def depth_test_enable(self, arg: bool, /) -> None: ...

    @property
    def depth_write_enable(self) -> bool: ...

    @depth_write_enable.setter
    def depth_write_enable(self, arg: bool, /) -> None: ...

    @property
    def depth_func(self) -> ComparisonFunc: ...

    @depth_func.setter
    def depth_func(self, arg: ComparisonFunc, /) -> None: ...

    @property
    def stencil_enable(self) -> bool: ...

    @stencil_enable.setter
    def stencil_enable(self, arg: bool, /) -> None: ...

    @property
    def stencil_read_mask(self) -> int: ...

    @stencil_read_mask.setter
    def stencil_read_mask(self, arg: int, /) -> None: ...

    @property
    def stencil_write_mask(self) -> int: ...

    @stencil_write_mask.setter
    def stencil_write_mask(self, arg: int, /) -> None: ...

    @property
    def front_face(self) -> DepthStencilOpDesc: ...

    @front_face.setter
    def front_face(self, arg: DepthStencilOpDescParam, /) -> None: ...

    @property
    def back_face(self) -> DepthStencilOpDesc: ...

    @back_face.setter
    def back_face(self, arg: DepthStencilOpDescParam, /) -> None: ...

DepthStencilDescDict = TypedDict("DepthStencilDescDict", {
    "format": Format,
    "depth_test_enable": bool,
    "depth_write_enable": bool,
    "depth_func": ComparisonFunc,
    "stencil_enable": bool,
    "stencil_read_mask": int,
    "stencil_write_mask": int,
    "front_face": DepthStencilOpDescParam,
    "back_face": DepthStencilOpDescParam
}, total = False)

DepthStencilDescParam = Union[DepthStencilDesc, DepthStencilDescDict]

class RasterizerDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def fill_mode(self) -> FillMode: ...

    @fill_mode.setter
    def fill_mode(self, arg: FillMode, /) -> None: ...

    @property
    def cull_mode(self) -> CullMode: ...

    @cull_mode.setter
    def cull_mode(self, arg: CullMode, /) -> None: ...

    @property
    def front_face(self) -> FrontFaceMode: ...

    @front_face.setter
    def front_face(self, arg: FrontFaceMode, /) -> None: ...

    @property
    def depth_bias(self) -> int: ...

    @depth_bias.setter
    def depth_bias(self, arg: int, /) -> None: ...

    @property
    def depth_bias_clamp(self) -> float: ...

    @depth_bias_clamp.setter
    def depth_bias_clamp(self, arg: float, /) -> None: ...

    @property
    def slope_scaled_depth_bias(self) -> float: ...

    @slope_scaled_depth_bias.setter
    def slope_scaled_depth_bias(self, arg: float, /) -> None: ...

    @property
    def depth_clip_enable(self) -> bool: ...

    @depth_clip_enable.setter
    def depth_clip_enable(self, arg: bool, /) -> None: ...

    @property
    def scissor_enable(self) -> bool: ...

    @scissor_enable.setter
    def scissor_enable(self, arg: bool, /) -> None: ...

    @property
    def multisample_enable(self) -> bool: ...

    @multisample_enable.setter
    def multisample_enable(self, arg: bool, /) -> None: ...

    @property
    def antialiased_line_enable(self) -> bool: ...

    @antialiased_line_enable.setter
    def antialiased_line_enable(self, arg: bool, /) -> None: ...

    @property
    def enable_conservative_rasterization(self) -> bool: ...

    @enable_conservative_rasterization.setter
    def enable_conservative_rasterization(self, arg: bool, /) -> None: ...

    @property
    def forced_sample_count(self) -> int: ...

    @forced_sample_count.setter
    def forced_sample_count(self, arg: int, /) -> None: ...

RasterizerDescDict = TypedDict("RasterizerDescDict", {
    "fill_mode": FillMode,
    "cull_mode": CullMode,
    "front_face": FrontFaceMode,
    "depth_bias": int,
    "depth_bias_clamp": float,
    "slope_scaled_depth_bias": float,
    "depth_clip_enable": bool,
    "scissor_enable": bool,
    "multisample_enable": bool,
    "antialiased_line_enable": bool,
    "enable_conservative_rasterization": bool,
    "forced_sample_count": int
}, total = False)

RasterizerDescParam = Union[RasterizerDesc, RasterizerDescDict]

class QueryType(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    timestamp = 0

    acceleration_structure_compacted_size = 1

    acceleration_structure_serialized_size = 2

    acceleration_structure_current_size = 3

class RayTracingPipelineFlags(enum.IntFlag):
    _member_names_: list = ['none', 'skip_triangles', 'skip_procedurals']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    skip_triangles = 1

    skip_procedurals = 2

class DeviceChild(Object):
    class MemoryUsage:
        @property
        def device(self) -> int:
            """The amount of memory in bytes used on the device."""

        @property
        def host(self) -> int:
            """The amount of memory in bytes used on the host."""

    @property
    def device(self) -> Device: ...

    @property
    def memory_usage(self) -> DeviceChild.MemoryUsage:
        """The memory usage by this resource."""

ALL_LAYERS: int = 4294967295

ALL_MIPS: int = 4294967295

class ResourceState(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    undefined = 0

    general = 1

    vertex_buffer = 2

    index_buffer = 3

    constant_buffer = 4

    stream_output = 5

    shader_resource = 6

    unordered_access = 7

    render_target = 8

    depth_read = 9

    depth_write = 10

    present = 11

    indirect_argument = 12

    copy_source = 13

    copy_destination = 14

    resolve_source = 15

    resolve_destination = 16

    acceleration_structure = 17

    acceleration_structure_build_output = 18

class BufferUsage(enum.IntFlag):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    vertex_buffer = 1

    index_buffer = 2

    constant_buffer = 4

    shader_resource = 8

    unordered_access = 16

    indirect_argument = 32

    copy_source = 64

    copy_destination = 128

    acceleration_structure = 256

    acceleration_structure_build_input = 512

    shader_table = 1024

    shared = 2048

class TextureUsage(enum.IntFlag):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    shader_resource = 1

    unordered_access = 2

    render_target = 4

    depth_stencil = 8

    present = 16

    copy_source = 32

    copy_destination = 64

    resolve_source = 128

    resolve_destination = 256

    typeless = 512

    shared = 1024

class TextureType(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    texture_1d = 0

    texture_1d_array = 1

    texture_2d = 2

    texture_2d_array = 3

    texture_2d_ms = 4

    texture_2d_ms_array = 5

    texture_3d = 6

    texture_cube = 7

    texture_cube_array = 8

class MemoryType(enum.Enum):
    _member_names_: list = ['device_local', 'upload', 'read_back']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    device_local = 0

    upload = 1

    read_back = 2

class Resource(DeviceChild):
    @property
    def native_handle(self) -> NativeHandle:
        """Get the native resource handle."""

class TextureAspect(enum.Enum):
    _member_names_: list = ['all', 'depth_only', 'stencil_only']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    all = 0

    depth_only = 1

    stencil_only = 2

class BufferRange:
    def __init__(self) -> None: ...

    @property
    def offset(self) -> int: ...

    @property
    def size(self) -> int: ...

    def __repr__(self) -> str: ...

class SubresourceRange:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def layer(self) -> int:
        """First array layer."""

    @layer.setter
    def layer(self, arg: int, /) -> None: ...

    @property
    def layer_count(self) -> int:
        """Number of array layers."""

    @layer_count.setter
    def layer_count(self, arg: int, /) -> None: ...

    @property
    def mip(self) -> int:
        """Most detailed mip level."""

    @mip.setter
    def mip(self, arg: int, /) -> None: ...

    @property
    def mip_count(self) -> int:
        """Number of mip levels."""

    @mip_count.setter
    def mip_count(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

SubresourceRangeDict = TypedDict("SubresourceRangeDict", {
    "layer": int,
    "layer_count": int,
    "mip": int,
    "mip_count": int
}, total = False)

SubresourceRangeParam = Union[SubresourceRange, SubresourceRangeDict]

class BufferDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def size(self) -> int:
        """Buffer size in bytes."""

    @size.setter
    def size(self, arg: int, /) -> None: ...

    @property
    def struct_size(self) -> int:
        """Struct size in bytes."""

    @struct_size.setter
    def struct_size(self, arg: int, /) -> None: ...

    @property
    def format(self) -> Format:
        """Buffer format. Used when creating typed buffer views."""

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def memory_type(self) -> MemoryType:
        """Memory type."""

    @memory_type.setter
    def memory_type(self, arg: MemoryType, /) -> None: ...

    @property
    def usage(self) -> BufferUsage:
        """Resource usage flags."""

    @usage.setter
    def usage(self, arg: BufferUsage, /) -> None: ...

    @property
    def default_state(self) -> ResourceState:
        """Initial resource state."""

    @default_state.setter
    def default_state(self, arg: ResourceState, /) -> None: ...

    @property
    def label(self) -> str:
        """Debug label."""

    @label.setter
    def label(self, arg: str, /) -> None: ...

BufferDescDict = TypedDict("BufferDescDict", {
    "size": int,
    "struct_size": int,
    "format": Format,
    "memory_type": MemoryType,
    "usage": BufferUsage,
    "default_state": ResourceState,
    "label": str
}, total = False)

BufferDescParam = Union[BufferDesc, BufferDescDict]

class Buffer(Resource):
    @property
    def desc(self) -> BufferDesc: ...

    @property
    def size(self) -> int: ...

    @property
    def struct_size(self) -> int: ...

    @property
    def device_address(self) -> int: ...

    @property
    def shared_handle(self) -> NativeHandle:
        """
        Get the shared resource handle. Note: Buffer must be created with the
        ``BufferUsage::shared`` usage flag.
        """

    @property
    def descriptor_handle_ro(self) -> DescriptorHandle:
        """Get bindless descriptor handle for read access."""

    @property
    def descriptor_handle_rw(self) -> DescriptorHandle:
        """Get bindless descriptor handle for read-write access."""

    def to_numpy(self) -> NDArray: ...

    def copy_from_numpy(self, data: ArrayLike) -> None: ...

    def to_torch(self, type: DataType = DataType.void, shape: Sequence[int] = [], strides: Sequence[int] = [], offset: int = 0) -> Annotated[ArrayLike, dict(device='cuda')]: ...

class BufferOffsetPair:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, buffer: Buffer) -> None: ...

    @overload
    def __init__(self, buffer: Buffer, offset: int = 0) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def buffer(self) -> Buffer: ...

    @buffer.setter
    def buffer(self, arg: Buffer, /) -> None: ...

    @property
    def offset(self) -> int: ...

    @offset.setter
    def offset(self, arg: int, /) -> None: ...

BufferOffsetPairDict = TypedDict("BufferOffsetPairDict", {
    "buffer": Buffer,
    "offset": int
}, total = False)

BufferOffsetPairParam = Union[BufferOffsetPair, BufferOffsetPairDict, Buffer]

class TextureDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def type(self) -> TextureType:
        """Texture type."""

    @type.setter
    def type(self, arg: TextureType, /) -> None: ...

    @property
    def format(self) -> Format:
        """Texture format."""

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def width(self) -> int:
        """Width in pixels."""

    @width.setter
    def width(self, arg: int, /) -> None: ...

    @property
    def height(self) -> int:
        """Height in pixels."""

    @height.setter
    def height(self, arg: int, /) -> None: ...

    @property
    def depth(self) -> int:
        """Depth in pixels."""

    @depth.setter
    def depth(self, arg: int, /) -> None: ...

    @property
    def array_length(self) -> int:
        """Array length."""

    @array_length.setter
    def array_length(self, arg: int, /) -> None: ...

    @property
    def mip_count(self) -> int:
        """Number of mip levels (ALL_MIPS for all mip levels)."""

    @mip_count.setter
    def mip_count(self, arg: int, /) -> None: ...

    @property
    def sample_count(self) -> int:
        """Number of samples per pixel."""

    @sample_count.setter
    def sample_count(self, arg: int, /) -> None: ...

    @property
    def sample_quality(self) -> int:
        """Quality level for multisampled textures."""

    @sample_quality.setter
    def sample_quality(self, arg: int, /) -> None: ...

    @property
    def memory_type(self) -> MemoryType: ...

    @memory_type.setter
    def memory_type(self, arg: MemoryType, /) -> None: ...

    @property
    def usage(self) -> TextureUsage: ...

    @usage.setter
    def usage(self, arg: TextureUsage, /) -> None: ...

    @property
    def default_state(self) -> ResourceState: ...

    @default_state.setter
    def default_state(self, arg: ResourceState, /) -> None: ...

    @property
    def label(self) -> str:
        """Debug label."""

    @label.setter
    def label(self, arg: str, /) -> None: ...

TextureDescDict = TypedDict("TextureDescDict", {
    "type": TextureType,
    "format": Format,
    "width": int,
    "height": int,
    "depth": int,
    "array_length": int,
    "mip_count": int,
    "sample_count": int,
    "sample_quality": int,
    "memory_type": MemoryType,
    "usage": TextureUsage,
    "default_state": ResourceState,
    "label": str
}, total = False)

TextureDescParam = Union[TextureDesc, TextureDescDict]

class TextureViewDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def format(self) -> Format: ...

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def aspect(self) -> TextureAspect: ...

    @aspect.setter
    def aspect(self, arg: TextureAspect, /) -> None: ...

    @property
    def subresource_range(self) -> SubresourceRange: ...

    @subresource_range.setter
    def subresource_range(self, arg: SubresourceRangeParam, /) -> None: ...

    @property
    def label(self) -> str: ...

    @label.setter
    def label(self, arg: str, /) -> None: ...

TextureViewDescDict = TypedDict("TextureViewDescDict", {
    "format": Format,
    "aspect": TextureAspect,
    "subresource_range": SubresourceRangeParam,
    "label": str
}, total = False)

TextureViewDescParam = Union[TextureViewDesc, TextureViewDescDict]

class SubresourceLayout:
    def __init__(self) -> None: ...

    @property
    def size(self) -> math.uint3:
        """Dimensions of the subresource (in texels)."""

    @size.setter
    def size(self, arg: uint3param, /) -> None: ...

    @property
    def col_pitch(self) -> int:
        """
        Stride in bytes between columns (i.e. blocks) of the subresource
        tensor.
        """

    @col_pitch.setter
    def col_pitch(self, arg: int, /) -> None: ...

    @property
    def row_pitch(self) -> int:
        """Stride in bytes between rows of the subresource tensor."""

    @row_pitch.setter
    def row_pitch(self, arg: int, /) -> None: ...

    @property
    def slice_pitch(self) -> int:
        """Stride in bytes between slices of the subresource tensor."""

    @slice_pitch.setter
    def slice_pitch(self, arg: int, /) -> None: ...

    @property
    def size_in_bytes(self) -> int:
        """
        Overall size required to fit the subresource data (typically size.z *
        slice_pitch).
        """

    @size_in_bytes.setter
    def size_in_bytes(self, arg: int, /) -> None: ...

    @property
    def block_width(self) -> int:
        """Block width in texels (1 for uncompressed formats)."""

    @block_width.setter
    def block_width(self, arg: int, /) -> None: ...

    @property
    def block_height(self) -> int:
        """Block height in texels (1 for uncompressed formats)."""

    @block_height.setter
    def block_height(self, arg: int, /) -> None: ...

    @property
    def row_count(self) -> int:
        """
        Number of rows. For uncompressed formats this matches size.y. For
        compressed formats this matches align_up(size.y, block_height) /
        block_height.
        """

    @row_count.setter
    def row_count(self, arg: int, /) -> None: ...

class Texture(Resource):
    @property
    def desc(self) -> TextureDesc: ...

    @property
    def type(self) -> TextureType: ...

    @property
    def format(self) -> Format: ...

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def depth(self) -> int: ...

    @property
    def array_length(self) -> int: ...

    @property
    def mip_count(self) -> int: ...

    @property
    def layer_count(self) -> int: ...

    @property
    def subresource_count(self) -> int: ...

    @property
    def shared_handle(self) -> NativeHandle:
        """
        Get the shared resource handle. Note: Texture must be created with the
        ``TextureUsage::shared`` usage flag.
        """

    def get_mip_width(self, mip: int = 0) -> int: ...

    def get_mip_height(self, mip: int = 0) -> int: ...

    def get_mip_depth(self, mip: int = 0) -> int: ...

    def get_mip_size(self, mip: int = 0) -> math.uint3: ...

    def get_subresource_layout(self, mip: int, row_alignment: int = 4294967295) -> SubresourceLayout:
        """
        Get layout of a texture subresource. By default, the row alignment
        used is that required by the target for direct buffer upload/download.
        Pass in 1 for a completely packed layout.
        """

    @overload
    def create_view(self, desc: TextureViewDescParam) -> TextureView: ...

    @overload
    def create_view(self, dict: dict) -> TextureView: ...

    @overload
    def create_view(self, format: Format = Format.undefined, aspect: TextureAspect = TextureAspect.all, layer: int = 0, layer_count: int = 4294967295, mip: int = 0, mip_count: int = 4294967295, label: str = '') -> TextureView: ...

    def to_bitmap(self, layer: int = 0, mip: int = 0) -> Bitmap: ...

    def to_numpy(self, layer: int = 0, mip: int = 0) -> NDArray: ...

    def copy_from_numpy(self, data: ArrayLike, layer: int = 0, mip: int = 0) -> None: ...

class TextureView(DeviceChild):
    @property
    def texture(self) -> Texture: ...

    @property
    def desc(self) -> TextureViewDesc: ...

    @property
    def format(self) -> Format: ...

    @property
    def aspect(self) -> TextureAspect: ...

    @property
    def subresource_range(self) -> SubresourceRange: ...

    @property
    def label(self) -> str: ...

    @property
    def descriptor_handle_ro(self) -> DescriptorHandle: ...

    @property
    def descriptor_handle_rw(self) -> DescriptorHandle: ...

    @property
    def native_handle(self) -> NativeHandle:
        """Get the native texture view handle."""

    def __repr__(self) -> str: ...

class SamplerDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def min_filter(self) -> TextureFilteringMode: ...

    @min_filter.setter
    def min_filter(self, arg: TextureFilteringMode, /) -> None: ...

    @property
    def mag_filter(self) -> TextureFilteringMode: ...

    @mag_filter.setter
    def mag_filter(self, arg: TextureFilteringMode, /) -> None: ...

    @property
    def mip_filter(self) -> TextureFilteringMode: ...

    @mip_filter.setter
    def mip_filter(self, arg: TextureFilteringMode, /) -> None: ...

    @property
    def reduction_op(self) -> TextureReductionOp: ...

    @reduction_op.setter
    def reduction_op(self, arg: TextureReductionOp, /) -> None: ...

    @property
    def address_u(self) -> TextureAddressingMode: ...

    @address_u.setter
    def address_u(self, arg: TextureAddressingMode, /) -> None: ...

    @property
    def address_v(self) -> TextureAddressingMode: ...

    @address_v.setter
    def address_v(self, arg: TextureAddressingMode, /) -> None: ...

    @property
    def address_w(self) -> TextureAddressingMode: ...

    @address_w.setter
    def address_w(self, arg: TextureAddressingMode, /) -> None: ...

    @property
    def mip_lod_bias(self) -> float: ...

    @mip_lod_bias.setter
    def mip_lod_bias(self, arg: float, /) -> None: ...

    @property
    def max_anisotropy(self) -> int: ...

    @max_anisotropy.setter
    def max_anisotropy(self, arg: int, /) -> None: ...

    @property
    def comparison_func(self) -> ComparisonFunc: ...

    @comparison_func.setter
    def comparison_func(self, arg: ComparisonFunc, /) -> None: ...

    @property
    def border_color(self) -> math.float4: ...

    @border_color.setter
    def border_color(self, arg: float4param, /) -> None: ...

    @property
    def min_lod(self) -> float: ...

    @min_lod.setter
    def min_lod(self, arg: float, /) -> None: ...

    @property
    def max_lod(self) -> float: ...

    @max_lod.setter
    def max_lod(self, arg: float, /) -> None: ...

    @property
    def label(self) -> str: ...

    @label.setter
    def label(self, arg: str, /) -> None: ...

SamplerDescDict = TypedDict("SamplerDescDict", {
    "min_filter": TextureFilteringMode,
    "mag_filter": TextureFilteringMode,
    "mip_filter": TextureFilteringMode,
    "reduction_op": TextureReductionOp,
    "address_u": TextureAddressingMode,
    "address_v": TextureAddressingMode,
    "address_w": TextureAddressingMode,
    "mip_lod_bias": float,
    "max_anisotropy": int,
    "comparison_func": ComparisonFunc,
    "border_color": float4param,
    "min_lod": float,
    "max_lod": float,
    "label": str
}, total = False)

SamplerDescParam = Union[SamplerDesc, SamplerDescDict]

class Sampler(DeviceChild):
    @property
    def desc(self) -> SamplerDesc: ...

    @property
    def descriptor_handle(self) -> DescriptorHandle: ...

    @property
    def native_handle(self) -> NativeHandle:
        """Get the native sampler handle."""

class FenceDesc:
    """Fence descriptor."""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def initial_value(self) -> int:
        """Initial fence value."""

    @initial_value.setter
    def initial_value(self, arg: int, /) -> None: ...

    @property
    def shared(self) -> bool:
        """Create a shared fence."""

    @shared.setter
    def shared(self, arg: bool, /) -> None: ...

FenceDescDict = TypedDict("FenceDescDict", {
    "initial_value": int,
    "shared": bool
}, total = False)

FenceDescParam = Union[FenceDesc, FenceDescDict]

class Fence(DeviceChild):
    """Fence."""

    @property
    def desc(self) -> FenceDesc: ...

    def signal(self, value: int = 18446744073709551615) -> int:
        """
        Signal the fence. This signals the fence from the host.

        Parameter ``value``:
            The value to signal. If ``AUTO``, the signaled value will be auto-
            incremented.

        Returns:
            The signaled value.
        """

    def wait(self, value: int = 18446744073709551615, timeout_ns: int = 18446744073709551615) -> None:
        """
        Wait for the fence to be signaled on the host. Blocks the host until
        the fence reaches or exceeds the specified value.

        Parameter ``value``:
            The value to wait for. If ``AUTO``, wait for the last signaled
            value.

        Parameter ``timeout_ns``:
            The timeout in nanoseconds. If ``TIMEOUT_INFINITE``, the function
            will block indefinitely.
        """

    @property
    def current_value(self) -> int:
        """Returns the currently signaled value on the device."""

    @property
    def signaled_value(self) -> int:
        """Returns the last signaled value on the device."""

    @property
    def shared_handle(self) -> NativeHandle:
        """
        Get the shared fence handle. Note: Fence must be created with the
        ``FenceDesc::shared`` flag.
        """

    @property
    def native_handle(self) -> NativeHandle:
        """Get the native fence handle."""

    AUTO: int = 18446744073709551615

    TIMEOUT_INFINITE: int = 18446744073709551615

class QueryPoolDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def type(self) -> QueryType:
        """Query type."""

    @type.setter
    def type(self, arg: QueryType, /) -> None: ...

    @property
    def count(self) -> int:
        """Number of queries in the pool."""

    @count.setter
    def count(self, arg: int, /) -> None: ...

QueryPoolDescDict = TypedDict("QueryPoolDescDict", {
    "type": QueryType,
    "count": int
}, total = False)

QueryPoolDescParam = Union[QueryPoolDesc, QueryPoolDescDict]

class QueryPool(DeviceChild):
    @property
    def desc(self) -> QueryPoolDesc: ...

    def reset(self) -> None: ...

    def get_result(self, index: int) -> int: ...

    def get_results(self, index: int, count: int) -> list[int]: ...

    def get_timestamp_result(self, index: int) -> float: ...

    def get_timestamp_results(self, index: int, count: int) -> list[float]: ...

class InputSlotClass(enum.Enum):
    _member_names_: list = ['per_vertex', 'per_instance']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    per_vertex = 0

    per_instance = 1

class InputElementDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def semantic_name(self) -> str:
        """The name of the corresponding parameter in shader code."""

    @semantic_name.setter
    def semantic_name(self, arg: str, /) -> None: ...

    @property
    def semantic_index(self) -> int:
        """
        The index of the corresponding parameter in shader code. Only needed
        if multiple parameters share a semantic name.
        """

    @semantic_index.setter
    def semantic_index(self, arg: int, /) -> None: ...

    @property
    def format(self) -> Format:
        """The format of the data being fetched for this element."""

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def offset(self) -> int:
        """
        The offset in bytes of this element from the start of the
        corresponding chunk of vertex stream data.
        """

    @offset.setter
    def offset(self, arg: int, /) -> None: ...

    @property
    def buffer_slot_index(self) -> int:
        """The index of the vertex stream to fetch this element's data from."""

    @buffer_slot_index.setter
    def buffer_slot_index(self, arg: int, /) -> None: ...

InputElementDescDict = TypedDict("InputElementDescDict", {
    "semantic_name": str,
    "semantic_index": int,
    "format": Format,
    "offset": int,
    "buffer_slot_index": int
}, total = False)

InputElementDescParam = Union[InputElementDesc, InputElementDescDict]

class VertexStreamDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def stride(self) -> int:
        """The stride in bytes for this vertex stream."""

    @stride.setter
    def stride(self, arg: int, /) -> None: ...

    @property
    def slot_class(self) -> InputSlotClass:
        """Whether the stream contains per-vertex or per-instance data."""

    @slot_class.setter
    def slot_class(self, arg: InputSlotClass, /) -> None: ...

    @property
    def instance_data_step_rate(self) -> int:
        """How many instances to draw per chunk of data."""

    @instance_data_step_rate.setter
    def instance_data_step_rate(self, arg: int, /) -> None: ...

VertexStreamDescDict = TypedDict("VertexStreamDescDict", {
    "stride": int,
    "slot_class": InputSlotClass,
    "instance_data_step_rate": int
}, total = False)

VertexStreamDescParam = Union[VertexStreamDesc, VertexStreamDescDict]

class InputLayoutDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def input_elements(self) -> list[InputElementDesc]: ...

    @input_elements.setter
    def input_elements(self, arg: Sequence[InputElementDescParam], /) -> None: ...

    @property
    def vertex_streams(self) -> list[VertexStreamDesc]: ...

    @vertex_streams.setter
    def vertex_streams(self, arg: Sequence[VertexStreamDescParam], /) -> None: ...

InputLayoutDescDict = TypedDict("InputLayoutDescDict", {
    "input_elements": Sequence[InputElementDescParam],
    "vertex_streams": Sequence[VertexStreamDescParam]
}, total = False)

InputLayoutDescParam = Union[InputLayoutDesc, InputLayoutDescDict]

class InputLayout(DeviceChild):
    @property
    def desc(self) -> InputLayoutDesc: ...

class Pipeline(DeviceChild):
    pass

class ComputePipelineDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def program(self) -> ShaderProgram: ...

    @program.setter
    def program(self, arg: ShaderProgram, /) -> None: ...

    @property
    def label(self) -> str: ...

    @label.setter
    def label(self, arg: str, /) -> None: ...

ComputePipelineDescDict = TypedDict("ComputePipelineDescDict", {
    "program": ShaderProgram,
    "label": str
}, total = False)

ComputePipelineDescParam = Union[ComputePipelineDesc, ComputePipelineDescDict]

class ComputePipeline(Pipeline):
    @property
    def thread_group_size(self) -> math.uint3:
        """
        Thread group size. Used to determine the number of thread groups to
        dispatch.
        """

    @property
    def native_handle(self) -> NativeHandle:
        """Get the native pipeline handle."""

class RenderPipelineDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def program(self) -> ShaderProgram: ...

    @program.setter
    def program(self, arg: ShaderProgram, /) -> None: ...

    @property
    def input_layout(self) -> InputLayout: ...

    @input_layout.setter
    def input_layout(self, arg: InputLayout, /) -> None: ...

    @property
    def primitive_topology(self) -> PrimitiveTopology: ...

    @primitive_topology.setter
    def primitive_topology(self, arg: PrimitiveTopology, /) -> None: ...

    @property
    def targets(self) -> list[ColorTargetDesc]: ...

    @targets.setter
    def targets(self, arg: Sequence[ColorTargetDescParam], /) -> None: ...

    @property
    def depth_stencil(self) -> DepthStencilDesc: ...

    @depth_stencil.setter
    def depth_stencil(self, arg: DepthStencilDescParam, /) -> None: ...

    @property
    def rasterizer(self) -> RasterizerDesc: ...

    @rasterizer.setter
    def rasterizer(self, arg: RasterizerDescParam, /) -> None: ...

    @property
    def multisample(self) -> MultisampleDesc: ...

    @multisample.setter
    def multisample(self, arg: MultisampleDescParam, /) -> None: ...

    @property
    def label(self) -> str: ...

    @label.setter
    def label(self, arg: str, /) -> None: ...

RenderPipelineDescDict = TypedDict("RenderPipelineDescDict", {
    "program": ShaderProgram,
    "input_layout": InputLayout,
    "primitive_topology": PrimitiveTopology,
    "targets": Sequence[ColorTargetDescParam],
    "depth_stencil": DepthStencilDescParam,
    "rasterizer": RasterizerDescParam,
    "multisample": MultisampleDescParam,
    "label": str
}, total = False)

RenderPipelineDescParam = Union[RenderPipelineDesc, RenderPipelineDescDict]

class RenderPipeline(Pipeline):
    @property
    def native_handle(self) -> NativeHandle:
        """Get the native pipeline handle."""

class HitGroupDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @overload
    def __init__(self, hit_group_name: str, closest_hit_entry_point: str = '', any_hit_entry_point: str = '', intersection_entry_point: str = '') -> None: ...

    @property
    def hit_group_name(self) -> str: ...

    @hit_group_name.setter
    def hit_group_name(self, arg: str, /) -> None: ...

    @property
    def closest_hit_entry_point(self) -> str: ...

    @closest_hit_entry_point.setter
    def closest_hit_entry_point(self, arg: str, /) -> None: ...

    @property
    def any_hit_entry_point(self) -> str: ...

    @any_hit_entry_point.setter
    def any_hit_entry_point(self, arg: str, /) -> None: ...

    @property
    def intersection_entry_point(self) -> str: ...

    @intersection_entry_point.setter
    def intersection_entry_point(self, arg: str, /) -> None: ...

HitGroupDescDict = TypedDict("HitGroupDescDict", {
    "hit_group_name": str,
    "closest_hit_entry_point": str,
    "any_hit_entry_point": str,
    "intersection_entry_point": str
}, total = False)

HitGroupDescParam = Union[HitGroupDesc, HitGroupDescDict]

class RayTracingPipelineDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def program(self) -> ShaderProgram: ...

    @program.setter
    def program(self, arg: ShaderProgram, /) -> None: ...

    @property
    def hit_groups(self) -> list[HitGroupDesc]: ...

    @property
    def max_recursion(self) -> int: ...

    @max_recursion.setter
    def max_recursion(self, arg: int, /) -> None: ...

    @property
    def max_ray_payload_size(self) -> int: ...

    @max_ray_payload_size.setter
    def max_ray_payload_size(self, arg: int, /) -> None: ...

    @property
    def max_attribute_size(self) -> int: ...

    @max_attribute_size.setter
    def max_attribute_size(self, arg: int, /) -> None: ...

    @property
    def flags(self) -> RayTracingPipelineFlags: ...

    @flags.setter
    def flags(self, arg: RayTracingPipelineFlags, /) -> None: ...

    @property
    def label(self) -> str: ...

    @label.setter
    def label(self, arg: str, /) -> None: ...

RayTracingPipelineDescDict = TypedDict("RayTracingPipelineDescDict", {
    "program": ShaderProgram,
    "max_recursion": int,
    "max_ray_payload_size": int,
    "max_attribute_size": int,
    "flags": RayTracingPipelineFlags,
    "label": str
}, total = False)

RayTracingPipelineDescParam = Union[RayTracingPipelineDesc, RayTracingPipelineDescDict]

class RayTracingPipeline(Pipeline):
    @property
    def native_handle(self) -> NativeHandle:
        """Get the native pipeline handle."""

class BaseReflectionObject(Object):
    @property
    def is_valid(self) -> bool: ...

class DeclReflection(BaseReflectionObject):
    class Kind(enum.Enum):
        """Different kinds of decl slang can return."""

        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        unsupported = 0

        struct = 1

        func = 2

        module = 3

        generic = 4

        variable = 5

    @property
    def kind(self) -> DeclReflection.Kind:
        """Decl kind (struct/function/module/generic/variable)."""

    @property
    def children(self) -> DeclReflectionChildList:
        """List of children of this cursor."""

    @property
    def child_count(self) -> int:
        """Get number of children."""

    @property
    def name(self) -> str: ...

    def children_of_kind(self, kind: DeclReflection.Kind) -> DeclReflectionIndexedChildList:
        """List of children of this cursor of a specific kind."""

    def as_type(self) -> TypeReflection:
        """Get type corresponding to this decl ref."""

    def as_variable(self) -> VariableReflection:
        """Get variable corresponding to this decl ref."""

    def as_function(self) -> FunctionReflection:
        """Get function corresponding to this decl ref."""

    def find_children_of_kind(self, kind: DeclReflection.Kind, child_name: str) -> DeclReflectionIndexedChildList:
        """
        Finds all children of a specific kind with a given name. Note: Only
        supported for types, functions and variables.
        """

    def find_first_child_of_kind(self, kind: DeclReflection.Kind, child_name: str) -> DeclReflection:
        """
        Finds the first child of a specific kind with a given name. Note: Only
        supported for types, functions and variables.
        """

    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> DeclReflection: ...

    def __repr__(self) -> str: ...

class DeclReflectionChildList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> DeclReflection: ...

class DeclReflectionIndexedChildList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> DeclReflection: ...

class Attribute(BaseReflectionObject):
    @property
    def name(self) -> str: ...

    @property
    def argument_count(self) -> int: ...

    def argument_type(self, index: int) -> TypeReflection: ...

    def __repr__(self) -> str: ...

class TypeReflection(BaseReflectionObject):
    class Kind(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        none = 0

        struct = 1

        array = 2

        matrix = 3

        vector = 4

        scalar = 5

        constant_buffer = 6

        resource = 7

        sampler_state = 8

        texture_buffer = 9

        shader_storage_buffer = 10

        parameter_block = 11

        generic_type_parameter = 12

        interface = 13

        output_stream = 14

        specialized = 16

        feedback = 17

        pointer = 18

    class ScalarType(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        none = 0

        void = 1

        bool = 2

        int32 = 3

        uint32 = 4

        int64 = 5

        uint64 = 6

        float16 = 7

        float32 = 8

        float64 = 9

        int8 = 10

        uint8 = 11

        int16 = 12

        uint16 = 13

    class ResourceShape(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        none = 0

        texture_1d = 1

        texture_2d = 2

        texture_3d = 3

        texture_cube = 4

        texture_buffer = 5

        structured_buffer = 6

        byte_address_buffer = 7

        unknown = 8

        acceleration_structure = 9

        texture_feedback_flag = 16

        texture_array_flag = 64

        texture_multisample_flag = 128

        texture_1d_array = 65

        texture_2d_array = 66

        texture_cube_array = 68

        texture_2d_multisample = 130

        texture_2d_multisample_array = 194

    class ResourceAccess(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        none = 0

        read = 1

        read_write = 2

        raster_ordered = 3

        access_append = 4

        access_consume = 5

        access_write = 6

    class ParameterCategory(enum.Enum):
        _member_names_: list = ...

        _member_map_: dict = ...

        _value2member_map_: dict = ...

        none = 0

        mixed = 1

        constant_buffer = 2

        shader_resource = 3

        unordered_access = 4

        varying_input = 5

        varying_output = 6

        sampler_state = 7

        uniform = 8

        descriptor_table_slot = 9

        specialization_constant = 10

        push_constant_buffer = 11

        register_space = 12

        generic = 13

        ray_payload = 14

        hit_attributes = 15

        callable_payload = 16

        shader_record = 17

        existential_type_param = 18

        existential_object_param = 19

    @property
    def kind(self) -> TypeReflection.Kind: ...

    @property
    def name(self) -> str: ...

    @property
    def full_name(self) -> str: ...

    @property
    def fields(self) -> TypeReflectionFieldList: ...

    @property
    def element_count(self) -> int: ...

    @property
    def element_type(self) -> TypeReflection: ...

    @property
    def row_count(self) -> int: ...

    @property
    def col_count(self) -> int: ...

    @property
    def scalar_type(self) -> TypeReflection.ScalarType: ...

    @property
    def resource_result_type(self) -> TypeReflection: ...

    @property
    def resource_shape(self) -> TypeReflection.ResourceShape: ...

    @property
    def resource_access(self) -> TypeReflection.ResourceAccess: ...

    def get_user_attribute_count(self) -> int: ...

    def get_user_attribute_by_index(self, index: int) -> Attribute: ...

    def find_user_attribute_by_name(self, name: str) -> Attribute: ...

    def unwrap_array(self) -> TypeReflection: ...

    def __repr__(self) -> str: ...

class TypeReflectionFieldList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> VariableReflection: ...

class TypeLayoutReflection(BaseReflectionObject):
    @property
    def kind(self) -> TypeReflection.Kind: ...

    @property
    def name(self) -> str: ...

    @property
    def size(self) -> int: ...

    @property
    def stride(self) -> int: ...

    @property
    def alignment(self) -> int: ...

    @property
    def type(self) -> TypeReflection: ...

    @property
    def fields(self) -> TypeLayoutReflectionFieldList: ...

    @property
    def element_type_layout(self) -> TypeLayoutReflection: ...

    def unwrap_array(self) -> TypeLayoutReflection: ...

    def __repr__(self) -> str: ...

class TypeLayoutReflectionFieldList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> VariableLayoutReflection: ...

class FunctionReflection(BaseReflectionObject):
    @property
    def name(self) -> str:
        """Function name."""

    @property
    def return_type(self) -> TypeReflection:
        """Function return type."""

    @property
    def parameters(self) -> FunctionReflectionParameterList:
        """List of all function parameters."""

    def has_modifier(self, modifier: ModifierID) -> bool:
        """Check if the function has a given modifier (e.g. 'differentiable')."""

    def specialize_with_arg_types(self, types: Sequence[TypeReflection]) -> FunctionReflection:
        """
        Specialize a generic or interface based function with a set of
        concrete argument types. Calling on a none-generic/interface function
        will simply validate all argument types can be implicitly converted to
        their respective parameter types. Where a function contains multiple
        overloads, specialize will identify the correct overload based on the
        arguments.
        """

    @property
    def is_overloaded(self) -> bool:
        """
        Check whether this function object represents a group of overloaded
        functions, accessible via the overloads list.
        """

    @property
    def overloads(self) -> FunctionReflectionOverloadList:
        """List of all overloads of this function."""

class ModifierID(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    shared = 0

    nodiff = 1

    static = 2

    const = 3

    export = 4

    extern = 5

    differentiable = 6

    mutating = 7

    inn = 8

    out = 9

    inout = 10

class FunctionReflectionParameterList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> VariableReflection: ...

class FunctionReflectionOverloadList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> FunctionReflection: ...

class VariableReflection(BaseReflectionObject):
    @property
    def name(self) -> str:
        """Variable name."""

    @property
    def type(self) -> TypeReflection:
        """Variable type reflection."""

    def has_modifier(self, modifier: ModifierID) -> bool:
        """Check if variable has a given modifier (e.g. 'inout')."""

class VariableLayoutReflection(BaseReflectionObject):
    @property
    def name(self) -> str: ...

    @property
    def variable(self) -> VariableReflection: ...

    @property
    def type_layout(self) -> TypeLayoutReflection: ...

    @property
    def offset(self) -> int: ...

    def __repr__(self) -> str: ...

class EntryPointLayout(BaseReflectionObject):
    @property
    def name(self) -> str: ...

    @property
    def name_override(self) -> str: ...

    @property
    def stage(self) -> ShaderStage: ...

    @property
    def compute_thread_group_size(self) -> math.uint3: ...

    @property
    def parameters(self) -> EntryPointLayoutParameterList: ...

    def __repr__(self) -> str: ...

class EntryPointLayoutParameterList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> VariableLayoutReflection: ...

class ProgramLayout(BaseReflectionObject):
    class HashedString:
        @property
        def string(self) -> str: ...

        @property
        def hash(self) -> int: ...

    @property
    def globals_type_layout(self) -> TypeLayoutReflection: ...

    @property
    def globals_variable_layout(self) -> VariableLayoutReflection: ...

    @property
    def parameters(self) -> ProgramLayoutParameterList: ...

    @property
    def entry_points(self) -> ProgramLayoutEntryPointList: ...

    def find_type_by_name(self, name: str) -> TypeReflection:
        """
        Find a given type by name. Handles generic specilization if generic
        variable values are provided.
        """

    def find_function_by_name(self, name: str) -> FunctionReflection:
        """
        Find a given function by name. Handles generic specilization if
        generic variable values are provided.
        """

    def find_function_by_name_in_type(self, type: TypeReflection, name: str) -> FunctionReflection:
        """
        Find a given function in a type by name. Handles generic specilization
        if generic variable values are provided.
        """

    def get_type_layout(self, type: TypeReflection) -> TypeLayoutReflection:
        """Get corresponding type layout from a given type."""

    def is_sub_type(self, sub_type: TypeReflection, super_type: TypeReflection) -> bool:
        """
        Test whether a type is a sub type of another type. Handles both struct
        inheritance and interface implementation.
        """

    @property
    def hashed_strings(self) -> list[ProgramLayout.HashedString]: ...

    def __repr__(self) -> str: ...

class ProgramLayoutParameterList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> VariableLayoutReflection: ...

class ProgramLayoutEntryPointList:
    def __len__(self) -> int: ...

    def __getitem__(self, arg: int, /) -> EntryPointLayout: ...

class ReflectionCursor:
    def __init__(self, shader_program: ShaderProgram) -> None: ...

    def is_valid(self) -> bool: ...

    def find_field(self, name: str) -> ReflectionCursor: ...

    def find_element(self, index: int) -> ReflectionCursor: ...

    def has_field(self, name: str) -> bool: ...

    def has_element(self, index: int) -> bool: ...

    @property
    def type_layout(self) -> TypeLayoutReflection: ...

    @property
    def type(self) -> TypeReflection: ...

    @overload
    def __getitem__(self, arg: str, /) -> ReflectionCursor: ...

    @overload
    def __getitem__(self, arg: int, /) -> None: ...

    def __getattr__(self, arg: str, /) -> ReflectionCursor: ...

    def __repr__(self) -> str: ...

class TypeConformance:
    """
    Type conformance entry. Type conformances are used to narrow the set
    of types supported by a slang interface. They can be specified on an
    entry point to omit generating code for types that do not conform.
    """

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, interface_name: str, type_name: str, id: int = -1) -> None: ...

    @overload
    def __init__(self, arg: tuple, /) -> None: ...

    @property
    def interface_name(self) -> str:
        """Name of the interface."""

    @interface_name.setter
    def interface_name(self, arg: str, /) -> None: ...

    @property
    def type_name(self) -> str:
        """Name of the concrete type."""

    @type_name.setter
    def type_name(self, arg: str, /) -> None: ...

    @property
    def id(self) -> int:
        """Unique id per type for an interface (optional)."""

    @id.setter
    def id(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

class SlangCompileError(Exception):
    pass

class SlangMatrixLayout(enum.Enum):
    _member_names_: list = ['row_major', 'column_major']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    row_major = 1

    column_major = 2

class SlangFloatingPointMode(enum.Enum):
    _member_names_: list = ['default', 'fast', 'precise']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    default = 0

    fast = 1

    precise = 2

class SlangDebugInfoLevel(enum.Enum):
    _member_names_: list = ['none', 'minimal', 'standard', 'maximal']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    minimal = 1

    standard = 2

    maximal = 3

class SlangOptimizationLevel(enum.Enum):
    _member_names_: list = ['none', 'default', 'high', 'maximal']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    default = 1

    high = 2

    maximal = 3

class SlangCompilerOptions:
    """Slang compiler options. Can be set when creating a Slang session."""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def include_paths(self) -> list[pathlib.Path]:
        """
        Specifies a list of include paths to be used when resolving
        module/include paths.
        """

    @include_paths.setter
    def include_paths(self, arg: Sequence[str | os.PathLike], /) -> None: ...

    @property
    def defines(self) -> dict[str, str]:
        """Specifies a list of preprocessor defines."""

    @defines.setter
    def defines(self, arg: Mapping[str, str], /) -> None: ...

    @property
    def shader_model(self) -> ShaderModel:
        """
        Specifies the shader model to use. Defaults to latest available on the
        device.
        """

    @shader_model.setter
    def shader_model(self, arg: ShaderModel, /) -> None: ...

    @property
    def matrix_layout(self) -> SlangMatrixLayout:
        """Specifies the matrix layout. Defaults to row-major."""

    @matrix_layout.setter
    def matrix_layout(self, arg: SlangMatrixLayout, /) -> None: ...

    @property
    def enable_warnings(self) -> list[str]:
        """Specifies a list of warnings to enable (warning codes or names)."""

    @enable_warnings.setter
    def enable_warnings(self, arg: Sequence[str], /) -> None: ...

    @property
    def disable_warnings(self) -> list[str]:
        """Specifies a list of warnings to disable (warning codes or names)."""

    @disable_warnings.setter
    def disable_warnings(self, arg: Sequence[str], /) -> None: ...

    @property
    def warnings_as_errors(self) -> list[str]:
        """
        Specifies a list of warnings to be treated as errors (warning codes or
        names, or "all" to indicate all warnings).
        """

    @warnings_as_errors.setter
    def warnings_as_errors(self, arg: Sequence[str], /) -> None: ...

    @property
    def report_downstream_time(self) -> bool:
        """Turn on/off downstream compilation time report."""

    @report_downstream_time.setter
    def report_downstream_time(self, arg: bool, /) -> None: ...

    @property
    def report_perf_benchmark(self) -> bool:
        """
        Turn on/off reporting of time spend in different parts of the
        compiler.
        """

    @report_perf_benchmark.setter
    def report_perf_benchmark(self, arg: bool, /) -> None: ...

    @property
    def skip_spirv_validation(self) -> bool:
        """
        Specifies whether or not to skip the validation step after emitting
        SPIRV.
        """

    @skip_spirv_validation.setter
    def skip_spirv_validation(self, arg: bool, /) -> None: ...

    @property
    def floating_point_mode(self) -> SlangFloatingPointMode:
        """Specifies the floating point mode."""

    @floating_point_mode.setter
    def floating_point_mode(self, arg: SlangFloatingPointMode, /) -> None: ...

    @property
    def debug_info(self) -> SlangDebugInfoLevel:
        """
        Specifies the level of debug information to include in the generated
        code.
        """

    @debug_info.setter
    def debug_info(self, arg: SlangDebugInfoLevel, /) -> None: ...

    @property
    def optimization(self) -> SlangOptimizationLevel:
        """Specifies the optimization level."""

    @optimization.setter
    def optimization(self, arg: SlangOptimizationLevel, /) -> None: ...

    @property
    def downstream_args(self) -> list[str]:
        """
        Specifies a list of additional arguments to be passed to the
        downstream compiler.
        """

    @downstream_args.setter
    def downstream_args(self, arg: Sequence[str], /) -> None: ...

    @property
    def dump_intermediates(self) -> bool:
        """When set will dump the intermediate source output."""

    @dump_intermediates.setter
    def dump_intermediates(self, arg: bool, /) -> None: ...

    @property
    def dump_intermediates_prefix(self) -> str:
        """The file name prefix for the intermediate source output."""

    @dump_intermediates_prefix.setter
    def dump_intermediates_prefix(self, arg: str, /) -> None: ...

SlangCompilerOptionsDict = TypedDict("SlangCompilerOptionsDict", {
    "include_paths": Sequence[str | os.PathLike],
    "defines": Mapping[str, str],
    "shader_model": ShaderModel,
    "matrix_layout": SlangMatrixLayout,
    "enable_warnings": Sequence[str],
    "disable_warnings": Sequence[str],
    "warnings_as_errors": Sequence[str],
    "report_downstream_time": bool,
    "report_perf_benchmark": bool,
    "skip_spirv_validation": bool,
    "floating_point_mode": SlangFloatingPointMode,
    "debug_info": SlangDebugInfoLevel,
    "optimization": SlangOptimizationLevel,
    "downstream_args": Sequence[str],
    "dump_intermediates": bool,
    "dump_intermediates_prefix": str
}, total = False)

SlangCompilerOptionsParam = Union[SlangCompilerOptions, SlangCompilerOptionsDict]

class SlangLinkOptions:
    """
    Slang link options. These can optionally be set when linking a shader
    program.
    """

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def floating_point_mode(self) -> Optional[SlangFloatingPointMode]:
        """Specifies the floating point mode."""

    @floating_point_mode.setter
    def floating_point_mode(self, arg: SlangFloatingPointMode, /) -> None: ...

    @property
    def debug_info(self) -> Optional[SlangDebugInfoLevel]:
        """
        Specifies the level of debug information to include in the generated
        code.
        """

    @debug_info.setter
    def debug_info(self, arg: SlangDebugInfoLevel, /) -> None: ...

    @property
    def optimization(self) -> Optional[SlangOptimizationLevel]:
        """Specifies the optimization level."""

    @optimization.setter
    def optimization(self, arg: SlangOptimizationLevel, /) -> None: ...

    @property
    def downstream_args(self) -> Optional[list[str]]:
        """
        Specifies a list of additional arguments to be passed to the
        downstream compiler.
        """

    @downstream_args.setter
    def downstream_args(self, arg: Sequence[str], /) -> None: ...

    @property
    def dump_intermediates(self) -> Optional[bool]:
        """When set will dump the intermediate source output."""

    @dump_intermediates.setter
    def dump_intermediates(self, arg: bool, /) -> None: ...

    @property
    def dump_intermediates_prefix(self) -> Optional[str]:
        """The file name prefix for the intermediate source output."""

    @dump_intermediates_prefix.setter
    def dump_intermediates_prefix(self, arg: str, /) -> None: ...

SlangLinkOptionsDict = TypedDict("SlangLinkOptionsDict", {
    "floating_point_mode": SlangFloatingPointMode,
    "debug_info": SlangDebugInfoLevel,
    "optimization": SlangOptimizationLevel,
    "downstream_args": Sequence[str],
    "dump_intermediates": bool,
    "dump_intermediates_prefix": str
}, total = False)

SlangLinkOptionsParam = Union[SlangLinkOptions, SlangLinkOptionsDict]

class SlangSessionDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def compiler_options(self) -> SlangCompilerOptions: ...

    @compiler_options.setter
    def compiler_options(self, arg: SlangCompilerOptionsParam, /) -> None: ...

    @property
    def add_default_include_paths(self) -> bool: ...

    @add_default_include_paths.setter
    def add_default_include_paths(self, arg: bool, /) -> None: ...

    @property
    def cache_path(self) -> Optional[pathlib.Path]: ...

    @cache_path.setter
    def cache_path(self, arg: str | os.PathLike, /) -> None: ...

SlangSessionDescDict = TypedDict("SlangSessionDescDict", {
    "compiler_options": SlangCompilerOptionsParam,
    "add_default_include_paths": bool,
    "cache_path": str | os.PathLike
}, total = False)

SlangSessionDescParam = Union[SlangSessionDesc, SlangSessionDescDict]

class SlangSession(Object):
    @property
    def device(self) -> Device: ...

    @property
    def desc(self) -> SlangSessionDesc: ...

    def load_module(self, module_name: str) -> SlangModule:
        """Load a module by name."""

    def load_module_from_source(self, module_name: str, source: str, path: Optional[str | os.PathLike] = None) -> SlangModule:
        """Load a module from string source code."""

    def link_program(self, modules: Sequence[SlangModule], entry_points: Sequence[SlangEntryPoint], link_options: Optional[SlangLinkOptionsParam] = None) -> ShaderProgram:
        """Link a program with a set of modules and entry points."""

    def load_program(self, module_name: str, entry_point_names: Sequence[str], additional_source: Optional[str] = None, link_options: Optional[SlangLinkOptionsParam] = None) -> ShaderProgram:
        """
        Load a program from a given module with a set of entry points.
        Internally this simply wraps link_program without requiring the user
        to explicitly load modules.
        """

    def load_source(self, module_name: str) -> str:
        """Load the source code for a given module."""

class SlangModule(Object):
    @property
    def session(self) -> SlangSession:
        """The session from which this module was built."""

    @property
    def name(self) -> str:
        """Module name."""

    @property
    def path(self) -> pathlib.Path:
        """
        Module source path. This can be empty if the module was generated from
        a string.
        """

    @property
    def layout(self) -> ProgramLayout: ...

    @property
    def entry_points(self) -> list[SlangEntryPoint]:
        """Build and return vector of all current entry points in the module."""

    @property
    def module_decl(self) -> DeclReflection:
        """Get root decl ref for this module"""

    def entry_point(self, name: str, type_conformances: Sequence[TypeConformance] = []) -> SlangEntryPoint:
        """Get an entry point, optionally applying type conformances to it."""

class SlangEntryPoint(Object):
    @property
    def name(self) -> str: ...

    @property
    def stage(self) -> ShaderStage: ...

    @property
    def layout(self) -> EntryPointLayout: ...

    def rename(self, new_name: str) -> SlangEntryPoint: ...

    def with_name(self, new_name: str) -> SlangEntryPoint:
        """Returns a copy of the entry point with a new name."""

class ShaderProgram(DeviceChild):
    @property
    def layout(self) -> ProgramLayout: ...

    @property
    def reflection(self) -> ReflectionCursor: ...

class AccelerationStructureHandle:
    """Acceleration structure handle."""

    def __init__(self) -> None: ...

class AccelerationStructureGeometryFlags(enum.IntFlag):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    opaque = 1

    no_duplicate_any_hit_invocation = 2

class AccelerationStructureInstanceFlags(enum.IntFlag):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    triangle_facing_cull_disable = 1

    triangle_front_counter_clockwise = 2

    force_opaque = 4

    no_opaque = 8

class AccelerationStructureInstanceDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def transform(self) -> math.float3x4: ...

    @transform.setter
    def transform(self, arg: float3x4param, /) -> None: ...

    @property
    def instance_id(self) -> int: ...

    @instance_id.setter
    def instance_id(self, arg: int, /) -> None: ...

    @property
    def instance_mask(self) -> int: ...

    @instance_mask.setter
    def instance_mask(self, arg: int, /) -> None: ...

    @property
    def instance_contribution_to_hit_group_index(self) -> int: ...

    @instance_contribution_to_hit_group_index.setter
    def instance_contribution_to_hit_group_index(self, arg: int, /) -> None: ...

    @property
    def flags(self) -> AccelerationStructureInstanceFlags: ...

    @flags.setter
    def flags(self, arg: AccelerationStructureInstanceFlags, /) -> None: ...

    @property
    def acceleration_structure(self) -> AccelerationStructureHandle: ...

    @acceleration_structure.setter
    def acceleration_structure(self, arg: AccelerationStructureHandle, /) -> None: ...

    def to_numpy(self) -> Annotated[NDArray, dict(dtype='uint8', shape=(64), writable=False)]: ...

AccelerationStructureInstanceDescDict = TypedDict("AccelerationStructureInstanceDescDict", {
    "transform": float3x4param,
    "instance_id": int,
    "instance_mask": int,
    "instance_contribution_to_hit_group_index": int,
    "flags": AccelerationStructureInstanceFlags,
    "acceleration_structure": AccelerationStructureHandle
}, total = False)

AccelerationStructureInstanceDescParam = Union[AccelerationStructureInstanceDesc, AccelerationStructureInstanceDescDict]

class AccelerationStructureBuildInputInstances:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def instance_buffer(self) -> BufferOffsetPair: ...

    @instance_buffer.setter
    def instance_buffer(self, arg: BufferOffsetPairParam, /) -> None: ...

    @property
    def instance_stride(self) -> int: ...

    @instance_stride.setter
    def instance_stride(self, arg: int, /) -> None: ...

    @property
    def instance_count(self) -> int: ...

    @instance_count.setter
    def instance_count(self, arg: int, /) -> None: ...

AccelerationStructureBuildInputInstancesDict = TypedDict("AccelerationStructureBuildInputInstancesDict", {
    "instance_buffer": BufferOffsetPairParam,
    "instance_stride": int,
    "instance_count": int
}, total = False)

AccelerationStructureBuildInputInstancesParam = Union[AccelerationStructureBuildInputInstances, AccelerationStructureBuildInputInstancesDict]

class AccelerationStructureBuildInputTriangles:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def vertex_buffers(self) -> list[BufferOffsetPair]: ...

    @vertex_buffers.setter
    def vertex_buffers(self, arg: Sequence[BufferOffsetPairParam], /) -> None: ...

    @property
    def vertex_format(self) -> Format: ...

    @vertex_format.setter
    def vertex_format(self, arg: Format, /) -> None: ...

    @property
    def vertex_count(self) -> int: ...

    @vertex_count.setter
    def vertex_count(self, arg: int, /) -> None: ...

    @property
    def vertex_stride(self) -> int: ...

    @vertex_stride.setter
    def vertex_stride(self, arg: int, /) -> None: ...

    @property
    def index_buffer(self) -> BufferOffsetPair: ...

    @index_buffer.setter
    def index_buffer(self, arg: BufferOffsetPairParam, /) -> None: ...

    @property
    def index_format(self) -> IndexFormat: ...

    @index_format.setter
    def index_format(self, arg: IndexFormat, /) -> None: ...

    @property
    def index_count(self) -> int: ...

    @index_count.setter
    def index_count(self, arg: int, /) -> None: ...

    @property
    def pre_transform_buffer(self) -> BufferOffsetPair: ...

    @pre_transform_buffer.setter
    def pre_transform_buffer(self, arg: BufferOffsetPairParam, /) -> None: ...

    @property
    def flags(self) -> AccelerationStructureGeometryFlags: ...

    @flags.setter
    def flags(self, arg: AccelerationStructureGeometryFlags, /) -> None: ...

AccelerationStructureBuildInputTrianglesDict = TypedDict("AccelerationStructureBuildInputTrianglesDict", {
    "vertex_buffers": Sequence[BufferOffsetPairParam],
    "vertex_format": Format,
    "vertex_count": int,
    "vertex_stride": int,
    "index_buffer": BufferOffsetPairParam,
    "index_format": IndexFormat,
    "index_count": int,
    "pre_transform_buffer": BufferOffsetPairParam,
    "flags": AccelerationStructureGeometryFlags
}, total = False)

AccelerationStructureBuildInputTrianglesParam = Union[AccelerationStructureBuildInputTriangles, AccelerationStructureBuildInputTrianglesDict]

class AccelerationStructureBuildInputProceduralPrimitives:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def aabb_buffers(self) -> list[BufferOffsetPair]: ...

    @aabb_buffers.setter
    def aabb_buffers(self, arg: Sequence[BufferOffsetPairParam], /) -> None: ...

    @property
    def aabb_stride(self) -> int: ...

    @aabb_stride.setter
    def aabb_stride(self, arg: int, /) -> None: ...

    @property
    def primitive_count(self) -> int: ...

    @primitive_count.setter
    def primitive_count(self, arg: int, /) -> None: ...

    @property
    def flags(self) -> AccelerationStructureGeometryFlags: ...

    @flags.setter
    def flags(self, arg: AccelerationStructureGeometryFlags, /) -> None: ...

AccelerationStructureBuildInputProceduralPrimitivesDict = TypedDict("AccelerationStructureBuildInputProceduralPrimitivesDict", {
    "aabb_buffers": Sequence[BufferOffsetPairParam],
    "aabb_stride": int,
    "primitive_count": int,
    "flags": AccelerationStructureGeometryFlags
}, total = False)

AccelerationStructureBuildInputProceduralPrimitivesParam = Union[AccelerationStructureBuildInputProceduralPrimitives, AccelerationStructureBuildInputProceduralPrimitivesDict]

class AccelerationStructureBuildInputMotionOptions:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def key_count(self) -> int: ...

    @key_count.setter
    def key_count(self, arg: int, /) -> None: ...

    @property
    def time_start(self) -> float: ...

    @time_start.setter
    def time_start(self, arg: float, /) -> None: ...

    @property
    def time_end(self) -> float: ...

    @time_end.setter
    def time_end(self, arg: float, /) -> None: ...

AccelerationStructureBuildInputMotionOptionsDict = TypedDict("AccelerationStructureBuildInputMotionOptionsDict", {
    "key_count": int,
    "time_start": float,
    "time_end": float
}, total = False)

AccelerationStructureBuildInputMotionOptionsParam = Union[AccelerationStructureBuildInputMotionOptions, AccelerationStructureBuildInputMotionOptionsDict]

class AccelerationStructureBuildMode(enum.Enum):
    _member_names_: list = ['build', 'update']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    build = 0

    update = 1

class AccelerationStructureBuildFlags(enum.IntFlag):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    none = 0

    allow_update = 1

    allow_compaction = 2

    prefer_fast_trace = 4

    prefer_fast_build = 8

    minimize_memory = 16

class AccelerationStructureBuildDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def inputs(self) -> list[Union[AccelerationStructureBuildInputInstances, AccelerationStructureBuildInputTriangles, AccelerationStructureBuildInputProceduralPrimitives]]:
        """List of build inputs. All inputs must be of the same type."""

    @inputs.setter
    def inputs(self, arg: Sequence[Union[AccelerationStructureBuildInputInstancesParam, AccelerationStructureBuildInputTrianglesParam, AccelerationStructureBuildInputProceduralPrimitivesParam]], /) -> None: ...

    @property
    def motion_options(self) -> AccelerationStructureBuildInputMotionOptions: ...

    @motion_options.setter
    def motion_options(self, arg: AccelerationStructureBuildInputMotionOptionsParam, /) -> None: ...

    @property
    def mode(self) -> AccelerationStructureBuildMode: ...

    @mode.setter
    def mode(self, arg: AccelerationStructureBuildMode, /) -> None: ...

    @property
    def flags(self) -> AccelerationStructureBuildFlags: ...

    @flags.setter
    def flags(self, arg: AccelerationStructureBuildFlags, /) -> None: ...

AccelerationStructureBuildDescDict = TypedDict("AccelerationStructureBuildDescDict", {
    "inputs": Sequence[Union[AccelerationStructureBuildInputInstancesParam, AccelerationStructureBuildInputTrianglesParam, AccelerationStructureBuildInputProceduralPrimitivesParam]],
    "motion_options": AccelerationStructureBuildInputMotionOptionsParam,
    "mode": AccelerationStructureBuildMode,
    "flags": AccelerationStructureBuildFlags
}, total = False)

AccelerationStructureBuildDescParam = Union[AccelerationStructureBuildDesc, AccelerationStructureBuildDescDict]

class AccelerationStructureCopyMode(enum.Enum):
    _member_names_: list = ['clone', 'compact']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    clone = 0

    compact = 1

class AccelerationStructureSizes:
    @property
    def acceleration_structure_size(self) -> int: ...

    @acceleration_structure_size.setter
    def acceleration_structure_size(self, arg: int, /) -> None: ...

    @property
    def scratch_size(self) -> int: ...

    @scratch_size.setter
    def scratch_size(self, arg: int, /) -> None: ...

    @property
    def update_scratch_size(self) -> int: ...

    @update_scratch_size.setter
    def update_scratch_size(self, arg: int, /) -> None: ...

class AccelerationStructureQueryDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def query_type(self) -> QueryType: ...

    @query_type.setter
    def query_type(self, arg: QueryType, /) -> None: ...

    @property
    def query_pool(self) -> QueryPool: ...

    @query_pool.setter
    def query_pool(self, arg: QueryPool, /) -> None: ...

    @property
    def first_query_index(self) -> int: ...

    @first_query_index.setter
    def first_query_index(self, arg: int, /) -> None: ...

AccelerationStructureQueryDescDict = TypedDict("AccelerationStructureQueryDescDict", {
    "query_type": QueryType,
    "query_pool": QueryPool,
    "first_query_index": int
}, total = False)

AccelerationStructureQueryDescParam = Union[AccelerationStructureQueryDesc, AccelerationStructureQueryDescDict]

class AccelerationStructureDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def size(self) -> int: ...

    @size.setter
    def size(self, arg: int, /) -> None: ...

    @property
    def label(self) -> str: ...

    @label.setter
    def label(self, arg: str, /) -> None: ...

AccelerationStructureDescDict = TypedDict("AccelerationStructureDescDict", {
    "size": int,
    "label": str
}, total = False)

AccelerationStructureDescParam = Union[AccelerationStructureDesc, AccelerationStructureDescDict]

class AccelerationStructure(DeviceChild):
    @property
    def desc(self) -> AccelerationStructureDesc: ...

    @property
    def handle(self) -> AccelerationStructureHandle: ...

class AccelerationStructureInstanceList(DeviceChild):
    @property
    def size(self) -> int: ...

    @property
    def instance_stride(self) -> int: ...

    def resize(self, size: int) -> None: ...

    @overload
    def write(self, index: int, instance: AccelerationStructureInstanceDescParam) -> None: ...

    @overload
    def write(self, index: int, instances: Sequence[AccelerationStructureInstanceDescParam]) -> None: ...

    def buffer(self) -> Buffer: ...

    def build_input_instances(self) -> AccelerationStructureBuildInputInstances: ...

class ShaderTableDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def program(self) -> ShaderProgram: ...

    @program.setter
    def program(self, arg: ShaderProgram, /) -> None: ...

    @property
    def ray_gen_entry_points(self) -> list[str]: ...

    @ray_gen_entry_points.setter
    def ray_gen_entry_points(self, arg: Sequence[str], /) -> None: ...

    @property
    def miss_entry_points(self) -> list[str]: ...

    @miss_entry_points.setter
    def miss_entry_points(self, arg: Sequence[str], /) -> None: ...

    @property
    def hit_group_names(self) -> list[str]: ...

    @hit_group_names.setter
    def hit_group_names(self, arg: Sequence[str], /) -> None: ...

    @property
    def callable_entry_points(self) -> list[str]: ...

    @callable_entry_points.setter
    def callable_entry_points(self, arg: Sequence[str], /) -> None: ...

ShaderTableDescDict = TypedDict("ShaderTableDescDict", {
    "program": ShaderProgram,
    "ray_gen_entry_points": Sequence[str],
    "miss_entry_points": Sequence[str],
    "hit_group_names": Sequence[str],
    "callable_entry_points": Sequence[str]
}, total = False)

ShaderTableDescParam = Union[ShaderTableDesc, ShaderTableDescDict]

class ShaderTable(DeviceChild):
    pass

class BufferElementCursor:
    """
    Represents a single element of a given type in a block of memory, and
    provides read/write tools to access its members via reflection.
    """

    @property
    def _offset(self) -> int: ...

    @overload
    def set_data(self, data: Annotated[ArrayLike, dict(device='cpu')]) -> None: ...

    @overload
    def set_data(self, data: Annotated[ArrayLike, dict(device='cpu')]) -> None: ...

    def __dir__(self) -> list[str]: ...

    def __repr__(self) -> str: ...

    def is_valid(self) -> bool:
        """N/A"""

    def find_field(self, name: str) -> BufferElementCursor:
        """N/A"""

    def find_element(self, index: int) -> BufferElementCursor:
        """N/A"""

    def has_field(self, name: str) -> bool:
        """N/A"""

    def has_element(self, index: int) -> bool:
        """N/A"""

    @overload
    def __getitem__(self, arg: str, /) -> BufferElementCursor: ...

    @overload
    def __getitem__(self, arg: int, /) -> BufferElementCursor: ...

    def __getattr__(self, arg: str, /) -> BufferElementCursor: ...

    def read(self) -> object:
        """N/A"""

    def __setattr__(self, name: str, val: object) -> None:
        """N/A"""

    @overload
    def __setitem__(self, index: str, val: object) -> None:
        """N/A"""

    @overload
    def __setitem__(self, index: int, val: object) -> None: ...

    def write(self, val: object) -> None:
        """N/A"""

class BufferCursor(Object):
    """
    Represents a list of elements in a block of memory, and provides
    simple interface to get a BufferElementCursor for each one. As this
    can be the owner of its data, it is a ref counted object that elements
    refer to.
    """

    @overload
    def __init__(self, device_type: DeviceType, element_layout: TypeLayoutReflection, size: int) -> None: ...

    @overload
    def __init__(self, element_layout: TypeLayoutReflection, buffer_resource: Buffer, load_before_write: bool = True) -> None: ...

    @overload
    def __init__(self, element_layout: TypeLayoutReflection, buffer_resource: Buffer, size: int, offset: int, load_before_write: bool = True) -> None: ...

    @property
    def element_type_layout(self) -> TypeLayoutReflection:
        """Get type layout of an element of the cursor."""

    @property
    def element_type(self) -> TypeReflection:
        """Get type of an element of the cursor."""

    def find_element(self, index: int) -> BufferElementCursor:
        """Get element at a given index."""

    @property
    def element_count(self) -> int:
        """Number of elements in the buffer."""

    @property
    def element_size(self) -> int:
        """Size of element."""

    @property
    def element_stride(self) -> int:
        """Stride of elements."""

    @property
    def size(self) -> int:
        """Size of whole buffer."""

    @property
    def is_loaded(self) -> bool:
        """Check if internal buffer exists."""

    def load(self) -> None:
        """In case of GPU only buffers, loads all data from GPU."""

    def apply(self) -> None:
        """In case of GPU only buffers, pushes all data to the GPU."""

    @property
    def resource(self) -> Buffer:
        """Get the resource this cursor represents (if any)."""

    def __getitem__(self, arg: int, /) -> BufferElementCursor: ...

    def __len__(self) -> int: ...

    def write_from_numpy(self, data: object, unchecked_copy: bool = True) -> None: ...

    def to_numpy(self) -> NDArray: ...

    def copy_from_numpy(self, data: ArrayLike) -> None: ...

    def __dir__(self) -> list[str]: ...

    def __getattr__(self, arg: str, /) -> object: ...

class ShaderObject(Object):
    pass

class ShaderOffset:
    """
    Represents the offset of a shader variable relative to its enclosing
    type/buffer/block.

    A `ShaderOffset` can be used to store the offset of a shader variable
    that might use ordinary/uniform data, resources like
    textures/buffers/samplers, or some combination.

    A `ShaderOffset` can also encode an invalid offset, to indicate that a
    particular shader variable is not present.
    """

    @property
    def uniform_offset(self) -> int: ...

    @property
    def binding_range_index(self) -> int: ...

    @property
    def binding_array_index(self) -> int: ...

    def is_valid(self) -> bool:
        """Check whether this offset is valid."""

class ShaderCursor:
    def __init__(self, shader_object: ShaderObject) -> None: ...

    @property
    def _offset(self) -> ShaderOffset: ...

    def dereference(self) -> ShaderCursor: ...

    def find_entry_point(self, index: int) -> ShaderCursor: ...

    def is_valid(self) -> bool:
        """N/A"""

    def find_field(self, name: str) -> ShaderCursor:
        """N/A"""

    def find_element(self, index: int) -> ShaderCursor:
        """N/A"""

    def has_field(self, name: str) -> bool:
        """N/A"""

    def has_element(self, index: int) -> bool:
        """N/A"""

    @overload
    def __getitem__(self, arg: str, /) -> ShaderCursor: ...

    @overload
    def __getitem__(self, arg: int, /) -> ShaderCursor: ...

    def __getattr__(self, arg: str, /) -> ShaderCursor: ...

    def __setattr__(self, name: str, val: object) -> None:
        """N/A"""

    @overload
    def __setitem__(self, index: str, val: object) -> None:
        """N/A"""

    @overload
    def __setitem__(self, index: int, val: object) -> None: ...

    def set_data(self, data: Annotated[ArrayLike, dict(device='cpu')]) -> None: ...

    def write(self, val: object) -> None:
        """N/A"""

class SurfaceInfo:
    @property
    def preferred_format(self) -> Format:
        """Preferred format for the surface."""

    @property
    def supported_usage(self) -> TextureUsage:
        """Supported texture usages."""

    @property
    def formats(self) -> list[Format]:
        """Supported texture formats."""

class SurfaceConfig:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def format(self) -> Format:
        """Surface texture format."""

    @format.setter
    def format(self, arg: Format, /) -> None: ...

    @property
    def usage(self) -> TextureUsage:
        """Surface texture usage."""

    @usage.setter
    def usage(self, arg: TextureUsage, /) -> None: ...

    @property
    def width(self) -> int:
        """Surface texture width."""

    @width.setter
    def width(self, arg: int, /) -> None: ...

    @property
    def height(self) -> int:
        """Surface texture height."""

    @height.setter
    def height(self, arg: int, /) -> None: ...

    @property
    def desired_image_count(self) -> int:
        """Desired number of images."""

    @desired_image_count.setter
    def desired_image_count(self, arg: int, /) -> None: ...

    @property
    def vsync(self) -> bool:
        """Enable/disable vertical synchronization."""

    @vsync.setter
    def vsync(self, arg: bool, /) -> None: ...

SurfaceConfigDict = TypedDict("SurfaceConfigDict", {
    "format": Format,
    "usage": TextureUsage,
    "width": int,
    "height": int,
    "desired_image_count": int,
    "vsync": bool
}, total = False)

SurfaceConfigParam = Union[SurfaceConfig, SurfaceConfigDict]

class Surface(Object):
    @property
    def info(self) -> SurfaceInfo:
        """Returns the surface info."""

    @property
    def config(self) -> Optional[SurfaceConfig]:
        """Returns the surface config."""

    @overload
    def configure(self, width: int, height: int, format: Format = Format.undefined, usage: TextureUsage = TextureUsage.none, desired_image_count: int = 3, vsync: bool = True) -> None:
        """Configure the surface."""

    @overload
    def configure(self, config: SurfaceConfigParam) -> None: ...

    def unconfigure(self) -> None:
        """Unconfigure the surface."""

    def acquire_next_image(self) -> Texture:
        """Acquries the next surface image."""

    def present(self) -> None:
        """Present the previously acquire image."""

class RenderState:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def stencil_ref(self) -> int: ...

    @stencil_ref.setter
    def stencil_ref(self, arg: int, /) -> None: ...

    @property
    def viewports(self) -> list[Viewport]: ...

    @viewports.setter
    def viewports(self, arg: Sequence[ViewportParam], /) -> None: ...

    @property
    def scissor_rects(self) -> list[ScissorRect]: ...

    @scissor_rects.setter
    def scissor_rects(self, arg: Sequence[ScissorRectParam], /) -> None: ...

    @property
    def vertex_buffers(self) -> list[BufferOffsetPair]: ...

    @vertex_buffers.setter
    def vertex_buffers(self, arg: Sequence[BufferOffsetPairParam], /) -> None: ...

    @property
    def index_buffer(self) -> BufferOffsetPair: ...

    @index_buffer.setter
    def index_buffer(self, arg: BufferOffsetPairParam, /) -> None: ...

    @property
    def index_format(self) -> IndexFormat: ...

    @index_format.setter
    def index_format(self, arg: IndexFormat, /) -> None: ...

RenderStateDict = TypedDict("RenderStateDict", {
    "stencil_ref": int,
    "viewports": Sequence[ViewportParam],
    "scissor_rects": Sequence[ScissorRectParam],
    "vertex_buffers": Sequence[BufferOffsetPairParam],
    "index_buffer": BufferOffsetPairParam,
    "index_format": IndexFormat
}, total = False)

RenderStateParam = Union[RenderState, RenderStateDict]

class RenderPassColorAttachment:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def view(self) -> TextureView: ...

    @view.setter
    def view(self, arg: TextureView, /) -> None: ...

    @property
    def resolve_target(self) -> TextureView: ...

    @resolve_target.setter
    def resolve_target(self, arg: TextureView, /) -> None: ...

    @property
    def load_op(self) -> LoadOp: ...

    @load_op.setter
    def load_op(self, arg: LoadOp, /) -> None: ...

    @property
    def store_op(self) -> StoreOp: ...

    @store_op.setter
    def store_op(self, arg: StoreOp, /) -> None: ...

    @property
    def clear_value(self) -> math.float4: ...

    @clear_value.setter
    def clear_value(self, arg: float4param, /) -> None: ...

RenderPassColorAttachmentDict = TypedDict("RenderPassColorAttachmentDict", {
    "view": TextureView,
    "resolve_target": TextureView,
    "load_op": LoadOp,
    "store_op": StoreOp,
    "clear_value": float4param
}, total = False)

RenderPassColorAttachmentParam = Union[RenderPassColorAttachment, RenderPassColorAttachmentDict]

class RenderPassDepthStencilAttachment:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def view(self) -> TextureView: ...

    @view.setter
    def view(self, arg: TextureView, /) -> None: ...

    @property
    def depth_load_op(self) -> LoadOp: ...

    @depth_load_op.setter
    def depth_load_op(self, arg: LoadOp, /) -> None: ...

    @property
    def depth_store_op(self) -> StoreOp: ...

    @depth_store_op.setter
    def depth_store_op(self, arg: StoreOp, /) -> None: ...

    @property
    def depth_clear_value(self) -> float: ...

    @depth_clear_value.setter
    def depth_clear_value(self, arg: float, /) -> None: ...

    @property
    def depth_read_only(self) -> bool: ...

    @depth_read_only.setter
    def depth_read_only(self, arg: bool, /) -> None: ...

    @property
    def stencil_load_op(self) -> LoadOp: ...

    @stencil_load_op.setter
    def stencil_load_op(self, arg: LoadOp, /) -> None: ...

    @property
    def stencil_store_op(self) -> StoreOp: ...

    @stencil_store_op.setter
    def stencil_store_op(self, arg: StoreOp, /) -> None: ...

    @property
    def stencil_clear_value(self) -> int: ...

    @stencil_clear_value.setter
    def stencil_clear_value(self, arg: int, /) -> None: ...

    @property
    def stencil_read_only(self) -> bool: ...

    @stencil_read_only.setter
    def stencil_read_only(self, arg: bool, /) -> None: ...

RenderPassDepthStencilAttachmentDict = TypedDict("RenderPassDepthStencilAttachmentDict", {
    "view": TextureView,
    "depth_load_op": LoadOp,
    "depth_store_op": StoreOp,
    "depth_clear_value": float,
    "depth_read_only": bool,
    "stencil_load_op": LoadOp,
    "stencil_store_op": StoreOp,
    "stencil_clear_value": int,
    "stencil_read_only": bool
}, total = False)

RenderPassDepthStencilAttachmentParam = Union[RenderPassDepthStencilAttachment, RenderPassDepthStencilAttachmentDict]

class RenderPassDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def color_attachments(self) -> list[RenderPassColorAttachment]: ...

    @color_attachments.setter
    def color_attachments(self, arg: Sequence[RenderPassColorAttachmentParam], /) -> None: ...

    @property
    def depth_stencil_attachment(self) -> Optional[RenderPassDepthStencilAttachment]: ...

    @depth_stencil_attachment.setter
    def depth_stencil_attachment(self, arg: RenderPassDepthStencilAttachmentParam, /) -> None: ...

RenderPassDescDict = TypedDict("RenderPassDescDict", {
    "color_attachments": Sequence[RenderPassColorAttachmentParam],
    "depth_stencil_attachment": RenderPassDepthStencilAttachmentParam
}, total = False)

RenderPassDescParam = Union[RenderPassDesc, RenderPassDescDict]

class CommandEncoder(DeviceChild):
    def begin_render_pass(self, desc: RenderPassDescParam) -> RenderPassEncoder: ...

    def begin_compute_pass(self) -> ComputePassEncoder: ...

    def begin_ray_tracing_pass(self) -> RayTracingPassEncoder: ...

    def copy_buffer(self, dst: Buffer, dst_offset: int, src: Buffer, src_offset: int, size: int) -> None:
        """
        Copy a buffer region.

        Parameter ``dst``:
            Destination buffer.

        Parameter ``dst_offset``:
            Destination offset in bytes.

        Parameter ``src``:
            Source buffer.

        Parameter ``src_offset``:
            Source offset in bytes.

        Parameter ``size``:
            Size in bytes.
        """

    @overload
    def copy_texture(self, dst: Texture, dst_subresource_range: SubresourceRangeParam, dst_offset: uint3param, src: Texture, src_subresource_range: SubresourceRangeParam, src_offset: uint3param, extent: uint3param = ...) -> None:
        """
        Copy a texture region.

        Parameter ``dst``:
            Destination texture.

        Parameter ``dst_subresource_range``:
            Destination subresource range.

        Parameter ``dst_offset``:
            Destination offset in texels.

        Parameter ``src``:
            Source texture.

        Parameter ``src_subresource_range``:
            Source subresource range.

        Parameter ``src_offset``:
            Source offset in texels.

        Parameter ``extent``:
            Size in texels (-1 for maximum possible size).
        """

    @overload
    def copy_texture(self, dst: Texture, dst_layer: int, dst_mip: int, dst_offset: uint3param, src: Texture, src_layer: int, src_mip: int, src_offset: uint3param, extent: uint3param = ...) -> None:
        """
        Copy a texture region.

        Parameter ``dst``:
            Destination texture.

        Parameter ``dst_layer``:
            Destination layer.

        Parameter ``dst_mip``:
            Destination mip level.

        Parameter ``dst_offset``:
            Destination offset in texels.

        Parameter ``src``:
            Source texture.

        Parameter ``src_layer``:
            Source layer.

        Parameter ``src_mip``:
            Source mip level.

        Parameter ``src_offset``:
            Source offset in texels.

        Parameter ``extent``:
            Size in texels (-1 for maximum possible size).
        """

    def copy_texture_to_buffer(self, dst: Buffer, dst_offset: int, dst_size: int, dst_row_pitch: int, src: Texture, src_layer: int, src_mip: int, src_offset: uint3param = ..., extent: uint3param = ...) -> None:
        """
        Copy a texture to a buffer.

        Parameter ``dst``:
            Destination buffer.

        Parameter ``dst_offset``:
            Destination offset in bytes.

        Parameter ``dst_size``:
            Destination size in bytes.

        Parameter ``dst_row_pitch``:
            Destination row stride in bytes.

        Parameter ``src``:
            Source texture.

        Parameter ``src_layer``:
            Source layer.

        Parameter ``src_mip``:
            Source mip level.

        Parameter ``src_offset``:
            Source offset in texels.

        Parameter ``extent``:
            Extent in texels (-1 for maximum possible extent).
        """

    def copy_buffer_to_texture(self, dst: Texture, dst_layer: int, dst_mip: int, dst_offset: uint3param, src: Buffer, src_offset: int, src_size: int, src_row_pitch: int, extent: uint3param = ...) -> None:
        """
        Copy a buffer to a texture.

        Parameter ``dst``:
            Destination texture.

        Parameter ``dst_layer``:
            Destination layer.

        Parameter ``dst_mip``:
            Destination mip level.

        Parameter ``dst_offset``:
            Destination offset in texels.

        Parameter ``src``:
            Source buffer.

        Parameter ``src_offset``:
            Source offset in bytes.

        Parameter ``src_size``:
            Size in bytes.

        Parameter ``src_row_pitch``:
            Source row stride in bytes.

        Parameter ``extent``:
            Extent in texels (-1 for maximum possible extent).
        """

    def upload_buffer_data(self, buffer: Buffer, offset: int, data: ArrayLike) -> None: ...

    @overload
    def upload_texture_data(self, texture: Texture, layer: int, mip: int, data: ArrayLike) -> None: ...

    @overload
    def upload_texture_data(self, texture: Texture, offset: uint3param, extent: uint3param, range: SubresourceRangeParam, subresource_data: Sequence[ArrayLike]) -> None: ...

    @overload
    def upload_texture_data(self, texture: Texture, offset: uint3param, extent: uint3param, range: SubresourceRangeParam, subresource_data: Sequence[ArrayLike]) -> None: ...

    @overload
    def upload_texture_data(self, texture: Texture, range: SubresourceRangeParam, subresource_data: Sequence[ArrayLike]) -> None: ...

    @overload
    def upload_texture_data(self, texture: Texture, subresource_data: Sequence[ArrayLike]) -> None: ...

    def clear_buffer(self, buffer: Buffer, range: BufferRange = ...) -> None: ...

    def clear_texture_float(self, texture: Texture, range: SubresourceRangeParam = ..., clear_value: float4param = ...) -> None: ...

    def clear_texture_uint(self, texture: Texture, range: SubresourceRangeParam = ..., clear_value: uint4param = ...) -> None: ...

    def clear_texture_sint(self, texture: Texture, range: SubresourceRangeParam = ..., clear_value: int4param = ...) -> None: ...

    def clear_texture_depth_stencil(self, texture: Texture, range: SubresourceRangeParam = ..., clear_depth: bool = True, depth_value: float = 0.0, clear_stencil: bool = True, stencil_value: int = 0) -> None: ...

    @overload
    def blit(self, dst: TextureView, src: TextureView, filter: TextureFilteringMode = TextureFilteringMode.linear) -> None:
        """
        Blit a texture view.

        Blits the full extent of the source texture to the destination
        texture.

        Parameter ``dst``:
            View of the destination texture.

        Parameter ``src``:
            View of the source texture.

        Parameter ``filter``:
            Filtering mode to use.
        """

    @overload
    def blit(self, dst: Texture, src: Texture, filter: TextureFilteringMode = TextureFilteringMode.linear) -> None:
        """
        Blit a texture.

        Blits the full extent of the source texture to the destination
        texture.

        Parameter ``dst``:
            Destination texture.

        Parameter ``src``:
            Source texture.

        Parameter ``filter``:
            Filtering mode to use.
        """

    def generate_mips(self, texture: Texture, layer: int = 0) -> None: ...

    def resolve_query(self, query_pool: QueryPool, index: int, count: int, buffer: Buffer, offset: int) -> None: ...

    def build_acceleration_structure(self, desc: AccelerationStructureBuildDescParam, dst: AccelerationStructure, src: Optional[AccelerationStructure], scratch_buffer: BufferOffsetPairParam, queries: Sequence[AccelerationStructureQueryDescParam] = []) -> None: ...

    def copy_acceleration_structure(self, src: AccelerationStructure, dst: AccelerationStructure, mode: AccelerationStructureCopyMode) -> None: ...

    def query_acceleration_structure_properties(self, acceleration_structures: Sequence[AccelerationStructure], queries: Sequence[AccelerationStructureQueryDescParam]) -> None: ...

    def serialize_acceleration_structure(self, dst: BufferOffsetPairParam, src: AccelerationStructure) -> None: ...

    def deserialize_acceleration_structure(self, dst: AccelerationStructure, src: BufferOffsetPairParam) -> None: ...

    def set_buffer_state(self, buffer: Buffer, state: ResourceState) -> None:
        """
        Transition resource state of a buffer and add a barrier if state has
        changed.

        Parameter ``buffer``:
            Buffer

        Parameter ``state``:
            New state
        """

    @overload
    def set_texture_state(self, texture: Texture, state: ResourceState) -> None:
        """
        Transition resource state of a texture and add a barrier if state has
        changed.

        Parameter ``texture``:
            Texture

        Parameter ``state``:
            New state
        """

    @overload
    def set_texture_state(self, texture: Texture, range: SubresourceRangeParam, state: ResourceState) -> None: ...

    def global_barrier(self) -> None:
        """N/A"""

    def push_debug_group(self, name: str, color: float3param) -> None:
        """Push a debug group."""

    def pop_debug_group(self) -> None:
        """Pop a debug group."""

    def insert_debug_marker(self, name: str, color: float3param) -> None:
        """
        Insert a debug marker.

        Parameter ``name``:
            Name of the marker.

        Parameter ``color``:
            Color of the marker.
        """

    def write_timestamp(self, query_pool: QueryPool, index: int) -> None:
        """
        Write a timestamp.

        Parameter ``query_pool``:
            Query pool.

        Parameter ``index``:
            Index of the query.
        """

    def finish(self) -> CommandBuffer: ...

    @property
    def native_handle(self) -> NativeHandle:
        """Get the command encoder handle."""

class PassEncoder(Object):
    def end(self) -> None: ...

    def push_debug_group(self, name: str, color: float3param) -> None:
        """Push a debug group."""

    def pop_debug_group(self) -> None:
        """Pop a debug group."""

    def insert_debug_marker(self, name: str, color: float3param) -> None:
        """
        Insert a debug marker.

        Parameter ``name``:
            Name of the marker.

        Parameter ``color``:
            Color of the marker.
        """

    def write_timestamp(self, query_pool: QueryPool, index: int) -> None:
        """N/A"""

class RenderPassEncoder(PassEncoder):
    def __enter__(self) -> RenderPassEncoder: ...

    def __exit__(self, exc_type: Optional[object] = None, exc_value: Optional[object] = None, traceback: Optional[object] = None) -> None: ...

    @overload
    def bind_pipeline(self, pipeline: RenderPipeline) -> ShaderObject: ...

    @overload
    def bind_pipeline(self, pipeline: RenderPipeline, root_object: ShaderObject) -> None: ...

    def set_render_state(self, state: RenderStateParam) -> None: ...

    def draw(self, args: DrawArgumentsParam) -> None: ...

    def draw_indexed(self, args: DrawArgumentsParam) -> None: ...

    def draw_indirect(self, max_draw_count: int, arg_buffer: BufferOffsetPairParam, count_buffer: BufferOffsetPairParam = ...) -> None: ...

    def draw_indexed_indirect(self, max_draw_count: int, arg_buffer: BufferOffsetPairParam, count_buffer: BufferOffsetPairParam = ...) -> None: ...

    def draw_mesh_tasks(self, dimensions: uint3param) -> None: ...

class ComputePassEncoder(PassEncoder):
    def __enter__(self) -> ComputePassEncoder: ...

    def __exit__(self, exc_type: Optional[object] = None, exc_value: Optional[object] = None, traceback: Optional[object] = None) -> None: ...

    @overload
    def bind_pipeline(self, pipeline: ComputePipeline) -> ShaderObject: ...

    @overload
    def bind_pipeline(self, pipeline: ComputePipeline, root_object: ShaderObject) -> None: ...

    def dispatch(self, thread_count: uint3param) -> None: ...

    def dispatch_compute(self, thread_group_count: uint3param) -> None: ...

    def dispatch_compute_indirect(self, arg_buffer: BufferOffsetPairParam) -> None: ...

class RayTracingPassEncoder(PassEncoder):
    def __enter__(self) -> RayTracingPassEncoder: ...

    def __exit__(self, exc_type: Optional[object] = None, exc_value: Optional[object] = None, traceback: Optional[object] = None) -> None: ...

    @overload
    def bind_pipeline(self, pipeline: RayTracingPipeline, shader_table: ShaderTable) -> ShaderObject: ...

    @overload
    def bind_pipeline(self, pipeline: RayTracingPipeline, shader_table: ShaderTable, root_object: ShaderObject) -> None: ...

    def dispatch_rays(self, ray_gen_shader_index: int, dimensions: uint3param) -> None: ...

class CommandBuffer(DeviceChild):
    pass

class CoopVecMatrixLayout(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    row_major = 0

    column_major = 1

    inferencing_optimal = 2

    training_optimal = 3

class CoopVecMatrixDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, rows: int, cols: int, element_type: DataType, layout: CoopVecMatrixLayout, size: int, offset: int) -> None: ...

    @property
    def rows(self) -> int: ...

    @rows.setter
    def rows(self, arg: int, /) -> None: ...

    @property
    def cols(self) -> int: ...

    @cols.setter
    def cols(self, arg: int, /) -> None: ...

    @property
    def element_type(self) -> DataType: ...

    @element_type.setter
    def element_type(self, arg: DataType, /) -> None: ...

    @property
    def layout(self) -> CoopVecMatrixLayout: ...

    @layout.setter
    def layout(self, arg: CoopVecMatrixLayout, /) -> None: ...

    @property
    def size(self) -> int: ...

    @size.setter
    def size(self, arg: int, /) -> None: ...

    @property
    def offset(self) -> int: ...

    @offset.setter
    def offset(self, arg: int, /) -> None: ...

class Kernel(DeviceChild):
    @property
    def program(self) -> ShaderProgram: ...

    @property
    def reflection(self) -> ReflectionCursor: ...

class ComputeKernelDesc:
    def __init__(self) -> None: ...

    @property
    def program(self) -> ShaderProgram: ...

    @program.setter
    def program(self, arg: ShaderProgram, /) -> None: ...

class ComputeKernel(Kernel):
    @property
    def pipeline(self) -> ComputePipeline: ...

    def dispatch(self, thread_count: uint3param, vars: dict = {}, command_encoder: Optional[CommandEncoder] = None, queue: CommandQueueType = CommandQueueType.graphics, cuda_stream: NativeHandle = ..., query_pool: Optional[QueryPool] = None, query_index_before: int = 0, query_index_after: int = 0, **kwargs) -> None: ...

class AdapterInfo:
    @property
    def name(self) -> str:
        """Descriptive name of the adapter."""

    @property
    def vendor_id(self) -> int:
        """
        Unique identifier for the vendor (only available for D3D12 and
        Vulkan).
        """

    @property
    def device_id(self) -> int:
        """
        Unique identifier for the physical device among devices from the
        vendor (only available for D3D12 and Vulkan).
        """

    @property
    def luid(self) -> list[int]:
        """Logically unique identifier of the adapter."""

    def __repr__(self) -> str: ...

class DeviceType(enum.Enum):
    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    automatic = 0

    d3d12 = 2

    vulkan = 3

    metal = 4

    wgpu = 7

    cpu = 5

    cuda = 6

class DeviceDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def type(self) -> DeviceType:
        """The type of the device."""

    @type.setter
    def type(self, arg: DeviceType, /) -> None: ...

    @property
    def enable_debug_layers(self) -> bool:
        """Enable debug layers."""

    @enable_debug_layers.setter
    def enable_debug_layers(self, arg: bool, /) -> None: ...

    @property
    def enable_cuda_interop(self) -> bool:
        """Enable CUDA interoperability."""

    @enable_cuda_interop.setter
    def enable_cuda_interop(self, arg: bool, /) -> None: ...

    @property
    def enable_print(self) -> bool:
        """Enable device side printing (adds performance overhead)."""

    @enable_print.setter
    def enable_print(self, arg: bool, /) -> None: ...

    @property
    def enable_hot_reload(self) -> bool:
        """Adapter LUID to select adapter on which the device will be created."""

    @enable_hot_reload.setter
    def enable_hot_reload(self, arg: bool, /) -> None: ...

    @property
    def enable_compilation_reports(self) -> bool:
        """Enable compilation reports."""

    @enable_compilation_reports.setter
    def enable_compilation_reports(self, arg: bool, /) -> None: ...

    @property
    def adapter_luid(self) -> Optional[list[int]]:
        """Adapter LUID to select adapter on which the device will be created."""

    @adapter_luid.setter
    def adapter_luid(self, arg: Sequence[int], /) -> None: ...

    @property
    def compiler_options(self) -> SlangCompilerOptions:
        """Compiler options (used for default slang session)."""

    @compiler_options.setter
    def compiler_options(self, arg: SlangCompilerOptionsParam, /) -> None: ...

    @property
    def shader_cache_path(self) -> Optional[pathlib.Path]:
        """
        Path to the shader cache directory (optional). If a relative path is
        used, the cache is stored in the application data directory.
        """

    @shader_cache_path.setter
    def shader_cache_path(self, arg: str | os.PathLike, /) -> None: ...

    @property
    def existing_device_handles(self) -> list[NativeHandle]:
        """N/A"""

    @existing_device_handles.setter
    def existing_device_handles(self, arg: Sequence[NativeHandle], /) -> None: ...

    @property
    def label(self) -> str:
        """N/A"""

    @label.setter
    def label(self, arg: str, /) -> None: ...

DeviceDescDict = TypedDict("DeviceDescDict", {
    "type": DeviceType,
    "enable_debug_layers": bool,
    "enable_cuda_interop": bool,
    "enable_print": bool,
    "enable_hot_reload": bool,
    "enable_compilation_reports": bool,
    "adapter_luid": Sequence[int],
    "compiler_options": SlangCompilerOptionsParam,
    "shader_cache_path": str | os.PathLike,
    "existing_device_handles": Sequence[NativeHandle],
    "label": str
}, total = False)

DeviceDescParam = Union[DeviceDesc, DeviceDescDict]

class DeviceLimits:
    @property
    def max_texture_dimension_1d(self) -> int:
        """Maximum dimension for 1D textures."""

    @property
    def max_texture_dimension_2d(self) -> int:
        """Maximum dimensions for 2D textures."""

    @property
    def max_texture_dimension_3d(self) -> int:
        """Maximum dimensions for 3D textures."""

    @property
    def max_texture_dimension_cube(self) -> int:
        """Maximum dimensions for cube textures."""

    @property
    def max_texture_layers(self) -> int:
        """Maximum number of texture layers."""

    @property
    def max_vertex_input_elements(self) -> int:
        """Maximum number of vertex input elements in a graphics pipeline."""

    @property
    def max_vertex_input_element_offset(self) -> int:
        """Maximum offset of a vertex input element in the vertex stream."""

    @property
    def max_vertex_streams(self) -> int:
        """Maximum number of vertex streams in a graphics pipeline."""

    @property
    def max_vertex_stream_stride(self) -> int:
        """Maximum stride of a vertex stream."""

    @property
    def max_compute_threads_per_group(self) -> int:
        """Maximum number of threads per thread group."""

    @property
    def max_compute_thread_group_size(self) -> math.uint3:
        """Maximum dimensions of a thread group."""

    @property
    def max_compute_dispatch_thread_groups(self) -> math.uint3:
        """Maximum number of thread groups per dimension in a single dispatch."""

    @property
    def max_viewports(self) -> int:
        """Maximum number of viewports per pipeline."""

    @property
    def max_viewport_dimensions(self) -> math.uint2:
        """Maximum viewport dimensions."""

    @property
    def max_framebuffer_dimensions(self) -> math.uint3:
        """Maximum framebuffer dimensions."""

    @property
    def max_shader_visible_samplers(self) -> int:
        """Maximum samplers visible in a shader stage."""

class DeviceInfo:
    @property
    def type(self) -> DeviceType:
        """The type of the device."""

    @property
    def api_name(self) -> str:
        """The name of the graphics API being used by this device."""

    @property
    def adapter_name(self) -> str:
        """The name of the graphics adapter."""

    @property
    def timestamp_frequency(self) -> int:
        """
        The frequency of the timestamp counter. To resolve a timestamp to
        seconds, divide by this value.
        """

    @property
    def limits(self) -> DeviceLimits:
        """Limits of the device."""

class ShaderCacheStats:
    @property
    def entry_count(self) -> int:
        """Number of entries in the cache."""

    @property
    def hit_count(self) -> int:
        """Number of hits in the cache."""

    @property
    def miss_count(self) -> int:
        """Number of misses in the cache."""

class ShaderHotReloadEvent:
    """Event data for hot reload hook."""

class HeapReport:
    """N/A"""

    @property
    def label(self) -> str:
        """N/A"""

    @label.setter
    def label(self, arg: str, /) -> None: ...

    @property
    def num_pages(self) -> int:
        """N/A"""

    @num_pages.setter
    def num_pages(self, arg: int, /) -> None: ...

    @property
    def total_allocated(self) -> int:
        """N/A"""

    @total_allocated.setter
    def total_allocated(self, arg: int, /) -> None: ...

    @property
    def total_mem_usage(self) -> int:
        """N/A"""

    @total_mem_usage.setter
    def total_mem_usage(self, arg: int, /) -> None: ...

    @property
    def num_allocations(self) -> int:
        """N/A"""

    @num_allocations.setter
    def num_allocations(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

class Device(Object):
    @overload
    def __init__(self, type: DeviceType = DeviceType.automatic, enable_debug_layers: bool = False, enable_cuda_interop: bool = False, enable_print: bool = False, enable_hot_reload: bool = True, enable_compilation_reports: bool = False, adapter_luid: Optional[Sequence[int]] = None, compiler_options: Optional[SlangCompilerOptionsParam] = None, shader_cache_path: Optional[str | os.PathLike] = None, existing_device_handles: Optional[Sequence[NativeHandle]] = None, label: str = '') -> None: ...

    @overload
    def __init__(self, desc: DeviceDescParam) -> None: ...

    @property
    def desc(self) -> DeviceDesc: ...

    @property
    def info(self) -> DeviceInfo:
        """Device information."""

    @property
    def shader_cache_stats(self) -> ShaderCacheStats:
        """Shader cache statistics."""

    @property
    def supported_shader_model(self) -> ShaderModel:
        """The highest shader model supported by the device."""

    @property
    def features(self) -> list[Feature]:
        """List of features supported by the device."""

    @property
    def supports_cuda_interop(self) -> bool:
        """True if the device supports CUDA interoperability."""

    @property
    def native_handles(self) -> list[NativeHandle]:
        """Get the native device handles."""

    def has_feature(self, feature: Feature) -> bool:
        """Check if the device supports a given feature."""

    def get_format_support(self, format: Format) -> FormatSupport:
        """Returns the supported resource states for a given format."""

    @property
    def slang_session(self) -> SlangSession:
        """Default slang session."""

    def close(self) -> None:
        r"""
        Close the device.

        This function should be called before the device is released. It waits
        for all pending work to be completed and releases internal resources,
        removing all cyclic references that might prevent the device from
        being destroyed. After closing the device, no new resources must be
        created and no new work must be submitted.

        \note The Python extension will automatically close all open devices
        when the interpreter is terminated through an `atexit` handler. If a
        device is to be destroyed at runtime, it must be closed explicitly.
        """

    @overload
    def create_surface(self, window: Window) -> Surface:
        """
        Create a new surface.

        Parameter ``window``:
            Window to create the surface for.

        Returns:
            New surface object.
        """

    @overload
    def create_surface(self, window_handle: WindowHandle) -> Surface:
        """
        Create a new surface.

        Parameter ``window_handle``:
            Native window handle to create the surface for.

        Returns:
            New surface object.
        """

    @overload
    def create_buffer(self, size: int = 0, element_count: int = 0, struct_size: int = 0, resource_type_layout: Optional[object] = None, format: Format = Format.undefined, memory_type: MemoryType = MemoryType.device_local, usage: BufferUsage = BufferUsage.none, default_state: ResourceState = ResourceState.undefined, label: str = '', data: Optional[ArrayLike] = None) -> Buffer:
        """
        Create a new buffer.

        Parameter ``size``:
            Buffer size in bytes.

        Parameter ``element_count``:
            Buffer size in number of struct elements. Can be used instead of
            ``size``.

        Parameter ``struct_size``:
            Struct size in bytes.

        Parameter ``resource_type_layout``:
            Resource type layout of the buffer. Can be used instead of
            ``struct_size`` to specify the size of the struct.

        Parameter ``format``:
            Buffer format. Used when creating typed buffer views.

        Parameter ``initial_state``:
            Initial resource state.

        Parameter ``usage``:
            Resource usage flags.

        Parameter ``memory_type``:
            Memory type.

        Parameter ``label``:
            Debug label.

        Parameter ``data``:
            Initial data to upload to the buffer.

        Parameter ``data_size``:
            Size of the initial data in bytes.

        Returns:
            New buffer object.
        """

    @overload
    def create_buffer(self, desc: BufferDescParam) -> Buffer: ...

    @overload
    def create_texture(self, type: TextureType = TextureType.texture_2d, format: Format = Format.undefined, width: int = 1, height: int = 1, depth: int = 1, array_length: int = 1, mip_count: int = 1, sample_count: int = 1, sample_quality: int = 0, memory_type: MemoryType = MemoryType.device_local, usage: TextureUsage = TextureUsage.none, default_state: ResourceState = ResourceState.undefined, label: str = '', data: Optional[ArrayLike] = None) -> Texture:
        """
        Create a new texture.

        Parameter ``type``:
            Texture type.

        Parameter ``format``:
            Texture format.

        Parameter ``width``:
            Width in pixels.

        Parameter ``height``:
            Height in pixels.

        Parameter ``depth``:
            Depth in pixels.

        Parameter ``array_length``:
            Array length.

        Parameter ``mip_count``:
            Mip level count. Number of mip levels (ALL_MIPS for all mip
            levels).

        Parameter ``sample_count``:
            Number of samples for multisampled textures.

        Parameter ``quality``:
            Quality level for multisampled textures.

        Parameter ``usage``:
            Resource usage.

        Parameter ``memory_type``:
            Memory type.

        Parameter ``label``:
            Debug label.

        Parameter ``data``:
            Initial data.

        Returns:
            New texture object.
        """

    @overload
    def create_texture(self, desc: TextureDescParam) -> Texture: ...

    @overload
    def create_sampler(self, min_filter: TextureFilteringMode = TextureFilteringMode.linear, mag_filter: TextureFilteringMode = TextureFilteringMode.linear, mip_filter: TextureFilteringMode = TextureFilteringMode.linear, reduction_op: TextureReductionOp = TextureReductionOp.average, address_u: TextureAddressingMode = TextureAddressingMode.wrap, address_v: TextureAddressingMode = TextureAddressingMode.wrap, address_w: TextureAddressingMode = TextureAddressingMode.wrap, mip_lod_bias: float = 0.0, max_anisotropy: int = 1, comparison_func: ComparisonFunc = ComparisonFunc.never, border_color: float4param = ..., min_lod: float = -1000.0, max_lod: float = 1000.0, label: str = '') -> Sampler:
        """
        Create a new sampler.

        Parameter ``min_filter``:
            Minification filter.

        Parameter ``mag_filter``:
            Magnification filter.

        Parameter ``mip_filter``:
            Mip-map filter.

        Parameter ``reduction_op``:
            Reduction operation.

        Parameter ``address_u``:
            Texture addressing mode for the U coordinate.

        Parameter ``address_v``:
            Texture addressing mode for the V coordinate.

        Parameter ``address_w``:
            Texture addressing mode for the W coordinate.

        Parameter ``mip_lod_bias``:
            Mip-map LOD bias.

        Parameter ``max_anisotropy``:
            Maximum anisotropy.

        Parameter ``comparison_func``:
            Comparison function.

        Parameter ``border_color``:
            Border color.

        Parameter ``min_lod``:
            Minimum LOD level.

        Parameter ``max_lod``:
            Maximum LOD level.

        Parameter ``label``:
            Debug label.

        Returns:
            New sampler object.
        """

    @overload
    def create_sampler(self, desc: SamplerDescParam) -> Sampler: ...

    @overload
    def create_fence(self, initial_value: int = 0, shared: bool = False) -> Fence:
        """
        Create a new fence.

        Parameter ``initial_value``:
            Initial fence value.

        Parameter ``shared``:
            Create a shared fence.

        Returns:
            New fence object.
        """

    @overload
    def create_fence(self, desc: FenceDescParam) -> Fence: ...

    def create_query_pool(self, type: QueryType, count: int) -> QueryPool:
        """
        Create a new query pool.

        Parameter ``type``:
            Query type.

        Parameter ``count``:
            Number of queries in the pool.

        Returns:
            New query pool object.
        """

    @overload
    def create_input_layout(self, input_elements: Sequence[InputElementDescParam], vertex_streams: Sequence[VertexStreamDescParam]) -> InputLayout:
        """
        Create a new input layout.

        Parameter ``input_elements``:
            List of input elements (see InputElementDesc for details).

        Parameter ``vertex_streams``:
            List of vertex streams (see VertexStreamDesc for details).

        Returns:
            New input layout object.
        """

    @overload
    def create_input_layout(self, desc: InputLayoutDescParam) -> InputLayout: ...

    def create_command_encoder(self, queue: CommandQueueType = CommandQueueType.graphics) -> CommandEncoder: ...

    def submit_command_buffers(self, command_buffers: Sequence[CommandBuffer], wait_fences: Sequence[Fence] = [], wait_fence_values: Sequence[int] = [], signal_fences: Sequence[Fence] = [], signal_fence_values: Sequence[int] = [], queue: CommandQueueType = CommandQueueType.graphics, cuda_stream: NativeHandle = ...) -> int:
        """
        Submit a list of command buffers to the device.

        The returned submission ID can be used to wait for the submission to
        complete.

        The wait fence values are optional. If not provided, the fence values
        will be set to AUTO, which means waiting for the last signaled value.

        The signal fence values are optional. If not provided, the fence
        values will be set to AUTO, which means incrementing the last signaled
        value by 1. *

        Parameter ``command_buffers``:
            List of command buffers to submit.

        Parameter ``wait_fences``:
            List of fences to wait for before executing the command buffers.

        Parameter ``wait_fence_values``:
            List of fence values to wait for before executing the command
            buffers.

        Parameter ``signal_fences``:
            List of fences to signal after executing the command buffers.

        Parameter ``signal_fence_values``:
            List of fence values to signal after executing the command
            buffers.

        Parameter ``queue``:
            Command queue to submit to.

        Parameter ``cuda_stream``:
            On none-CUDA backends, when interop is enabled, this is the stream
            to sync with before/after submission (assuming any resources are
            shared with CUDA) and use for internal copies. If not specified,
            sync will happen with the NULL (default) CUDA stream. On CUDA
            backends, this is the CUDA stream to use for the submission. If
            not specified, the default stream of the command queue will be
            used, which for CommandQueueType::graphics is the NULL stream. It
            is an error to specify a stream for none-CUDA backends that have
            interop disabled.

        Returns:
            Submission ID.
        """

    def submit_command_buffer(self, command_buffer: CommandBuffer, queue: CommandQueueType = CommandQueueType.graphics, cuda_stream: NativeHandle = ...) -> int:
        """
        Submit a command buffer to the device.

        The returned submission ID can be used to wait for the submission to
        complete.

        Parameter ``command_buffer``:
            Command buffer to submit.

        Parameter ``queue``:
            Command queue to submit to.

        Returns:
            Submission ID.
        """

    def is_submit_finished(self, id: int) -> bool:
        """
        Check if a submission is finished executing.

        Parameter ``id``:
            Submission ID.

        Returns:
            True if the submission is finished executing.
        """

    def wait_for_submit(self, id: int) -> None:
        """
        Wait for a submission to finish execution.

        Parameter ``id``:
            Submission ID.
        """

    def wait_for_idle(self, queue: CommandQueueType = CommandQueueType.graphics) -> None:
        """
        Wait for the command queue to be idle.

        Parameter ``queue``:
            Command queue to wait for.
        """

    def sync_to_cuda(self, cuda_stream: int = 0) -> None:
        """
        Synchronize CUDA -> device.

        This signals a shared CUDA semaphore from the CUDA stream and then
        waits for the signal on the command queue.

        Parameter ``cuda_stream``:
            CUDA stream
        """

    def sync_to_device(self, cuda_stream: int = 0) -> None:
        """
        Synchronize device -> CUDA.

        This waits for a shared CUDA semaphore on the CUDA stream, making sure
        all commands on the device have completed.

        Parameter ``cuda_stream``:
            CUDA stream
        """

    def get_acceleration_structure_sizes(self, desc: AccelerationStructureBuildDescParam) -> AccelerationStructureSizes:
        """
        Query the device for buffer sizes required for acceleration structure
        builds.

        Parameter ``desc``:
            Acceleration structure build description.

        Returns:
            Acceleration structure sizes.
        """

    @overload
    def create_acceleration_structure(self, size: int = 0, label: str = '') -> AccelerationStructure: ...

    @overload
    def create_acceleration_structure(self, desc: AccelerationStructureDescParam) -> AccelerationStructure: ...

    def create_acceleration_structure_instance_list(self, size: int) -> AccelerationStructureInstanceList: ...

    @overload
    def create_shader_table(self, program: ShaderProgram, ray_gen_entry_points: Sequence[str] = [], miss_entry_points: Sequence[str] = [], hit_group_names: Sequence[str] = [], callable_entry_points: Sequence[str] = []) -> ShaderTable: ...

    @overload
    def create_shader_table(self, desc: ShaderTableDescParam) -> ShaderTable: ...

    def create_slang_session(self, compiler_options: Optional[SlangCompilerOptionsParam] = None, add_default_include_paths: bool = True, cache_path: Optional[str | os.PathLike] = None) -> SlangSession:
        """
        Create a new slang session.

        Parameter ``compiler_options``:
            Compiler options (see SlangCompilerOptions for details).

        Returns:
            New slang session object.
        """

    def reload_all_programs(self) -> None: ...

    def load_module(self, module_name: str) -> SlangModule: ...

    def load_module_from_source(self, module_name: str, source: str, path: Optional[str | os.PathLike] = None) -> SlangModule: ...

    def link_program(self, modules: Sequence[SlangModule], entry_points: Sequence[SlangEntryPoint], link_options: Optional[SlangLinkOptionsParam] = None) -> ShaderProgram: ...

    def load_program(self, module_name: str, entry_point_names: Sequence[str], additional_source: Optional[str] = None, link_options: Optional[SlangLinkOptionsParam] = None) -> ShaderProgram: ...

    def create_root_shader_object(self, shader_program: ShaderProgram) -> ShaderObject: ...

    @overload
    def create_shader_object(self, type_layout: TypeLayoutReflection) -> ShaderObject: ...

    @overload
    def create_shader_object(self, cursor: ReflectionCursor) -> ShaderObject: ...

    @overload
    def create_compute_pipeline(self, program: ShaderProgram, defer_target_compilation: bool = False, label: Optional[str] = None) -> ComputePipeline: ...

    @overload
    def create_compute_pipeline(self, desc: ComputePipelineDescParam) -> ComputePipeline: ...

    @overload
    def create_render_pipeline(self, program: ShaderProgram, input_layout: Optional[InputLayout], primitive_topology: PrimitiveTopology = PrimitiveTopology.triangle_list, targets: Sequence[ColorTargetDescParam] = [], depth_stencil: Optional[DepthStencilDescParam] = None, rasterizer: Optional[RasterizerDescParam] = None, multisample: Optional[MultisampleDescParam] = None, defer_target_compilation: bool = False, label: Optional[str] = None) -> RenderPipeline: ...

    @overload
    def create_render_pipeline(self, desc: RenderPipelineDescParam) -> RenderPipeline: ...

    @overload
    def create_ray_tracing_pipeline(self, program: ShaderProgram, hit_groups: Sequence[HitGroupDescParam], max_recursion: int = 0, max_ray_payload_size: int = 0, max_attribute_size: int = 8, flags: RayTracingPipelineFlags = RayTracingPipelineFlags.none, defer_target_compilation: bool = False, label: Optional[str] = None) -> RayTracingPipeline: ...

    @overload
    def create_ray_tracing_pipeline(self, desc: RayTracingPipelineDescParam) -> RayTracingPipeline: ...

    @overload
    def create_compute_kernel(self, program: ShaderProgram) -> ComputeKernel: ...

    @overload
    def create_compute_kernel(self, desc: ComputeKernelDesc) -> ComputeKernel: ...

    def flush_print(self) -> None:
        """Block and flush all shader side debug print output."""

    def flush_print_to_string(self) -> str:
        """Block and flush all shader side debug print output to a string."""

    def wait(self) -> None:
        """Wait for all device work to complete."""

    def register_shader_hot_reload_callback(self, callback: Callable[[ShaderHotReloadEvent], None]) -> None:
        """
        Register a hot reload hook, called immediately after any module is
        reloaded.
        """

    def register_device_close_callback(self, callback: Callable[[Device], None]) -> None:
        """Register a device close callback, called at start of device close."""

    def coopvec_query_matrix_size(self, rows: int, cols: int, layout: CoopVecMatrixLayout, element_type: DataType) -> int: ...

    def coopvec_create_matrix_desc(self, rows: int, cols: int, layout: CoopVecMatrixLayout, element_type: DataType, offset: int = 0) -> CoopVecMatrixDesc: ...

    def coopvec_convert_matrix_host(self, src: Annotated[ArrayLike, dict(device='cpu')], dst: Annotated[ArrayLike, dict(device='cpu')], src_layout: Optional[CoopVecMatrixLayout] = None, dst_layout: Optional[CoopVecMatrixLayout] = None) -> int: ...

    @overload
    def coopvec_convert_matrix_device(self, src: Buffer, src_desc: CoopVecMatrixDesc, dst: Buffer, dst_desc: CoopVecMatrixDesc, encoder: Optional[CommandEncoder] = None) -> None: ...

    @overload
    def coopvec_convert_matrix_device(self, src: Buffer, src_desc: Sequence[CoopVecMatrixDesc], dst: Buffer, dst_desc: Sequence[CoopVecMatrixDesc], encoder: Optional[CommandEncoder] = None) -> None: ...

    def coopvec_align_matrix_offset(self, offset: int) -> int: ...

    def coopvec_align_vector_offset(self, offset: int) -> int: ...

    def set_hot_reload_delay(self, timeout_ms: int) -> None:
        """N/A"""

    def hot_reload_check(self) -> None:
        """N/A"""

    @staticmethod
    def enumerate_adapters(type: DeviceType = DeviceType.automatic) -> list[AdapterInfo]:
        """Enumerates all available adapters of a given device type."""

    @staticmethod
    def get_created_devices() -> list[Device]:
        """N/A"""

    @staticmethod
    def report_live_objects() -> None:
        """
        Report live objects in the rhi layer. This is useful for checking
        clean shutdown with all resources released properly.
        """

    def report_heaps(self) -> list[HeapReport]:
        """N/A"""

def get_cuda_current_context_native_handles() -> list[NativeHandle]:
    """N/A"""

class TextureLoader(Object):
    def __init__(self, device: Device) -> None: ...

    class Options:
        @overload
        def __init__(self) -> None: ...

        @overload
        def __init__(self, arg: dict, /) -> None: ...

        @property
        def load_as_normalized(self) -> bool:
            """Load 8/16-bit integer data as normalized resource format."""

        @load_as_normalized.setter
        def load_as_normalized(self, arg: bool, /) -> None: ...

        @property
        def load_as_srgb(self) -> bool:
            """
            Use ``Format::rgba8_unorm_srgb`` format if bitmap is 8-bit RGBA with
            sRGB gamma.
            """

        @load_as_srgb.setter
        def load_as_srgb(self, arg: bool, /) -> None: ...

        @property
        def extend_alpha(self) -> bool:
            """Extend RGB to RGBA if RGB texture format is not available."""

        @extend_alpha.setter
        def extend_alpha(self, arg: bool, /) -> None: ...

        @property
        def allocate_mips(self) -> bool:
            """Allocate mip levels for the texture."""

        @allocate_mips.setter
        def allocate_mips(self, arg: bool, /) -> None: ...

        @property
        def generate_mips(self) -> bool:
            """Generate mip levels for the texture."""

        @generate_mips.setter
        def generate_mips(self, arg: bool, /) -> None: ...

        @property
        def usage(self) -> TextureUsage: ...

        @usage.setter
        def usage(self, arg: TextureUsage, /) -> None: ...

    OptionsDict = TypedDict("OptionsDict", {
        "load_as_normalized": bool,
        "load_as_srgb": bool,
        "extend_alpha": bool,
        "allocate_mips": bool,
        "generate_mips": bool,
        "usage": TextureUsage
    }, total = False)

    OptionsParam = Union[Options, OptionsDict]

    @overload
    def load_texture(self, bitmap: Bitmap, options: Optional[TextureLoader.OptionsParam] = None) -> Texture:
        """
        Load a texture from a bitmap.

        Parameter ``bitmap``:
            Bitmap to load.

        Parameter ``options``:
            Texture loading options.

        Returns:
            New texture object.
        """

    @overload
    def load_texture(self, path: str | os.PathLike, options: Optional[TextureLoader.OptionsParam] = None) -> Texture:
        """
        Load a texture from an image file.

        Parameter ``path``:
            Image file path.

        Parameter ``options``:
            Texture loading options.

        Returns:
            New texture object.
        """

    @overload
    def load_textures(self, bitmaps: Sequence[Bitmap], options: Optional[TextureLoader.OptionsParam] = None) -> list[Texture]:
        """
        Load textures from a list of bitmaps.

        Parameter ``bitmaps``:
            Bitmaps to load.

        Parameter ``options``:
            Texture loading options.

        Returns:
            List of new of texture objects.
        """

    @overload
    def load_textures(self, paths: Sequence[str | os.PathLike], options: Optional[TextureLoader.OptionsParam] = None) -> list[Texture]:
        """
        Load textures from a list of image files.

        Parameter ``paths``:
            Image file paths.

        Parameter ``options``:
            Texture loading options.

        Returns:
            List of new texture objects.
        """

    @overload
    def load_texture_array(self, bitmaps: Sequence[Bitmap], options: Optional[TextureLoader.OptionsParam] = None) -> Texture:
        """
        Load a texture array from a list of bitmaps.

        All bitmaps need to have the same format and dimensions.

        Parameter ``bitmaps``:
            Bitmaps to load.

        Parameter ``options``:
            Texture loading options.

        Returns:
            New texture array object.
        """

    @overload
    def load_texture_array(self, paths: Sequence[str | os.PathLike], options: Optional[TextureLoader.OptionsParam] = None) -> Texture:
        """
        Load a texture array from a list of image files.

        All images need to have the same format and dimensions.

        Parameter ``paths``:
            Image file paths.

        Parameter ``options``:
            Texture loading options.

        Returns:
            New texture array object.
        """

class AppDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def device(self) -> Device:
        """
        Device to use for rendering. If not provided, a default device will be
        created.
        """

    @device.setter
    def device(self, arg: Device, /) -> None: ...

AppDescDict = TypedDict("AppDescDict", {
    "device": Device
}, total = False)

AppDescParam = Union[AppDesc, AppDescDict]

class App(Object):
    @overload
    def __init__(self, arg: AppDescParam, /) -> None: ...

    @overload
    def __init__(self, device: Optional[Device] = None) -> None: ...

    @property
    def device(self) -> Device: ...

    def run(self) -> None: ...

    def run_frame(self) -> None: ...

    def terminate(self) -> None: ...

class AppWindowDesc:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: dict, /) -> None: ...

    @property
    def width(self) -> int:
        """Width of the window in pixels."""

    @width.setter
    def width(self, arg: int, /) -> None: ...

    @property
    def height(self) -> int:
        """Height of the window in pixels."""

    @height.setter
    def height(self, arg: int, /) -> None: ...

    @property
    def title(self) -> str:
        """Title of the window."""

    @title.setter
    def title(self, arg: str, /) -> None: ...

    @property
    def mode(self) -> WindowMode:
        """Window mode."""

    @mode.setter
    def mode(self, arg: WindowMode, /) -> None: ...

    @property
    def resizable(self) -> bool:
        """Whether the window is resizable."""

    @resizable.setter
    def resizable(self, arg: bool, /) -> None: ...

    @property
    def surface_format(self) -> Format:
        """Format of the swapchain images."""

    @surface_format.setter
    def surface_format(self, arg: Format, /) -> None: ...

    @property
    def enable_vsync(self) -> bool:
        """Enable/disable vertical synchronization."""

    @enable_vsync.setter
    def enable_vsync(self, arg: bool, /) -> None: ...

AppWindowDescDict = TypedDict("AppWindowDescDict", {
    "width": int,
    "height": int,
    "title": str,
    "mode": WindowMode,
    "resizable": bool,
    "surface_format": Format,
    "enable_vsync": bool
}, total = False)

AppWindowDescParam = Union[AppWindowDesc, AppWindowDescDict]

class AppWindow(Object):
    def __init__(self, app: App, width: int = 1920, height: int = 1280, title: str = 'slangpy', mode: WindowMode = WindowMode.normal, resizable: bool = True, surface_format: Format = Format.undefined, enable_vsync: bool = False) -> None: ...

    class RenderContext:
        @property
        def surface_texture(self) -> Texture: ...

        @property
        def command_encoder(self) -> CommandEncoder: ...

    @property
    def device(self) -> Device: ...

    @property
    def screen(self) -> ui.Screen: ...

    def render(self, render_context: AppWindow.RenderContext) -> None: ...

    def on_resize(self, width: int, height: int) -> None: ...

    def on_keyboard_event(self, event: KeyboardEvent) -> None: ...

    def on_mouse_event(self, event: MouseEvent) -> None: ...

    def on_gamepad_event(self, event: GamepadEvent) -> None: ...

    def on_drop_files(self, files: Sequence[str]) -> None: ...

SHADER_PATH: str = ...
