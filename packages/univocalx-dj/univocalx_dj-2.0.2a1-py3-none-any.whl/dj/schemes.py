import os
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from dj.constants import (
    PROGRAM_NAME,
    SEARCH_RESULTS_FILE_FORMATS,
)
from dj.utils import (
    clean_string,
    format_file_size,
    resolve_internal_dir,
    validate_string,
)


class BaseSettingsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="ignore",
        env_prefix=PROGRAM_NAME,
    )


class Dataset(BaseModel):
    id: int
    name: str
    domain: str
    created_at: datetime
    description: str | None
    total_files: int


class DJConfigCLI(BaseSettingsConfig):
    command: str = Field(
        default="config",
        description="Command to execute (config, load, etc.)",
    )
    subcommand: str | None = Field(
        default=None,
        description="Subcommand for the main command (e.g., add, remove for tags)",
    )
    log_dir: str | None = Field(default=None)
    verbose: bool = Field(default=False)
    plain: bool = Field(default=False, description="Disable colors and loading bar")


class StorageConfig(BaseSettingsConfig):
    s3endpoint: str | None = Field(default=None)


class DatabaseConfig(BaseSettingsConfig):
    database_endpoint: str | None = Field(
        default=None,
        description="Database connection URL. If not provided, SQLite will be used.",
    )
    echo: bool = Field(
        default=False, description="If True, the Engine will log all statements"
    )
    pool_size: int = Field(
        default=5,
        description="The number of connections to keep open in the connection pool",
    )
    max_overflow: int = Field(
        default=10,
        description="The number of connections to allow in connection pool overflow",
    )

    @field_validator("database_endpoint")
    @classmethod
    def set_default_database_url(cls, v: str | None) -> str:
        if v is None:
            db_path: Path = Path(resolve_internal_dir()) / f"{PROGRAM_NAME}.db"
            return f"sqlite:///{db_path.absolute()}"

        parsed = urlparse(v)
        if parsed.scheme not in ("postgresql", "postgres", "sqlite"):
            raise ValueError("Only PostgreSQL or SQLite databases are supported")

        # Ensure SQLite URLs have the correct format
        if parsed.scheme == "sqlite":
            if not v.startswith("sqlite:///"):
                return f"sqlite:///{Path(parsed.path).absolute()}"
        return v


class RegistryConfig(StorageConfig, DatabaseConfig):
    s3bucket: str | None = Field(default=None)
    s3prefix: str = Field(default=PROGRAM_NAME)
    plain: bool = Field(default=False, description="disable colors.")


class ConfigureRegistryConfig(BaseSettingsConfig):
    set_s3endpoint: str | None = Field(default=None, description="Set S3 endpoint URL")
    set_s3bucket: str | None = Field(default=None, description="Set S3 bucket")
    set_s3prefix: str | None = Field(default=None, description="Set S3 prefix")

    set_database_endpoint: str | None = Field(
        default=None, description="Set database endpoint URL"
    )
    set_echo: bool = Field(default=False, description="Enable SQL command echoing")
    set_pool_size: int | None = Field(
        default=None, description="Set database connection pool size"
    )
    set_max_overflow: int | None = Field(
        default=None, description="Set max overflow for database connections"
    )


class LoadDataConfig(BaseSettingsConfig):
    paths: list[str]
    tags: list[str] | None = Field(default=None)
    filters: list[str] | None = Field(default=None)

    @field_validator("tags")
    def clean_tags(cls, tags: list[str] | None) -> list[str] | None:
        if tags:
            tags = [clean_string(tag) for tag in tags]

        return tags

    @staticmethod
    def _abs_path(paths: list[str]) -> list[str]:
        abs_paths: list[str] = []
        for path in paths:
            if os.path.exists(path):
                abs_paths.append(os.path.abspath(path))
            else:
                abs_paths.append(path)
        return abs_paths

    @field_validator("paths")
    def abs_path(cls, paths: list[str]) -> list[str]:
        return cls._abs_path(paths)


class CreateDatasetConfig(LoadDataConfig):
    name: str
    description: str | None = Field(default=None)
    paths: list[str] | None = Field(default=None)  # type: ignore[assignment]
    exists_ok: bool = Field(
        default=False,
        description="If True, will not raise an error if the dataset exists",
    )
    manifest: Path | None = Field(
        default=None,
        description="YAML/JSON with data sha256s.",
    )

    @field_validator("name")
    def validate_name(cls, string: str) -> str:
        return validate_string(string).lower()

    @field_validator("paths")
    def abs_path(cls, paths: list[str] | None) -> list[str] | None:  # type: ignore[override]
        if paths:
            return cls._abs_path(cast(list[str], paths))
        return paths  # type: ignore[return-value]


