import configparser
import os
from pathlib import Path

import pytest
from solidipes.utils.utils import ExecError

from solidipes_core_plugin.mounters.rclone import RcloneMounter


def reveal(obscured):
    import subprocess

    completed = subprocess.run(
        ["rclone", "reveal", obscured],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


@pytest.fixture
def rclone_config() -> dict:
    config = configparser.ConfigParser()
    fname = RcloneMounter.rclone_config_fname()
    config.read(fname)
    return dict(config.items("webdav-local"))


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skip mount tests in CI")
def test_mount_rclone(rclone_config, study_dir) -> None:
    import os

    print(study_dir)
    print(rclone_config)
    conf = rclone_config
    with pytest.raises(ExecError):
        RcloneMounter.run_and_check_return(f"solidipes mount rclone-webdav {conf['url']}".split(), cwd=study_dir)

    assert "cloud.yaml" not in os.listdir(study_dir / ".solidipes")
    print(os.listdir(study_dir / ".solidipes"))

    with pytest.raises(ExecError):
        RcloneMounter.run_and_check_return(
            f"solidipes mount rclone-webdav {conf['url']} --password {conf['pass']}".split(), cwd=study_dir
        )

    assert "cloud.yaml" not in os.listdir(study_dir / ".solidipes")
    print(os.listdir(study_dir / ".solidipes"))

    with pytest.raises(ExecError):
        RcloneMounter.run_and_check_return(
            f"solidipes mount rclone-webdav {conf['url']} --user {conf['user']}".split(), cwd=study_dir
        )

    assert "cloud.yaml" not in os.listdir(study_dir / ".solidipes")
    print(os.listdir(study_dir / ".solidipes"))

    with pytest.raises(ExecError):
        RcloneMounter.run_and_check_return(
            f"solidipes mount rclone-webdav {conf['url']} --user {conf['user']} --pass toto".split(), cwd=study_dir
        )

    assert "cloud.yaml" not in os.listdir(study_dir / ".solidipes")
    print(os.listdir(study_dir / ".solidipes"))

    out, err = RcloneMounter.run_and_check_return(
        f"solidipes mount rclone-webdav {conf['url']} --password {reveal(conf['pass'])} --user {conf['user']} data".split(),
        cwd=study_dir,
    )
    print(out, err)

    assert os.path.ismount(study_dir / "data")
    assert os.path.exists(study_dir / ".solidipes" / "cloud.yaml")
    assert not os.path.exists(study_dir / "data" / "cloud.yaml")
    assert os.path.exists(study_dir / "data" / "data" / "image_with_exif.jpg")

    out, err = RcloneMounter.run_and_check_return(
        "solidipes unmount".split(),
        cwd=study_dir,
    )

    print(out, err)

    assert not os.path.ismount(study_dir / "data")
    assert os.path.exists(study_dir / ".solidipes" / "cloud.yaml")
    assert os.path.exists(study_dir / "data" / "cloud_info.yaml")
    assert not os.path.exists(study_dir / "data" / "data" / "image_with_exif.jpg")

    cloud_yaml = open(study_dir / "data" / "cloud_info.yaml").read()
    import yaml

    cloud_yaml = yaml.safe_load(cloud_yaml)
    print(cloud_yaml)
    mount_id = cloud_yaml["mount_id"]

    out, err = RcloneMounter.run_and_check_return(
        f"solidipes mount rclone --remote {mount_id} data".split(),
        cwd=study_dir,
    )
    print(out, err)

    assert os.path.ismount(study_dir / "data")
    assert os.path.exists(study_dir / ".solidipes" / "cloud.yaml")
    assert not os.path.exists(study_dir / "data" / "cloud.yaml")
    assert os.path.exists(study_dir / "data" / "data" / "image_with_exif.jpg")

    out, err = RcloneMounter.run_and_check_return(
        "solidipes unmount data".split(),
        cwd=study_dir,
    )

    assert not os.path.ismount(study_dir / "data")
    assert os.path.exists(study_dir / ".solidipes" / "cloud.yaml")
    assert os.path.exists(study_dir / "data" / "cloud_info.yaml")
    assert not os.path.exists(study_dir / "data" / "data" / "image_with_exif.jpg")

    out, err = RcloneMounter.run_and_check_return(
        "solidipes unmount -f data".split(),
        cwd=study_dir,
    )

    assert not os.path.exists(study_dir / "data" / "cloud_info.yaml")
    cloud_yaml = open(study_dir / ".solidipes" / "cloud.yaml").read()
    import yaml

    cloud_yaml = yaml.safe_load(cloud_yaml)
    assert "data" not in cloud_yaml

    config = configparser.ConfigParser()
    fname = RcloneMounter.rclone_config_fname()
    config.read(fname)
    assert mount_id not in config


def test_download_rclone(rclone_config, tmp_path) -> None:
    import os

    tmp_dir = tmp_path
    print(tmp_dir)
    print(rclone_config)
    conf = rclone_config

    out, err = RcloneMounter.run_and_check_return(
        f"solidipes download rclone-webdav --remote tmp-origin {conf['url']} --password {reveal(conf['pass'])} --user"
        f" {conf['user']} {tmp_dir}".split()
    )
    print(out, err)

    print(os.listdir(tmp_dir))
    print(os.listdir(tmp_dir / "data"))

    assert os.path.exists(tmp_dir / "data")
    assert os.path.exists(tmp_dir / ".solidipes")
    assert os.path.exists(tmp_dir / "data" / "image_with_exif.jpg")

    import random
    import string

    # Generate random filename
    name = "".join(random.choices(string.ascii_lowercase + string.digits, k=8)) + ".txt"
    path = os.path.join(tmp_path, name)

    # Write random content
    with open(path, "wb") as f:
        f.write(os.urandom(1024))  # 1 KB of random data

    print(path)

    out, err = RcloneMounter.run_and_check_return(
        "solidipes upload rclone --remote tmp-origin".split(),
        cwd=tmp_dir,
    )
    import time

    time.sleep(3)

    assert os.path.exists(tmp_dir / path)
    assert os.path.exists(Path("/tmp/webdav_root") / path)

    os.remove(Path("/tmp/webdav_root") / path)
