import base64

from solidipes.loaders.file import File


class PDF(File):
    """Image loaded as base64"""

    from ..viewers.pdf import PDF as PDFViewer

    supported_mime_types = {"application/pdf": "pdf"}
    _compatible_viewers = [PDFViewer]

    @File.loadable
    def pdf(self):
        with open(self.file_info.path, "rb") as f:
            try:
                base64_pdf = base64.b64encode(f.read()).decode("utf-8")
                return base64_pdf
            except Exception:
                raise RuntimeError(f"could not load file {self.file_info.path}")
