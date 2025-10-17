import os

import requests
from solidipes.downloaders.downloader import Downloader
from solidipes.scripts.init import create_solidipes_directory
from solidipes.utils import DataRepositoryException, logging, set_study_metadata
from solidipes.utils.utils import optional_parameter

from ..utils.dspace5_utils import check_response, download_files, get_host_and_id

################################################################

logger = logging.getLogger()
################################################################


class Dspace5Downloader(Downloader):
    parser_key = ["dspace5", "ethresearchcollection"]
    command_help = "Download study from Dspace5"

    def download(self):
        main(self)

    @optional_parameter
    def only_metadata() -> bool:
        "Only download metadata (overrides destination directory's metadata!)"
        return False


def main(args):
    """Download content from Dspace5"""

    from solidipes.utils.metadata import dc_to_solidipes

    try:
        host, study_id = get_host_and_id(args.url)
        url = f"https://{host}/rest/api/items/{study_id}/metadata"

        # Scan record
        response = requests.get(url)
        check_response(response, 200, "retrieve record")
        response_record = response.json()
        record = {}

        for x in response_record:
            # TODO beware repeatable fields?
            record[x["key"]] = x["value"]

        print(f"Retrieving study {study_id} from {host}...")

        # Create destination folder if it does not exist
        if not args.destination:
            args.destination = f"{study_id}"
        if not os.path.exists(args.destination):
            os.makedirs(args.destination)

        # Create Solidipes directory if it does not exist
        try:
            create_solidipes_directory(args.destination)
        except FileExistsError:
            pass

        # Save metadata in YAML file
        print("Saving metadata...")

        metadata = process_metadata(dc_to_solidipes(record))
        metadata["zz_orig_metadata"] = record
        metadata["zz_orig_metadata"]["00solidipes_platform"] = "dspace5"
        metadata["zz_orig_metadata"]["00solidipes_host"] = host
        metadata["zz_orig_metadata"]["00solidipes_study_id"] = study_id

        set_study_metadata(metadata, initial_path=args.destination)

        if args.only_metadata:
            return

        url = f"https://{host}/rest/api/items/{study_id}/bitstreams"
        response = requests.get(url)
        check_response(response, 200, "locate files")
        bitstreams = response.json()

        # patch download links, they are relative at least in the ETHZ Research Collection
        for k in range(len(bitstreams)):
            if not bitstreams[k]["retrieveLink"].startswith("http"):
                bitstreams[k]["retrieveLink"] = f"https://{host}/rest/api/{bitstreams[k]['retrieveLink']}"

        download_files(bitstreams, destination=args.destination, progressbar=True)

    except Exception as e:
        if type(e) is not DataRepositoryException:
            raise e

        print(e)
        return


def process_metadata(metadata):
    """Process metadata to make dataset uploadable again"""

    # TODO ignoring this for the moment

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
        license_type = metadata["license"].get("id")
        if license_type:
            metadata["license"] = license_type.lower()
        else:
            del metadata["license"]

    related_identifiers = metadata.get("related_identifiers", [])
    for related in related_identifiers:
        if related.get("relation") == "isVersionOf":
            related_identifiers.remove(related)

    return metadata
