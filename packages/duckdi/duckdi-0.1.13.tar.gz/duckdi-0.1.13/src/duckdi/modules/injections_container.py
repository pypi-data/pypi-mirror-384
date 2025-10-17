from typing import Any, Type

class InjectionsContainer:
    """
    # Internal structure that holds the mappings between registered interfaces and adapters.

    # Attributes:
        - adapters (dict): Maps the serialized interface name to its registered adapter class.
        - interfaces (dict): Maps the serialized interface name to its interface class.
    """

    adapters: dict[str, Any] = {}
    interfaces: dict[str, Type] = {}

