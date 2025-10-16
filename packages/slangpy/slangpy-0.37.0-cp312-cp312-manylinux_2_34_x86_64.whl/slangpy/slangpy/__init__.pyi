from collections.abc import Mapping, Sequence
import enum
from typing import TypedDict, Union
from numpy.typing import NDArray
from typing import Annotated

from numpy.typing import ArrayLike

import slangpy
import slangpy.TypeReflection


class AccessType(enum.Enum):
    _new_member_ = __new__

    _use_args_: bool = False

    _member_names_: list = ['none', 'read', 'write', 'readwrite']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    _unhashable_values_: list = []

    _value_repr_: None = None

    none = 0

    read = 1

    write = 2

    readwrite = 3

class CallMode(enum.Enum):
    _new_member_ = __new__

    _use_args_: bool = False

    _member_names_: list = ['prim', 'bwds', 'fwds']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    _unhashable_values_: list = []

    _value_repr_: None = None

    prim = 0

    bwds = 1

    fwds = 2

class CallDataMode(enum.Enum):
    _new_member_ = __new__

    _use_args_: bool = False

    _member_names_: list = ['global_data', 'entry_point']

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    _unhashable_values_: list = []

    _value_repr_: None = None

    global_data = 0

    entry_point = 1

def unpack_args(*args) -> list:
    """N/A"""

def unpack_refs_and_args(refs: list, *args) -> list:
    """N/A"""

def unpack_kwargs(**kwargs) -> dict:
    """N/A"""

def unpack_refs_and_kwargs(refs: list, **kwargs) -> dict:
    """N/A"""

def unpack_arg(arg: object) -> object:
    """N/A"""

def pack_arg(arg: object, unpacked_arg: object) -> None:
    """N/A"""

def get_value_signature(o: object) -> str:
    """N/A"""

