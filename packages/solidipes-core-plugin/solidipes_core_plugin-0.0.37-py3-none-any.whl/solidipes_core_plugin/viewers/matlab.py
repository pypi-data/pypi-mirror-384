import streamlit as st
from IPython.display import display
from solidipes.loaders.data_container import DataContainer
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class MatlabData(Viewer):
    """Viewer for Matlab Data .mat file"""

    def __init__(self, data=None):
        #: Text to display
        self.arrays = {}
        super().__init__(data)

    def add(self, data_container):
        """Append text to the viewer"""
        self.check_data_compatibility(data_container)

        if isinstance(data_container, DataContainer):
            self.arrays.update(data_container.arrays)

    def show(self):
        for k, v in self.arrays.items():
            if viewer_backends.current_backend == "jupyter notebook":
                display(f"{k} ({type(v).__name__})")
                display(v)

            elif viewer_backends.current_backend == "streamlit":
                with st.expander(f"{k} ({type(v).__name__})"):
                    st.write(v)
            else:  # python
                print(f"{k} ({type(v).__name__})")
                print(v)
