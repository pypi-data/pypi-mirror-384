import json
import os
import posixpath
import re
from glob import glob
from importlib.resources import files as resource_files
from logging import Logger, getLogger
from time import sleep
from typing import Any, Iterable, TypeVar
from urllib.parse import quote

import yaml
from rich.console import Console
from rich.progress import track
from rich.table import Table

from dj.constants import (
    ASSETS_DIRECTORY,
    DEFAULT_DELAY,
    FALSE_STRINGS,
    PROGRAM_NAME,
    TRUE_STRINGS,
)

logger: Logger = getLogger(__name__)

T = TypeVar("T")

console = Console()


def str2bool(v) -> bool | None:
    if isinstance(v, bool):
        return v
    if v.lower() in TRUE_STRINGS:
        return True
    elif v.lower() in FALSE_STRINGS:
        return False
    else:
        raise ValueError(f'Cant convert "{v}" to a bool')


def hours2seconds(hours: float) -> int:
    return int(hours * 3600)


def seconds2hours(seconds: int) -> float:
    return round(seconds / 3600, 4)


def resolve_internal_dir() -> str:
    return os.path.expanduser(os.path.join("~/", "." + PROGRAM_NAME))


def serialize_string(
    input_str: str,
    regex_pattern: str = r"[^a-z0-9]",
    replacement: str = "",
    force_lowercase: bool = True,
) -> str:
    if force_lowercase:
        input_str = input_str.lower()

    pattern = re.compile(regex_pattern)
    cleaned: str = pattern.sub(replacement, input_str)

    return cleaned


def split_s3uri(s3uri: str) -> tuple[str, str]:
    if not s3uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3uri}. Must start with 's3://'")

    # Remove the s3:// prefix
    path: str = s3uri[5:]

    if not path:
        raise ValueError("Invalid S3 URI: No bucket specified")

    # Split on first '/' to separate bucket from prefix
    parts: list[str] = path.split("/", 1)
    s3bucket: str = parts[0]
    s3prefix: str = parts[1] if len(parts) > 1 else ""

    if not s3bucket:
        raise ValueError("Invalid S3 URI: Empty bucket name")

    return s3bucket, s3prefix


def merge_s3uri(*parts: str) -> str:
    if not parts:
        raise ValueError("Bucket name cannot be empty")

    return f"s3://{posixpath.join(*parts)}"


def load_asset(file_name: str) -> str:
    asset_file = resource_files(ASSETS_DIRECTORY).joinpath(file_name)
    logger.debug(f"loading asset file: {asset_file}")
    return asset_file.read_text()


def get_directory_size(directory: str) -> float:
    total_bytes: int = 0

    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath: str = os.path.join(dirpath, filename)
            total_bytes += os.path.getsize(filepath)

    dir_size_gp: float = total_bytes / (1024**3)
    logger.debug(f'directory size: "{dir_size_gp}"')
    return dir_size_gp


def clean_string(
    filename: str,
    regex: str = r"[^a-zA-Z0-9/.]",
    case: str = "lower",
) -> str:
    base_name, ext = os.path.splitext(filename)
    cleaned_base = re.sub(regex, "", base_name)

    if case == "lower":
        cleaned_base = cleaned_base.lower()
        ext = ext.lower()
    elif case == "upper":
        cleaned_base = cleaned_base.upper()
        ext = ext.upper()

    cleaned_name = cleaned_base + ext

    return cleaned_name


def validate_string(
    string: str, pattern: str = r"^[a-zA-Z0-9._/]+$", error_message: str | None = None
) -> str:
    """Validate string against a pattern."""
    if not re.match(pattern, string):
        if error_message is None:
            # Create default error message by finding invalid characters
            invalid_chars = (
                set(re.findall(f"[^{pattern[2:-2]}]", string))
                if pattern.startswith("^") and pattern.endswith("$")
                else set()
            )
            error_message = (
                f"String contains invalid characters: {sorted(invalid_chars)}. "
                f"Only characters matching pattern '{pattern}' are allowed."
            )
        raise ValueError(error_message)
    return string


