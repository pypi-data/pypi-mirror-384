import json
import os
import re
import urllib.parse
import zipfile
from getpass import getpass

import requests
from solidipes.utils import solidipes_logging as logging
from solidipes.utils.progress import get_progress_bar
from solidipes.utils.utils import DataRepositoryException, get_zenodo_infos, save_yaml, set_zenodo_infos
from tqdm import tqdm

print = logging.invalidPrint
logger = logging.getLogger()


download_chunk_size = 1024


def get_host_and_id(identifier):
    """Extract host and study ID from string identifier

    The identifier could be a number of forms:
    - https://infoscience.epfl.ch/entities/product/<guid>
    - https://infoscience.epfl.ch/handle/<handle code>
    - https://doi.org/10.5075/XXXXXX
    - 10.5075/XXXXXXXXXX

    Args:
        identifier (str): URL or DOI of the study to download

    Returns:
        (str, str): DSpace host and study ID
            host: "infoscience.epfl.ch" or some other instance
              For an extensive list of potential servers:
              https://registry.lyrasis.org/?gv_search=7.x&filter_10=DSpace&filter_4_6&filter_3&filter_20&filter_28&mode=all#gv-view-178-1
    """

    hostnames = (
        "infoscience.epfl.ch",
        "infoscience-test.epfl.ch",
        "infoscience-sb.epfl.ch",
        "boris-portal.unibe.ch",
        # "iris.unil.ch", # TODO Their API is exposed at api.unil.ch/iris, how to deal with this case?
        "digitalcollection.zhaw.ch",
        "dspace.houghton.edu",
        "dukespace.lib.duke.edu",
        "oaktrust.library.tamu.edu",
        "openknowledge.fao.org",
    )

    guid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
    doi_regex = r"(doi.org\/){0,1}(10\.\d{4,9}\/[-._;()\/:A-Z0-9])+$"

    schemes = [{"pattern": rf"{x}/entities/product/({guid_regex})", "host": x} for x in hostnames]
    schemes += [{"pattern": rf"{x}/entities/publication/({guid_regex})", "host": x} for x in hostnames]
    schemes += [{"pattern": rf"{x}/items/({guid_regex})", "host": x} for x in hostnames]
    h_schemes = [{"pattern": rf"{x}/handle/(.*)", "host": x} for x in hostnames]

    for scheme in schemes:
        match = re.search(scheme["pattern"], identifier)
        if match:
            return scheme["host"], match.group(1)

    for scheme in h_schemes:
        match = re.search(scheme["pattern"], identifier)
        if match:
            handle = match.group(1)
            hdlparam = urllib.parse.quote_plus(f"hdl:{handle}")
            # For consistence: resolve to a UUID and fall back to UUID case
            url = f"https://{scheme['host']}/server/api/pid/find?id={hdlparam}"
            r = requests.get(url)
            data = r.json()
            uuid = data["uuid"]
            return scheme["host"], uuid

    match = re.match(doi_regex, identifier)
    if match:
        doi = match.group(1)
        url = f"https://api.datacite.org/dois/{doi}"
        r = requests.get(url)
        data = r.json()
        url_identifier = data["attributes"]["url"]
        return get_host_and_id(url_identifier)

    raise ValueError(f"Invalid identifier: {identifier}")


def check_response(response, expected_status_code, task_description):
    if response.status_code == expected_status_code:
        return

    error_message = f"Error {task_description}: {response.status_code}"

    try:
        data = response.json()

        if "message" in data:
            error_message += f" {data['message']}"

        if "errors" in data:
            for sub_data in data["errors"]:
                error_message += f"\n- {sub_data['field']}: {sub_data['messages']}"
    except requests.exceptions.JSONDecodeError:
        error_message += f"\n\n{response.text}"

    raise DataRepositoryException(error_message)


def list_collections(hostname):
    # A Dspace record must be part of a collection
    # collections will depend on local configuration details, so the user will need to choose...
    url = f"https://{hostname}/server/api/core/collections"
    r = requests.get(url, timeout=500)
    collections = r.json()["_embedded"]["collections"]
    return collections


