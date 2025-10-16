"""
"""
# pyright: reportPrivateImportUsage=false

from __future__ import annotations

import gc
import multiprocessing
import os
import shutil
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import copy_context
from pathlib import Path
from typing import Any
from typing import Callable

import torch
from torch.overrides import TorchFunctionMode
from torch.overrides import resolve_name
from torch.utils._python_dispatch import is_traceable_wrapper_subclass
from torch.utils._python_dispatch import transform_subclass
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_map_only
from torch.utils.weak import WeakTensorKeyDictionary

from ...config import Config
from ..tqdm import tqdm
from ..utils import malloc_trim
from . import cudart
from .packing import ZeroGPUTensorPack
from .packing import pack_tensors
from .packing import pack_to_cuda
from .static import *
from .utils import empty_like_raw_alloc
from .types import AliasId


PINNED_MEMORY_RATIO_LIMIT = 0.1

OPS_INPUTS_CHECK_NO_RETURN = (
    torch.Tensor.equal,
)

OPS_INPUT_CHECK_SELF_RETURN = (
    torch.Tensor.set_, # probably never dispatched
    torch.ops.aten.set_.source_Tensor, # pyright: ignore [reportAttributeAccessIssue]
)

OFFLOADED_ERROR_MESSAGE = "Cannot apply function {} on disk-offloaded Tensor {}"

_tensor_make_subclass = torch.Tensor._make_subclass
_asarray           = torch.asarray
_device            = torch.device
_cuda_init         = torch._C._cuda_init
_cuda_exchange_device = torch.cuda._exchange_device
_cuda_available      = torch.cuda.is_available
_cuda_device_count   = torch.cuda.device_count
_cuda_current_device = torch.cuda.current_device
_cuda_synchronize    = torch.cuda.synchronize
_cuda_get_device_capability   = torch.cuda.get_device_capability
_cuda_get_device_properties   = torch.cuda.get_device_properties
_cuda_get_device_name         = torch.cuda.get_device_name
_cuda_memory_stats_as_nested_dict = torch.cuda.memory.memory_stats_as_nested_dict
_cuda_cudart = torch.cuda.cudart

# PyTorch 2.3
_cuda_maybe_exchange_device = getattr(torch.cuda, '_maybe_exchange_device', None)


cuda_aliases: dict[torch.Tensor, torch.Tensor | None] = WeakTensorKeyDictionary() # pyright: ignore [reportAssignmentType]

tensor_packs: list[ZeroGPUTensorPack] = []

class ZeroGPUTensor(torch.Tensor):
    pass

def empty_fake(tensor: torch.Tensor):
    fake = empty_like_raw_alloc(tensor, requires_grad=tensor.requires_grad)
    if fake.__class__ != tensor.__class__:
        fake = _tensor_make_subclass(tensor.__class__, fake, require_grad=tensor.requires_grad) # pyright: ignore [reportArgumentType]
    return fake

# Torch 2.5: https://github.com/pytorch/pytorch/issues/144152
def no_int_device(*args, **kwargs):
    if len(args) and isinstance(index := args[0], int):
        args = (f'cuda:{index}', *args[1:])
    if isinstance(index := kwargs.get('device'), int):
        kwargs['device'] = f'cuda:{index}'
    return args, kwargs


