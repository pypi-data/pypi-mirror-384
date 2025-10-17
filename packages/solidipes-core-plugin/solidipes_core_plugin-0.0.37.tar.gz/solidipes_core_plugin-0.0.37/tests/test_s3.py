import subprocess
from pathlib import Path

import pytest
from solidipes.mounters.cloud import get_cloud_info, set_cloud_info
from solidipes.scripts.mount import main as mount_command
from solidipes.scripts.unmount import main as unmount_command

from solidipes_core_plugin.mounters.s3 import S3Mounter

local_path = "data/s3"
remote_path = "test"
endpoint_url = "test_endpoint_url"
bucket_name = "test_bucket_name"
access_key_id = "test_access_key_id"
secret_access_key = "test_secret_access_key"


class SubprocessReturn:
    def __init__(self, fail=False) -> None:
        self.fail = fail
        self.stdout = "OK".encode()
        self.stderr = "error occurred".encode()
        if fail:
            self.stdout = "".encode()
        else:
            self.stderr = "".encode()

    def check_returncode(self) -> None:
        if self.fail:
            raise subprocess.CalledProcessError(1, "test")


def test_mount_s3fs(study_dir, monkeypatch) -> None:
    mount_info = {
        "type": "s3",
        "endpoint_url": endpoint_url,
        "bucket_name": bucket_name,
        "access_key_id": access_key_id,
        "secret_access_key": secret_access_key,
        "remote_dir_name": remote_path,
    }

    # Mount without info
    with pytest.raises(ValueError):
        S3Mounter()

    with pytest.raises(ValueError):
        m = S3Mounter(path=local_path)
        m.mount()

    # Mount with arg info
    # Successful mount
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: SubprocessReturn())
    m = S3Mounter(path=local_path, **mount_info)
    # Mount with config info
    m.store_keys_publicly = True
    m.save_config()
    # Successful mount
    S3Mounter(path=local_path)

    # Unsuccessful mount
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: SubprocessReturn(fail=True))
    with pytest.raises(RuntimeError):
        m = S3Mounter(path=local_path)
        m.mount()


def test_mount_command(study_dir, user_path, monkeypatch) -> None:
    class Args:
        def __init__(self, **kwargs) -> None:
            self.list_existing = False
            self.all = False
            self.force = None
            self.type = "s3"
            self.remote_dir_name = None
            self.convert = None
            self.public_keys = None
            self.access_key_id = "XXXX"
            self.secret_access_key = "XXXX"
            self.__dict__.update(kwargs)

    # Mount without info (print error)
    args = Args(path=local_path, allow_root=False)
    with pytest.raises(ValueError):
        mount_command(args)

    # Mount with arg info (juicefs)
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: SubprocessReturn())
    monkeypatch.setattr("solidipes.mounters.cloud.Mounter.wait_mount", lambda path: None)
    args = Args(
        path=local_path,
        type="s3",
        endpoint_url=endpoint_url,
        bucket_name=bucket_name,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        remote_dir_name=remote_path,
        allow_root=False,
    )
    mount_command(args)

    # Mount with saved info
    args = Args(
        path=local_path,
        allow_root=False,
    )
    mount_command(args)

    # Convert
    set_cloud_info({})  # Forget previous mount
    Path(local_path).mkdir(parents=True, exist_ok=True)
    Path(local_path, "test").touch()  # Create a file
    args = Args(
        local_path=local_path,
        type="s3",
        endpoint_url=endpoint_url,
        bucket_name=bucket_name,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        remote_dir_name=remote_path,
        convert=True,
        allow_root=False,
    )
    print("conversion of remote mount currently disabled")
    # mount_command(args)
    # assert not Path(local_path, "test").exists()  # File was deleted


def test_unmount_command(study_dir, monkeypatch) -> None:
    class Args:
        def __init__(self, **kwargs) -> None:
            self.forget = None
            self.local_path = None
            self.list_mounted = None
            self.all = True
            self.__dict__.update(kwargs)

    set_cloud_info({
        local_path: {
            "type": "s3",
            "endpoint_url": endpoint_url,
            "bucket_name": bucket_name,
            "access_key_id": access_key_id,
            "secret_access_key": secret_access_key,
        }
    })

    monkeypatch.setattr("os.path.ismount", lambda *args, **kwargs: True)

    # Fail
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: SubprocessReturn(fail=True))
    args = Args()
    unmount_command(args)

    # Successes
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: SubprocessReturn())

    # Unmount without info (all saved)
    args = Args()
    unmount_command(args)

    # Unmount with arg info
    args = Args(local_path=local_path)
    unmount_command(args)

    # Forget
    args = Args(forget=True)
    unmount_command(args)
    config = get_cloud_info()
    assert local_path not in config
