from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class PythonPickle(Viewer):
    """Viewer for Python pickled objects"""

    def __init__(self, data=None):
        from ..loaders.python_pickle import PythonPickle

        self.compatible_data_types = [PythonPickle]
        #: Image to display
        self.datasets = None
        super().__init__(data)

    def add(self, data_container):
        """Replace the viewer's hdf5"""
        self.check_data_compatibility(data_container)
        self.obj = data_container.obj

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            from IPython.display import display

            display(type(self.obj))
            display(self.obj)

        elif viewer_backends.current_backend == "streamlit":
            import streamlit as st

            st.markdown(f"## *Contained Object:* {type(self.obj).__name__}")
            st.write(self.obj)
        else:  # python
            print(type(self.obj))
            print(self.obj)
