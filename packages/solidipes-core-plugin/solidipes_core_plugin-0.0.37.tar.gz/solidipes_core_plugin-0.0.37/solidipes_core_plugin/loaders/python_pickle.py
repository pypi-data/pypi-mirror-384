from solidipes.loaders.file import File


class PythonPickle(File):
    """Python Pickle file"""

    supported_mime_types = {"python/pickle": ["pkl"]}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from ..viewers.python_pickle import PythonPickle as PythonPickleViewer

        self.preferred_viewer = PythonPickleViewer

    @File.loadable
    def obj(self):
        f = open(self.file_info.path, "rb")
        import pickle

        return pickle.load(f)
