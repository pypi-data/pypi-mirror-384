import contextlib
from .base import LibraryComponent as LibraryComponent
from .browser import Browser as Browser
from .utils import AutoClosingLevel as AutoClosingLevel, PlaywrightLogTypes as PlaywrightLogTypes, close_process_tree as close_process_tree, find_free_port as find_free_port, logger as logger
from Browser.entry.constant import PLAYWRIGHT_BROWSERS_PATH as PLAYWRIGHT_BROWSERS_PATH, ensure_playwright_browsers_path as ensure_playwright_browsers_path
from Browser.generated import playwright_pb2_grpc as playwright_pb2_grpc
from Browser.generated.playwright_pb2 import Request as Request
from _typeshed import Incomplete
from collections.abc import Generator
from functools import cached_property as cached_property
from pathlib import Path
from subprocess import Popen
from typing import TextIO

class Playwright(LibraryComponent):
    port: str | None
    enable_playwright_debug: Incomplete
    host: Incomplete
    playwright_log: Incomplete
    def __init__(self, library: Browser, enable_playwright_debug: PlaywrightLogTypes | bool, host: str | None = None, port: int | None = None, playwright_log: Path | TextIO | None = ...) -> None: ...
    def ensure_node_dependencies(self) -> None: ...
    def start_playwright(self) -> Popen | None: ...
    def wait_until_server_up(self) -> None: ...
    @contextlib.contextmanager
    def grpc_channel(self, original_error: bool = False) -> Generator[Incomplete]: ...
    def close(self) -> None: ...
