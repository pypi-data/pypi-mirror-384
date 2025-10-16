from typing import Any, Callable, Coroutine, TypeGuard

from planar.utils import P, R, T, U
from planar.workflows.wrappers import StepWrapper


def func_full_name(func: Callable[..., Any]) -> str:
    return f"{func.__module__}.{func.__qualname__}"


def is_workflow_step(
    callable: Callable[P, Coroutine[T, U, R]],
) -> TypeGuard[StepWrapper[P, T, U, R]]:
    return isinstance(callable, StepWrapper)


def unwrap_workflow_step(step_fn: Callable) -> Callable:
    """
    Return the underlying function for wrapped step callables
    or return the function itself if it is not a workflow step.
    """

    if is_workflow_step(step_fn):
        return step_fn.original_fn
    return step_fn
