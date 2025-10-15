from argparse import ArgumentParser
from importlib.metadata import version
from logging import Logger, getLogger

from dj.constants import DISTRO_NAME

logger: Logger = getLogger(__name__)


def parser(prog_name: str) -> dict:
    main_parser: ArgumentParser = ArgumentParser(prog=prog_name)

    # Global flags
    main_parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version(DISTRO_NAME)}"
    )
    main_parser.add_argument("--s3prefix", type=str, help="S3 prefix for data storage")
    main_parser.add_argument("--s3bucket", type=str, help="S3 bucket for data storage")
    main_parser.add_argument("--s3endpoint", type=str, help="S3 endpoint URL")
    main_parser.add_argument(
        "--database-endpoint", type=str, help="database endpoint URL"
    )
    main_parser.add_argument(
        "--echo", action="store_const", const=True, help="Echo SQL commands"
    )
    main_parser.add_argument(
        "--pool-size", type=int, help="Database connection pool size"
    )
    main_parser.add_argument(
        "--max-overflow", type=int, help="Max overflow for database connections"
    )
    main_parser.add_argument("--log-dir", type=str, help="Directory for log files")
    main_parser.add_argument(
        "--verbose",
        action="store_const",
        const=True,
        help="Enable verbose logging",
    )
    main_parser.add_argument(
        "--plain",
        action="store_const",
        const=True,
        help="Disable loading bar and colors",
    )

    # Subparsers
    sub_parsers = main_parser.add_subparsers(dest="command", required=True)

    # Config
    config_parser: ArgumentParser = sub_parsers.add_parser(
        "config", help="configure registry settings."
    )
    config_parser.add_argument("--set-s3endpoint", type=str, help="Set S3 endpoint URL")
    config_parser.add_argument("--set-s3bucket", type=str, help="Set S3 bucket")
    config_parser.add_argument("--set-s3prefix", type=str, help="Set S3 prefix")
    config_parser.add_argument(
        "--set-database-endpoint",
        type=str,
        help="Set database endpoint URL",
    )
    config_parser.add_argument(
        "--set-echo",
        action="store_const",
        const=True,
        help="Enable SQL command echoing",
    )
    config_parser.add_argument(
        "--set-pool-size", type=int, help="Set database connection pool size"
    )
    config_parser.add_argument(
        "--set-max-overflow", type=int, help="Set max overflow for database connections"
    )

    # Load
    load_parser: ArgumentParser = sub_parsers.add_parser(
        "load", help="load data into registry."
    )
    load_parser.add_argument(
        "paths",
        nargs="+",
        help="Source of data files (local or S3), S3 support filters.",
    )
    load_parser.add_argument(
        "--filters",
        nargs="+",
        help="Filter files by extension. will overwrite glob patterns.",
    )
    load_parser.add_argument("--tags", nargs="+", help="Tags for the dataset")

    # Create
    create_parser: ArgumentParser = sub_parsers.add_parser(
        "create", help="create a new dataset."
    )
    create_parser.add_argument("name", type=str, help="Name of the dataset")
    create_parser.add_argument(
        "paths", nargs="*", help="Paths to data files (optional, zero or more)"
    )
    create_parser.add_argument("--tags", "-t", nargs="+", help="Tags for the files")
    create_parser.add_argument(
        "--filters", "-f", nargs="+", help="Filter files by extension"
    )
    create_parser.add_argument("--exists-ok", "-e", action="store_const", const=True)
    create_parser.add_argument(
        "--description", "-d", type=str, help="Description of the dataset version"
    )
    create_parser.add_argument(
        "--manifest",
        "-m",
        type=str,
        help="File paths to config files",
    )

    # Update
    update_parser: ArgumentParser = sub_parsers.add_parser(
        "update", help="create a new dataset version."
    )
    update_parser.add_argument("name", type=str, help="Name of the dataset")
    update_parser.add_argument(
        "paths", nargs="*", help="Paths to data files (optional, zero or more)"
    )
    update_parser.add_argument("--tags", "-t", nargs="+", help="Tags for the files")
    update_parser.add_argument(
        "--filters", "-f", nargs="+", help="Filter files by extension"
    )
    update_parser.add_argument("--exists-ok", "-e", action="store_const", const=True)
    update_parser.add_argument(
        "--description", "-d", type=str, help="Description of the dataset version"
    )
    update_parser.add_argument(
        "--manifest",
        "-m",
        type=str,
        help="File paths to config files",
    )

    # List
    list_parser: ArgumentParser = sub_parsers.add_parser(
        "list", help="list datasets in the registry."
    )
    list_parser.add_argument(
        "pattern", nargs="?", type=str, help="Pattern to filter dataset names"
    )
    list_parser.add_argument(
        "--limit", type=int, help="Limit the number of datasets to list"
    )
    list_parser.add_argument(
        "--offset", type=int, help="Offset for pagination of datasets"
    )

    # Search
    search_parser: ArgumentParser = sub_parsers.add_parser(
        "search", help="search data."
    )
    search_parser.add_argument(
        "results_filepath", type=str, help="File path to save search results."
    )
    search_parser.add_argument(
        "dataset_pattern",
        nargs="?",
        type=str,
        help="Pattern to filter dataset names (example: mozilla/v3)",
    )
    search_parser.add_argument(
        "--sha256s",
        "-s",
        nargs="+",
        type=str,
        help="a list of registry files sha256 checksums.",
    )
    search_parser.add_argument(
        "--file-types",
        dest="mime_patterns",
        nargs="+",
        type=str,
        help="File types to filter by.",
    )
    search_parser.add_argument(
        "--included-tags",
        nargs="+",
        type=str,
        help="Files Tags to include.",
    )
    search_parser.add_argument(
        "--excluded-tags",
        nargs="+",
        type=str,
        help="Files Tags to exclude.",
    )
    search_parser.add_argument(
        "--limit", "-l", type=int, help="Limit the number of results."
    )

    # Fetch
    fetch_parser: ArgumentParser = sub_parsers.add_parser(
        "fetch", help="fetch data from registry."
    )
    fetch_parser.add_argument(
        "output_dir",
        nargs="?",
        type=str,
        help="Directory to save fetched files",
    )
    fetch_parser.add_argument(
        "--overwrite",
        action="store_const",
        const=True,
        help="Overwrite existing files during fetch",
    )
    fetch_parser.add_argument(
        "--flat",
        action="store_const",
        const=True,
        help="Store files in a flat structure without subdirectories",
    )
    fetch_parser.add_argument(
        "--manifest",
        type=str,
        help="YAML/JSON/ with data sha256s.",
    )
    fetch_parser.add_argument(
        "--dataset",
        dest="dataset_pattern",
        type=str,
        help="Dataset name pattern to filter by",
    )
    fetch_parser.add_argument(
        "--sha256s",
        "-s",
        nargs="+",
        type=str,
        help="a list of registry files sha256 checksums.",
    )
    fetch_parser.add_argument(
        "--file-types",
        dest="mime_patterns",
        nargs="+",
        type=str,
        help="File types to filter by.",
    )
    fetch_parser.add_argument(
        "--included-tags",
        nargs="+",
        type=str,
        help="Files Tags to include.",
    )
    fetch_parser.add_argument(
        "--excluded-tags",
        nargs="+",
        type=str,
        help="Files Tags to exclude.",
    )
    fetch_parser.add_argument(
        "--limit", "-l", type=int, help="Limit the number of results."
    )
    fetch_parser.add_argument(
        "results_filepath",
        nargs="?",
        type=str,
        help="File path to save search results.",
    )
    # Tag
    tag_parser: ArgumentParser = sub_parsers.add_parser(
        "tag", help="tag data files in the registry."
    )
    tag_parser.add_argument(
        "manifest",
        type=str,
        help="YAML/JSON with data sha256s.",
    )
    tag_parser.add_argument(
        "tags", nargs="+", type=str, help="Tags to add to the specified data files"
    )
    # Untag
    untag_parser: ArgumentParser = sub_parsers.add_parser(
        "untag", help="remove tags from data files in the registry."
    )
    untag_parser.add_argument(
        "manifest",
        type=str,
        help="YAML/JSON with data sha256s.",
    )
    untag_parser.add_argument(
        "tags", nargs="+", type=str, help="Tags to remove from the specified data files"
    )

    # Delete data
    delete_parser: ArgumentParser = sub_parsers.add_parser(
        "delete", help="delete data files from the registry."
    )
    delete_parser.add_argument(
        "manifest",
        type=str,
        help="YAML/JSON/ with data sha256s.",
    )
    delete_parser.add_argument(
        "--dry",
        action="store_const",
        const=True,
        help="If True, will only simulate the deletion without making changes",
    )
    # Delete dataset
    delete_dataset_parser: ArgumentParser = sub_parsers.add_parser(
        "delete-dataset",
        help="delete a dataset and all its versions from the registry.",
    )
    delete_dataset_parser.add_argument(
        "dataset_name", type=str, help="Name of the dataset to delete"
    )
    delete_dataset_parser.add_argument(
        "--dry",
        action="store_const",
        const=True,
        help="If True, will only simulate the deletion without making changes",
    )

    return {k: v for k, v in vars(main_parser.parse_args()).items() if v is not None}
