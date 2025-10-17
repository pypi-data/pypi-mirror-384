import base64
import os
from typing import TYPE_CHECKING, Literal, Optional
from uuid import uuid4

if TYPE_CHECKING:
    import streamlit as st
else:
    import lazy_loader as lazy

    st = lazy.load("streamlit")

from solidipes.utils import logging
from solidipes.utils.git_infos import GitInfos

from .solidipes_widget import SolidipesWidget as SPW

print = logging.invalidPrint
logger = logging.getLogger()

################################################################
jupyter_icon_filename = os.path.join(os.path.dirname(__file__), "../jupyter_logo.png")
_jupyter_icon = base64.b64encode(open(jupyter_icon_filename, "rb").read()).decode("utf-8")
_git_infos = GitInfos()
################################################################


class SolidipesButtons(SPW):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.git_infos = _git_infos

    def _link_button(self, label, url, action=None, **kwargs):
        """Create a Streamlit link button that opens in the same tab"""

        def wrap_action(action):
            def foo(url):
                action()
                self._open_link_same_tab(url)

            return foo

        if action is None:
            action = self._open_link_same_tab
        else:
            action = wrap_action(action)
        return self.layout.button(
            label,
            on_click=action,
            args=(url,),
            **kwargs,
        )

    def _html_link_button(
        self,
        label: str,
        url: str,
        type: Literal["primary", "secondary"] = "secondary",
        disabled: bool = False,
        use_container_width: bool = False,
        custom_style: Optional[dict] = None,
        new_tab: bool = False,
    ):
        """Return an HTML string link button, usable in Streamlit html component."""

        class_name = "_" + uuid4().hex
        background_color = "transparent"
        primary_color = "#ff4b4b"
        dark_primary_color = "#ff3333"
        secondary_text_color = "light-dark(#33313f, rgb(250, 250, 250))"
        disabled_color = "light-dark(rgba(49, 51, 63, 0.4), rgba(250, 250, 250, 0.4))"
        secondary_border_color = "light-dark(rgba(49, 51, 63, 0.2), rgba(250, 250, 250, 0.2))"

        if disabled:
            button_color = background_color
            button_hover_color = button_color
            button_click_color = button_color
            text_color = disabled_color
            text_hover_color = text_color
            text_click_color = text_color
            border_color = secondary_border_color
            border_hover_color = border_color
            border_click_color = border_color
        elif type == "primary":
            button_color = primary_color
            button_hover_color = dark_primary_color
            button_click_color = background_color
            text_color = "white"
            text_hover_color = "white"
            text_click_color = primary_color
            border_color = button_color
            border_hover_color = button_hover_color
            border_click_color = text_click_color
        else:  # type == "secondary"
            button_color = background_color
            button_hover_color = background_color
            button_click_color = primary_color
            text_color = secondary_text_color
            text_hover_color = primary_color
            text_click_color = "white"
            border_color = secondary_border_color
            border_hover_color = primary_color
            border_click_color = primary_color

        style = {
            "background-color": button_color,
            "border": "1px solid",
            "border-color": border_color,
            "border-radius": "0.5rem",
            "color": f"{text_color} !important",
            "display": "inline-block",
            "height": "min-content",
            "padding": "0.35rem 0.75rem",
            "text-align": "center",
            "text-decoration": "none",
        }
        if use_container_width:
            style["width"] = "100%"
        style.update(custom_style or {})
        style_str = "".join([f"{k}:{v};" for k, v in style.items()])

        return f"""<style>
    .{class_name} {{
        {style_str}
    }}
    .{class_name}:hover {{
        background-color: {button_hover_color};
        border-color: {border_hover_color};
        color: {text_hover_color} !important;
        text-decoration: none;
    }}
    .{class_name}:active {{
        background-color: {button_click_color};
        border-color: {border_click_color};
        color: {text_click_color} !important;
        text-decoration: none;
    }}
    .{class_name}[disabled] {{
        cursor: not-allowed;
    }}
    .{class_name} p {{
        margin: 0;
    }}
</style>
<a
    {f'href="{url}"' if not disabled else ""}
    target="{"_blank" if new_tab else "_self"}"
    class="{class_name}"
    {"disabled" if disabled else ""}
>
    <p>{label}</p>
</a>"""

    def _force_rescan_button(self):
        return self.layout.button("Force new file scan", use_container_width=True)

    def _force_reset_cache(self):
        return self.layout.button("Cache reset", use_container_width=True, type="primary")

    def _open_in_gitlab_button(self, origin):
        if origin is not None:
            self._link_button("View/Edit in Gitlab repository", origin, use_container_width=True)
        else:
            pass
            # self.layout.error("Gitlab origin not accessible")

    def _open_in_jupyterlab_button(self):
        with self.layout:
            self._write_jupyter_link()

    def _open_in_filebrowser_button(self):
        with self.layout:
            self._write_filebrowser_link()

    def _open_link_same_tab(self, url):
        from streamlit.components.v1 import html

        open_script = """
            <script type="text/javascript">
                window.parent.open('%s', '_self');
            </script>
        """ % (url)
        html(open_script)

    def _write_jupyter_link(self):
        try:
            _link = self._get_jupyter_link()
            self._link_button("View/Edit in Jupyterlab", _link, use_container_width=True)
        except Exception:  # as err:
            # st.error("Jupyter not accessible: " + str(err))
            pass

    def _iframe_filebrowser(self, dirname):
        dirname = os.path.abspath(dirname)
        try:
            _link = self._get_filebrowser_link()
            st.markdown(
                f"""
<iframe width="100%" height="800px" src="{_link}" title="Acquisition File Browser" style="flex-grow: 1; border: none;
margin: 0; padding: 0;"></iframe>
""",
                unsafe_allow_html=True,
            )
        except RuntimeError as e:
            st.markdown(
                '<center><p style="font-size: 6em; font-weight: normal;">⚠ </p><p style="font-size: 1.5em;'
                ' font-weight: bold;">You are using the web report on your local machine. The acquisition step should'
                " be done locally.</p><br><p>The report was launched from the following directory: <em><a"
                f' href="file://{dirname}">{dirname}</a></em><br>Please edit your files in that directory via your'
                " computer’s file browser.</p></center>",
                unsafe_allow_html=True,
            )
            with st.expander("detail"):
                st.warning(str(e))

    def _write_filebrowser_link(self):
        try:
            _link = self._get_filebrowser_link()
            self._link_button("View/Edit with file browser", _link, use_container_width=True)
        except Exception:  # as err:
            # st.error("Filebrowser not accessible: " + str(err))
            pass

    def _get_jupyter_link(self):
        try:
            session = os.environ["RENKU_BASE_URL"]
            dir_path = os.getcwd()
            rel_path = os.path.relpath(dir_path, self.git_infos.root)
            if rel_path == ".":
                _link = f"{session}/lab/"
            else:
                _link = f"{session}/lab/tree/{rel_path}"
            return _link
        except Exception as e:
            logger.error(e)
            raise RuntimeError("Not in a renku session")

    def _get_filebrowser_link(self):
        try:
            session = os.environ["RENKU_BASE_URL"]
            dir_path = os.getcwd()
            rel_path = os.path.relpath(dir_path, self.git_infos.root)
            _link = f"{session}/filebrowser/files/{rel_path}"
            return _link
        except Exception:
            raise RuntimeError("Not in a renku session")

    def _jupyter_link(self, uri, size):
        _img = f'<a href="{uri}"><img height="{size}" src="data:image/png;base64,{_jupyter_icon}"></a>'
        return _img


