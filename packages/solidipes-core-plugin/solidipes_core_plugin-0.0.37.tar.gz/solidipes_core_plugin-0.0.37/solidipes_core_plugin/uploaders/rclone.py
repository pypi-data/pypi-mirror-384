from solidipes.uploaders.uploader import Uploader
from solidipes.utils.utils import classproperty

from solidipes_core_plugin.utils.rclone_utils import RcloneUtils, declare_subclasses

# from solidipes.utils.utils import optional_parameter

################################################################


class RcloneUploader(Uploader, RcloneUtils):
    "Publish study using rclone"

    parser_key = "rclone"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "_remote"):
            if "://" not in self.url:
                self._remote = self.url
            else:
                raise RuntimeError("A remote name must be provided")

    def upload(self):
        print(self.directory, self.remote)
        self.sync(self.directory, self.remote + ":", "--progress")

    @classproperty
    def report_widget_class(self):
        return


################################################################
subclasses = declare_subclasses(RcloneUploader, "Uploader")
globals().update(subclasses)
