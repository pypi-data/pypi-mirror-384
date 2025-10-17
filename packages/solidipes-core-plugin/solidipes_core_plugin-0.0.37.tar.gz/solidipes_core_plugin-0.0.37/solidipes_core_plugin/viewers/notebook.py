import streamlit as st
from IPython.display import Markdown, display
from solidipes.loaders.data_container import DataContainer
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class Notebook(Viewer):
    """Viewer for notebooks"""

    def __init__(self, data=None):
        #: Text to display
        self.notebook = None
        super().__init__(data)

    def add(self, data_container):
        """Append text to the viewer"""
        self.check_data_compatibility(data_container)

        if isinstance(data_container, DataContainer):
            self.notebook = data_container.notebook

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            from nbconvert import PythonExporter

            python_exporter = PythonExporter()
            script, resources = python_exporter.from_notebook_node(self.notebook)
            display(Markdown(script))

        elif viewer_backends.current_backend == "streamlit":
            from nbconvert import HTMLExporter

            html_exporter = HTMLExporter(template_name="classic")
            (body, resources) = html_exporter.from_notebook_node(self.notebook)
            st.components.v1.html(body, height=1000, scrolling=True)
            # st.markdown(resources, unsafe_allow_html=True)
        else:  # python
            from nbconvert import PythonExporter

            python_exporter = PythonExporter()
            script, resources = python_exporter.from_notebook_node(self.notebook)
            print(script)
