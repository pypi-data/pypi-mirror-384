import os

from solidipes.uploaders.uploader import Uploader
from solidipes.utils import generate_readme, include_metadata_description
from solidipes.utils import study_medatada_mandatory_fields as mandatory_fields
from solidipes.utils import study_medatada_removed_fields_upload as removed_fields
from solidipes.utils.utils import classproperty

################################################################


class DToolUploader(Uploader):
    parser_key = "dtool"
    command_help = "Publish study to dtool"
    name = "DTool"

    def upload(self, args) -> None:
        main(args)

    @classproperty
    def report_widget_class(self):
        from solidipes_core_plugin.reports.widgets.dtool import DToolPublish

        return DToolPublish


################################################################


def main(args) -> None:
    """Upload content to a DTool repository."""
    from ..utils.utils import get_study_root_path

    if args.directory is None:
        args.root_directory = get_study_root_path()
    else:
        args.root_directory = args.directory

    # Zip directory into temporary file
    generate_readme()
    # create_archive(args)
    print("Uploading archive")
    # get_deposition_uri(args)
    # upload_deposition_metadata(**vars(args))
    # upload the archive
    raise RuntimeError("TOIMPLEMENT")
    # upload_archive(progressbar=progressbar, **vars(args))
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


def load_and_check_metadata(config):
    """Load/create metadata file and check if mandatory fields are present"""

    dir_path = config.root_directory
    from ..utils import get_study_metadata, get_study_metadata_path

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
