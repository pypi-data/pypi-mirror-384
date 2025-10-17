#!/bin/env python
################################################################
import os
from abc import ABC, abstractmethod

import markdown
import streamlit as st
from streamlit_ace import st_ace
from streamlit_editable_list import editable_list
from streamlit_quill import st_quill

################################################################


class EditWidget(ABC):
    def __init__(self, caption="", key="", disable_view=False):
        self.layout = st.container()
        self.caption = caption
        self.disable_view = disable_view
        self.key = f"{self.__class__.__name__}_{key}"

    @property
    def edit_mode(self):
        if self.disable_view:
            return True
        state_key = f"edit_mode_{self.key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False
        return st.session_state[state_key]

    @edit_mode.setter
    def edit_mode(self, value):
        print("change edit mode")
        if self.disable_view:
            return

        state_key = f"edit_mode_{self.key}"
        st.session_state[state_key] = value

    @abstractmethod
    def edit(self):
        pass

    @abstractmethod
    def view(self, layout=None):
        pass

    def show(self):
        self.layout.button(
            f"{self.caption} :pencil:",
            key=f"edit_{self.key}",
            on_click=lambda: setattr(self, "edit_mode", not self.edit_mode),
        )
        if self.edit_mode:
            self.edit()
        else:
            self.view()


################################################################


class EditTextBox(EditWidget):
    def __init__(self, value, fmt="{0}", on_apply=None, single_line=False, **kwargs):
        super().__init__(**kwargs)
        self.fmt = fmt
        self.value = value
        self.on_apply = on_apply
        self.single_line = single_line
        self.show()

    def edit(self):
        _edit = st.empty()
        view, edit = _edit.columns(2)
        _view = view.empty()
        self.view(_view)
        with edit:
            inp = st.text_area
            if self.single_line:
                inp = st.text_input
            content = inp("", value=self.value, key=f"text_area_{self.key}")

            if content != self.value:
                self.value = content
                self.view(_view)
            if st.button("Apply", key=f"apply_{self.key}") and self.on_apply:
                try:
                    self.on_apply(self.value)
                    self.edit_mode = False
                    _edit.empty()
                    self.show()
                except Exception as err:
                    st.error(err)

    def view(self, layout=None):
        if layout is None:
            layout = self.layout
        if isinstance(self.fmt, str):
            formatted = self.fmt.format(self.value)
        if callable(self.fmt):
            formatted = self.fmt(self.value)

        layout.markdown(formatted, unsafe_allow_html=True)


################################################################


class EditRichTextBox(EditWidget):
    def __init__(self, value, fmt="{0}", on_apply=None, **kwargs):
        super().__init__(**kwargs)
        self.fmt = fmt
        self.value = value
        self.on_apply = on_apply
        self.show()

    def edit(self):
        _edit = st.empty()
        edit = _edit.container()
        with edit:
            content = st_quill(value=self.value, html=True, preserve_whitespace=False, key=f"rich_text_area_{self.key}")

            if content != self.value:
                self.value = content
                if self.on_apply:
                    self.on_apply(self.value)

    def view(self, layout=None):
        if layout is None:
            layout = self.layout
        layout.markdown(self.fmt.format(self.value), unsafe_allow_html=True)

    def show(self):
        self.edit()


################################################################


class EditList(EditWidget):
    def __init__(self, data, input_params=[], fmt="{0}", on_apply=None, **kwargs):
        super().__init__(**kwargs)
        self.fmt = fmt
        self.data = data
        self.input_params = input_params
        self.on_apply = on_apply
        self.component_key = f"component_{self.key}"
        self.show()

    def edit(self):
        self.data = editable_list(self.data, self.input_params, key=self.component_key)

        if self.on_apply:
            try:
                self.on_apply(self.data)
            except Exception as err:
                st.error(err)

    def view(self, layout=None):
        if layout is None:
            layout = self.layout
        if isinstance(self.fmt, str):
            formatted = self.fmt.format(self.data)
        if callable(self.fmt):
            formatted = self.fmt(self.data)

        layout.markdown(formatted, unsafe_allow_html=True)


################################################################


@st.cache_data
def _format(fmt, value):
    return fmt.format(value)


class EditProgBox(EditWidget):
    def __init__(self, value, fmt="{0}", language="text", on_apply=None, single_line=False, **kwargs):
        super().__init__(**kwargs)
        self.fmt = fmt
        self.value = value
        self.language = language
        self.on_apply = on_apply
        self.single_line = single_line
        self.show()

    def edit(self):
        _edit = st.empty()
        edit = _edit.container()
        with edit:
            content = st_ace(
                value=self.value,
                language=self.language,
                theme="textmate",
                show_gutter=False,
                key=f"prog_area_{self.key}",
            )

            if content != self.value:
                self.value = content
                self.edit_mode = False
                if self.on_apply:
                    self.on_apply(self.value)
                self.value = content
                _edit.empty()
                st.rerun()
            ex = st.button(
                "Exit",
                key=f"exit_button_{self.key}",
            )
            if ex:
                self.edit_mode = False
                _edit.empty()

    def view(self, layout=None):
        if layout is None:
            layout = self.layout
        if isinstance(self.fmt, str):
            formatted = _format(self.fmt, self.value)
        if callable(self.fmt):
            formatted = self.fmt(self.value)

        if self.language == "markdown":
            formatted = markdown.markdown(
                formatted,
                extensions=["tables"],
                tab_length=2,
            )
            st.write(formatted, unsafe_allow_html=True)
            # st_quill(
            #     value=formatted,
            #     toolbar=[],
            #     readonly=True,
            #     html=True,
            #     preserve_whitespace=False,
            #     key=f"rich_text_area_read_only_{self.key}",
            # )
        else:
            layout.text(formatted)


################################################################


class SpeechBubble:
    def __init__(self, author, value):
        self.value = value
        self.author = author
        self.show()

    def show(self):
        st.markdown(f"<style> {css} </style>", unsafe_allow_html=True)
        html = open(html_path, encoding="utf-8").read()
        html = html.replace("<blockquote>", f"<blockquote>{self.value}")
        html = html.replace('<p id="author">', f'<p id="author">{self.author}')
        st.markdown(html, unsafe_allow_html=True)


################################################################


css_path = os.path.join(os.path.dirname(__file__), "speech_bubble.css")
html_path = os.path.join(os.path.dirname(__file__), "speech_bubble.html")
css = open(css_path, encoding="utf-8").read()
