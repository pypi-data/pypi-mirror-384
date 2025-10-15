from typing import Any, Type, cast

from planar.task_local import TaskLocal

data: TaskLocal[Any] = TaskLocal()


def set_tool_context(ctx: Any):
    return data.set(ctx)


def get_tool_context[T](_: Type[T]) -> T:
    return cast(T, data.get())


def clear_tool_context():
    return data.clear()
