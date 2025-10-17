import os
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import streamlit as st
else:
    import lazy_loader as lazy

    st = lazy.load("streamlit")

from solidipes.utils import logging

logger = logging.getLogger()


class StateWrapper:
    def __init__(self, f):
        self.key = "solidipes_state_GUI_" + f.unique_identifier
        self.f = f
        if "GUI_files" not in st.session_state:
            st.session_state["GUI_files"] = {}
        if self.key not in st.session_state["GUI_files"]:
            st.session_state["GUI_files"][self.key] = {}

    def __getattribute__(self, name):
        if name in ["key", "f"]:
            return super().__getattribute__(name)

        try:
            if name not in st.session_state["GUI_files"][self.key]:
                st.session_state["GUI_files"][self.key][name] = None
            return st.session_state["GUI_files"][self.key][name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        if name in ["key", "f"]:
            super().__setattr__(name, value)
            return

        try:
            if self.key not in st.session_state["GUI_files"]:
                st.session_state["GUI_files"][self.key] = {}
            st.session_state["GUI_files"][self.key][name] = value
        except KeyError:
            pass


################################################################


class FileWrapper:
    def __init__(self, f):
        self.state = StateWrapper(f)
        self.f = f

    def __getattr__(self, name):
        if name in ["state", "f"]:
            return super().__getattr__(name)

        return getattr(self.f, name)


################################################################


def transform_to_subtree(h, subtree=""):
    tree = []
    for name, f in h.items():
        if isinstance(f, dict):
            current_dir = os.path.join(subtree, name)
            s = transform_to_subtree(f, current_dir)
            if s:
                tree.append({"label": name, "value": current_dir, "children": s})
            else:
                tree.append({"label": name, "value": current_dir})
    return tree


################################################################


def redirect(url, wait_time=5):
    wbox = st.empty()
    while wait_time > 0:
        wbox.write(f"### You will be redirected in {wait_time} seconds")
        sleep(1)
        wait_time -= 1

    st.markdown(
        f"""
<meta http-equiv="refresh" content="0; url={url}">
 """,
        unsafe_allow_html=True,
    )