class SignatureBuilder(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    def add(self, value: str) -> None:
        """N/A"""

    @property
    def str(self) -> str:
        """N/A"""

    @property
    def bytes(self) -> bytes:
        """N/A"""

class NativeObject(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def slangpy_signature(self) -> str: ...

    @slangpy_signature.setter
    def slangpy_signature(self, arg: str, /) -> None: ...

    def read_signature(self, builder: SignatureBuilder) -> None:
        """N/A"""

class NativeSlangType(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def type_reflection(self) -> slangpy.TypeReflection:
        """N/A"""

    @type_reflection.setter
    def type_reflection(self, arg: slangpy.TypeReflection, /) -> None: ...

    @property
    def shape(self) -> Shape:
        """N/A"""

    @shape.setter
    def shape(self, arg: Shape, /) -> None: ...

    def _py_element_type(self) -> NativeSlangType: ...

    def _py_has_derivative(self) -> bool: ...

    def _py_derivative(self) -> NativeSlangType: ...

    def _py_uniform_type_layout(self) -> slangpy.TypeLayoutReflection: ...

    def _py_buffer_type_layout(self) -> slangpy.TypeLayoutReflection: ...

    def __repr__(self) -> str: ...

class NativeMarshall(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def concrete_shape(self) -> Shape:
        """N/A"""

    @concrete_shape.setter
    def concrete_shape(self, arg: Shape, /) -> None: ...

    @property
    def match_call_shape(self) -> bool:
        """N/A"""

    @match_call_shape.setter
    def match_call_shape(self, arg: bool, /) -> None: ...

    def get_shape(self, value: object) -> Shape:
        """N/A"""

    @property
    def slang_type(self) -> NativeSlangType:
        """N/A"""

    @slang_type.setter
    def slang_type(self, arg: NativeSlangType, /) -> None: ...

    def write_shader_cursor_pre_dispatch(self, context: CallContext, binding: NativeBoundVariableRuntime, cursor: slangpy.ShaderCursor, value: object, read_back: list) -> None:
        """N/A"""

    def create_calldata(self, arg0: CallContext, arg1: NativeBoundVariableRuntime, arg2: object, /) -> object:
        """N/A"""

    def read_calldata(self, arg0: CallContext, arg1: NativeBoundVariableRuntime, arg2: object, arg3: object, /) -> None:
        """N/A"""

    def create_output(self, arg0: CallContext, arg1: NativeBoundVariableRuntime, /) -> object:
        """N/A"""

    def read_output(self, arg0: CallContext, arg1: NativeBoundVariableRuntime, arg2: object, /) -> object:
        """N/A"""

    @property
    def has_derivative(self) -> bool:
        """N/A"""

    @property
    def is_writable(self) -> bool:
        """N/A"""

    def gen_calldata(self, cgb: object, context: object, binding: object) -> None:
        """N/A"""

    def reduce_type(self, context: object, dimensions: int) -> NativeSlangType:
        """N/A"""

    def resolve_type(self, context: object, bound_type: NativeSlangType) -> NativeSlangType:
        """N/A"""

    def resolve_dimensionality(self, context: object, binding: object, vector_target_type: NativeSlangType) -> int:
        """N/A"""

    def build_shader_object(self, context: object, data: object) -> slangpy.ShaderObject:
        """N/A"""

class NativeBoundVariableRuntime(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def access(self) -> tuple[AccessType, AccessType]:
        """N/A"""

    @access.setter
    def access(self, arg: tuple[AccessType, AccessType], /) -> None: ...

    @property
    def transform(self) -> Shape:
        """N/A"""

    @transform.setter
    def transform(self, arg: Shape, /) -> None: ...

    @property
    def python_type(self) -> NativeMarshall:
        """N/A"""

    @python_type.setter
    def python_type(self, arg: NativeMarshall, /) -> None: ...

    @property
    def vector_type(self) -> NativeSlangType:
        """N/A"""

    @vector_type.setter
    def vector_type(self, arg: NativeSlangType, /) -> None: ...

    @property
    def shape(self) -> Shape:
        """N/A"""

    @shape.setter
    def shape(self, arg: Shape, /) -> None: ...

    @property
    def is_param_block(self) -> bool:
        """N/A"""

    @is_param_block.setter
    def is_param_block(self, arg: bool, /) -> None: ...

    @property
    def variable_name(self) -> str:
        """N/A"""

    @variable_name.setter
    def variable_name(self, arg: str, /) -> None: ...

    @property
    def children(self) -> dict[str, NativeBoundVariableRuntime] | None:
        """N/A"""

    @children.setter
    def children(self, arg: Mapping[str, NativeBoundVariableRuntime], /) -> None: ...

    def populate_call_shape(self, arg0: Sequence[int], arg1: object, arg2: NativeCallData, /) -> None:
        """N/A"""

    def read_call_data_post_dispatch(self, arg0: CallContext, arg1: dict, arg2: object, /) -> None:
        """N/A"""

    def write_raw_dispatch_data(self, arg0: dict, arg1: object, /) -> None:
        """N/A"""

    def read_output(self, arg0: CallContext, arg1: object, /) -> object:
        """N/A"""

class NativeBoundCallRuntime(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def args(self) -> list[NativeBoundVariableRuntime]:
        """N/A"""

    @args.setter
    def args(self, arg: Sequence[NativeBoundVariableRuntime], /) -> None: ...

    @property
    def kwargs(self) -> dict[str, NativeBoundVariableRuntime]:
        """N/A"""

    @kwargs.setter
    def kwargs(self, arg: Mapping[str, NativeBoundVariableRuntime], /) -> None: ...

    def find_kwarg(self, arg: str, /) -> NativeBoundVariableRuntime:
        """N/A"""

    def calculate_call_shape(self, arg0: int, arg1: list, arg2: dict, arg3: NativeCallData, /) -> Shape:
        """N/A"""

    def read_call_data_post_dispatch(self, arg0: CallContext, arg1: dict, arg2: list, arg3: dict, /) -> None:
        """N/A"""

    def write_raw_dispatch_data(self, arg0: dict, arg1: dict, /) -> None:
        """N/A"""

class NativeCallRuntimeOptions(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def uniforms(self) -> list:
        """N/A"""

    @uniforms.setter
    def uniforms(self, arg: list, /) -> None: ...

    @property
    def _native_this(self) -> object:
        """N/A"""

    @_native_this.setter
    def _native_this(self, arg: object, /) -> None: ...

    @property
    def cuda_stream(self) -> slangpy.NativeHandle:
        """N/A"""

    @cuda_stream.setter
    def cuda_stream(self, arg: slangpy.NativeHandle, /) -> None: ...

class NativeCallData(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    @property
    def device(self) -> slangpy.Device:
        """N/A"""

    @device.setter
    def device(self, arg: slangpy.Device, /) -> None: ...

    @property
    def pipeline(self) -> slangpy.Pipeline:
        """N/A"""

    @pipeline.setter
    def pipeline(self, arg: slangpy.Pipeline, /) -> None: ...

    @property
    def shader_table(self) -> slangpy.ShaderTable:
        """N/A"""

    @shader_table.setter
    def shader_table(self, arg: slangpy.ShaderTable, /) -> None: ...

    @property
    def call_dimensionality(self) -> int:
        """N/A"""

    @call_dimensionality.setter
    def call_dimensionality(self, arg: int, /) -> None: ...

    @property
    def runtime(self) -> NativeBoundCallRuntime:
        """N/A"""

    @runtime.setter
    def runtime(self, arg: NativeBoundCallRuntime, /) -> None: ...

    @property
    def call_mode(self) -> CallMode:
        """N/A"""

    @call_mode.setter
    def call_mode(self, arg: CallMode, /) -> None: ...

    @property
    def call_data_mode(self) -> CallDataMode:
        """N/A"""

    @call_data_mode.setter
    def call_data_mode(self, arg: CallDataMode, /) -> None: ...

    @property
    def last_call_shape(self) -> Shape:
        """N/A"""

    @property
    def debug_name(self) -> str:
        """N/A"""

    @debug_name.setter
    def debug_name(self, arg: str, /) -> None: ...

    @property
    def logger(self) -> slangpy.Logger:
        """N/A"""

    @logger.setter
    def logger(self, arg: slangpy.Logger | None) -> None: ...

    def call(self, opts: NativeCallRuntimeOptions, *args, **kwargs) -> object:
        """N/A"""

    def append_to(self, opts: NativeCallRuntimeOptions, command_buffer: slangpy.CommandEncoder, *args, **kwargs) -> object:
        """N/A"""

    def _py_torch_call(self, function: NativeFunctionNode, opts: NativeCallRuntimeOptions, args: tuple, kwargs: dict) -> object:
        """N/A"""

    @property
    def call_group_shape(self) -> Shape:
        """N/A"""

    @call_group_shape.setter
    def call_group_shape(self, arg: Shape | None) -> None: ...

    @property
    def torch_integration(self) -> bool:
        """N/A"""

    @torch_integration.setter
    def torch_integration(self, arg: bool) -> None: ...

    @property
    def torch_autograd(self) -> bool:
        """N/A"""

    @torch_autograd.setter
    def torch_autograd(self, arg: bool) -> None: ...

    def log(self, level: slangpy.LogLevel, msg: str, frequency: slangpy.LogFrequency = slangpy.LogFrequency.always) -> None:
        """
        Log a message.

        Parameter ``level``:
            The log level.

        Parameter ``msg``:
            The message.

        Parameter ``frequency``:
            The log frequency.
        """

    def log_debug(self, msg: str) -> None: ...

    def log_info(self, msg: str) -> None: ...

    def log_warn(self, msg: str) -> None: ...

    def log_error(self, msg: str) -> None: ...

    def log_fatal(self, msg: str) -> None: ...

class NativeCallDataCache(slangpy.Object):
    def __init__(self) -> None:
        """N/A"""

    def get_value_signature(self, builder: SignatureBuilder, o: object) -> None:
        """N/A"""

    def get_args_signature(self, builder: SignatureBuilder, *args, **kwargs) -> None:
        """N/A"""

    def find_call_data(self, signature: str) -> NativeCallData:
        """N/A"""

    def add_call_data(self, signature: str, call_data: NativeCallData) -> None:
        """N/A"""

    def lookup_value_signature(self, o: object) -> str | None:
        """N/A"""

class Shape:
    def __init__(self, *args) -> None:
        """N/A"""

    def __add__(self, arg: Shape, /) -> Shape:
        """N/A"""

    def __getitem__(self, index: int) -> int:
        """N/A"""

    def __len__(self) -> int:
        """N/A"""

    @property
    def valid(self) -> bool:
        """N/A"""

    @property
    def concrete(self) -> bool:
        """N/A"""

    def as_tuple(self) -> tuple:
        """N/A"""

    def as_list(self) -> list[int]:
        """N/A"""

    def calc_contiguous_strides(self) -> Shape:
        """N/A"""

    def __repr__(self) -> str:
        """N/A"""

    def __str__(self) -> str:
        """N/A"""

    def __eq__(self, arg: object, /) -> bool:
        """N/A"""

class CallContext(slangpy.Object):
    def __init__(self, device: slangpy.Device, call_shape: Shape, call_mode: CallMode) -> None:
        """N/A"""

    @property
    def device(self) -> slangpy.Device:
        """N/A"""

    @property
    def call_shape(self) -> Shape:
        """N/A"""

    @property
    def call_mode(self) -> CallMode:
        """N/A"""

class TensorRef(NativeObject):
    def __init__(self, id: int, tensor: Annotated[ArrayLike, dict(device='cuda')]) -> None:
        """N/A"""

    @property
    def id(self) -> int:
        """N/A"""

    @id.setter
    def id(self, arg: int) -> None: ...

    @property
    def tensor(self) -> Annotated[ArrayLike, dict(device='cuda')] | None:
        """N/A"""

    @tensor.setter
    def tensor(self, arg: Annotated[ArrayLike, dict(device='cuda')] | None) -> None: ...

    @property
    def interop_buffer(self) -> slangpy.Buffer:
        """N/A"""

    @interop_buffer.setter
    def interop_buffer(self, arg: slangpy.Buffer | None) -> None: ...

    @property
    def grad_in(self) -> TensorRef:
        """N/A"""

    @grad_in.setter
    def grad_in(self, arg: TensorRef | None) -> None: ...

    @property
    def grad_out(self) -> TensorRef:
        """N/A"""

    @grad_out.setter
    def grad_out(self, arg: TensorRef | None) -> None: ...

    @property
    def last_access(self) -> tuple[AccessType, AccessType]:
        """N/A"""

    @last_access.setter
    def last_access(self, arg: tuple[AccessType, AccessType]) -> None: ...

class StridedBufferViewDesc:
    def __init__(self) -> None: ...

    @property
    def dtype(self) -> NativeSlangType: ...

    @dtype.setter
    def dtype(self, arg: NativeSlangType, /) -> None: ...

    @property
    def element_layout(self) -> slangpy.TypeLayoutReflection: ...

    @element_layout.setter
    def element_layout(self, arg: slangpy.TypeLayoutReflection, /) -> None: ...

    @property
    def offset(self) -> int: ...

    @offset.setter
    def offset(self, arg: int, /) -> None: ...

    @property
    def shape(self) -> Shape: ...

    @shape.setter
    def shape(self, arg: Shape, /) -> None: ...

    @property
    def strides(self) -> Shape: ...

    @strides.setter
    def strides(self, arg: Shape, /) -> None: ...

    @property
    def usage(self) -> slangpy.BufferUsage: ...

    @usage.setter
    def usage(self, arg: slangpy.BufferUsage, /) -> None: ...

    @property
    def memory_type(self) -> slangpy.MemoryType: ...

    @memory_type.setter
    def memory_type(self, arg: slangpy.MemoryType, /) -> None: ...

class StridedBufferView(NativeObject):
    def __init__(self, arg0: slangpy.Device, arg1: StridedBufferViewDesc, arg2: slangpy.Buffer, /) -> None: ...

    @property
    def device(self) -> slangpy.Device: ...

    @property
    def dtype(self) -> NativeSlangType: ...

    @property
    def offset(self) -> int: ...

    @property
    def shape(self) -> Shape: ...

    @property
    def strides(self) -> Shape: ...

    @property
    def element_count(self) -> int: ...

    @property
    def usage(self) -> slangpy.BufferUsage: ...

    @property
    def memory_type(self) -> slangpy.MemoryType: ...

    @property
    def storage(self) -> slangpy.Buffer: ...

    def clear(self, cmd: slangpy.CommandEncoder | None = None) -> None: ...

    def cursor(self, start: int | None = None, count: int | None = None) -> slangpy.BufferCursor: ...

    def uniforms(self) -> dict: ...

    def to_numpy(self) -> NDArray:
        """N/A"""

    def to_torch(self) -> ArrayLike:
        """N/A"""

    def copy_from_numpy(self, data: ArrayLike) -> None:
        """N/A"""

    def copy_from_torch(self, tensor: object) -> None: ...

    def is_contiguous(self) -> bool:
        """N/A"""

    def point_to(self, target: StridedBufferView) -> None:
        """N/A"""

class NativeNDBufferDesc(StridedBufferViewDesc):
    def __init__(self) -> None: ...

class NativeNDBuffer(StridedBufferView):
    def __init__(self, device: slangpy.Device, desc: NativeNDBufferDesc, buffer: slangpy.Buffer | None = None) -> None: ...

    def broadcast_to(self, shape: Shape) -> NativeNDBuffer: ...

    def view(self, shape: Shape, strides: Shape = ..., offset: int = 0) -> NativeNDBuffer: ...

    def __getitem__(self, arg: object, /) -> NativeNDBuffer: ...

    def __repr__(self) -> str: ...

class NativeNDBufferMarshall(NativeMarshall):
    def __init__(self, dims: int, writable: bool, slang_type: NativeSlangType, slang_element_type: NativeSlangType, element_layout: slangpy.TypeLayoutReflection) -> None:
        """N/A"""

    @property
    def dims(self) -> int: ...

    @property
    def writable(self) -> bool: ...

    @property
    def slang_element_type(self) -> NativeSlangType: ...

class NativeNumpyMarshall(NativeNDBufferMarshall):
    def __init__(self, dims: int, slang_type: NativeSlangType, slang_element_type: NativeSlangType, element_layout: slangpy.TypeLayoutReflection, numpydtype: object) -> None:
        """N/A"""

    @property
    def dtype(self) -> "dlpack::dtype": ...

class FunctionNodeType(enum.Enum):
    _new_member_ = __new__

    _use_args_: bool = False

    _member_names_: list = ...

    _member_map_: dict = ...

    _value2member_map_: dict = ...

    _unhashable_values_: list = []

    _value_repr_: None = None

    unknown = 0

    uniforms = 1

    kernelgen = 2

    this = 3

    cuda_stream = 4

    ray_tracing = 5

class NativeFunctionNode(NativeObject):
    def __init__(self, parent: NativeFunctionNode | None, type: FunctionNodeType, data: object | None) -> None:
        """N/A"""

    @property
    def _native_parent(self) -> NativeFunctionNode: ...

    @property
    def _native_type(self) -> FunctionNodeType: ...

    @property
    def _native_data(self) -> object: ...

    def _find_native_root(self) -> NativeFunctionNode:
        """N/A"""

    def _native_build_call_data(self, cache: NativeCallDataCache, *args, **kwargs) -> NativeCallData:
        """N/A"""

    def _native_call(self, cache: NativeCallDataCache, *args, **kwargs) -> object:
        """N/A"""

    def _native_append_to(self, cache: NativeCallDataCache, command_encoder: slangpy.CommandEncoder, *args, **kwargs) -> None:
        """N/A"""

    def generate_call_data(self, *args, **kwargs) -> NativeCallData:
        """N/A"""

    def read_signature(self, builder: SignatureBuilder) -> None:
        """N/A"""

    def gather_runtime_options(self, options: NativeCallRuntimeOptions) -> None:
        """N/A"""

    def __repr__(self) -> str: ...

class NativePackedArg(NativeObject):
    def __init__(self, python: NativeMarshall, shader_object: slangpy.ShaderObject, python_object: object) -> None:
        """N/A"""

    @property
    def python(self) -> NativeMarshall:
        """N/A"""

    @property
    def shader_object(self) -> slangpy.ShaderObject:
        """N/A"""

    @property
    def python_object(self) -> object:
        """N/A"""

    def __repr__(self) -> str: ...

def get_texture_shape(texture: slangpy.Texture, mip: int = 0) -> Shape:
    """N/A"""

class NativeBufferMarshall(NativeMarshall):
    def __init__(self, slang_type: NativeSlangType, usage: slangpy.BufferUsage) -> None:
        """N/A"""

    def write_shader_cursor_pre_dispatch(self, context: CallContext, binding: NativeBoundVariableRuntime, cursor: slangpy.ShaderCursor, value: object, read_back: list) -> None:
        """N/A"""

    def get_shape(self, value: object) -> Shape:
        """N/A"""

    @property
    def usage(self) -> slangpy.BufferUsage: ...

    @property
    def slang_type(self) -> NativeSlangType: ...

class NativeTextureMarshall(NativeMarshall):
    def __init__(self, slang_type: NativeSlangType, element_type: NativeSlangType, resource_shape: slangpy.TypeReflection.ResourceShape, format: slangpy.Format, usage: slangpy.TextureUsage, dims: int) -> None:
        """N/A"""

    def write_shader_cursor_pre_dispatch(self, context: CallContext, binding: NativeBoundVariableRuntime, cursor: slangpy.ShaderCursor, value: object, read_back: list) -> None:
        """N/A"""

    def get_shape(self, value: object) -> Shape:
        """N/A"""

    def get_texture_shape(self, texture: slangpy.Texture, mip: int) -> Shape:
        """N/A"""

    @property
    def resource_shape(self) -> slangpy.TypeReflection.ResourceShape:
        """N/A"""

    @property
    def usage(self) -> slangpy.TextureUsage:
        """N/A"""

    @property
    def texture_dims(self) -> int:
        """N/A"""

    @property
    def slang_element_type(self) -> NativeSlangType:
        """N/A"""

class NativeTensorDesc(StridedBufferViewDesc):
    def __init__(self) -> None: ...

class NativeTensor(StridedBufferView):
    def __init__(self, desc: NativeTensorDesc, storage: slangpy.Buffer, grad_in: NativeTensor | None, grad_out: NativeTensor | None) -> None: ...

    @property
    def grad_in(self) -> NativeTensor: ...

    @grad_in.setter
    def grad_in(self, arg: NativeTensor, /) -> None: ...

    @property
    def grad_out(self) -> NativeTensor: ...

    @grad_out.setter
    def grad_out(self, arg: NativeTensor, /) -> None: ...

    @property
    def grad(self) -> NativeTensor: ...

    def broadcast_to(self, shape: Shape) -> NativeTensor: ...

    def view(self, shape: Shape, strides: Shape = ..., offset: int = 0) -> NativeTensor: ...

    def __getitem__(self, arg: object, /) -> NativeTensor: ...

    def with_grads(self, grad_in: NativeTensor | None = None, grad_out: NativeTensor | None = None, zero: bool = True) -> NativeTensor: ...

    def detach(self) -> NativeTensor: ...

    def __repr__(self) -> str: ...

class NativeTensorMarshall(NativeMarshall):
    def __init__(self, dims: int, writable: bool, slang_type: NativeSlangType, slang_element_type: NativeSlangType, element_layout: slangpy.TypeLayoutReflection, d_in: NativeTensorMarshall | None, d_out: NativeTensorMarshall | None) -> None:
        """N/A"""

    @property
    def dims(self) -> int: ...

    @property
    def writable(self) -> bool: ...

    @property
    def slang_element_type(self) -> NativeSlangType: ...

    @property
    def d_in(self) -> NativeTensorMarshall: ...

    @property
    def d_out(self) -> NativeTensorMarshall: ...

class NativeValueMarshall(NativeMarshall):
    def __init__(self) -> None:
        """N/A"""
