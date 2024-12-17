import typing, types, inspect, re, json, yaml, datetime, base64, os, uuid
from termcolor import colored


def open_file(path, mode):
    return open(path, mode, encoding="utf-8")


def generate_uuid() -> str:
    return str(uuid.uuid4())


def serialize(obj):
    if isinstance(obj, datetime.date | datetime.datetime):
        return obj.timestamp()
    elif isinstance(obj, list | tuple | set):
        return [serialize(e) for e in obj]
    elif isinstance(obj, dict):
        return dict((serialize(k), serialize(v)) for k, v in obj.items())
    elif hasattr(obj, "__serialize__"):
        return serialize(obj.__serialize__())
    elif hasattr(obj, "__dict__"):
        if hasattr(obj, "__serialization_exclusions__"):
            skip_keys = obj.__serialization_exclusions__()
        else:
            skip_keys = set()
        # d = {k: v for k, v in obj.__dict__.items() if k not in skip_keys}
        d = {
            k: v
            for k, v in inspect.getmembers(obj)
            if k not in skip_keys
            and not (k.startswith("__") and k.endswith("__"))
            and not inspect.isabstract(v)
            and not inspect.isbuiltin(v)
            and not inspect.isfunction(v)
            and not inspect.isgenerator(v)
            and not inspect.isgeneratorfunction(v)
            and not inspect.ismethod(v)
            and not inspect.ismethoddescriptor(v)
            and not inspect.isroutine(v)
        }
        return serialize(d)
    return obj


def deserialize(data, target_type=typing.Any):
    origin = typing.get_origin(target_type)
    args = typing.get_args(target_type)
    if target_type is typing.Any:
        return data
    elif origin == types.UnionType:
        for t in args:
            try:
                return deserialize(data, t)
            except:
                pass
        raise ValueError(f"Failed to deserialize data: {data} into {target_type}")
    else:
        try:
            if data is None and target_type == types.NoneType:
                return None
            elif origin == typing.Literal and data in args:
                return data
            elif isinstance(data, float) and target_type == datetime.datetime:
                return datetime.datetime.fromtimestamp(data)
            elif isinstance(data, dict) and origin == dict and len(args) >= 2:
                return dict(
                    (deserialize(k, args[0]), deserialize(v, args[1]))
                    for k, v in data.items()
                )
            elif isinstance(data, dict) and origin == dict and len(args) == 1:
                return dict((deserialize(k, args[0]), v) for k, v in data.items())
            elif isinstance(data, list | tuple | set | dict) and len(args) >= 1:
                return origin(deserialize(e, args[0]) for e in data)
            elif isinstance(data, dict) and target_type != dict and origin != dict:
                return target_type(
                    **dict(
                        (k, deserialize(v, target_type.__annotations__[k]))
                        for k, v in data.items()
                        if k in target_type.__annotations__
                    )
                )
            else:
                return target_type(data)
        except Exception as e:
            raise ValueError(
                f"Failed to deserialize data: {data} into {target_type}"
            ) from e


def ask_yes_no(question: str, default: bool | None = None) -> bool:
    while True:
        answer = input(
            f"{question} [{"Y" if default is True else "y"}/{"N" if default is False else "n"}] "
        ).lower()
        if answer in {"y", "yes"}:
            return True
        elif answer in {"n", "no"}:
            return False
        elif answer == "" and default is not None:
            return default
        else:
            print(colored("Invalid answer.", "red"))


def log_warning(message: str):
    print(colored(f"Warning: {message}", "yellow"))


def log_error(e: Exception, retry: bool | int = False):
    print(colored(f"Error: {e}", "red"))
    retry_is_bool = retry is True or retry is False
    if retry_is_bool and retry:
        print("Retrying...")
    elif not retry_is_bool:
        print(f"Retrying ({retry} attempts left)...")


async def try_loop_async(
    func: typing.Callable,
    max_retries: int = 3,
    raise_on_retry_exceed: bool = True,
):
    exception = Exception()
    for num_retries in range(max_retries, -1, -1):
        try:
            return await func()
        except Exception as e:
            exception = e
            log_error(e, retry=num_retries)
    if raise_on_retry_exceed:
        raise exception
    return None