class ZeroGPUFunctionMode(TorchFunctionMode):

    def __torch_function__(self, func, types, args=(), kwargs: dict[str, Any] | None = None):

        kwargs = {} if kwargs is None else kwargs

        if func == torch._C._nn._parse_to: # pyright: ignore [reportAttributeAccessIssue]
            args, kwargs = no_int_device(*args, **kwargs)
            return func(*args, **kwargs)

        # Redispatch: tensor.cuda() -> tensor.to(device='cuda')
        if func == torch.Tensor.cuda or func == torch.Tensor.cpu:
            memory_format = kwargs.get('memory_format')
            return self.__torch_function__(torch.Tensor.to, types, (args[0],), {
                'device': 'cuda' if func == torch.Tensor.cuda else 'cpu',
                **({'memory_format': memory_format} if memory_format is not None else {}),
            })

        # Redispatch: tensor.to('cuda') -> tensor.to(device='cuda')
        if func == torch.Tensor.to and len(args) > 1:
            parse_to_args, parse_to_kwargs = no_int_device(*args[1:], **kwargs)
            # We are using nn._parse_to utility to parse generic Tensor.to but nn does not accept copy kwarg
            copy_kwarg = {'copy': parse_to_kwargs.pop('copy')} if 'copy' in parse_to_kwargs else {}
            device, dtype, _, memory_format = torch._C._nn._parse_to(*parse_to_args, **parse_to_kwargs) # pyright: ignore [reportAttributeAccessIssue]
            return self.__torch_function__(torch.Tensor.to, types, (args[0],), {
                'device': device,
                'dtype': dtype,
                'memory_format': memory_format,
            } | copy_kwarg)

        if func == torch.Tensor.data.__set__: # pyright: ignore [reportAttributeAccessIssue]
            self, target = args
            if target in cuda_aliases:
                if (target_original := cuda_aliases[target]) is None:
                    raise Exception(OFFLOADED_ERROR_MESSAGE.format(resolve_name(func), target))
                original = empty_fake(self)
                original.data = target_original
                cuda_aliases[self] = original
            elif self in cuda_aliases:
                del cuda_aliases[self]
            self.data = target
            return

        if func == torch.Tensor.device.__get__:
            tensor, = args
            if tensor in cuda_aliases:
                return torch.device('cuda', index=0)

        elif func == torch.Tensor.__repr__:
            tensor, = args
            if tensor in cuda_aliases:
                if (original := cuda_aliases[tensor]) is None:
                    original = tensor.to('meta')
                original_class = original.__class__
                original.__class__ = ZeroGPUTensor
                try:
                    return func(original, **kwargs)
                finally:
                    original.__class__ = original_class

        elif func == torch.Tensor.untyped_storage:
            tensor, = args
            if tensor in cuda_aliases:
                if (original := cuda_aliases[tensor]) is None:
                    raise Exception(OFFLOADED_ERROR_MESSAGE.format(resolve_name(func), tensor))
                res = func(original, **kwargs)
                res._zerogpu = True
                return res

        cuda: bool | None = None

        # Handle device kwarg
        if (device := kwargs.get('device')) is not None:
            device = torch.device(device)
            if device.type == 'cuda':
                kwargs['device'] = torch.device('cpu')
                cuda = True
            else:
                cuda = False

        # Swap fake inputs with original data
        swapped = {}
        inputs_are_cuda = set()
        def swap(tensor: torch.Tensor):
            nonlocal inputs_are_cuda
            if tensor not in cuda_aliases:
                inputs_are_cuda |= {False}
                return tensor
            if (original := cuda_aliases[tensor]) is None:
                raise Exception(OFFLOADED_ERROR_MESSAGE.format(resolve_name(func), tensor))
            swapped[original] = tensor
            inputs_are_cuda |= {True}
            return original
        args_ = tree_map_only(torch.Tensor, swap, args)
        kwargs_ = tree_map_only(torch.Tensor, swap, kwargs)
        if inputs_are_cuda == {True}:
            if cuda is not False:
                cuda = True

        # Wrapper tensors special case (torchao quickix)
        if len(args) == 1 and is_traceable_wrapper_subclass(wrapper_tensor := args[0]):
            if func in {
                torch.Tensor.detach,
                torch.ops.aten.alias.default, # pyright: ignore [reportAttributeAccessIssue]
                torch.ops.aten.clone.default, # pyright: ignore [reportAttributeAccessIssue]
            }:
                with self:
                    return transform_subclass(wrapper_tensor, lambda _, t: func(t))

        res = func(*args_, **kwargs_)

        # Re-generate swapped fakes in case of mutation
        for original, fake in swapped.items():
            fake.data = empty_fake(original)

        # Special case for Tensor indexing where only 'self' matters
        if func in {
            torch.ops.aten.index.Tensor, # pyright: ignore [reportAttributeAccessIssue]
            torch.Tensor.__getitem__, # PyTorch 2.4+
        }:
            self = args[0]
            cuda = self in cuda_aliases
            inputs_are_cuda = {cuda}

        # Emulate device check
        if isinstance(res, torch.Tensor) or func in OPS_INPUTS_CHECK_NO_RETURN:
            self = None
            if len(args_) >= 1 and isinstance(args_[0], torch.Tensor):
                self = args_[0]
            # Only raise if func does not return its first input (Tensor.copy_)
            if res is not self or func in OPS_INPUT_CHECK_SELF_RETURN:
                if inputs_are_cuda == {True, False}:
                    raise RuntimeError(
                        "Expected all tensors to be on the same device, "
                        "but found at least two devices, cuda:0 (ZeroGPU) and cpu!"
                    )

        # Register output
        def register(tensor: torch.Tensor):
            if tensor in swapped and cuda is not False:
                return swapped[tensor]
            if cuda is not True:
                return tensor
            fake = empty_fake(tensor)
            cuda_aliases[fake] = tensor
            return fake

        return tree_map_only(torch.Tensor, register, res)

