class AdapterAlreadyRegisteredError(Exception):
    def __init__(self, adapter_name: str):
        message = f"""
[DuckDi Error] Adapter already registered.

The adapter label '{adapter_name}' is already associated with another implementation.

Make sure:
  - You are not registering the same adapter more than once.
  - No duplicate labels are used across different adapters.

Suggestion:
🧠 Verify the labels used in your registration logic and avoid accidental re-registration.

Example:
    register(MyAdapter, label="{adapter_name}")  # Check if this call is being repeated
""".strip()
        super().__init__(message)
