"""Tests for Dspace5, using the Research Collection (read-only)"""

import os

# import re
import shutil

import pytest
from solidipes.scripts.download import main as download

from solidipes_core_plugin.downloaders.dspace5 import process_metadata

host = "www.research-collection.ethz.ch"
study_id = "99999/777777"
item_id = "1346346134635-346236-6361"
test_file_name = "README.txt"
test_zip_name = "Dataset.zip"
test_zip_url = f"https://{host}/rest/api/{test_zip_name}"


@pytest.fixture
def mock_dspace5_api(requests_mock, tmp_path):
    """Mock Research Collection/Dspace5 API."""

    # Record retrieval
    # record_url = f"https://{host}/entities/product/{study_id}"
    # file_url = f"https://{host}/api/files/{study_id}/{test_file_name}"
    response_handle = {"id": item_id}

    requests_mock.get(f"https://{host}/rest/api/handle/{study_id}", json=response_handle, status_code=200)

    response_metadata = [
        {"key": "dc.title", "value": "mock title"},
    ]
    requests_mock.get(f"https://{host}/rest/api/items/{item_id}/metadata", json=response_metadata, status_code=200)

    response_bitstreams = [
        {"retrieveLink": test_zip_name, "name": test_zip_name, "bundleName": "ORIGINAL"},
        {"retrieveLink": "not_important.txt", "name": "random.txt", "bundleName": "whatever"},
    ]
    requests_mock.get(f"https://{host}/rest/api/items/{item_id}/bitstreams", json=response_bitstreams, status_code=200)

    # File download
    file_path = tmp_path / test_file_name
    file_path.write_text("test content")
    # zip tmp directory and set as response
    zip_path = tmp_path / test_zip_name
    path_without_extension = os.path.splitext(zip_path)[0]
    shutil.make_archive(path_without_extension, "zip", tmp_path)
    with open(zip_path, "rb") as f:
        requests_mock.get(test_zip_url, content=f.read(), status_code=200)

    # TODO adapt Zenodo workflow to Dspace5
    # # Deposition creation
    # bucked_id = str(uuid.uuid4())
    # bucket_url = f"https://{host}/api/files/{bucked_id}"
    # deposition_url = f"https://{host}/api/deposit/depositions/{study_id}"
    # deposition_response = {
    #     "id": study_id,
    #     "links": {
    #         "bucket": bucket_url,
    #         "html": f"https://{host}/deposit/{study_id}",
    #         "self": deposition_url,
    #     },
    # }
    # # regex: match optional query "?access_token=..."
    # deposition_creation_regex = re.compile(rf"https://{host}/api/deposit/depositions(?:\?.*)?")
    # requests_mock.post(deposition_creation_regex, json=deposition_response, status_code=201)

    # # Metadata update
    # deposition_regex = re.compile(rf"{deposition_url}(?:\?.*)?")
    # requests_mock.put(deposition_regex, status_code=200)

    # # Get existing deposition info
    # requests_mock.get(deposition_regex, json=deposition_response, status_code=200)

    # # Files listing and deletion
    # files_regex = re.compile(f"{deposition_url}/files.*")
    # response = [
    #     {
    #         "id": test_file_name,
    #         "filename": test_file_name,
    #     },
    # ]
    # requests_mock.get(files_regex, json=response, status_code=200)
    # requests_mock.delete(files_regex, status_code=204)

    # # File upload (match any remote file path)
    # file_upload_url = re.compile(f"{bucket_url}/.*")
    # requests_mock.put(file_upload_url, status_code=201)


def test_download(mock_dspace5_api, tmp_path):
    dest_path = tmp_path / "downloaded"

    import argparse

    args = argparse.Namespace(
        platform="dspace5",
        url=f"https://{host}/handle/{study_id}",
        destination=str(dest_path),
        only_metadata=False,
    )
    download(args)

    downloaded_file_path = dest_path / test_file_name
    assert downloaded_file_path.exists()


def test_process_downloaded_metadata():
    # Empty metadata
    metadata = {}
    processed_metadata = processed_metadata = process_metadata(metadata)
    assert processed_metadata["upload_type"] == "dataset"

    # Fields that must be modified
    journal_fields = ["title", "volume", "issue", "pages"]
    metadata = {"resource_type": {"type": "publication"}, "journal": {}}
    for field in journal_fields:
        metadata["journal"][field] = field

    processed_metadata = process_metadata(metadata)
    assert processed_metadata["upload_type"] == "publication"
    for field in journal_fields:
        assert processed_metadata[f"journal_{field}"] == field
