from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class DictViewer(Viewer):
    def __init__(self, data=None):
        self.dict = {}
        super().__init__(data)

    def add(self, data_container):
        self.check_data_compatibility(data_container)
        self.dict.update(data_container.dict)

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            from IPython.display import display

            display(self.dict)

        elif viewer_backends.current_backend == "streamlit":
            import streamlit as st

            st.write(self.dict)
        else:  # python
            print(self.dict)
