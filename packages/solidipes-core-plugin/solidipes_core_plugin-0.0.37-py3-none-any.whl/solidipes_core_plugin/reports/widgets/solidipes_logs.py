import streamlit as st

from .solidipes_widget import SolidipesWidget as SPW


class SolidipesLogs(SPW):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.layout.expander("Logs", expanded=True):
            from solidipes.utils import get_study_log_path

            col1, col2 = st.columns(2)
            log_filename = get_study_log_path()

            def refresh():
                st.rerun

            def clear_log():
                open(log_filename, "w").close()
                refresh()

            col1.button("Refresh", on_click=refresh)
            col2.button("Clear", on_click=clear_log)
            import streamlit_scrollable_textbox as stx

            with st.spinner("Loading logs"):
                stx.scrollableTextbox(
                    "\n".join(open(log_filename, encoding="utf-8").read().split("\n")[::-1]), height=300
                )
