import os
import shutil
from copy import deepcopy

import dtoolcore.utils
import yaml
from dtoolcore import DataSet
from solidipes.downloaders.downloader import Downloader
from solidipes.utils import logging
from solidipes.utils.utils import optional_parameter

################################################################
logger = logging.getLogger()
################################################################


class DToolDownloader(Downloader):
    "Download study from DTool"

    parser_key = "dtool"

    def download(self) -> None:
        main(self)

    @optional_parameter
    def subdir() -> str:
        "Place downloaded ietms within this subdirectoy of the detsination folder."
        return "data"

    @optional_parameter
    def only_metadata() -> bool:
        "Only download metadata (overrides destination directory's metadata!)"
        return False


def main(args) -> None:
    """Download content from dtool dataset"""

    from solidipes.scripts.init import create_solidipes_directory
    from solidipes.utils import set_study_metadata

    try:
        dtool_dataset_uri = dtoolcore.utils.sanitise_uri(args.url)

        dtool_dataset_admin_metadata = dtoolcore._admin_metadata_from_uri(dtool_dataset_uri, None)

        dtool_dataset = DataSet.from_uri(dtool_dataset_uri)

        if not args.destination:
            args.destination = dtool_dataset.name
        if not os.path.exists(args.destination):
            os.makedirs(args.destination)

        # Create Solidipes directory if it does not exist
        try:
            create_solidipes_directory(args.destination)
        except FileExistsError:
            pass

        # retrieve tags
        tags = dtool_dataset.list_tags()

        # retrieve annotations
        annotation_names = dtool_dataset.list_annotation_names()
        annotation_dict = {
            annotation_name: dtool_dataset.get_annotation(annotation_name) for annotation_name in annotation_names
        }

        metadata_dict = {}
        dtool_native_metadata_dict = {**dtool_dataset_admin_metadata}

        # retrieve yaml readme
        readme_dict = {}
        try:
            readme_content = dtool_dataset.get_readme_content()
            readme_dict = yaml.safe_load(readme_content)

            creators = readme_dict.get("owners", [])

            metadata_dict["description"] = readme_dict.get("description", "")
            metadata_dict["title"] = readme_dict.get("project", "")
            metadata_dict["creators"] = deepcopy(creators)
            metadata_dict["language"] = readme_dict.get("language", "eng")

            if len(readme_dict) > 0:
                dtool_native_metadata_dict["readme"] = readme_dict

            if "upload_type" not in readme_dict:
                if "resource_type" in readme_dict:
                    metadata_dict["upload_type"] = readme_dict["resource_type"]["type"]
                else:
                    metadata_dict["upload_type"] = "dataset"

            if "journal" in readme_dict:
                journal = readme_dict["journal"]
                for field in ["title", "volume", "issue", "pages"]:
                    if field in journal:
                        metadata_dict[f"journal_{field}"] = journal[field]

            if "license" in readme_dict:
                license_type = readme_dict["license"].get("id")
                if license_type:
                    metadata_dict["license"] = license_type.lower()

        except yaml.YAMLError as exc:
            logger.warning(exc)
            if len(readme_content) > 0:
                dtool_native_metadata_dict["readme"] = readme_content

        manifest = dtool_dataset.generate_manifest()
        dtool_native_metadata_dict["manifest"] = manifest

        if len(tags) > 0:
            metadata_dict["keywords"] = deepcopy(tags)
            dtool_native_metadata_dict["tags"] = deepcopy(tags)

        if len(annotation_dict) > 0:
            dtool_native_metadata_dict["annotations"] = annotation_dict

        metadata_dict["dtool"] = dtool_native_metadata_dict
        metadata_dict = deepcopy(metadata_dict)

        set_study_metadata(metadata_dict, initial_path=args.destination)

        if args.only_metadata:
            return

        subdir = os.path.join(args.destination, args.subdir)

        if not os.path.exists(subdir):
            os.makedirs(subdir)

        for uuid, entry in manifest["items"].items():
            relpath = entry["relpath"]
            fpath = dtool_dataset.item_content_abspath(uuid)
            dest_path = os.path.join(subdir, relpath)
            shutil.copyfile(fpath, dest_path)

    except Exception as e:
        print(e)
        return
