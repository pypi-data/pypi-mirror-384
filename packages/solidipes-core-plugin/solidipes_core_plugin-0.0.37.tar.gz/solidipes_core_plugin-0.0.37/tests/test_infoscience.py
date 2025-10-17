"""Tests for DSpace7, using the Infoscience sandbox"""

import os
import random
import re
import shutil
import uuid
from argparse import Namespace as Args

import pytest
from solidipes.scripts.download import main as download
from solidipes.scripts.upload import main as upload
from solidipes.utils import set_study_metadata

from solidipes_core_plugin.downloaders.dspace7 import process_metadata

host = "infoscience-sb.epfl.ch"
study_id = "a0c90826-53bb-4cb9-bde8-02aa6933fdc9"
collection_id = str(uuid.uuid4())
workspaceitem_id = random.randrange(1000)
test_file_name = "README.txt"
test_zip_name = "Dataset.zip"
test_zip_url = f"https://{host}/server/api/core/bitstreams/fake_uuid/content"


@pytest.fixture
def mock_dspace7_api(requests_mock, tmp_path):
    """Mock Infoscience/Dspace7 API."""

    # Record retrieval
    # record_url = f"https://{host}/entities/product/{study_id}"
    file_url = f"https://{host}/api/files/{study_id}/{test_file_name}"
    response = {
        "metadata": {"dc.title": [{"value": "mock dataset"}]},
        "_embedded": {
            "bundles": {
                "_embedded": {
                    "bundles": [
                        {
                            "name": "ORIGINAL",
                            "_embedded": {
                                "bitstreams": {
                                    "_embedded": {
                                        "bitstreams": [
                                            {"name": "test.zip", "_links": {"content": {"href": test_zip_url}}}
                                        ]
                                    }
                                }
                            },
                        }
                    ]
                }
            }
        },
        "files": [
            {
                "links": {
                    "self": file_url,
                },
                "key": test_file_name,
            },
        ],
    }

    requests_mock.get(
        f"https://{host}/server/api/core/items/{study_id}?embed=bundles/bitstreams", json=response, status_code=200
    )
    requests_mock.get(f"https://{host}/server/api/core/items/{study_id}", json=response, status_code=200)
    requests_mock.patch(f"https://{host}/server/api/core/items/{study_id}", status_code=200)

    # File download
    file_path = tmp_path / test_file_name
    file_path.write_text("test content")
    # zip tmp directory and set as response
    zip_path = tmp_path / test_zip_name
    path_without_extension = os.path.splitext(zip_path)[0]
    shutil.make_archive(path_without_extension, "zip", tmp_path)
    with open(zip_path, "rb") as f:
        requests_mock.get(test_zip_url, content=f.read(), status_code=200)

    # Deposition creation

    bucket_url = f"https://{host}/server/api/submission/workspaceitems/{workspaceitem_id}"
    deposition_url = f"https://{host}/server/api/submission/workspaceitems?owningCollection={collection_id}"

    # Absolutely minimal response for the purpose of this test. To be enriched as needed in the future.
    deposition_response = {
        "id": workspaceitem_id,
        "_embedded": {
            "item": {
                "id": study_id,
                "_links": {"self": {"href": bucket_url}},
            },
        },
    }

    deposition_creation_regex = re.compile(rf"https://{host}/server/api/submission/workspaceitems\?owningCollection=.*")
    print(re.match(deposition_creation_regex, deposition_url))
    requests_mock.post(deposition_creation_regex, json=deposition_response, status_code=201)

    # Metadata update and file upload
    deposition_regex = re.compile(rf"https://{host}/server/api/submission/workspaceitems/\d*")
    requests_mock.patch(deposition_regex, status_code=200)
    requests_mock.post(deposition_regex, status_code=201)


def test_download(mock_dspace7_api, tmp_path):
    dest_path = tmp_path / "downloaded"

    import argparse

    args = argparse.Namespace(
        platform="dspace7",
        url=f"https://{host}/entities/product/{study_id}",
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


def test_infoscience_upload(mock_dspace7_api, monkeypatch, tmp_path):
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

    monkeypatch.setattr("solidipes_core_plugin.uploaders.dspace7.get_access_token", lambda: "infoscience_token")

    # First upload
    args = Args()
    args.platform = "dspace7"
    args.host = host
    args.directory = str(study_path)
    args.sandbox = True
    args.new_deposition = True
    args.no_cleanup = False
    args.access_token = "FAKE_TOKEN"
    args.collection = collection_id
    args.tmp_dir = "/tmp"
    args.existing_identifier = False
    args.access_token = False

    upload(args)

    # TODO Second upload (delete and replace remote files)
    args.new_deposition = None
    # upload(args)
