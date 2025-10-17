from typing import Callable, Optional, Type, TypeVar, Union, overload

from duckdi.errors.interface_already_registered import InterfaceAlreadyRegisteredError
from duckdi.modules.injections_container import InjectionsContainer
from duckdi.utils.serializers import to_snake

T = TypeVar("T")

@overload
def Interface(_interface: Type[T]) -> Type[T]: ...

@overload
def Interface(*, label: Optional[str]) -> Callable[[Type[T]], Type[T]]: ...


def Interface(_interface: Optional[Type[T]] = None, *, label: Optional[str] = None) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """
    Registers an interface class for dependency injection.

    This decorator marks an abstract interface so it can be mapped to a concrete adapter
    within the dependency injection container. It supports usage with or without parameters.

    Args:
        _interface (Type[T], optional): The interface class to register (when used without parentheses).
        label (Optional[str], optional): A custom registration label. If omitted, a snake_case version
                                         of the class name will be used as the registration key.

    Returns:
        Union[Type[T], Callable[[Type[T]], Type[T]]]: Returns the same class (if used without arguments),
        or a decorator (if used with arguments).

    Raises:
        InterfaceAlreadyRegisteredError: If the interface or label is already registered.

    Examples:
        >>> @Interface
        ... class IUserRepository: ...

        >>> @Interface(label="user_repo")
        ... class IUserRepository: ...
    """
    def wrap(_interface: Type[T]) -> Type[T]:
        interface_name = label if label is not None else to_snake(_interface)
        if InjectionsContainer.interfaces.get(interface_name) is not None:
            raise InterfaceAlreadyRegisteredError(interface_name)

        InjectionsContainer.interfaces[interface_name] = _interface
        return _interface

    if _interface is not None:
        return wrap(_interface)

    return wrap

