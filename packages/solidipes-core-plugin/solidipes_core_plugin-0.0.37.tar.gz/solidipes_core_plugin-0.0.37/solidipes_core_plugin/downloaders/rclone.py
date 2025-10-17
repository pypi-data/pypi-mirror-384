# import os

from solidipes.downloaders.downloader import Downloader
from solidipes.utils import solidipes_logging as logging

from solidipes_core_plugin.utils.rclone_utils import RcloneUtils, declare_subclasses

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class RcloneDownloader(Downloader, RcloneUtils):
    parser_key = "rclone"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "_remote"):
            if "://" not in self.url:
                self._remote = self.url
            else:
                raise RuntimeError("A remote name must be provided")

    def download(self):
        self.sync(self.remote + ":", self.destination, "--progress")


################################################################
subclasses = declare_subclasses(RcloneDownloader, "Downloader")
globals().update(subclasses)