class UpdateDatasetConfig(LoadDataConfig):
    name: str
    description: str | None = Field(default=None)
    paths: list[str] | None = Field(default=None)  # type: ignore[assignment]
    manifest: Path | None = Field(
        default=None,  # type: ignore[assignment]
        description="YAML/JSON with data sha256s.",
    )

    @field_validator("name")
    def validate_name(cls, string: str) -> str:
        return validate_string(string).lower()

    @field_validator("paths")
    def abs_path(cls, paths: list[str] | None) -> list[str] | None:  # type: ignore[override]
        if paths is None:
            return None  # type: ignore[override]
        return cls._abs_path(paths)

    @model_validator(mode="after")
    def check_paths_or_manifest(self):
        if not self.paths and not self.manifest:
            raise ValueError("Either 'paths' or 'manifest' must be provided.")
        return self


class ListDatasetsConfig(BaseSettingsConfig):
    pattern: str | None = Field(default=None)
    limit: int | None = Field(default=None)
    offset: int | None = Field(default=None)


class SearchDataConfig(BaseSettingsConfig):
    dataset_pattern: str | None = Field(default=None)
    sha256s: list[str] | None = Field(default=None)
    mime_patterns: list[str] | None = Field(default=None)
    included_tags: list[str] | None = Field(default=None)
    excluded_tags: list[str] | None = Field(default=None)
    results_filepath: str | None = Field(default=None)
    limit: int = Field(default=100)

    @field_validator("dataset_pattern")
    def validate_name(cls, string: str | None) -> str | None:
        if string:
            string = validate_string(string).lower()
        return string

    @field_validator("included_tags", "excluded_tags")
    def clean_tags(cls, tags: list[str] | None) -> list[str] | None:
        if tags:
            tags = [clean_string(tag) for tag in tags]

        return tags

    @field_validator("results_filepath")
    def is_supported_format(cls, filepath: str | None) -> str | None:
        if filepath:
            format: str = os.path.splitext(filepath)[1].lower().replace(".", "")

            if format not in SEARCH_RESULTS_FILE_FORMATS:
                raise ValueError(
                    f"supported export formats: {', '.join(SEARCH_RESULTS_FILE_FORMATS)}"
                )

        return filepath


class FetchDataConfig(SearchDataConfig):
    output_dir: str = Field(default=".")
    overwrite: bool = Field(default=False, description="Overwrite existing files")
    flat: bool = Field(default=False, description="Store files in a flat structure")

    manifest: Path | None = Field(
        default=None,
        description="YAML/JSON/ with data sha256s.",
    )

    @field_validator("output_dir")
    def abs_path(cls, output_dir: str) -> str:
        return os.path.abspath(output_dir)


class TagDataConfig(BaseSettingsConfig):
    manifest: Path = Field(
        description="YAML/JSON/ with data sha256s.",
    )
    tags: list[str]

    @field_validator("tags")
    def clean_tags(cls, tags: list[str]) -> list[str]:
        return [clean_string(tag) for tag in tags]


class DeleteDataConfig(BaseSettingsConfig):
    manifest: Path = Field(
        description="YAML/JSON/ with data sha256s.",
    )
    dry: bool = Field(
        default=False,
        description="If True, will only simulate the deletion without making changes",
    )


class DeleteDatasetConfig(BaseSettingsConfig):
    dataset_name: str
    dry: bool = Field(
        default=False,
        description="If True, will only simulate the deletion without making changes",
    )

    @field_validator("dataset_name")
    def validate_name(cls, string: str) -> str:
        return validate_string(string).lower()


class FileMetadata(BaseModel):
    filepath: Path
    size_bytes: int = Field(..., description="size in bytes")
    sha256: str = Field(..., description="Cryptographic hash")
    mime_type: str

    @computed_field  # type: ignore[misc]
    @cached_property
    def size_human(self) -> str:
        return format_file_size(self.size_bytes)

    @computed_field  # type: ignore[misc]
    @cached_property
    def filename(self) -> str:
        return os.path.basename(self.filepath)
