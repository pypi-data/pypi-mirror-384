import os

from datasize import DataSize
from solidipes.uploaders.uploader import Uploader
from solidipes.utils import generate_readme, include_metadata_description
from solidipes.utils import study_medatada_mandatory_fields as mandatory_fields
from solidipes.utils import study_medatada_removed_fields_upload as removed_fields
from solidipes.utils.utils import classproperty, optional_parameter, populate_parser

from ..utils.zenodo_utils import (
    ZenodoException,
    clean_deposition,
    create_deposition,
    get_access_token,
    get_existing_deposition_identifier,
    get_existing_deposition_infos,
    save_deposition_identifier,
    upload_archive,
    upload_deposition_metadata,
)

################################################################


class ZenodoUploader(Uploader):
    "Publish study to Zenodo"

    parser_key = ["zenodo", "inveniordm"]

    def upload(self):
        try:
            main(self)
        except ZenodoException as e:
            handle_zenodo_exception(e)

    @classmethod
    def populate_parser(cls, parser) -> None:
        populate_parser(cls, parser)

        deposition_group = parser.add_mutually_exclusive_group()

        deposition_group.add_argument(
            "--new-deposition",
            help="create a new deposition instead of updating a previously created one",
            action="store_true",
        )

        deposition_group.add_argument(
            "--tmp_dir",
            help=(
                "specify an existing directory where to store the temporary objects. Default to the system's temporary"
                " directory."
            ),
            default="/tmp" if os.name != "nt" else os.path.expanduser(r"~\AppData\Local\Temp"),
            type=str,
        )

        deposition_group.add_argument(
            "--existing-deposition",
            dest="existing_identifier",
            nargs="?",
            help="URL or DOI of the study to update. It must be in unplublished state.",
        )

    @optional_parameter
    def sandbox() -> bool:
        "use Zenodo sandbox test platform"
        return False

    @optional_parameter
    def access_token() -> str:
        "Provide the Zenodo token"
        pass

    @optional_parameter
    def no_cleanup() -> bool:
        "Do not clean the produced archive"
        return False

    @classproperty
    def report_widget_class(self):
        from solidipes_core_plugin.reports.widgets.zenodo import ZenodoPublish

        return ZenodoPublish


################################################################


def handle_zenodo_exception(e):
    print(e)

    if "has been deleted" in str(e) or "does not exist" in str(e):
        print(
            'Run the command with the "--new-deposition" option to create'
            ' a new entry, or the "--existing-deposition" option to use'
            " another existing entry."
        )

    if "Error deleting file" in str(e):
        print("Please check that the deposition is in draft state.")


################################################################


def main(args):
    """Upload content to Zenodo"""

    if not hasattr(args, "existing_identifier"):
        args.existing_identifier = None
    if not hasattr(args, "tmp_dir"):
        args.tmp_dir = "/tmp" if os.name != "nt" else os.path.expanduser(r"~\AppData\Local\Temp")
    if not hasattr(args, "new_deposition"):
        args.new_deposition = False
    # fetch where is the root of the things to Zip
    get_root_directory(args)

    # Zip directory into temporary file
    # mount_all()
    generate_readme()
    create_archive(args)
    print("Uploading archive")
    get_deposition_uri(args)
    upload_deposition_metadata(args.deposition_url, args.metadata, args.access_token)
    # upload the archive
    upload_archive(args.bucket_url, args.archive_path, args.access_token)

    # Final message
    print("Upload complete.")
    print("Please review your deposition and publish it when ready.")

    # Remove temporary file
    if args.no_cleanup:
        print(f'The archive has been kept at "{args.archive_path}".')
    else:
        os.remove(args.archive_path)
        print("Deleted temporary archive.")


################################################################


def get_root_directory(config):
    from solidipes.utils.utils import get_study_root_path

    if config.directory is None:
        config.root_directory = get_study_root_path()
    else:
        config.root_directory = config.directory


################################################################


def get_deposition_uri(config):
    root_directory = config.root_directory
    # Check if the directory exists
    if not os.path.isdir(root_directory):
        raise ValueError(f"Error: directory {root_directory} does not exist")

    # Check if the metadata file exists and load it
    metadata = load_and_check_metadata(config)

    if config.access_token is None:
        config.access_token = get_access_token()

    get_cleaned_deposition_infos(config)
    config.metadata = metadata


################################################################


