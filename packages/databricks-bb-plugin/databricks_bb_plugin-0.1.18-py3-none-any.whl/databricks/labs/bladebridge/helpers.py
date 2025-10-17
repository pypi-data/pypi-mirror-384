import os
import json

from json.decoder import WHITESPACE  # type: ignore[attr-defined]
from pathlib import Path, PurePath, PureWindowsPath
from typing import Any, TypeVar
from urllib.parse import urlparse, unquote_to_bytes

from lsprotocol.types import Range, Position


def full_range(source_code: str) -> Range:
    source_lines = source_code.split("\n")
    return Range(
        start=Position(0, 0), end=Position(len(source_lines), len(source_lines[-1]))
    )


# TODO: This Function hard codes the mapping between dialects and source technologies
def map_dialect_to_source_tech(dialect: str) -> str:
    dialect = dialect.upper()
    mapping = {
        "INFORMATICA (DESKTOP EDITION)": "INFAPC",
        "INFORMATICA CLOUD": "INFACLOUD",
    }
    for key, value in mapping.items():
        if key in dialect:
            return value
    return dialect


P = TypeVar("P", bound=PurePath)


def from_uri(uri: str, *, path_prototype: P = Path()) -> P:  # type: ignore[assignment]
    """Return a new path from the given 'file' URI.

    This is the inverse of `Path.as_uri()`.

    Arguments:
        uri: the 'file' URI to convert to a path.
        path_prototype: an example of the type of path to return. Default: Path() (which is
            platform-specific)
    Returns:
        A new path that corresponds to the given URI.
    """
    uri_parsed = urlparse(uri)
    if uri_parsed.scheme != "file":
        raise ValueError(f"Not a 'file' URI: {uri!r}")
    encoded_path = uri_parsed.path

    # Note: use of a prototype to specify the factory (and return) type is because instantiating
    # Path() provides the platform-specific type, but Path itself is an ABC and not
    # platform-specific. That is: type[Path()] is _not_ Path, but rather PosixPath or WindowsPath.
    path_type = type(path_prototype)

    # A hostname indicates a UNC path on Windows, unless it's localhost which is a special case
    # for 'local' file.
    match uri_parsed.netloc:
        case "" | "localhost":
            if issubclass(path_type, PureWindowsPath):
                # On Windows, we might have to strip a leading '/' from the path. But only if the
                # path looks like a DOS device or UNC path. (The UNC host can be specified either
                # in the authority or as part of the path.)
                if encoded_path.startswith("///") or (
                    encoded_path.startswith("/") and encoded_path[2:3] in ":|"
                ):
                    encoded_path = encoded_path[1:]
                # Another quirk: the drive letter may be followed by a '|' instead of a ':'.
                if encoded_path[1:2] == "|":
                    encoded_path = encoded_path[:1] + ":" + encoded_path[2:]
        case authority if issubclass(path_type, PureWindowsPath):
            # Prepend the authority as a UNC path prefix
            encoded_path = f"//{authority}{encoded_path}"
        case _:
            raise ValueError(f"Unsupported 'file' URI authority: {authority!r}")

    unquoted_path = unquote_to_bytes(encoded_path)
    decoded_path = os.fsdecode(unquoted_path)
    path = path_type(decoded_path)
    if not path.is_absolute():
        msg = f"URI is not absolute: {uri!r} (path={path!s})"
        raise ValueError(msg)
    return path


class _JsonDecoder(json.JSONDecoder):

    def decode(self, s: str, _w=WHITESPACE.match) -> Any:
        s = "\n".join(self._strip_comments(line) for line in s.split("\n"))
        return super().decode(s, _w)

    @classmethod
    def _strip_comments(cls, line: str) -> str:
        idx = line.find("//")
        if idx < 0:
            return line
        if idx == 0:
            return ""
        # assume the '//' is not within a literal
        return line[0:idx]


# pylint: disable=too-few-public-methods
class JSONReader:

    @staticmethod
    def load(path: Path) -> Any:
        with open(path, encoding="utf-8") as f:
            return json.load(f, cls=_JsonDecoder)