def try_loop(
    func: typing.Callable,
    max_retries: int = 3,
    raise_on_retry_exceed: bool = True,
):
    exception = Exception()
    for num_retries in range(max_retries, -1, -1):
        try:
            return func()
        except Exception as e:
            exception = e
            log_error(e, retry=num_retries)
    if raise_on_retry_exceed:
        raise exception
    return None


def dump_json(data: typing.Any, **kwargs) -> str:
    return json.dumps(data, default=serialize, ensure_ascii=False, indent=4, **kwargs)


def dump_yaml(data: typing.Any, **kwargs) -> str:
    return yaml.dump(data, allow_unicode=True, **kwargs)


def load_json(json_str: str, target_type=typing.Any) -> typing.Any:
    return deserialize(json.loads(json_str) if json_str.strip() else None, target_type)


def load_yaml(yaml_str: str) -> typing.Any:
    return yaml.safe_load(yaml_str)


def extract_code_blocks(
    text: str, target_cls: str | None = None
) -> list[tuple[str, str]]:
    matches = re.findall(r"```(.*?)\n(.*?)\n```", text, re.DOTALL)
    code_blocks = [
        (str(cls), str(code).strip()) for cls, code in matches if cls == target_cls
    ]
    return code_blocks


def extract_json(text: str) -> tuple[str, typing.Any]:
    json_codes = [code for _, code in extract_code_blocks(text, target_cls="json")]

    if len(json_codes or []) != 1:
        raise ValueError("Expected exactly one JSON code block in the text")

    json_code = str(json_codes[0]).strip()
    data = load_json(json_code)
    return json_code, data


def extract_yaml(text: str) -> tuple[str, typing.Any]:
    yaml_codes = [code for _, code in extract_code_blocks(text, target_cls="yaml")]

    if len(yaml_codes or []) != 1:
        raise ValueError("Expected exactly one YAML code block in the text")

    yaml_code = str(yaml_codes[0]).strip()
    data = load_yaml(yaml_code)

    return yaml_code, data


def match_type(data: typing.Any, schema: type | dict | list | typing.Any) -> bool:
    if isinstance(schema, type):
        return isinstance(data, schema)
    elif (origin := typing.get_origin(schema)) in {
        list,
        tuple,
        set,
        dict,
        typing.Literal,
    }:
        args = typing.get_args(schema)
        if origin == typing.Literal:
            return data in args
        elif not isinstance(data, origin):
            return False
        elif origin == dict and len(args) >= 2:
            assert isinstance(data, dict)
            return all(
                match_type(k, args[0]) and match_type(v, args[1])
                for k, v in data.items()
            )
        elif origin in {list, tuple, set, dict} and len(args) >= 1:
            return all(match_type(e, args[0]) for e in data)
    elif type(data) != type(schema):
        return False
    elif isinstance(schema, dict):
        for key, value in schema.items():
            if key not in data:
                return False
            if not match_type(data[key], value):
                return False
        return True
    elif isinstance(schema, list | tuple):
        if len(data) != len(schema):
            return False
        for d, p in zip(data, schema):
            if not match_type(d, p):
                return False
        return True
    raise ValueError(f"Invalid schema: {schema}")


def encode_image_to_base64_data_uri(file_path):
    # Determine the MIME type based on the file extension
    mime_type = None
    extension = str(os.path.splitext(file_path)[1]).lower()

    if extension in {".jpg", ".jpeg"}:
        mime_type = "image/jpeg"
    elif extension == ".png":
        mime_type = "image/png"
    elif extension == ".gif":
        mime_type = "image/gif"
    elif extension == ".bmp":
        mime_type = "image/bmp"
    else:
        raise ValueError("Unsupported file extension")

    # Open the image file in binary mode
    with open(file_path, "rb") as image_file:
        # Read the file content
        image_data = image_file.read()
        # Encode the binary data to base64
        encoded_image = base64.b64encode(image_data)
        # Convert the encoded bytes to a string
        encoded_string = encoded_image.decode("utf-8")

    # Format as a data URI
    data_uri = f"data:{mime_type};base64,{encoded_string}"
    return data_uri