################################################################
#     def get_file_title(self, e):
#         path = e.file_info.path
#         if isinstance(e.f, FileSequence):
#             path = e.f.path
#
#         file_title = f"{path}"
#
#         if isinstance(e.f, FileSequence):
#             file_size = e.total_size
#         else:
#             file_size = e.file_info.size
#
#         file_title += f"&nbsp; &nbsp; **{e.file_info.type.strip()}/{DataSize(file_size):.2a}** "
#         title = file_title
#
#         if e.state.valid and (not e.discussions or e.archived_discussions):
#             title = ":white_check_mark: &nbsp; &nbsp;" + file_title
#         else:
#             title = ":no_entry_sign: &nbsp; &nbsp; " + file_title
#
#         # if e.discussions or e.state.view:
#         #    title += "&nbsp; :arrow_forward: &nbsp; &nbsp; "
#
#         if e.state.view:
#             title += "&nbsp; :open_book:"
#
#         if e.discussions:
#             title += "&nbsp;:e-mail: &nbsp; :arrow_forward: **You have a message**"
#
#         return title
#
#     def get_file_edit_link(self, e):
#         _path = e.file_info.path
#         while os.path.islink(_path):
#             dirname = os.path.dirname(_path)
#             _path = os.path.join(dirname, os.readlink(_path))
#
#         url = self.git_infos.origin + "/-/edit/master/data/" + _path
#         return url
#
#     def show_discussions(self, e):
#         from solidipes.reports.widgets.custom_widgets import SpeechBubble
#
#         if not e.discussions:
#             return
#         if not e.archived_discussions:
#             st.markdown("### :speech_balloon: Discussions")
#             for author, message in e.discussions:
#                 SpeechBubble(author, message)
#             st.markdown("<br>", unsafe_allow_html=True)
#
#             st.button(
#                 "Respond",
#                 on_click=lambda: setattr(e.state, "adding_comment", True),
#                 key=f"respond_button_{e.unique_identifier}",
#             )
#             st.markdown("---")
#
#         if self.show_advanced:
#             if e.discussions:
#                 st.markdown("---")
#                 if not e.archived_discussions:
#                     st.button("Archive messages", on_click=e.archive_discussions())
#                 else:
#                     st.button("Unarchive messages", on_click=e.archive_discussions(False))
#
#                 st.markdown("---")
