from solidipes.loaders.file import File


class MatlabData(File):
    """Matlab .mat file"""

    from ..viewers.matlab import MatlabData as MatlabDataViewer

    supported_mime_types = {"application/x-matlab-data": "mat"}
    _compatible_viewers = [MatlabDataViewer]

    @File.loadable
    def arrays(self):
        import scipy.io

        mat = scipy.io.loadmat(self.file_info.path)
        return mat
