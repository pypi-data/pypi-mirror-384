import os

import streamlit as st
from IPython.display import display
from solidipes.viewers import backends as viewer_backends

from .text import Text


def guess_language(path):
    ext = os.path.splitext(path)[1]
    if ext == ".py":
        return "python"
    if ext in [".c", ".cc", ".cpp", ".cxx", ".h", ".hpp"]:
        return "cpp"
    if ext == ".m":
        return "matlab"
    return "python"


class Code(Text):
    def __init__(self, data=None, display_lint=True):
        self.display_lint = display_lint
        if data is not None:
            self.path = data.file_info.path
        super().__init__(data)

    def add(self, data_container):
        """Append code to the viewer"""

        super().add(data_container)
        self.lint = data_container.lint

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            display(self.text)
            print("pylint")
            for m in self.lint:
                print(m)

        elif viewer_backends.current_backend == "streamlit":
            if len(self.text) > 50000:
                self.text = self.text[:50000] + "\n... more truncated content ..."
            st.code(self.text, language=guess_language(self.path), line_numbers=True)
            if not self.display_lint:
                return
            with st.expander("Linting feedback"):
                errors = [m[1] for m in self.lint if m[0][0] in ["E", "F"]]
                warnings = [m[1] for m in self.lint if m[0][0] not in ["E", "F"]]
                if errors:
                    st.markdown("### Errors")
                    for m in errors:
                        st.text(m)
                if warnings:
                    st.markdown("### Warnings")
                    for m in warnings:
                        st.text(m)

        else:  # pure python
            print(self.text)
            print("pylint")
            for m in self.lint:
                print(m)