# Upload methods ##############################################################


def get_access_password(hostname):
    # Alternative login method, available if necessary - an API token is more convenient
    user = input("Enter username: ")
    password = getpass("Enter DSpace password: ")

    # Initial step: get XSRF token and cookie
    url1 = f"https://{hostname}/server/api"
    r = requests.get(url1)
    xsrfktoken = r.headers["DSPACE-XSRF-TOKEN"]
    cookies = r.headers["Set-Cookie"].split("; ")
    xsrfcookie = [c for c in cookies if c.startswith("DSPACE-XSRF-COOKIE=")][0]

    # 2nd step: authenticate using login and password
    headers = {"X-XSRF-TOKEN": xsrfktoken, "Cookies": xsrfcookie}
    data = {"user": user, "password": password}
    auth_url = f"{url1}/authn/login"
    r = requests.post(auth_url, headers=headers, data=data)
    access_token = r.headers["Authorization"]

    logger.info("Moving on...")
    return access_token


def get_access_token(hostname):
    # Hostname should not be necessary
    return getpass("Enter Dspace API access token: ")


def get_existing_deposition_infos(identifier, access_token):
    host, study_id = get_host_and_id(identifier)

    # Build URL
    deposition_url = f"https://{host}/server/api/core/items/{study_id}?embed=bundles/bitstreams"
    params = {"Authorization": f"Bearer {access_token}"}

    # Get deposition infos
    response = requests.get(deposition_url, params=params)
    check_response(response, 200, "getting existing deposition infos")
    bucket_url = response.json()["links"]["bucket"]
    web_url = response.json()["links"]["html"]

    return deposition_url, bucket_url, web_url


def upload_deposition_metadata(deposition_url, metadata, access_token):
    from solidipes.utils.metadata import solidipes_to_dspace7

    # Update metadata
    url = f"{deposition_url}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    response = requests.patch(url, data=json.dumps(solidipes_to_dspace7(metadata)), headers=headers)

    check_response(response, 200, "updating deposition metadata")


def clean_deposition(deposition_url, access_token):
    # Get list of files
    url = f"{deposition_url}/files"
    params = {"access_token": access_token}
    response = requests.get(url, params=params)
    check_response(response, 200, "getting list of files")

    # Delete files
    for file in response.json():
        url = f"{deposition_url}/files/{file['id']}"
        response = requests.delete(url, params=params)
        check_response(response, 204, f'deleting file "{file["filename"]}"')


def create_deposition(access_token, hostname, collection):
    # Create a new deposition
    # At this point, we create a workspace item, not a full record
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    url = f"https://{hostname}/server/api/submission/workspaceitems?owningCollection={collection}&embed=item"
    response = requests.post(url, json={}, headers=headers)
    check_response(response, 201, "creating deposition")

    # Get deposition ID and bucket URL
    data = response.json()

    submission_id = data["id"]
    item_id = data["_embedded"]["item"]["id"]

    deposition_url = f"https://{hostname}/server/api/core/items/{item_id}"
    bucket_url = f"https://{hostname}/server/api/submission/workspaceitems/{submission_id}"
    web_url = data["_embedded"]["item"]["_links"]["self"]["href"]

    return deposition_url, bucket_url, web_url


def get_existing_deposition_identifier(root_dir):
    data = get_zenodo_infos(initial_path=root_dir)
    if "deposition_identifier" in data:
        return data["deposition_identifier"]
    return None


def save_deposition_identifier(web_url, root_dir):
    data = get_zenodo_infos(initial_path=root_dir)
    data["deposition_identifier"] = web_url
    set_zenodo_infos(data, initial_path=root_dir)