def load_and_check_metadata(config):
    """Load/create metadata file and check if mandatory fields are present"""

    dir_path = config.root_directory
    from solidipes.utils.utils import get_study_metadata, get_study_metadata_path

    metadata = get_study_metadata(initial_path=dir_path, check_existence=True)
    metadata_path = get_study_metadata_path(initial_path=dir_path)

    # Replace description with content from DESCRIPTION.md converted in HTML
    metadata = include_metadata_description(metadata, md_to_html=True, use_readme=False, initial_path=dir_path)

    # Check if mandatory fields are present
    for field in mandatory_fields.keys():
        if field not in metadata or not metadata[field]:
            raise ValueError(
                f'Error: field "{field}" is missing from metadata file or is empty. Please edit {metadata_path} and try'
                " again."
            )

    # Check that creators is a list
    if not isinstance(metadata["creators"], list):
        raise ValueError(f'Error: field "creators" must be a list. Please edit {metadata_path} and try again.')

    # Check that each creator has a name
    for creator in metadata["creators"]:
        if "name" not in creator or not creator["name"]:
            raise ValueError(
                f'Error: field "name" is missing from one of the creators. Please edit {metadata_path} and try again.'
            )

    # Clean
    for field in removed_fields:
        if field in metadata:
            del metadata[field]

    if "related_identifiers" in metadata:
        for related_identifier in metadata["related_identifiers"]:
            if "relation" in related_identifier and related_identifier["relation"] == "isVersionOf":
                related_identifier["relation"] = "isNewVersionOf"

    return metadata


################################################################


def create_archive(config, _print=print):
    """Create a temporary zip archive of the directory"""

    if hasattr(config, "_print"):
        _print = config._print

    dir_path = config.root_directory
    import zipfile

    from solidipes.scanners.scanner_local import ExportScanner
    from solidipes.utils.progress import get_progress_bar
    from solidipes.utils.utils import bcolors

    archive_filename = _get_archive_filename(dir_path)

    if config.tmp_dir:
        config.tmp_dir = "/tmp" if os.name != "nt" else os.path.expanduser(r"~\AppData\Local\Temp")

    archive_path = os.path.join(config.tmp_dir, archive_filename)
    scanner = ExportScanner()
    filepaths = scanner.get_filepath_list()

    if os.path.exists(archive_path) and scanner.get_modified_time() < os.path.getmtime(archive_path):
        _print(f"Using existing archive {archive_path}...")
        config.archive_path = archive_path
        return

    _print(f"Creating archive {archive_path}...")

    with get_progress_bar("Creating archive", total=len(filepaths)) as progress:
        with zipfile.ZipFile(archive_path, "w", strict_timestamps=False) as zip_file:
            previous_dirnames = []

            for filepath in filepaths:
                progress.update(advance=1, text=filepath)
                try:
                    zip_file.write(os.path.abspath(filepath), filepath)

                    # Print tree structure
                    dirnames = filepath.split(os.sep)[:-1]
                    filename = os.path.basename(filepath)
                    depth = len(dirnames)
                    if dirnames != previous_dirnames:
                        for i in range(depth):
                            if i >= len(previous_dirnames) or dirnames[i] != previous_dirnames[i]:
                                _print("│   " * i + f"{bcolors.BRIGHT_BLUE}{dirnames[i]}{bcolors.RESET}")
                        previous_dirnames = dirnames
                    _print("│   " * depth + filename)

                except Exception as e:
                    _print(f"Error adding {filepath}: {e}")

    print(f"\nArchive size: {DataSize(os.path.getsize(archive_path)):.2a}\n")
    config.archive_path = archive_path


################################################################


def _get_archive_filename(dir_path: str) -> str:
    dir_name = os.path.basename(os.path.normpath(dir_path))
    archive_name = dir_name if dir_name != "." else "archive"
    archive_name = f"{archive_name}.zip"
    return archive_name


################################################################


def get_cleaned_deposition_infos(config):
    """Get deposition urls

    If no deposition has been created yet, or if new_deposition is True, create a new deposition.
    Otherwise, the saved deposition or the one specified by existing_identifier is used.
    """

    new_deposition = config.new_deposition
    existing_identifier = config.existing_identifier
    access_token = config.access_token
    sandbox = config.sandbox
    root_directory = config.root_directory

    deposition_identifier = None
    # Get existing deposition identifier, if any
    if existing_identifier:
        deposition_identifier = existing_identifier
    elif not new_deposition:
        # Otherwise, load saved identifier
        deposition_identifier = get_existing_deposition_identifier(root_directory)

    if deposition_identifier:
        # Update existing record
        deposition_url, bucket_url, web_url = get_existing_deposition_infos(
            deposition_identifier, access_token, sandbox
        )
        print(f"Updating deposition at {web_url}")
        # Delete current files
        clean_deposition(deposition_url, access_token)

    else:
        # Create deposition
        deposition_url, bucket_url, web_url = create_deposition(access_token, sandbox)
        print(f"Deposition created: {web_url}")

    # Save deposition identifier if successfully created or accessed
    save_deposition_identifier(web_url, root_directory)
    config.deposition_url = deposition_url
    config.bucket_url = bucket_url
