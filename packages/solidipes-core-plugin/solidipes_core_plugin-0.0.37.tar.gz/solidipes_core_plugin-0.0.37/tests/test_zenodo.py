import os
import re
import shutil
import uuid

import pytest
from solidipes.scripts.download import main as download
from solidipes.scripts.upload import main as upload
from solidipes.utils import set_study_metadata

from solidipes_core_plugin.downloaders.zenodo import process_metadata

host = "sandbox.zenodo.org"
study_id = 123456
test_file_name = "test.txt"
test_zip_name = "test.zip"


@pytest.fixture
def mock_zenodo_api(requests_mock, tmp_path):
    """Mock Zenodo API."""

    # Record retrieval
    file_url = f"https://{host}/api/files/{study_id}/{test_file_name}"
    response = {
        "metadata": {},
        "files": [
            {
                "links": {
                    "self": file_url,
                },
                "key": test_file_name,
            },
        ],
    }
    requests_mock.get(f"https://{host}/api/records/{study_id}", json=response, status_code=200)

    # File download
    file_path = tmp_path / test_file_name
    file_path.write_text("test content")
    # zip tmp directory and set as response
    zip_path = tmp_path / test_zip_name
    path_without_extension = os.path.splitext(zip_path)[0]
    shutil.make_archive(path_without_extension, "zip", tmp_path)
    with open(zip_path, "rb") as f:
        requests_mock.get(file_url, content=f.read(), status_code=200)

    # Deposition creation
    bucked_id = str(uuid.uuid4())
    bucket_url = f"https://{host}/api/files/{bucked_id}"
    deposition_url = f"https://{host}/api/deposit/depositions/{study_id}"
    deposition_response = {
        "id": study_id,
        "links": {
            "bucket": bucket_url,
            "html": f"https://{host}/deposit/{study_id}",
            "self": deposition_url,
        },
    }
    # regex: match optional query "?access_token=..."
    deposition_creation_regex = re.compile(rf"https://{host}/api/deposit/depositions(?:\?.*)?")
    requests_mock.post(deposition_creation_regex, json=deposition_response, status_code=201)

    # Metadata update
    deposition_regex = re.compile(rf"{deposition_url}(?:\?.*)?")
    requests_mock.put(deposition_regex, status_code=200)

    # Get existing deposition info
    requests_mock.get(deposition_regex, json=deposition_response, status_code=200)

    # Files listing and deletion
    files_regex = re.compile(f"{deposition_url}/files.*")
    response = [
        {
            "id": test_file_name,
            "filename": test_file_name,
        },
    ]
    requests_mock.get(files_regex, json=response, status_code=200)
    requests_mock.delete(files_regex, status_code=204)

    # File upload (match any remote file path)
    file_upload_url = re.compile(f"{bucket_url}/.*")
    requests_mock.put(file_upload_url, status_code=201)


def test_download(mock_zenodo_api, tmp_path):
    dest_path = tmp_path / "downloaded"

    import argparse

    args = argparse.Namespace(
        platform="zenodo",
        url=f"https://{host}/records/{study_id}",
        destination=str(dest_path),
        only_metadata=False,
    )

    print(args)
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


def test_zenodo_upload(mock_zenodo_api, monkeypatch, tmp_path):
    study_path = tmp_path / "study"
    solidipes_path = study_path / ".solidipes"
    solidipes_path.mkdir(parents=True)
    os.chdir(study_path)

    metadata = {
        "title": "test",
        "upload_type": "dataset",
        "description": "description",
        "creators": [{"name": "Name"}],
        "keywords": ["keyword"],
        "language": "eng",
        "license": "cc-by-4.0",
    }
    set_study_metadata(metadata, initial_path=study_path)

    from argparse import Namespace as Args

    monkeypatch.setattr("solidipes_core_plugin.uploaders.zenodo.get_access_token", lambda: "zenodo_token")

    # First upload
    args = Args()
    args.platform = "zenodo"
    args.directory = str(study_path)
    args.sandbox = True
    args.access_token = ""
    args.no_cleanup = False

    os.chdir(study_path)
    upload(args)

    # Second upload (delete and replace remote files)
    upload(args)
