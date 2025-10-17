class MissingInjectionPayloadError(FileNotFoundError):
    def __init__(self, path: str):
        message = f"""
[DuckDi Error] No configuration file found for dependency injections.

Expected: {path}

Make sure the file exists and contains the injection definitions in valid TOML format.

Example of expected content:
[injections]
"user_repository" = "postgres_user_repository"

Solution:
🛠️ You must create the '{path}' file manually or by using the following command:

    duckdi init {path}

Then, specify the injection file path by setting the environment variable:

    INJECTIONS_PATH={path}

This variable is required so DuckDi knows where to find the injection payload.
""".strip()
        super().__init__(message)
