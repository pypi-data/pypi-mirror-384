import os
from logging import Logger, getLogger

from sqlalchemy import and_, func, not_, or_, select

from dj.exceptions import (
    DatasetExist,
    DatasetNotFound,
    FailedToGatherFiles,
    FileRecordExist,
    FileRecordNotFound,
    S3KeyNotFound,
    TagExist,
    TagNotFound,
)
from dj.inspect import FileInspector
from dj.registry.actor import RegistryActor
from dj.registry.models import (
    DatasetRecord,
    DatasetVersionRecord,
    FileRecord,
    TagRecord,
    dataset_version_files,
    file_tags,
)
from dj.schemes import (
    CreateDatasetConfig,
    DeleteDataConfig,
    DeleteDatasetConfig,
    FetchDataConfig,
    FileMetadata,
    ListDatasetsConfig,
    LoadDataConfig,
    SearchDataConfig,
    TagDataConfig,
    UpdateDatasetConfig,
)
from dj.utils import (
    collect_files,
    export_data,
    merge_s3uri,
    unified_table,
    unified_track,
)

logger: Logger = getLogger(__name__)


class RegistryJournalist(RegistryActor):
    def gather_files(self, paths: list[str], filters: list[str] | None) -> set[str]:
        datafiles: set[str] = set()

        logger.debug(f"Attempting to gather files, filters: {filters}")
        for path in paths:
            if path.startswith("s3://"):
                logger.info("gathering files from S3")
                s3objects: list[str] = self.storage.list_objects(
                    path,
                    filters,
                )

                for s3obj in s3objects:
                    datafiles.add(merge_s3uri(path, s3obj))
            else:
                logger.debug("gathering files from local storage")
                datafiles.update(collect_files(path, filters, recursive=True))

        logger.info(f"Gathered {len(datafiles)} file\\s")
        return datafiles

    def _load_file2registry(self, filepath: str, tags: list[str] | None) -> str:
        with self._get_local_path(filepath) as local_path:
            metadata: FileMetadata = FileInspector(local_path).metadata
            with self.transaction():
                try:
                    file_record: FileRecord = self._create_file_record(metadata)
                except FileRecordExist as e:
                    logger.debug(e, exc_info=e)
                    logger.warning(e)
                    file_record = self._get_file_by_sha256(metadata.sha256)

                if tags:
                    file_record = self._associate_tags_with_file(metadata.sha256, tags)

                if not self.storage.obj_exists(file_record.s3uri):  # type: ignore[arg-type]
                    self.storage.upload(local_path, file_record.s3uri)  # type: ignore[arg-type]

            return file_record.sha256  # type: ignore[return-value]

    def create_tags(self, tag_names: list[str]) -> list[str]:
        created_tags: list[str] = []
        with self.transaction():
            for name in tag_names:
                try:
                    self._create_tag_record(name)
                    created_tags.append(name)
                except TagExist:
                    logger.warning(f'Tag "{name}" already exists. Skipping.')
                else:
                    self.session.commit()

        if created_tags:
            logger.info(f'Created Tag(s): "{", ".join(created_tags)}"')
        return created_tags

    def load_data(self, load_cfg: LoadDataConfig) -> list[str]:
        logger.info("Starting to load files to registry.")
        gathered_files: set[str] = self.gather_files(load_cfg.paths, load_cfg.filters)

        if not gathered_files:
            raise FailedToGatherFiles(
                f"Failed to gather data files from {load_cfg.paths}"
            )

        created_sha256s: list[str] = []

        # Convert to list to get accurate total
        files_list = list(gathered_files)

        if load_cfg.tags:
            self.create_tags(load_cfg.tags)

        for filepath in unified_track(files_list, desc="☁️  Loading"):
            file_sha256 = self._load_file2registry(filepath, load_cfg.tags)
            if file_sha256:
                created_sha256s.append(file_sha256)

        return created_sha256s

    def create_dataset(self, create_cfg: CreateDatasetConfig) -> None:
        # Create/Get Dataset Record
        try:
            dataset: DatasetRecord = self._create_dataset_record(name=create_cfg.name)
            logger.info(f'Created dataset "{create_cfg.name}" successfully.')
        except DatasetExist:
            if not create_cfg.exists_ok:
                raise

            dataset = self._get_dataset_by_name(create_cfg.name)
            logger.warning(f'Dataset "{create_cfg.name}" already exists.')
        else:
            self.session.commit()

        file_sha256s: list[str] = []
        with self.transaction():
            # Load Local Files
            if create_cfg.paths:
                file_sha256s.extend(self.load_data(create_cfg))

            # Parse Manifest
            if create_cfg.manifest:
                file_sha256s.extend(
                    record_dict["sha256"]
                    for record_dict in self._parse_manifest(create_cfg.manifest)  # type: ignore[arg-type]
                )

            # Create Dataset Version
            if file_sha256s:
                total_linking: int = len(file_sha256s)
                logger.debug(f"Linking {total_linking} file(s) to dataset.")

                dataset_version: int = self._create_dataset_version(  # type: ignore[assignment]
                    dataset_name=dataset.name,  # type: ignore[arg-type]
                    file_sha256s=file_sha256s,  # type: ignore[arg-type]
                    description=create_cfg.description,
                ).version

                logger.info(
                    f'Created "{dataset.name}/v{dataset_version}" with {total_linking} file(s).'
                )

    def update_dataset(self, update_cfg: UpdateDatasetConfig) -> None:
        logger.info(f'Updating dataset: "{update_cfg.name}"')
        dataset: DatasetRecord = self._get_dataset_by_name(update_cfg.name)
        if not dataset:
            raise DatasetNotFound(f'Dataset "{update_cfg.name}" not found.')

        # Gather new files
        all_sha256s: set[str] = set()
        if update_cfg.paths:
            all_sha256s.update(self.load_data(update_cfg))

        if update_cfg.manifest:
            all_sha256s.update(
                record_dict["sha256"]
                for record_dict in self._parse_manifest(update_cfg.manifest)  # type: ignore[arg-type]
            )

        # Get previous files from latest version
        latest_version: DatasetVersionRecord | None = self._get_latest_dataset_version(
            dataset.name  # type: ignore[arg-type]
        )

        # Include files from previous version
        if latest_version:
            all_sha256s.update(file.sha256 for file in latest_version.files)

        # Create new dataset version with all files
        if all_sha256s:
            with self.transaction():
                dataset_version = self._create_dataset_version(
                    dataset_name=dataset.name,  # type: ignore[arg-type]
                    file_sha256s=list(all_sha256s),
                    description=update_cfg.description,
                ).version
            logger.info(
                f'Created "{dataset.name}/v{dataset_version}" with {len(all_sha256s)} file(s).'
            )
        else:
            logger.warning("No new files to add to the dataset.")

    def list_datasets(self, list_config: ListDatasetsConfig) -> list[DatasetRecord]:
        query = self.session.query(DatasetRecord)

        if list_config.pattern:
            query = query.filter(DatasetRecord.name.ilike(f"%{list_config.pattern}%"))

        if list_config.limit:
            query = query.limit(list_config.limit)
        if list_config.offset:
            query = query.offset(list_config.offset)

        datasets: list[DatasetRecord] = query.all()

        datasets_metadata: list[dict[str, str | int]] = []
        for dataset in datasets:
            latest_version: DatasetVersionRecord | None = (
                self._get_latest_dataset_version(dataset.name)  # type: ignore[arg-type]
            )

            datasets_metadata.append(
                {
                    "id": dataset.id,  # type: ignore[dict-item]
                    "name": dataset.name,  # type: ignore[dict-item]
                    "creation_date": dataset.created_at,  # type: ignore[dict-item]
                    "latest_version": latest_version.version  # type: ignore[dict-item]
                    if latest_version
                    else "None",
                    "file_count": latest_version.files.count() if latest_version else 0,
                }  # type: ignore[dict-item]
            )

        if datasets_metadata:
            logger.info(f'Found "{len(datasets_metadata)}" dataset(s).')
            logger.debug(datasets_metadata)
            unified_table(
                datasets_metadata,
                title="Datasets",
            )
        else:
            logger.info("No datasets found matching the criteria")
        return datasets

    def search(self, search_cfg: SearchDataConfig) -> list[FileRecord]:
        logger.info("Searching for files.")

        search_cfg_dict: dict = search_cfg.model_dump()
        logger.debug(search_cfg_dict)
        unified_table(
            title="🔍 Filters",
            data=[
                {"filter": k, "value": str(v) if v is not None else "None"}
                for k, v in search_cfg.model_dump().items()
            ],
        )

        query = select(FileRecord)
        filters = []

        if search_cfg.dataset_pattern:
            dataset_name, version_number = self._parse_dataset_pattern(
                search_cfg.dataset_pattern
            )

            # Join through dataset_versions -> datasets to search dataset names and versions
            dataset_subquery = (
                select(FileRecord.id)
                .select_from(FileRecord)
                .join(
                    dataset_version_files,
                    FileRecord.id == dataset_version_files.c.file_id,
                )
                .join(
                    DatasetVersionRecord,
                    dataset_version_files.c.dataset_version_id
                    == DatasetVersionRecord.id,
                )
                .join(
                    DatasetRecord, DatasetVersionRecord.dataset_id == DatasetRecord.id
                )
            )

            # Apply dataset name filter with ilike
            if dataset_name:
                dataset_subquery = dataset_subquery.where(
                    DatasetRecord.name.ilike(f"%{dataset_name}%")
                )

            # If version is specified, use exact version
            if version_number:
                dataset_subquery = dataset_subquery.where(
                    DatasetVersionRecord.version == version_number
                )
            else:
                latest_versions_subquery = (
                    select(
                        DatasetVersionRecord.dataset_id,
                        func.max(DatasetVersionRecord.version).label("latest_version"),
                    )
                    .join(
                        DatasetRecord,
                        DatasetVersionRecord.dataset_id == DatasetRecord.id,
                    )
                    .where(DatasetRecord.name.ilike(f"%{dataset_name}%"))
                    .group_by(DatasetVersionRecord.dataset_id)
                    .subquery()
                )

                # Filter to only include files from the latest versions
                dataset_subquery = dataset_subquery.join(
                    latest_versions_subquery,
                    and_(
                        DatasetVersionRecord.dataset_id
                        == latest_versions_subquery.c.dataset_id,
                        DatasetVersionRecord.version
                        == latest_versions_subquery.c.latest_version,
                    ),
                )

            dataset_subquery = dataset_subquery.distinct()
            filters.append(FileRecord.id.in_(dataset_subquery))

        # SHA256 filter (exact match)
        if search_cfg.sha256s:
            filters.append(FileRecord.sha256.in_(search_cfg.sha256s))

        # MIME type patterns filter (multiple patterns with OR logic)
        if search_cfg.mime_patterns:
            mime_filters = []
            for pattern in search_cfg.mime_patterns:
                mime_filters.append(FileRecord.mime_type.ilike(f"%{pattern}%"))
            filters.append(or_(*mime_filters))  # type: ignore[arg-type]

        # Tags filtering
        if search_cfg.included_tags:
            # For each included tag, we need to ensure the file has that tag
            for tag_name in search_cfg.included_tags:
                tag_subquery = (
                    select(file_tags.c.file_id)
                    .join(TagRecord, file_tags.c.tag_id == TagRecord.id)
                    .where(TagRecord.name == tag_name)
                )
                filters.append(FileRecord.id.in_(tag_subquery))

        if search_cfg.excluded_tags:
            # Exclude files that have any of the excluded tags
            excluded_subquery = (
                select(file_tags.c.file_id)
                .join(TagRecord, file_tags.c.tag_id == TagRecord.id)
                .where(TagRecord.name.in_(search_cfg.excluded_tags))
            )
            filters.append(not_(FileRecord.id.in_(excluded_subquery)))

        # Apply all filters with AND logic
        if filters:
            query = query.where(and_(*filters))

        # Apply limit
        if search_cfg.limit:
            query = query.limit(search_cfg.limit)

        # Execute the query
        results = self.session.execute(query).scalars().all()

        # Export results to file if specified
        if search_cfg.results_filepath:
            logger.info(
                f'Writing "{len(results)}" results to: "{search_cfg.results_filepath}"'
            )

            export_data(
                search_cfg.results_filepath,
                {"files": [record.model2dict() for record in results]},
            )

        return results  # type: ignore[return-value]

    def fetch_data(self, fetch_cfg: FetchDataConfig) -> list[FileRecord]:
        file_records: list[FileRecord] = self.search(fetch_cfg)

        # Parse and join manifest records to search results
        if fetch_cfg.manifest:
            existing_sha256s: set[str] = set(record.sha256 for record in file_records)  # type: ignore[misc]
            manifest_records: list[FileRecord] = []

            for record_dict in self._parse_manifest(fetch_cfg.manifest):  # type: ignore[arg-type]
                try:
                    file_record: FileRecord = FileRecord.dict2model(record_dict)
                except KeyError:
                    logger.warning(
                        f"Skipping record: {record_dict} Missing required field."
                    )

                if file_record.sha256 not in existing_sha256s:
                    manifest_records.append(file_record)

            file_records.extend(manifest_records)

        # Iterate over each record and attempt to download it
        logger.info(f'Found "{len(file_records)}" suitable file(s).')
        for file_record in unified_track(
            file_records,
            desc="⬇️   Downloading",
        ):
            filename: str = os.path.basename(file_record.s3uri)
            filepath: str = (
                os.path.join(fetch_cfg.output_dir, file_record.mime_type, filename)
                if not fetch_cfg.flat
                else os.path.join(fetch_cfg.output_dir, filename)
            )

            try:
                self.storage.download_obj(
                    file_record.s3uri,  # type: ignore[arg-type]
                    filepath,
                    overwrite=fetch_cfg.overwrite,
                )
            except S3KeyNotFound:
                logger.warning(f"Missing object: {file_record.s3uri}")
        return file_records

    def tag_data(self, tagging_cfg: TagDataConfig) -> set[str]:
        # Parse manifest records
        manifest_records: list[dict[str, str]] = self._parse_manifest(
            tagging_cfg.manifest  # type: ignore[arg-type]
        )
        logger.info(
            f"Found positionals {len(manifest_records)} file(s) in the manifest."
        )

        # Create Tags
        self.create_tags(tagging_cfg.tags)

        # Associate tags with files
        processed_sha256s: set[str] = set()
        for record_dict in unified_track(manifest_records, desc="🏷️   Tagging"):
            try:
                sha256: str = record_dict["sha256"]

                if sha256 not in processed_sha256s:
                    with self.transaction():
                        self._associate_tags_with_file(sha256, tagging_cfg.tags)

                    processed_sha256s.add(sha256)
                else:
                    logger.debug(f"Skipping duplicate sha256: {sha256}")

            except KeyError:
                logger.warning(f"Skipping record: {record_dict} Missing sha256 field.")

            except FileRecordNotFound as e:
                processed_sha256s.add(sha256)
                logger.warning(e)

        logger.info(f"Tagged {len(processed_sha256s)} file(s).")
        return processed_sha256s

    def untag_data(self, tagging_cfg: TagDataConfig) -> set[str]:
        # Parse manifest records
        manifest_records: list[dict[str, str]] = self._parse_manifest(
            tagging_cfg.manifest  # type: ignore[arg-type]
        )
        logger.info(
            f"Found {len(manifest_records)} file(s) in the manifest for untagging."
        )

        # Disassociate tags with files
        processed_sha256s: set[str] = set()
        for record_dict in unified_track(manifest_records, desc="🏷️   Untagging"):
            try:
                sha256: str = record_dict["sha256"]

                if sha256 not in processed_sha256s:
                    with self.transaction():
                        self._disassociate_tags_from_file(sha256, tagging_cfg.tags)

                    processed_sha256s.add(sha256)
                else:
                    logger.debug(f"Skipping duplicate sha256: {sha256}")

            except KeyError:
                logger.warning(f"Skipping record: {record_dict} Missing sha256 field.")

            except TagNotFound as e:
                processed_sha256s.add(sha256)
                logger.warning(e)

            except FileRecordNotFound as e:
                processed_sha256s.add(sha256)
                logger.warning(e)

        logger.info(f"Untagged {len(processed_sha256s)} file(s).")
        return processed_sha256s

    def delete_data(
        self, delete_data_cfg: DeleteDataConfig
    ) -> list[DatasetVersionRecord]:
        manifest_records: list[dict[str, str]] = self._parse_manifest(
            delete_data_cfg.manifest  # type: ignore[arg-type]
        )
        logger.info(
            f"Found {len(manifest_records)} file(s) in the manifest for deletion."
        )

        unique_versions_dict: dict[tuple[str, int], DatasetVersionRecord] = {}
        for record_dict in manifest_records:
            try:
                sha256: str = record_dict["sha256"]
                logger.debug(f"Attempting to delete file with sha256: {sha256}")
                modified_dataset_versions: list[DatasetVersionRecord] = (
                    self._delete_file_by_sha256(sha256, dry=delete_data_cfg.dry)
                )

                for dv in modified_dataset_versions:
                    unique_key: tuple[str, int] = (dv.dataset_id, dv.version)  # type: ignore[assignment]
                    if unique_key not in unique_versions_dict:
                        unique_versions_dict[unique_key] = dv

                formatted_versions: list[str] = [
                    f"{self._get_dataset_by_id(dv.dataset_id).name}/v{dv.version}"  # type: ignore[arg-type]
                    for dv in modified_dataset_versions
                ]
                logger.info(
                    f"Deleting {sha256} affects {formatted_versions} dataset versions."
                )

            except KeyError:
                logger.warning(f"Skipping record: {record_dict} Missing sha256 field.")
            except FileRecordNotFound as e:
                logger.warning(e)

        total_modified_dataset_versions: list[DatasetVersionRecord] = list(
            unique_versions_dict.values()
        )
        logger.info(
            f"Affected dataset versions: {len(total_modified_dataset_versions)}."
        )
        return total_modified_dataset_versions

    def delete_dataset(self, delete_dataset_cfg: DeleteDatasetConfig) -> None:
        logger.info(f'Deleting dataset: "{delete_dataset_cfg.dataset_name}"')
        dataset: DatasetRecord = self._get_dataset_by_name(
            delete_dataset_cfg.dataset_name
        )

        logger.info(f"Dataset has {dataset.versions.count()} version(s).")
        if not delete_dataset_cfg.dry:
            with self.transaction():
                self.session.delete(dataset)
                logger.info(
                    f'Dataset "{delete_dataset_cfg.dataset_name}" deleted successfully.'
                )
