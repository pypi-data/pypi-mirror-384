from os.path import isfile

from toml import load

from duckdi.errors import MissingInjectionPayloadError


def read_toml(path: str) -> dict[str, dict[str, str]]:
    if not isfile(path):
        raise MissingInjectionPayloadError(path)

    return load(open(path))
