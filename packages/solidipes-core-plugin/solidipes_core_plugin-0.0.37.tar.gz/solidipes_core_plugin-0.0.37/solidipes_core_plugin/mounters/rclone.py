################################################################
from solidipes.mounters.cloud import Mounter
from solidipes.utils import solidipes_logging as logging

from solidipes_core_plugin.utils.rclone_utils import RcloneUtils, declare_subclasses

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class RcloneMounter(Mounter, RcloneUtils):
    """Mount a remote file system through rclone."""

    parser_key = "rclone"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._remote = self.mount_id

    def umount(self, path, headless=False, **kwargs) -> None:
        """Unmount rclone remote; depends on the host OS"""
        import platform

        if platform.system() == "Windows":
            # QUESTION does this also apply?
            command = ["fusermount", "-u", path]

        elif platform.system() == "Darwin":
            command = ["umount", path]

        else:
            command = ["fusermount", "-u", path]

        self.run_and_check_return(command, fail_message="Unmounting failed")

        if "forget" in kwargs and kwargs["forget"] is True:
            self.forget_config(path)

    def save_config(self) -> None:
        self.check_connection()
        super().save_config()
        self.save_rclone_config()

    @classmethod
    def remove_config(cls, path, config) -> None:
        mount_id = config["mount_id"]
        cls.run_and_check_return(f"rclone config delete {mount_id}".split(), fail_message="remove config failed")
        for _cls in cls.mro()[1:]:
            if hasattr(_cls, "remove_config"):
                _cls.remove_config(path, config)


################################################################
subclasses = declare_subclasses(RcloneMounter, "Mounter")
globals().update(subclasses)
