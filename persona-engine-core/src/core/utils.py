import orjson
from typing import Any

def fast_json_dumps(data: Any) -> str:
    """
    OPTIMIZATION: Helper to use orjson for dumps.
    Returns string, decoding bytes automatically.
    """
    return orjson.dumps(data).decode('utf-8')

def fast_json_loads(data: str | bytes) -> Any:
    return orjson.loads(data)