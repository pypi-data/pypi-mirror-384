class InterfaceAlreadyRegisteredError(Exception):
    def __init__(self, interface_name: str):
        message = f"""
[DuckDi Error] Interface already registered.

The interface '{interface_name}' is already registered.

Make sure:
  - You are not trying to register the same interface multiple times.
  - The registration logic isn't being called more than once (e.g., during multiple imports or initializations).

Suggestion:
🔁 Check your container or bootstrapping logic to ensure that '{interface_name}' is only registered once.
""".strip()
        super().__init__(message)
