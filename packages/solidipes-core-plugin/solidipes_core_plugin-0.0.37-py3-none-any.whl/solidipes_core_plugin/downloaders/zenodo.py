import os

from solidipes.downloaders.downloader import Downloader
from solidipes.utils import get_study_description_path
from solidipes.utils.utils import optional_parameter

from ..utils.zenodo_utils import ZenodoException, check_response, download_files, get_host_and_id


class ZenodoDownloader(Downloader):
    "Download study from Zenodo"

    parser_key = "zenodo"

    def download(self):
        main(self)

    @optional_parameter
    def only_metadata() -> bool:
        "Only download metadata (overrides destination directory's metadata!)"
        return False

    @optional_parameter
    def preview() -> str:
        "Specify a preview token if necessary to access the entry"
        pass


def main(args):
    """Download content from Zenodo"""

    import requests
    from solidipes.scripts.init import main as init
    from solidipes.utils.utils import include_metadata_description, set_study_metadata

    try:
        host, study_id = get_host_and_id(args.url)

        try:
            preview = getattr(args, "preview")
        except ValueError:
            preview = None
        if preview:
            url = f"https://{host}/api/deposit/depositions/{study_id}?preview=1&token=" + args.preview

        else:
            url = f"https://{host}/api/records/{study_id}"

        # Scan record
        response = requests.get(url)
        check_response(response, 200, "retrieve record")
        record = response.json()

        print(f"Retrieving study {study_id} from {host}...")

        # Create destination folder if it does not exist
        if not args.destination:
            args.destination = study_id
        if not os.path.exists(args.destination):
            os.makedirs(args.destination)

        if not args.only_metadata:
            download_files(record, destination=args.destination, preview=preview)

        # Initialize solidipes study
        class InitArgs:
            directory = str(args.destination)
            force = None

        try:
            init(InitArgs())
        except FileExistsError:
            pass

        # # Save metadata in YAML file
        print("Saving metadata...")
        metadata = process_metadata(record["metadata"])
        description_path = get_study_description_path(initial_path=args.destination)
        if "description" in metadata:
            with open(description_path, "a") as f:
                f.write(metadata["description"])
        metadata = include_metadata_description(metadata, initial_path=args.destination)
        set_study_metadata(metadata, initial_path=args.destination)

    except ZenodoException as e:
        print(e)


def process_metadata(metadata):
    """Process metadata to make dataset uploadable again"""

    if "upload_type" not in metadata:
        if "resource_type" in metadata:
            metadata["upload_type"] = metadata["resource_type"]["type"]
            del metadata["resource_type"]
        else:
            metadata["upload_type"] = "dataset"

    if "journal" in metadata:
        journal = metadata["journal"]
        for field in ["title", "volume", "issue", "pages"]:
            if field in journal:
                metadata[f"journal_{field}"] = journal[field]
        del metadata["journal"]

    if "license" in metadata:
        license_type = metadata["license"]
        if not isinstance(license_type, str):
            license_type = license_type.get("id")
        if license_type:
            metadata["license"] = license_type.lower()
        else:
            del metadata["license"]

    related_identifiers = metadata.get("related_identifiers", [])
    for related in related_identifiers:
        if related.get("relation") == "isVersionOf":
            related_identifiers.remove(related)

    return metadata
