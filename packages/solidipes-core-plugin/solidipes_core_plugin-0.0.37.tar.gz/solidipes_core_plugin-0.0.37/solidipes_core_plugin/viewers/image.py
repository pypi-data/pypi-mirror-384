import base64

import numpy as np
import streamlit as st
from IPython.display import display
from PIL import Image as PILImage
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class Image(Viewer):
    """Viewer for images"""

    def __init__(self, data=None):
        #: Image to display
        self.image = None
        super().__init__(data)

    def add(self, data_container):
        """Replace the viewer's image"""
        self.check_data_compatibility(data_container)
        self.image = data_container.image

    def svg_format(self, svg):
        b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
        st.write(html, unsafe_allow_html=True)

    def show(self):
        from ..loaders.image import SVGWrapper

        if not isinstance(self.image, list):
            images = [self.image]
        else:
            images = self.image

        if not images:
            if viewer_backends.current_backend == "jupyter notebook":
                display("No image to display")

            elif viewer_backends.current_backend == "streamlit":
                st.warning("**No image to display**")
            else:
                print("No image to display")

        for img in images:
            if viewer_backends.current_backend == "jupyter notebook":
                display(img)

            elif viewer_backends.current_backend == "streamlit":
                with st.container():
                    if isinstance(img, SVGWrapper):
                        self.svg_format(img.src)
                    else:
                        if img.mode == "I;16B":
                            a = np.array(img) * (1 / 255)
                            a = a.astype(np.int8)
                            img = PILImage.fromarray(a)
                        else:
                            img = img
                        st.image(img.convert("RGBA"))
            else:  # python
                img.show()
