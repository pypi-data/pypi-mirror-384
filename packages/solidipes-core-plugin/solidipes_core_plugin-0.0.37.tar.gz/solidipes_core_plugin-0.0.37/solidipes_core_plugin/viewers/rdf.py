import streamlit as st
from IPython.display import display
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class RDF(Viewer):
    """Viewer for rdf text files"""

    def __init__(self, data=None):
        self.rdf = []
        super().__init__(data)

    def add(self, data_container):
        """Append text to the viewer"""
        self.check_data_compatibility(data_container)
        self.rdf.append(data_container.rdf)

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            display(self.rdf)

        elif viewer_backends.current_backend == "streamlit":
            with st.container():
                st.write(self.rdf)
        else:  # python
            import yaml

            print(yaml.dump(self.rdf))
