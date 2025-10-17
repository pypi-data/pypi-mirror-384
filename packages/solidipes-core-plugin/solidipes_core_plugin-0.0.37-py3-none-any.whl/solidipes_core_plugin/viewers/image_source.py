import streamlit as st
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer

from .code_snippet import Code
from .image import Image
from .pdf import PDF


class ImageSource(Viewer):
    """Viewer for images produced by sources"""

    def __init__(self, data=None):
        #: Image to display
        self.image = None
        self.source = None
        super().__init__(data)

    def add(self, data_container):
        """Replace the viewer's image"""
        self.check_data_compatibility(data_container)
        self.data_container = data_container

    def show(self):
        if viewer_backends.current_backend == "streamlit":
            gen_error = False
            from solidipes.utils import solidipes_logging as logging

            logger = logging.getLogger()

            try:
                if self.data_container.file_info.type == "application/x-latex/tikz":
                    self.data_container.pdf
                    PDF(self.data_container)
                else:
                    Image(self.data_container)
            except Exception as e:
                st.error("Error while generating the figure")
                logger.error(e)
                st.code(str(e))
                gen_error = True

            if not self.data_container.image:
                gen_error = True

            with st.expander("Source Code", expanded=gen_error):
                Code(self.data_container, display_lint=False)

        else:  # python
            Code(self.data_container)
            if hasattr(self.image, "pdf"):
                PDF(self.data_container)
            else:
                Image(self.data_container)
