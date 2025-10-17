import os
import subprocess

import yaml
from dtoolcore import DataSet

dtool_endpoint = "s3://test-bucket/1a1f9fad-8589-413e-9602-5bbd66bfe675"


def check_dtool_credentials() -> None:
    fname = os.path.join(os.path.expanduser("~"), ".config", "dtool", "dtool.json")
    print("dtool_conf: ", fname)
    script_path = os.path.dirname(__file__)
    t_fname = os.path.join(script_path, "assets", "dtool.json")
    if not os.path.exists(fname):
        if "DTOOL_S3_SECRET_ACCESS_KEY" not in os.environ:
            raise RuntimeError("cannot run dtool tests without a test instance")
        if not os.path.exists(t_fname):
            raise RuntimeError(f"cannot find template dtool conf file {os.getcwd()} {t_fname}")
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        conf = open(t_fname).read().replace("AAAA", os.environ["DTOOL_S3_SECRET_ACCESS_KEY"])
        with open(fname, "w") as f:
            f.write(conf)
    if not os.path.exists(fname):
        raise RuntimeError(f"Could not create the conf file {fname}")
    else:
        os.system(f"cat {fname}")


def test_remote_instance_connection() -> None:
    check_dtool_credentials()
    dtool_dataset = DataSet.from_uri(dtool_endpoint)
    manifest = dtool_dataset.generate_manifest()
    print(manifest)


def test_dtool_remote_scan(study_dir) -> None:
    print(study_dir)
    check_dtool_credentials()
    cmd = ["solidipes", "report", "curation", "--remote", f"dtool:{dtool_endpoint}"]
    print(" ".join(cmd))
    ret = subprocess.run(cmd)
    assert ret.returncode == 0


def test_dtool_download(study_dir) -> None:
    check_dtool_credentials()
    ret = subprocess.run(
        ["solidipes", "download", "dtool", dtool_endpoint, "."],
        cwd="./",
    )
    assert ret.returncode == 0


def test_dtool_mount(study_dir) -> None:
    check_dtool_credentials()
    ret = subprocess.run(
        ["solidipes", "mount", "dtool", dtool_endpoint, "data-dtool"],
        cwd="./",
    )
    assert ret.returncode == 0

    cloud_info = yaml.safe_load(open("data-dtool/cloud_info.yaml", "r").read())
    assert cloud_info["endpoint"] == dtool_endpoint
    assert cloud_info["path"] == "data-dtool"
    assert cloud_info["type"] == "dtool"

    ret = subprocess.run(
        ["solidipes", "report", "curation"],
        capture_output=True,
        cwd="./",
    )

    assert ret.returncode == 0

    output = ret.stderr.decode()
    output = output.split("\n")
    valid = False
    for out in output:
        if "data-dtool/simple_text_file.txt" in out:
            valid = True
            if "OK" not in out:
                valid = False
            break

    print(out)
    assert valid
