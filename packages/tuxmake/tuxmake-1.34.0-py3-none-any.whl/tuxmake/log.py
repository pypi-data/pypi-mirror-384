from pathlib import Path
from typing import Tuple

ERRORS: Tuple[str, ...] = (
    "compiler lacks",
    "no configuration exists",
    "not found",
    "no such file or directory",
    "no rule to make target",
    "failed to merge target specific data of file",
    "undefined reference to",
)


class LogParser:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def parse(self, filepath: Path) -> None:
        for orig_line in filepath.open("r", errors="ignore"):
            line = orig_line.lower()
            if "error:" in line or any([s in line for s in ERRORS]):
                self.errors += 1
            if "warning:" in line.lower():
                self.warnings += 1
