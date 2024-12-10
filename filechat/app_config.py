import os, yaml, typing


config = {}
if os.path.exists(config_path := "config.yaml"):
    with open(config_path) as file:
        config = yaml.safe_load(file)


def get(key_path: typing.Iterable[str] | str, default=None) -> typing.Any:
    value = config
    if isinstance(key_path, str):
        key_path = [key_path]
    for key in key_path:
        if key not in value:
            return default
        value = value[key]
    return value if value is not None else default


def get_required(
    key_path: typing.Iterable[str] | str, exception: Exception
) -> typing.Any:
    value = config
    if isinstance(key_path, str):
        key_path = [key_path]
    for key in key_path:
        if key not in value:
            raise exception
        value = value[key]
    if value is None:
        raise exception
    return value