def collect_files(
    pattern: str, filters: Iterable[str] | None = None, recursive: bool = False
) -> set[str]:
    filepaths: set[str] = set()
    abs_pattern: str = os.path.abspath(pattern)

    # If pattern is a file, just return it
    if os.path.isfile(abs_pattern):
        filepaths.add(abs_pattern)
        return filepaths

    # If pattern is a directory, we need to add wildcards for glob to work
    if os.path.isdir(abs_pattern):
        if recursive:
            pattern = os.path.join(pattern, "**", "*")
        else:
            pattern = os.path.join(pattern, "*")

    logger.debug(f'Collecting files, pattern: "{pattern}"')
    matches = glob(pattern, recursive=recursive)
    for match in matches:
        full_path = os.path.abspath(match)
        if os.path.isfile(full_path):
            filepaths.add(full_path)

    if filters:
        filters = set(filters)
        logger.debug(f"Extensions: {', '.join(filters)}")
        filepaths = {f for f in filepaths if any(f.endswith(ext) for ext in filters)}

    logger.debug(f"Collected {len(filepaths)} file(s)")
    return filepaths


def format_file_size(size_bytes: int, unit: str | None = None) -> str:
    units: list[str] = ["B", "KB", "MB", "GB", "TB", "PB"]
    original_size: float = float(size_bytes)
    result: str = ""

    if unit:
        unit = unit.upper()
        if unit in units:
            index: int = units.index(unit)
            size: float = original_size / (1024**index)
            result = f"{size:.2f}{unit}"
        else:
            result = f"{original_size:.2f}B"
    else:
        size = original_size
        for u in units:
            if size < 1024.0 or u == units[-1]:
                result = f"{size:.2f}{u}"
                break
            size /= 1024.0

    return result


def unified_track(
    iterable: Iterable[T],
    desc: str = "Processing",
) -> Iterable[T]:
    return track(
        iterable,
        description=f"{desc}",
    )


def unified_table(data: list[dict[str, Any]], title: str | None = None) -> None:
    if not data:
        console.print("[yellow]No data to display[/yellow]")
        return

    # Get column names from first dictionary keys
    columns = list(data[0].keys())

    # Create table with clean styling
    table = Table(
        title=title,
        title_style="bold magenta",
        show_header=True,
        header_style="bold cyan",
        show_edge=True,
        pad_edge=True,
        show_lines=True,  # This adds clear separation between rows
    )

    # Add columns with centered values
    for column in columns:
        # Format column names (snake_case to Title Case)
        column_name = str(column).replace("_", " ").title()
        table.add_column(
            column_name,
            style="cyan",
            min_width=8,
            max_width=50,
            overflow="fold",
            justify="center",  # This centers the values
        )

    # Add rows without alternating colors or special formatting
    for row in data:
        formatted_row = [str(row.get(col, "")) for col in columns]
        table.add_row(*formatted_row)

    console.print()
    console.print(table)


def resolve_data_s3uri(
    s3bucket: str,
    s3prefix: str,
    mime_type: str,
    sha256: str,
    ext: str | None = None,
) -> str:
    def clean(part: str) -> str:
        return quote(str(part).strip("/ ")) if part else ""

    path: str = "/".join(clean(part) for part in [s3prefix, mime_type, sha256] if part)
    s3uri_no_ext: str = f"s3://{clean(s3bucket)}/{path}"
    s3uri: str = s3uri_no_ext + ext if ext else s3uri_no_ext
    return s3uri


def export_data(filepath: str, data: Any) -> None:
    format: str = os.path.splitext(filepath)[1].lower()
    abs_filepath: str = os.path.abspath(filepath)

    os.makedirs(os.path.dirname(abs_filepath), exist_ok=True)
    logger.debug(f"Exporting data -> {filepath}")

    with open(filepath, "w") as export_file:
        if format == ".json":
            json.dump(data, export_file, indent=4)
        elif format in [".yaml", ".yml"]:
            yaml.dump(data, export_file, indent=4, default_flow_style=False)
        else:
            raise ValueError(
                f"Unsupported file format: {format}. Supported formats: .json, .yaml, .yml"
            )


def delay(seconds: int | None = None) -> None:
    logger.debug(f"Delaying for {seconds} seconds...")
    sleep(seconds or DEFAULT_DELAY)


def generate_unique_filepath(filepath: str) -> str:
    counter: int = 0
    unique_path: str = filepath

    while os.path.exists(unique_path):
        counter += 1
        base, extension = os.path.splitext(filepath)
        unique_path = f"{base} ({counter}){extension}"

    return unique_path
