"""Widget to display validations on a DataContainer. Must be lazy-loaded to avoid loading Streamlit."""

import streamlit as st  # Cannot lazy import because of st.fragment decorator
from solidipes.utils import get_ignore, set_ignore
from solidipes.utils.config import ignore_filename

from solidipes_core_plugin.reports.widgets.solidipes_widget import SolidipesWidget

VALIDATION_RELOAD_SLEEP_TIME = 1.5


class IgnoreWidget(SolidipesWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.layout is st:
            self.layout = st.container()

        with self.layout:
            self.display()

    @st.fragment
    def display(self):
        with st.expander("Ignored files"):
            patterns = "\n".join(get_ignore())
            value = st.text_area(label=".solidipes/" + ignore_filename, value=patterns, height=500)
            if st.button("Save"):
                set_ignore(value.split("\n"))
                st.write("Saving")
                st.rerun()
