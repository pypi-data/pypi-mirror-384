import json
import os
import re
import zipfile
from getpass import getpass

import requests
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper

from ..utils import solidipes_logging as logging
from .utils import DataRepositoryException, get_zenodo_infos, save_yaml, set_zenodo_infos

print = logging.invalidPrint
logger = logging.getLogger()


download_chunk_size = 1024


def get_host_and_id(identifier):
    """Extract Zenodo host and study ID from string identifier

    URL has one of the following forms:
    - https://zenodo.org/record/1234567#xxx
    - https://zenodo.org/deposit/1234567#xxx
    - https://sandbox.zenodo.org/record/1234567#xxx
    - https://sandbox.zenodo.org/deposit/1234567#xxx
    - https://doi.org/10.5281/zenodo.1234567

    DOI has the form 10.5281/zenodo.1234567

    Args:
        identifier (str): URL or DOI of the study to download

    Returns:
        (str, str): Zenodo host and study ID
            host: "zenodo.org" or "sandbox.zenodo.org"
    """

    schemes = [
        # must check "sandbox.zenodo" first, otherwise "zenodo" will match
        {
            "pattern": r"sandbox.zenodo.org/records/(\d+)",
            "host": "sandbox.zenodo.org",
        },
        {
            "pattern": r"sandbox.zenodo.org/deposit/(\d+)",
            "host": "sandbox.zenodo.org",
        },
        {
            "pattern": r"zenodo.org/records/(\d+)",
            "host": "zenodo.org",
        },
        {
            "pattern": r"zenodo.org/deposit/(\d+)",
            "host": "zenodo.org",
        },
        {
            "pattern": r"10.5072/zenodo.(\d+)",
            "host": "sandbox.zenodo.org",
        },
        {
            "pattern": r"10.5281/zenodo.(\d+)",
            "host": "zenodo.org",
        },
    ]

    for scheme in schemes:
        match = re.search(scheme["pattern"], identifier)
        if match:
            return scheme["host"], match.group(1)

    raise ValueError(f"Invalid identifier: {identifier}")


def check_response(response, expected_status_code, task_description):
    if response.status_code == expected_status_code:
        return

    error_message = f"Error {task_description}: {response.status_code}"
    data = response.json()

    if "message" in data:
        error_message += f" {data['message']}"

    if "errors" in data:
        for sub_data in data["errors"]:
            error_message += f"\n- {sub_data['field']}: {sub_data['messages']}"

    raise DataRepositoryException(error_message)


# Upload methods ##############################################################


def get_access_token():
    return getpass("Enter Zenodo access token: ")


def get_existing_deposition_infos(identifier, access_token, sandbox=False):
    host, study_id = get_host_and_id(identifier)

    if sandbox and "sandbox" not in host:
        raise ValueError(f'Error: {host} is not a sandbox host. Remove the "--sandbox" flag.')

    # Build URL
    deposition_url = f"https://{host}/api/deposit/depositions/{study_id}"
    params = {"access_token": access_token}

    # Get deposition infos
    response = requests.get(deposition_url, params=params)
    check_response(response, 200, "getting existing deposition infos")
    bucket_url = response.json()["links"]["bucket"]
    web_url = response.json()["links"]["html"]

    return deposition_url, bucket_url, web_url


def upload_deposition_metadata(deposition_url, metadata, access_token, **kwargs):
    # Update metadata
    url = f"{deposition_url}?access_token={access_token}"
    headers = {"Content-Type": "application/json"}
    response = requests.put(url, data=json.dumps({"metadata": metadata}), headers=headers)
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


def create_deposition(access_token, sandbox=False):
    host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
    deposition_url = f"https://{host}/api/deposit/depositions"

    # Create a new deposition
    url = f"{deposition_url}?access_token={access_token}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json={}, headers=headers)
    check_response(response, 201, "creating deposition")

    # Get deposition ID and bucket URL
    data = response.json()
    deposition_url = data["links"]["self"]
    bucket_url = data["links"]["bucket"]
    web_url = data["links"]["html"]

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


def upload_archive(bucket_url=None, archive_path=None, access_token=None, progressbar=None, **kwargs):
    size = os.path.getsize(archive_path)
    filename = os.path.basename(archive_path)

    url = f"{bucket_url}/{filename}"
    params = {"access_token": access_token}

    with open(archive_path, "rb") as f:
        if progressbar is not None:
            bar = progressbar(filename, size)

            f = CallbackIOWrapper(bar.update, f)

        response = requests.put(url, data=f, params=params)

        if progressbar:
            bar.close()

    check_response(response, 201, "uploading archive")


# Download methods ############################################################


def download_files(record, destination, progressbar=False):
    # Download files
    n_files = len(record["files"])
    key = ""
    path = ""

    for i in range(n_files):
        file = record["files"][i]
        url = file["links"]["self"]
        key = file["key"]
        path = os.path.join(destination, key)

        # Download file
        logger.info(f"({i + 1}/{n_files}) Downloading {key}...")
        try:
            download_file(url, key, path, progressbar)
        except ValueError as e:
            logger.error(e)
            continue

    # If only one file which is a zip, unzip it and remove the zip
    if n_files == 1 and key.endswith(".zip"):
        logger.info("Unzipping...")
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
