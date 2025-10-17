from duckdi.errors.invalid_adapter_implementation_error import InvalidAdapterImplementationError
from duckdi.modules.injections_container import InjectionsContainer
from duckdi.modules.injections_payload import InjectionsPayload
from duckdi.utils.serializers import to_snake
from typing import Literal, Optional, Type, TypeVar, Union, overload

T = TypeVar("T")

@overload
def Get(
    interface: Type[T],
    label: Optional[str] = None,
    adapter: Optional[str] = None,
    instance: Literal[True] = True
) -> T: ...
@overload
def Get(
    interface: Type[T],
    label: Optional[str] = None,
    adapter: Optional[str] = None,
    instance: Literal[False] = False
) -> Type[T]: ...

def Get(interface: Type[T], label: Optional[str] = None, adapter: Optional[str] = None, instance: bool = True) -> Union[T, Type[T]]:
    """
    # Resolves and returns an instance of the adapter associated with the given interface.
    # This function is the main entry point for resolving dependencies at runtime.

    # Args:
        - interface (Type[T]): The interface class decorated with @Interface.
        - label (Optional[str]): Optional custom label used during interface registration. 
          If omitted, the snake_case name of the interface class is used.
        - adapter (Optional[str]): Optional adapter name to explicitly resolve a specific 
          implementation. When provided, this parameter overrides the adapter resolution 
          defined in the injection payload.

    # Returns:
        - T: An instance of the adapter class bound to the interface.

    # Raises:
        - KeyError: If the interface or adapter is not found in the injection payload.
        - InvalidAdapterImplementationError: If the resolved adapter does not implement the expected interface.

    # Example:
    .   @Interface
    .   class IUserRepository:
    .       ...
    .
    .   register(PostgresUserRepository)
    .   user_repo = Get(IUserRepository)
    .
    .   # Explicitly resolving a different adapter:
    .   user_repo = Get(IUserRepository, adapter="mock_user_repository")
    """

    interface_name = label if label is not None else to_snake(interface)
    adapter_name = adapter if adapter is not None else InjectionsPayload().load()[interface_name]
    _adapter = InjectionsContainer.adapters[adapter_name]

    if not isinstance(_adapter, type):
        if not isinstance(_adapter, interface):
            raise InvalidAdapterImplementationError(
                interface.__name__, type(_adapter).__name__
            )
        return _adapter if instance else type(_adapter)

    if not issubclass(_adapter, interface):
        raise InvalidAdapterImplementationError(interface.__name__, _adapter.__name__)

    return _adapter() if instance else _adapter

