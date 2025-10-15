#!python3.12

from logging import Logger, getLogger
from sys import exit as sys_exit

from pydantic_core._pydantic_core import ValidationError

from dj.cli import parser
from dj.constants import PROGRAM_NAME
from dj.exceptions import (
    DatasetExist,
    DatasetNotFound,
    FailedToGatherFiles,
    FileRecordNotFound,
    InvalidSetting,
    S3BucketNotFound,
    TagNotFound,
    UnsuffiecentPermissions,
)
from dj.logging import configure_logging
from dj.registry.config import RegistryConfigManager
from dj.registry.journal import RegistryJournalist
from dj.schemes import (
    ConfigureRegistryConfig,
    CreateDatasetConfig,
    DeleteDataConfig,
    DeleteDatasetConfig,
    DJConfigCLI,
    FetchDataConfig,
    ListDatasetsConfig,
    LoadDataConfig,
    RegistryConfig,
    SearchDataConfig,
    TagDataConfig,
    UpdateDatasetConfig,
)

logger: Logger = getLogger(PROGRAM_NAME)


def main() -> None:
    parsed_args: dict = parser(PROGRAM_NAME)
    dj_cli_cfg: DJConfigCLI = DJConfigCLI(**parsed_args)
    configure_logging(
        PROGRAM_NAME,
        log_dir=dj_cli_cfg.log_dir,
        plain=dj_cli_cfg.plain,
        verbose=dj_cli_cfg.verbose,
    )

    registry_config_manager: RegistryConfigManager = RegistryConfigManager(
        RegistryConfig(**parsed_args)
    )

    logger.debug(f"CLI Arguments: {parsed_args}")
    logger.debug(f"DJ CLI Config: {dj_cli_cfg.model_dump()}")
    logger.debug(f"Registry Config: {registry_config_manager.cfg.model_dump()}")

    registry_cfg: RegistryConfig = registry_config_manager.cfg.model_copy(
        update=parsed_args
    )
    try:
        match dj_cli_cfg.command:
            case "config":
                registry_config_manager.configure(
                    ConfigureRegistryConfig(**parsed_args)
                )

            case "load":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.load_data(LoadDataConfig(**parsed_args))

            case "create":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.create_dataset(CreateDatasetConfig(**parsed_args))

            case "update":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.update_dataset(UpdateDatasetConfig(**parsed_args))

            case "list":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.list_datasets(ListDatasetsConfig(**parsed_args))

            case "search":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.search(SearchDataConfig(**parsed_args))

            case "fetch":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.fetch_data(FetchDataConfig(**parsed_args))

            case "tag":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.tag_data(TagDataConfig(**parsed_args))

            case "untag":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.untag_data(TagDataConfig(**parsed_args))

            case "delete":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.delete_data(DeleteDataConfig(**parsed_args))

            case "delete-dataset":
                with RegistryJournalist(registry_cfg) as journalist:
                    journalist.delete_dataset(DeleteDatasetConfig(**parsed_args))

    except (
        S3BucketNotFound,
        UnsuffiecentPermissions,
        DatasetExist,
        DatasetNotFound,
        FailedToGatherFiles,
        FileRecordNotFound,
        TagNotFound,
        InvalidSetting,
        ValidationError,
    ) as e:
        logger.debug(e, exc_info=True)
        logger.error(e)
        sys_exit(1)
