from ..base import LibraryComponent as LibraryComponent
from ..generated.playwright_pb2 import Request as Request
from ..utils import CoverageType as CoverageType, keyword as keyword, logger as logger
from os import PathLike
from pathlib import Path

class Coverage(LibraryComponent):
    def start_coverage(self, *, config_file: PathLike | None = None, coverage_type: CoverageType = ..., path: Path = ..., raw: bool = False, reportAnonymousScripts: bool = False, resetOnNavigation: bool = True) -> str: ...
    def stop_coverage(self) -> Path: ...
    def merge_coverage_reports(self, input_folder: Path, output_folder: Path, config_file: Path | None = None, name: str | None = None, reports: list[str] | None = None) -> Path: ...
