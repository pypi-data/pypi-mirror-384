"""
"""
from __future__ import annotations

import inspect
from functools import wraps
from packaging import version
from typing import Any
from typing import Callable
from typing import Literal
from typing import NamedTuple
from typing import TYPE_CHECKING
import warnings

import gradio as gr
from gradio.context import Context
from gradio.context import LocalContext
from gradio.helpers import Progress
from gradio.helpers import TrackedIterable
from gradio.queueing import Queue
from typing_extensions import ParamSpec
from typing_extensions import TypeAlias

from ..utils import SimpleQueue
from .types import GeneratorResQueueResult
from .types import GradioQueueEvent
from .types import RegularResQueueResult


QUEUE_RPC_METHODS = [
    "set_progress",
    "log_message",
]


try:
    Success = gr.Success # pyright: ignore[reportAttributeAccessIssue] (Gradio<5.10)
except AttributeError: # pragma: no cover
    Success = gr.Info

Level: TypeAlias = "Literal['success', 'info', 'warning']"

def modal(level: Level):
    if level == 'info':
        return gr.Info
    if level == 'success':
        return Success
    if level == 'warning':
        return gr.Warning


class GradioPartialContext(NamedTuple):
    event_id: str | None
    in_event_listener: bool
    progress: Progress | None

    @staticmethod
    def get():
        TrackedIterable.__reduce__ = tracked_iterable__reduce__
        return GradioPartialContext(
            event_id=LocalContext.event_id.get(None),
            in_event_listener=LocalContext.in_event_listener.get(False),
            progress=LocalContext.progress.get(None),
        )

    @staticmethod
    def apply(context: 'GradioPartialContext'):
        LocalContext.event_id.set(context.event_id)
        LocalContext.in_event_listener.set(context.in_event_listener)
        LocalContext.progress.set(context.progress)


def get_queue_instance():
    blocks = LocalContext.blocks.get(None)
    if blocks is None: # pragma: no cover
        return None
    return blocks._queue


def get_event():
    queue = get_queue_instance()
    event_id = LocalContext.event_id.get(None)
    if queue is None:
        return None
    if event_id is None: # pragma: no cover
        return None
    for job in queue.active_jobs:
        if job is None: # pragma: no cover
            continue
        for event in job:
            if event._id == event_id:
                return event


def get_server_port() -> int | None:
    from_request_context = True
    if (blocks := LocalContext.blocks.get(None)) is None: # Request
        from_request_context = False
        if (blocks := Context.root_block) is None: # Caching
            return None
    if (server := getattr(blocks, 'server', None)) is None: # pragma: no cover (Gradio 4)
        if from_request_context:
            warnings.warn("Gradio: No blocks.server inside a request") # pragma: no cover
        return -1
    if TYPE_CHECKING:
        assert (server := blocks.server)
    return server.config.port


def try_process_queue_event(method_name: str, *args, **kwargs):
    queue = get_queue_instance()
    if queue is None: # pragma: no cover
        warnings.warn("ZeroGPU: Cannot get Gradio app Queue instance")
        return
    method = getattr(queue, method_name, None)
    assert callable(method)
    method(*args, **kwargs)


def patch_gradio_queue(
    res_queue: SimpleQueue[RegularResQueueResult | None] | SimpleQueue[GeneratorResQueueResult | None],
):

    def rpc_method(method_name: str):
        def method(*args, **kwargs):
            if args and isinstance(args[0], Queue):
                args = args[1:] # drop `self`
            res_queue.put(GradioQueueEvent(method_name, args, kwargs))
        return method

    for method_name in QUEUE_RPC_METHODS:
        if (method := getattr(Queue, method_name, None)) is None: # pragma: no cover
            warnings.warn(f"ZeroGPU: Gradio Queue has no {method_name} attribute")
            continue
        if not callable(method): # pragma: no cover
            warnings.warn(f"ZeroGPU: Gradio Queue {method_name} is not callable")
            continue
        setattr(Queue, method_name, rpc_method(method_name))

    TrackedIterable.__reduce__ = tracked_iterable__reduce__


def tracked_iterable__reduce__(self):
    res: tuple = super(TrackedIterable, self).__reduce__() # type: ignore
    cls, base, state, *_ = res
    return cls, base,{**state, **{
        'iterable': None,
        '_tqdm': None,
    }}


def supports_auth():
    return version.parse(gr.__version__) >= version.Version('4.27.0')


Param = ParamSpec('Param')

_orig_launch = gr.Blocks.launch

def one_launch(task: Callable[Param, None], *task_args: Param.args, **task_kwargs: Param.kwargs):
    @wraps(gr.Blocks.launch)
    def launch(*args, **kwargs):
        task(*task_args, **task_kwargs)
        gr.Blocks.launch = _orig_launch
        return gr.Blocks.launch(*args, **kwargs)
    gr.Blocks.launch = launch


class HTMLError(gr.Error):
    def __str__(self): # pragma: no cover
        return str(self.message)


def error(title: str, message: str, html: bool = False):
    params = inspect.signature(gr.Error).parameters
    kwargs: dict[str, Any] = {}
    if 'title' in params:
        kwargs = {**kwargs, 'title': title}
    if 'print_exception' in params:
        kwargs = {**kwargs, 'print_exception': False}
    error_cls = HTMLError if html else gr.Error
    return error_cls(message, **kwargs)


def info(title: str, message: str, level: Level = 'info'):
    params = inspect.signature(gr.Info).parameters
    kwargs: dict[str, Any] = {}
    if 'title' in params:
        kwargs = {**kwargs, 'title': title}
    info_cls = modal(level)
    return info_cls(message, **kwargs)
