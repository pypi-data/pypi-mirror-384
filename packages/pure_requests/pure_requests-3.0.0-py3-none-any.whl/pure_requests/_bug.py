from dataclasses import (
    dataclass,
)


@dataclass
class LibraryBug(Exception):
    traceback: Exception

    def __str__(self) -> str:
        return "If raised then there is a bug in the `pure_requests` library"
