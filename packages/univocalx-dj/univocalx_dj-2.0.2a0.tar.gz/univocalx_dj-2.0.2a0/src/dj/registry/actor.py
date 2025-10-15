import json
import os
from contextlib import contextmanager
from logging import Logger, getLogger
from tempfile import gettempdir
from typing import Any

import yaml
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from dj.exceptions import (
    DatasetExist,
    DatasetNotFound,
    FileRecordExist,
    FileRecordNotFound,
    InvalidSetting,
    TagExist,
    TagNotFound,
)
from dj.registry.models import (
    Base,
    DatasetRecord,
    DatasetVersionRecord,
    FileRecord,
    TagRecord,
    dataset_version_files,
    file_tags,
)
from dj.registry.storage import Storage
from dj.schemes import FileMetadata, RegistryConfig
from dj.utils import resolve_data_s3uri

logger: Logger = getLogger(__name__)


class RegistryActor:
    def __init__(self, cfg: RegistryConfig):
        self.cfg: RegistryConfig = cfg
        self.storage: Storage = Storage(cfg)

        if not cfg.s3bucket:
            raise InvalidSetting("Please configure S3 bucket!")

        self.__initialize_database__()

    def __initialize_database__(self) -> None:
        logger.debug(f"Initializing database: {self.cfg.database_endpoint}")

        self.engine: Engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
        self.session: Session = self.Session()

        logger.debug("Creating database tables...")
        Base.metadata.create_all(self.engine)

        if str(self.cfg.database_endpoint).startswith("sqlite"):
            db_path = str(self.cfg.database_endpoint).replace("sqlite:///", "")
            db_abspath: str = os.path.abspath(db_path)
            logger.debug(f"SQLite database: {db_abspath}")

        logger.debug("initialization completed")

    def _create_engine(self) -> Engine:
        logger.debug(f"Creating database engine for: {self.cfg.database_endpoint}")

        kwargs: dict = {
            "echo": self.cfg.echo,
            "pool_size": self.cfg.pool_size,
            "max_overflow": self.cfg.max_overflow,
        }

        # SQLite specific configuration
        if str(self.cfg.database_endpoint).startswith("sqlite"):
            logger.debug("Configuring SQLite-specific engine settings")
            kwargs.update(
                {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": None,  # SQLite doesn't need connection pooling
                }
            )

        # PostgreSQL specific configuration
        elif str(self.cfg.database_endpoint).startswith(("postgresql", "postgres")):
            logger.debug("Configuring PostgreSQL-specific engine settings")
            kwargs.update(
                {
                    "pool_pre_ping": True,  # Test connections for liveness
                    "pool_recycle": 3600,  # Recycle connections after 1 hour
                }
            )

        logger.debug(f"Engine configuration: {kwargs}")
        engine = create_engine(str(self.cfg.database_endpoint), **kwargs)
        logger.debug("Database engine created successfully")
        return engine

    def __enter__(self):
        logger.debug("Entering context manager")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Exiting context manager")
        if exc_type:
            logger.debug(
                f"Exception in context manager: {exc_type.__name__}: {exc_val}"
            )
        self.close()

    @contextmanager
    def _get_local_path(self, filepath: str):
        if filepath.startswith("s3://"):
            tmpfile: str = os.path.join(gettempdir(), os.path.basename(filepath))
            self.storage.download_obj(filepath, tmpfile)
            try:
                yield tmpfile
            finally:
                if os.path.exists(tmpfile):
                    os.remove(tmpfile)
        else:
            yield filepath

    @contextmanager
    def transaction(self):
        logger.debug("Starting database transaction")
        try:
            yield self  # Provide access to the journalist instance
            self.session.commit()  # Only commit if no exceptions occurred
            logger.debug("Transaction committed successfully")
        except Exception:
            logger.debug("Transaction failed, rolling back")
            self.session.rollback()
            raise

    def close(self) -> None:
        logger.debug("Closing database session")
        self.session.close()

    def _create_dataset_record(self, name: str) -> DatasetRecord:
        logger.debug(f"Creating new dataset: {name}")
        dataset: DatasetRecord = DatasetRecord(name=name)
        self.session.add(dataset)

        try:
            self.session.flush()  # Try to write to DB, but don't commit yet
        except IntegrityError:
            self.session.rollback()
            raise DatasetExist(f'Dataset "{name}" already exists.')

        return dataset

    def _create_file_record(self, metadata: FileMetadata) -> FileRecord:
        if not self.cfg.s3bucket:
            raise InvalidSetting("S3 bucket is not configured.")

        s3uri: str = resolve_data_s3uri(
            s3bucket=self.cfg.s3bucket,
            s3prefix=self.cfg.s3prefix,
            mime_type=metadata.mime_type,
            sha256=metadata.sha256,
            ext=os.path.splitext(metadata.filename)[1],
        )

        file_record: FileRecord = FileRecord(
            sha256=metadata.sha256,
            s3uri=s3uri,
            filename=metadata.filename,
            mime_type=metadata.mime_type,
            size_bytes=metadata.size_bytes,
        )

        self.session.add(file_record)
        try:
            self.session.flush()  # Ensure file_record gets an ID
        except IntegrityError:
            self.session.rollback()
            raise FileRecordExist(
                f'File record "{metadata.filename}" ({metadata.sha256[:10]}...) already exists.'
            )

        return file_record

    def _get_file_by_sha256(self, sha256: str) -> FileRecord:
        logger.debug(f"Searching by sha256: {sha256}")
        record: FileRecord | None = (
            self.session.query(FileRecord).filter(FileRecord.sha256 == sha256).first()
        )
        if not record:
            raise FileRecordNotFound(f"File with sha256 '{sha256}' not found.")
        return record

    def _get_tag_by_name(self, name: str) -> TagRecord:
        logger.debug(f"Searching tag by name: {name}")
        tag: TagRecord | None = (
            self.session.query(TagRecord).filter(TagRecord.name == name).first()
        )
        if not tag:
            raise TagNotFound(f'Tag "{name}" not found.')
        return tag

    def _create_tag_record(self, name: str) -> TagRecord:
        tag: TagRecord = TagRecord(name=name)
        self.session.add(tag)

        try:
            self.session.flush()  # Try to write to DB, but don't commit yet
        except IntegrityError:
            self.session.rollback()
            raise TagExist(f'Tag "{name}" already exists.')

        return tag

    def _associate_tags_with_file(
        self, file_sha256: str, tag_names: list[str]
    ) -> FileRecord:
        file_record: FileRecord = self._get_file_by_sha256(file_sha256)

        logger.debug(f"Associating tags {tag_names} with file {file_sha256}")
        for name in tag_names:
            tag: TagRecord = self._get_tag_by_name(name)

            if file_record not in tag.files:
                tag.files.append(file_record)

        self.session.flush()
        return file_record

    def _disassociate_tags_from_file(
        self, file_sha256: str, tag_names: list[str]
    ) -> FileRecord:
        file_record: FileRecord = self._get_file_by_sha256(file_sha256)

        logger.debug(f"Disassociating tags {tag_names} from file {file_sha256}")
        for name in tag_names:
            tag: TagRecord = self._get_tag_by_name(name)

            if file_record in tag.files:
                tag.files.remove(file_record)

        self.session.flush()

        return file_record

    def _create_dataset_version(
        self,
        dataset_name: str,
        file_sha256s: list[str],
        description: str | None = None,
    ) -> DatasetVersionRecord:
        logger.debug(f"Creating new dataset version for '{dataset_name}'")
        dataset: DatasetRecord | None = (
            self.session.query(DatasetRecord)
            .filter(DatasetRecord.name == dataset_name)
            .first()
        )
        if not dataset:
            raise DatasetNotFound(f'Dataset "{dataset_name}" not found.')

        # Get the latest version and increment
        latest_version_record: DatasetVersionRecord | None = (
            self._get_latest_dataset_version(
                dataset.name  # type: ignore[arg-type]
            )
        )
        next_version: int = (
            1
            if latest_version_record is None
            else int(latest_version_record.version) + 1  # type: ignore[arg-type]
        )
        logger.debug(
            f"Next version for dataset '{dataset_name}' will be {next_version}"
        )

        dataset_version: DatasetVersionRecord = DatasetVersionRecord(
            dataset_id=dataset.id,
            version=next_version,
            description=description,
        )

        # Associate files
        for sha256 in file_sha256s:
            file_record = self._get_file_by_sha256(sha256)
            dataset_version.files.append(file_record)

        self.session.add(dataset_version)
        self.session.flush()

        return dataset_version

    def _get_latest_dataset_version(self, name: str) -> DatasetVersionRecord | None:
        dataset = self._get_dataset_by_name(name)

        # Get latest version (may be None)
        return (
            self.session.query(DatasetVersionRecord)
            .filter(DatasetVersionRecord.dataset_id == dataset.id)
            .order_by(DatasetVersionRecord.version.desc())
            .first()
        )

    def _get_dataset_by_name(self, name: str) -> DatasetRecord:
        logger.debug(f"Retrieving dataset by name: {name}")
        dataset: DatasetRecord | None = (
            self.session.query(DatasetRecord).filter(DatasetRecord.name == name).first()
        )
        if not dataset:
            raise DatasetNotFound(f'Dataset "{name}" not found.')
        return dataset

    def _get_dataset_by_id(self, id: str) -> DatasetRecord:
        logger.debug(f"Retrieving dataset by id: {id}")
        dataset: DatasetRecord | None = (
            self.session.query(DatasetRecord).filter(DatasetRecord.id == id).first()
        )
        if not dataset:
            raise DatasetNotFound(f"Dataset id:{id} not found.")
        return dataset

    def _is_dataset_exists(self, name: str) -> bool:
        logger.debug(f"Checking if dataset exists: {name}")
        return (
            self.session.query(DatasetRecord).filter(DatasetRecord.name == name).count()
            > 0
        )

    def _parse_manifest(self, manifest_path: str) -> list[dict[str, Any]]:
        ext = os.path.splitext(manifest_path)[1].lower().lstrip(".")

        with open(manifest_path, "r") as f:
            data = yaml.safe_load(f) if ext in ["yaml", "yml"] else json.load(f)

        if not isinstance(data, dict) or not isinstance(data.get("files"), list):
            raise ValueError(
                "Manifest must be a dict with a 'files' list of file records."
            )

        records: list[dict[str, Any]] = [
            item
            for item in data["files"]
            if isinstance(item, dict) and "sha256" in item
        ]

        logger.debug(
            f"Parsed {len(records)} file records from manifest {manifest_path}"
        )
        return records

    def _parse_dataset_pattern(
        self, dataset_pattern: str
    ) -> tuple[str | None, int | None]:
        last_slash_index: int = dataset_pattern.rfind("/")

        dataset_name: str | None = None
        version_number: int | None = None

        if last_slash_index != -1:
            dataset_name_part: str = dataset_pattern[:last_slash_index].strip()
            version_part: Any = dataset_pattern[last_slash_index + 1 :].strip()

            if dataset_name_part:
                dataset_name = dataset_name_part

            if version_part.isdigit():
                version_number = int(version_part)

        else:
            if dataset_pattern.strip():
                dataset_name = dataset_pattern.strip()

        return dataset_name, version_number

    def _delete_file_by_sha256(
        self, sha256: str, dry: bool = False
    ) -> list[DatasetVersionRecord]:
        logger.debug(f'Deleting file record: "{sha256}"')

        # Get the file record
        file_record: FileRecord = self._get_file_by_sha256(sha256)
        if not file_record:
            raise FileRecordNotFound(f'File "{sha256}" not found.')

        # Get dataset versions that will be modified (before deletion)
        dataset_versions_to_modify: list[DatasetVersionRecord] = (
            self.session.query(DatasetVersionRecord)
            .join(dataset_version_files)
            .filter(dataset_version_files.c.file_id == file_record.id)
            .all()
        )

        # Log what's going to be deleted
        logger.debug(f"File to be deleted SHA256: {file_record.sha256}")
        logger.debug(
            f"Dataset versions to be modified: {[f'Dataset v{dv.version}' for dv in dataset_versions_to_modify]}"
        )

        if not dry:
            with self.transaction():
                # Remove tag associations
                self.session.execute(
                    file_tags.delete().where(file_tags.c.file_id == file_record.id)
                )

                # Remove dataset version associations
                self.session.execute(
                    dataset_version_files.delete().where(
                        dataset_version_files.c.file_id == file_record.id
                    )
                )

                # Delete the file record itself
                self.session.delete(file_record)
                self.session.flush()

                # Delete the S3 object
                self.storage.delete_obj(file_record.s3uri)  # type: ignore[arg-type]

        logger.debug(f"Successfully deleted file {file_record.sha256}.")
        return dataset_versions_to_modify
