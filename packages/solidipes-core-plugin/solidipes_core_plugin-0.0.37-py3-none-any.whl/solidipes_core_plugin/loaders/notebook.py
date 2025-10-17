import nbformat
from solidipes.loaders.file import File


class Notebook(File):
    """Notebook file, in Jupyter style"""

    from ..viewers.notebook import Notebook as NotebookViewer

    supported_mime_types = {"application/jupyter-notebook": "ipynb", "application/json": "ipynb"}
    _compatible_viewers = [NotebookViewer]

    @File.loadable
    def notebook(self):
        return nbformat.read(self.file_info.path, as_version=4)
