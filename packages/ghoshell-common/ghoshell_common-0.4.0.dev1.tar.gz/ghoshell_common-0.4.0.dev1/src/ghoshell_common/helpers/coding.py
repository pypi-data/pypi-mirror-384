from typing import TypeVar, Union, Callable
from types import ModuleType

T = TypeVar("T")


def unwrap(value: Union[T, Callable[[], T]]) -> T:
    """
    unwrap T from value or a callable
    """
    if isinstance(value, Callable):
        return value()
    return value


def reflect_module_code(module: ModuleType) -> str:
    """
    get the module's code from file
    """
    with open(module.__file__) as f:
        return f.read()
