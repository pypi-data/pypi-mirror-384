from abc import ABC  # , abstractmethod


class SolidipesWidget(ABC):
    def __init__(self, layout=None, progress_layout=None, **kwargs):
        self.layout = self.set_layout(layout)
        self.progress_layout = self.set_layout(progress_layout)

    def set_layout(self, layout):
        if layout is None:
            import streamlit as st

            return st
        return layout
