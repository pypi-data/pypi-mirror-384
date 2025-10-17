import os

from solidipes.mounters.cloud import Mounter, optional_parameter, parameter

################################################################


class UnixMount(Mounter):
    parser_key = None

    def __init__(self, mount_command_type, headless=False, **kwargs) -> None:
        super().__init__(**kwargs)
        # Create directory if it does not exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Mount using "mount" command
        endpoint = self.mount_info["endpoint"]
        command = [
            "sudo",
            "mount",
            "-t",
            mount_command_type,
            endpoint,
            self.path,
        ]

        if headless:
            command.insert(1, "-S")  # read password from stdin

        options = []
        if "username" in self.mount_info:
            options.append(f"username={self.mount_info['username']}")
        if "password" in self.mount_info:
            options.append(f"password={self.mount_info['password']}")
        elif headless:
            options.append("password=''")
        if "domain" in self.mount_info:
            options.append(f"domain={self.mount_info['domain']}")
        if len(options) > 0:
            command.extend(["-o", ",".join(options)])

        self.run_and_check_return(command, fail_message="Mounting failed")


################################################################
class NFSMounter(UnixMount):
    """NFS file system."""

    parser_key = "nfs"

    def __init__(self, **kwargs) -> None:
        super().__init__("nfs", **kwargs)

    @parameter
    def endpoint() -> str:
        """host:path."""
        pass


################################################################


class SMBMounter(UnixMount):
    """Samba (Windows share) file system."""

    parser_key = "smb"
    credential_names = ["password"]

    def mount(self, **kwargs) -> None:
        super().__init__("cifs", **kwargs)

    @parameter
    def endpoint() -> str:
        """//host/path."""
        pass

    @optional_parameter
    def username() -> str:
        """Samba Username."""
        return ""

    @optional_parameter
    def domain() -> str:
        """Samba Domain."""
        return ""
