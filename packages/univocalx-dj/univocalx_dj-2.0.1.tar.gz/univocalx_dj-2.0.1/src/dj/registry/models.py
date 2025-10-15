# mypy: ignore-errors

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Association table for many-to-many relationship between files and tags
file_tags = Table(
    "file_tags",
    Base.metadata,
    Column("file_id", Integer, ForeignKey("files.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

# Association table for many-to-many relationship between dataset versions and files
dataset_version_files = Table(
    "dataset_version_files",
    Base.metadata,
    Column(
        "dataset_version_id",
        Integer,
        ForeignKey(
            "dataset_versions.id", ondelete="CASCADE"
        ),  # Cascade when version is deleted
        primary_key=True,
    ),
    Column(
        "file_id",
        Integer,
        ForeignKey("files.id"),  # NO cascade
        primary_key=True,
    ),
)


class TagRecord(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    files = relationship(
        "FileRecord",
        secondary="file_tags",
        backref=None,  # No backref to FileRecord
        lazy="dynamic",
    )


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sha256 = Column(String(64), unique=True, nullable=False)
    s3uri = Column(String(2048), nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)

    def model2dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sha256": self.sha256,
            "s3uri": self.s3uri,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
        }

    @staticmethod
    def dict2model(data: dict[str, Any]) -> "FileRecord":
        return FileRecord(
            id=data.get("id"),
            sha256=data["sha256"],
            s3uri=data["s3uri"],
            filename=data["filename"],
            mime_type=data["mime_type"],
            size_bytes=data["size_bytes"],
        )


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # enables cascade deletion
    versions = relationship(
        "DatasetVersionRecord",
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic",
    )


class DatasetVersionRecord(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    version = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint("dataset_id", "version"),)

    files = relationship(
        "FileRecord",
        secondary=dataset_version_files,
        lazy="dynamic",
    )

    dataset = relationship("DatasetRecord", back_populates="versions")
