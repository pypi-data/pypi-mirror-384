import streamlit as st
from IPython.display import Markdown as MarkdownIPython
from IPython.display import display
from solidipes.loaders.data_container import DataContainer
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer


class Text(Viewer):
    """Viewer for formatted text"""

    def __init__(self, data=None):
        self.compatible_data_types = [str]
        #: Text to display
        self.text = ""
        self.max_length = 5000
        self.max_lines = 20
        super().__init__(data)

    def add(self, data_container):
        """Append text to the viewer"""
        self.check_data_compatibility(data_container)

        if isinstance(data_container, DataContainer):
            self.text += data_container.text

        elif isinstance(data_container, str):
            self.text += data_container

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            display(MarkdownIPython(self.text))

        elif viewer_backends.current_backend == "streamlit":
            text_layout = st.container()
            button_layout = st.empty()

            if button_layout.button("**more content....**"):
                self.max_length = 1000000
                self.max_lines = 1000000
                button_layout.empty()

            with text_layout:
                lines = self.text[: self.max_length].split("\n")
                if len(self.text) > self.max_length or len(lines) > self.max_lines:
                    text = self.text[: self.max_length]
                    lines = text.split("\n")[: self.max_lines]
                    text = "\n".join(lines)
                    st.text(text)
                else:
                    st.text(self.text)
        else:  # python
            print(self.text)


class Markdown(Text):
    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            display(MarkdownIPython(self.text))

        elif viewer_backends.current_backend == "streamlit":
            st.markdown(self.text)

        else:  # pure python
            print(self.text)
