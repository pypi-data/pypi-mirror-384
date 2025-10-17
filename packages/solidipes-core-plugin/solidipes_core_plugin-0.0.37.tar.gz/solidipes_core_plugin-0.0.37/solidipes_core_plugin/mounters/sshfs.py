import os

################################################################
from solidipes.mounters.cloud import Mounter, parameter
from solidipes.utils import solidipes_logging as logging

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class SSHFSMounter(Mounter):
    """Mount a remote file system through ssh (sshfs file system)."""

    parser_key = "ssh"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def mount(self, headless=False) -> None:
        # Create directory if it does not exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Mount SSH file system
        endpoint = self.mount_info["endpoint"]
        command = [
            "sshfs",
            endpoint,
            self.path,
        ]

        options = []
        if headless:
            options.append("password_stdin")
        if len(options) > 0:
            command += ["-o", ",".join(options)]

        # logger.error(command)

        self.run_and_check_return(command, headless=headless, fail_message="Mounting failed")

    @parameter
    def endpoint() -> str:
        """[user@]host[:path]."""
        pass