def upload_archive(bucket_url=None, archive_path=None, access_token=None, **kwargs):
    size = os.path.getsize(archive_path)
    filename = os.path.basename(archive_path)

    url = f"{bucket_url}"
    headers = {"Authorization": f"Bearer {access_token}"}

    with get_progress_bar("Uploading archive to Dspace", total=size, show_datasize=True) as progress_bar:
        with open(archive_path, "rb") as f:
            read_original = f.read

            def read_update_progress(*args, **kwargs):
                chunk = read_original(*args, **kwargs)
                progress_bar.update(len(chunk))
                return chunk

            f.read = read_update_progress
            archive = {"file": f}
            response = requests.post(url, files=archive, headers=headers)

    check_response(response, 201, "uploading archive")

    # Send file-level metadata
    # TODO: pass the license instead of N/A
    file_metadata = [
        {
            "op": "add",
            "path": "/sections/upload-product/files/0/metadata/dc.title",
            "value": [{"value": filename}],
        },
        {
            "op": "add",
            "path": "/sections/upload-product/files/0/metadata/dc.type",
            "value": [{"value": "main dataset"}],
        },
        {
            "op": "add",
            "path": "/sections/upload-product/files/0/metadata/oaire.licenseCondition",
            "value": [{"value": "N/A"}],
        },
        {
            "op": "add",
            "path": "/sections/upload-product/files/0/accessConditions",
            "value": [{"name": "openaccess"}],
        },
    ]

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    response = requests.patch(url, data=json.dumps(file_metadata), headers=headers)
    check_response(response, 200, "adding file-level metadata")


# Download methods ############################################################


def download_files(record, destination, progressbar=False):
    bundles = record["_embedded"]["bundles"]["_embedded"]["bundles"]
    # Identify the bundle that contains actual file information (if any)
    file_bundles = [b for b in bundles if b["name"] == "ORIGINAL"]
    if len(file_bundles) > 0:
        bitstreams = file_bundles[0]["_embedded"]["bitstreams"]["_embedded"]["bitstreams"]
        n_files = len(bitstreams)
    else:
        logger.error("The record has no associated files")
        n_files = 0

    # Download files

    key = ""
    path = ""

    for i in range(n_files):
        file = bitstreams[i]
        url = file["_links"]["content"]["href"]
        key = file["name"]
        path = os.path.join(destination, key)

        # Download file
        logger.info(f"({i + 1}/{n_files}) Downloading {key}...")
        try:
            download_file(url, key, path, progressbar)
        except ValueError as e:
            logger.error(e)
            continue

    # If only one file is a zip, unzip it and remove the zip
    zips = [file["name"] for file in bitstreams if file["name"].endswith(".zip")]
    if len(zips) == 1:
        logger.info("Unzipping...")
        path = os.path.join(destination, zips[0])
        with zipfile.ZipFile(path, "r") as zip_ref:
            zip_ref.extractall(destination)
        os.remove(path)


def download_file(url, key, path, progressbar=False):
    # Create directory if necessary
    os.makedirs(os.path.dirname(path), exist_ok=True)

    response = requests.get(url, stream=True)
    check_response(response, 200, "downloading file")

    size = int(response.headers.get("content-length", 0))
    with open(path, "wb") as f:
        if progressbar:
            bar = tqdm(
                desc=key,
                total=size,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            )

        for data in response.iter_content(chunk_size=download_chunk_size):
            size = f.write(data)
            if progressbar:
                bar.update(size)

        if progressbar:
            bar.close()


# Developer methods ###########################################################


def _download_zenodo_licenses():
    url = "https://zenodo.org/api/licenses/?size=10000"
    script_directory = os.path.dirname(os.path.realpath(__file__))
    output_filename = os.path.join(script_directory, "zenodo_licenses.yaml")
    output_file_path = os.path.join(script_directory, output_filename)

    response = requests.get(url)
    check_response(response, 200, "getting zenodo accepted licenses")
    json = response.json()

    licences = {}
    for info in json["hits"]["hits"]:
        id = info["id"].lower()
        title = info["metadata"]["title"]
        licences[id] = title

    save_yaml(output_file_path, licences)
