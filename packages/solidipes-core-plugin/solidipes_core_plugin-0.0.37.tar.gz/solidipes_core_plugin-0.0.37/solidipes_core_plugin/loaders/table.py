import pandas as pd
from solidipes.loaders.file import File
from solidipes.utils import solidipes_logging as logging
from solidipes.validators.validator import add_validation_error, validator

logger = logging.getLogger()


class Table(File):
    """Table file loaded with Pandas"""

    from ..viewers.table import Table as TableViewer

    supported_mime_types = {
        "text/csv": "csv",
        "text/ssv": "ssv",
        "text/plain": ["csv", "ssv"],
        "application/vnd.ms-excel": ["csv", "xlsx"],
        "application/numpy/array": "npy",
        "application/octet-stream": "npy",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    }

    _compatible_viewers = [TableViewer]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        path = kwargs["path"]

        # find loader matching file extension
        if self.file_info.type == "text/csv" or self.file_info.extension in ["csv"]:
            self.pandas_loader = self.read_csv
        elif self.file_info.type == "text/ssv" or self.file_info.extension in ["ssv"]:
            self.pandas_loader = self.read_ssv
        elif self.file_info.type == "text/plain":
            self.pandas_loader = pd.read_csv
        elif self.file_info.type == "application/vnd.ms-excel" or self.file_info.extension in ["xlsx"]:
            self.pandas_loader = pd.read_excel
        elif self.file_info.extension.startswith("application/numpy") or self.file_info.extension == "npy":
            self.pandas_loader = self.read_numpy
        else:
            raise RuntimeError(f"File type not supported: {path} {self.file_info.type} {self.file_info.extension}")

    def read_csv(self, fname, **kwargs):
        ret = pd.read_csv(fname, sep=r",", **kwargs)
        return ret

    def read_ssv(self, fname, **kwargs):
        ret = pd.read_csv(fname, sep=r"\s+", **kwargs)
        return ret

    def read_numpy(self, fname, **kwargs):
        import numpy

        f = numpy.load(fname)
        f = pd.DataFrame(f)
        return f

    @validator(description="Table has valid header")
    def _has_valid_header(self) -> bool:
        for h in self.header_list:
            try:
                h = float(h)
                add_validation_error([f"Incorrect header: {self.header_list}"])
                return False
            except Exception:
                pass
            if h.startswith("Unnamed"):
                add_validation_error([f"Incorrect header: {self.header_list}"])
                return False

        return True

    @File.loadable
    def header_list(self):
        data = self.pandas_loader(self.file_info.path, nrows=0)
        logger.debug(data)
        logger.debug(data.columns)
        header_list = list(data.columns)
        return header_list

    @File.loadable
    def header(self):
        return ", ".join(self.header_list)

    @File.loadable
    def table(self):
        return self.pandas_loader(self.file_info.path)
