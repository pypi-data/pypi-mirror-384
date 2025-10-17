from Browser.utils import logger as logger
from collections.abc import Callable as Callable
from typing import Any

def convert_pos_args_to_named(deprecated_pos_args: tuple[Any, ...], old_args: dict[str, Any], keyword_name: str, additional_msg: str = ''): ...
