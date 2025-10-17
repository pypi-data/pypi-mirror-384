from solidipes.loaders.data_container import TemporaryFile
from solidipes.utils import solidipes_logging as logging

from .code_snippet import CodeSnippet

logger = logging.getLogger()


class TIKZ(CodeSnippet):
    supported_mime_types = {"latex/tikz": "tikz", "text/x-tex": "tikz"}

    from ..viewers.image import Image
    from ..viewers.image_source import ImageSource as ImageSourceViewer
    from ..viewers.pdf import PDF as PDFViewer

    _compatible_viewers = [ImageSourceViewer, Image, PDFViewer]

    @CodeSnippet.cached_loadable
    def gen_image(self):
        import base64
        import subprocess

        tmp = TemporaryFile(delete=False)
        tmp.add_extensions(["pdf", "png"])
        fp = tmp.open("pdf", "wb")
        fp.write(base64.b64decode(self.pdf))
        fp.flush()
        p = subprocess.Popen(f"pdftoppm -png {tmp.fname('pdf')} > {tmp.fname('png')}", shell=True)
        p.wait()
        if p.returncode:
            error = p.stderr.read().decode()
            logger.debug(error)
            raise RuntimeError(error)

        logger.info(f"Building: {tmp}")
        return tmp

    @CodeSnippet.loadable
    def image(self):
        tmp = self.gen_image
        from PIL import Image as PILImage

        img = PILImage.open(tmp.fname("png"))
        return img

    @CodeSnippet.cached_loadable
    def gen_pdf(self):
        text = self.text
        if r"\begin{document}" not in text:
            header = r"""
            \documentclass[tikz,convert={outfile=\jobname.svg}]{standalone}
\usetikzlibrary{calc,patterns,snakes}
% \usetikzlibrary{...}% tikz package already loaded by 'tikz' option
            """

            import os

            source_path = os.path.dirname(self.file_info.path)
            source_path = os.path.abspath(source_path)
            header += r"\graphicspath{{" + source_path + "}}"

            if "gnuplot" in text:
                header += r"""
                \usepackage{gnuplot-lua-tikz}
                """
            header += r"""
            \begin{document}
            """

            text = header + text + r"\end{document}"

        tmp = TemporaryFile(delete=False)
        tmp.add_extensions(["tex", "pdf", "aux", "log", "rubbercache"])
        fp = tmp.open("tex", "wb")
        fp.write(text.encode())
        fp.flush()
        import subprocess

        p = subprocess.Popen(f"rubber -d {tmp.fname('tex')}", shell=True, cwd=tmp._dir, stderr=subprocess.PIPE)
        p.wait()
        if p.returncode:
            error = p.stderr.read().decode()
            logger.debug(error)
            raise RuntimeError(error)
        return tmp

    @CodeSnippet.loadable
    def pdf(self):
        tmp = self.gen_pdf
        from .pdf import PDF

        pdf = PDF(path=tmp.fname("pdf")).pdf
        return pdf