# When enabling DispatchMode, some aten ops are dispatched to FunctionMode
# We are using it for aten.alias.default and aten.set_.source_Tensor
class DefaultDispatchMode(TorchDispatchMode):
    def __torch_dispatch__(self, func, types, args=(), kwargs: dict[str, Any] | None = None):
        return func(*args, **(kwargs or {}))


function_mode = ZeroGPUFunctionMode()
dispatch_mode = DefaultDispatchMode()


def _untyped_storage_new_register(*args, **kwargs):
    cuda = False
    if (device := kwargs.get('device')) is not None:
        device = torch.device(device)
        if device.type == 'cuda':
            cuda = True
            del kwargs['device']
    storage = torch._C.StorageBase.__new__(*args, **kwargs)
    if cuda:
        storage._zerogpu = True
    return storage

@property
def _untyped_storage_device(self):
    if hasattr(self, '_zerogpu'):
        return torch.device('cuda', index=0)
    return torch._C.StorageBase.device.__get__(self) # pyright: ignore [reportAttributeAccessIssue]

# Force dispatch
def _tensor_make_subclass_function_mode(*args, **kwargs):
    with torch._C.DisableTorchFunction():
        return function_mode.__torch_function__(_tensor_make_subclass, (), args=args, kwargs=kwargs)
def _asarray_function_mode(*args, **kwargs):
    with torch._C.DisableTorchFunction():
        return function_mode.__torch_function__(_asarray, (), args=args, kwargs=kwargs)

class _DeviceStringOnlyMeta(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, _device)

class _DeviceStringOnly(metaclass=_DeviceStringOnlyMeta):
    def __new__(cls, *args, **kwargs):
        args, kwargs = no_int_device(*args, **kwargs)
        return _device(*args, **kwargs)

def _cuda_init_raise():
    raise RuntimeError(
        "CUDA must not be initialized in the main process "
        "on Spaces with Stateless GPU environment.\n"
        "You can look at this Stacktrace to find out "
        "which part of your code triggered a CUDA init"
    )

def _cuda_dummy_exchange_device(device):
    assert device in {-1, 0}
    return device

def patch():
    function_mode.__enter__()
    dispatch_mode.__enter__()
    # TODO: only patch bellow methods on current Thread to be consistent with TorchModes
    # (or hijack threading.Thread.__init__ to force Modes on all threads)
    torch.Tensor._make_subclass = _tensor_make_subclass_function_mode # pyright: ignore [reportAttributeAccessIssue]
    torch.UntypedStorage.__new__ = _untyped_storage_new_register
    torch.UntypedStorage.device  = _untyped_storage_device # pyright: ignore [reportAttributeAccessIssue]
    torch.asarray           = _asarray_function_mode
    torch.device            = _DeviceStringOnly
    torch._C._cuda_init     = _cuda_init_raise
    torch.cuda._exchange_device = _cuda_dummy_exchange_device
    torch.cuda.is_available   = lambda: True
    torch.cuda.device_count   = lambda: 1
    torch.cuda.current_device = lambda: 0
    torch.cuda.synchronize    = lambda *args: None
    torch.cuda.get_device_capability = lambda *args, **kwargs: CUDA_DEVICE_CAPABILITY
    torch.cuda.get_device_properties = lambda *args, **kwargs: CUDA_DEVICE_PROPERTIES
    torch.cuda.get_device_name       = lambda *args, **kwargs: CUDA_DEVICE_NAME
    torch.cuda.memory.memory_stats_as_nested_dict = lambda *args, **kwargs: CUDA_MEMORY_STATS_AS_NESTED_DICT
    torch.cuda.cudart = lambda: cudart
    # PyTorch 2.3
    if _cuda_maybe_exchange_device is not None: # pragma: no cover
        setattr(torch.cuda, '_maybe_exchange_device', _cuda_dummy_exchange_device)
    bitsandbytes().patch()

