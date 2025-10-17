import json

from solidipes.loaders.file import File


class JSON(File):
    from ..viewers.dictionary import DictViewer

    supported_mime_types = {"text/plain": ["json"], "application/json": ["json"]}
    _compatible_viewers = [DictViewer]

    @File.loadable
    def dict(self):
        _dict = {}
        with open(self.file_info.path) as json_data:
            _dict.update(json.loads(json_data.read()))
        return _dict
