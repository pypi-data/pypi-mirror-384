import os
import tempfile

from solidipes.mounters.cloud import Mounter, optional_parameter, parameter

################################################################


class S3Mounter(Mounter):
    """Mount an S3 bucket."""

    parser_key = "s3"
    credential_names = ["access_key_id", "secret_access_key"]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def mount(self):
        # Check that keys are available
        if "access_key_id" not in self.mount_info or "secret_access_key" not in self.mount_info:
            raise RuntimeError("Mounting failed: access_key_id and secret_access_key are not available.")

        # Create directory if it does not exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Create temporary passwd file
        passwd_path = self.write_temp_passwd_file()

        # Mount S3 bucket
        bucket_path = self.mount_info["bucket_name"]
        remote_dir_name = self.mount_info.get("remote_dir_name", self.mount_id)
        if remote_dir_name != ".":
            bucket_path += f":/{remote_dir_name.rstrip('/')}"

        cmd = [
            "s3fs",
            bucket_path,
            self.path,
            "-o",
            f"passwd_file={passwd_path}",
            "-o",
            f"url={self.mount_info['endpoint_url']}",
            "-o",
            "nonempty",
        ]

        self.run_and_check_return(cmd, fail_message="Mounting failed")
        # Remove temporary passwd file
        os.remove(passwd_path)

    def write_temp_passwd_file(self):
        access_key_id = (self.mount_info["access_key_id"],)
        secret_access_key = self.mount_info["secret_access_key"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".passwd", delete=False) as f:
            f.write(f"{access_key_id}:{secret_access_key}\n")
            file_path = f.name

        return file_path

    @parameter
    def endpoint_url() -> str:
        """URL of the S3 endpoint."""
        pass

    @optional_parameter
    def bucket_name() -> str:
        ("Name of the S3 bucket",)
        pass

    @optional_parameter
    def access_key_id() -> str:
        """Access key ID."""
        pass

    @optional_parameter
    def secret_access_key() -> str:
        """Secret access key."""
        pass

    @optional_parameter
    def remote_dir_name() -> str:
        """Name of the mounted directory in the bucket."""
        "If not specified, a random unique name is attributed."
        pass


################################################################
