from duckdi.modules.injections_container import InjectionsContainer
from duckdi.errors import AdapterAlreadyRegisteredError
from duckdi.utils import to_snake
from typing import Optional, Type

def register[T](
    adapter: Type[T], label: Optional[str] = None, is_singleton: bool = False
) -> None:
    """
    # Registers an adapter (concrete implementation) for a previously registered interface.

    # This function maps an implementation class (adapter) to a label, making it available
    # for runtime resolution via the Get function. It also supports singleton behavior by
    # storing an already-instantiated adapter instance if `is_singleton` is set to True.

    # Args:
        - adapter (Type[T]): The concrete implementation class to register.
        - label (Optional[str]): An optional custom label for the adapter. If not provided, a snake_case version of the adapter class name will be used.
        - is_singleton (bool): If True, the adapter is instantiated immediately and reused on every resolution. If False, a new instance will be created each time.

    # Raises:
        - AdapterAlreadyRegisteredError: If an adapter has already been registered under the same label.

    # Example:
    .   register(PostgresUserRepository)

    # Example with a custom label:
    .   register(PostgresUserRepository, label="postgres_repo")

    # Example as a singleton:
    .   register(PostgresUserRepository, is_singleton=True)
    """
    adapter_name = label if label is not None else to_snake(adapter)

    if InjectionsContainer.adapters.get(adapter_name) is not None:
        raise AdapterAlreadyRegisteredError(adapter_name)

    InjectionsContainer.adapters[adapter_name] = adapter() if is_singleton else adapter

