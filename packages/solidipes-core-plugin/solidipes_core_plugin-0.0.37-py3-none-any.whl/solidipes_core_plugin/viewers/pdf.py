import streamlit as st
from IPython.display import display
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class PDF(Viewer):
    """Viewer for pdfs"""

    def __init__(self, data=None, height=1000):
        #: Image to display
        self.pdf = None
        self.height = height
        super().__init__(data)

    def add(self, data_container):
        """Replace the viewer's image"""
        self.check_data_compatibility(data_container)
        self.pdf = data_container.pdf

    def show(self):
        if self.height is None:
            pdf_display = (
                f'<iframe src="data:application/pdf;base64,{self.pdf}" width="100%" type="application/pdf"></iframe>'
            )
        else:
            pdf_display = (
                f'<iframe src="data:application/pdf;base64,{self.pdf}" width="100%" height="{self.height}"'
                ' type="application/pdf"></iframe>'
            )

        if viewer_backends.current_backend == "jupyter notebook":
            from IPython.core.display import HTML

            display(HTML(pdf_display))

        elif viewer_backends.current_backend == "streamlit":
            st.markdown(pdf_display, unsafe_allow_html=True)

        else:  # python
            import subprocess
            import tempfile

            with tempfile.TemporaryFile() as tmp:
                tmp.write(self.pdf.decode())
                tmp.flush()
                subprocess.call("open {tmp.name}", shell=True)