def unpatch():
    try:
        dispatch_mode.__exit__(None, None, None)
        function_mode.__exit__(None, None, None)
    except RuntimeError:
        pass # patch() and unpatch() called from != threads
    torch.Tensor._make_subclass = _tensor_make_subclass
    torch.UntypedStorage.__new__ = torch._C.StorageBase.__new__
    torch.UntypedStorage.device  = torch._C.StorageBase.device # pyright: ignore [reportAttributeAccessIssue]
    torch.asarray           = _asarray
    torch.device            = _device
    torch._C._cuda_init     = _cuda_init
    torch.cuda._exchange_device = _cuda_exchange_device
    torch.cuda.is_available   = _cuda_available
    torch.cuda.device_count   = _cuda_device_count
    torch.cuda.current_device = _cuda_current_device
    torch.cuda.synchronize    = _cuda_synchronize
    torch.cuda.get_device_capability = _cuda_get_device_capability
    torch.cuda.get_device_properties = _cuda_get_device_properties
    torch.cuda.get_device_name       = _cuda_get_device_name
    torch.cuda.memory.memory_stats_as_nested_dict = _cuda_memory_stats_as_nested_dict
    torch.cuda.cudart = _cuda_cudart
    # PyTorch 2.3
    if _cuda_maybe_exchange_device is not None: # pragma: no cover
        setattr(torch.cuda, '_maybe_exchange_device', _cuda_exchange_device)
    bitsandbytes().unpatch()


def _total_unpacked_size():
    tensors = [tensor for tensor in cuda_aliases.values() if tensor is not None]
    deduped = {AliasId.from_tensor(tensor): tensor for tensor in tensors}
    return sum([tensor.numel() * tensor.element_size() for tensor in deduped.values()])


def _pack(offload_dir: str):
    # Pack to disk
    originals: set[torch.Tensor] = set()
    originals_dedup: dict[AliasId, torch.Tensor] = {}
    fakes: dict[torch.Tensor, list[torch.Tensor]] = defaultdict(list)
    for fake, original in cuda_aliases.items():
        # TODO filter-out sparse Tensors
        if original is not None:
            original_id = AliasId.from_tensor(original)
            if original_id not in originals_dedup:
                originals_dedup[original_id] = original
                originals |= {original}
            fakes[originals_dedup[original_id]] += [fake]
    total_size = _total_unpacked_size()
    progress = tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        desc="ZeroGPU tensors packing",
    ) if tqdm is not None else nullcontext()
    with progress as progress:
        update = progress.update if progress is not None else lambda _: None
        pack = pack_tensors(originals, fakes, offload_dir, callback=update)
    tensor_packs.append(pack)
    # Free memory
    for fake_list in fakes.values():
        for fake in fake_list:
            cuda_aliases[fake] = None
    return total_size

def pack():
    shutil.rmtree(Config.zerogpu_offload_dir, ignore_errors=True)
    Path(Config.zerogpu_offload_dir).mkdir(parents=True)
    total_size = _pack(Config.zerogpu_offload_dir)
    gc.collect()
    malloc_trim()
    return total_size

def init(nvidia_uuid: str):
    os.environ['CUDA_VISIBLE_DEVICES'] = nvidia_uuid
    torch.Tensor([0]).cuda()

def size():
    return _total_unpacked_size() + sum([pack.total_size for pack in tensor_packs])

def _move(callback: Callable[[int]] | None = None):
    callback = callback if callback is not None else lambda _: None
    # CPU -> CUDA
    pinned_limit = _total_unpacked_size() * PINNED_MEMORY_RATIO_LIMIT
    moved: dict[AliasId, torch.Tensor] = {}
    for fake, original in cuda_aliases.items():
        if original is not None:
            original = torch.Tensor(original) # unwrap subclass
            original_id = AliasId.from_tensor(original)
            if original_id not in moved:
                if original.numel() * original.element_size() < pinned_limit:
                    original_cuda = original.pin_memory().cuda(non_blocking=True)
                else:
                    original_cuda = original.cuda()
                moved[original_id] = original_cuda
                callback(fake.numel() * fake.element_size())
    torch.cuda.synchronize()
    for fake, original in cuda_aliases.items():
        if original is not None:
            fake.data = moved[AliasId.from_tensor(original)]
    # Disk -> CUDA
    for tensor_pack in tensor_packs:
        pack_to_cuda(tensor_pack, callback=callback)
    bitsandbytes().move()

def move(callback: Callable[[int]] | None = None):
    callback = callback if callback is not None else lambda _: None
    with ThreadPoolExecutor(1) as e:
        e.submit(copy_context().run, _move, callback=callback).result()
    torch.cuda.synchronize()

def is_in_bad_fork():
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context('fork')) as e:
        f = e.submit(torch.cuda._is_in_bad_fork)
        return f.result()

def bitsandbytes():
    # Lazy import
    from . import bitsandbytes
    return bitsandbytes
