import h5py
from solidipes.loaders.file import File


class HDF5(File):
    """HDF5 loader"""

    from ..viewers.hdf5 import HDF5 as HDF5Viewer

    supported_mime_types = {"application/x-hdf5": ["hdf", "h5", "hdf5"], "application/x-hdf": ["h5", "hdf5"]}
    _compatible_viewers = [HDF5Viewer]

    @File.loadable
    def datasets(self):
        return h5py.File(self.file_info.path)
