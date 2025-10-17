class InvalidAdapterImplementationError(TypeError):
    def __init__(self, interface_name: str, adapter_name: str):
        message = f"""
[DuckDi Error] Invalid adapter implementation.

The adapter '{adapter_name}' does not implement the expected interface '{interface_name}'.

Make sure:
  - The adapter class correctly implements all required methods from the interface.
  - The injection payload maps the interface to the correct adapter class.

Suggestion:
🔧 Double-check the entry in your '.toml' injections file:

    [{interface_name}]
    = "{adapter_name}"
""".strip()
        super().__init__(message)
