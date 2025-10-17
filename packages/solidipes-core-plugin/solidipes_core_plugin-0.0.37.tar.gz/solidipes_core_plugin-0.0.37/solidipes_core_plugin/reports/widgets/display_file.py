import os

import streamlit as st
from datasize import DataSize
from solidipes.loaders.file_sequence import FileSequence
from solidipes.loaders.group import loader_list as group_loader_list
from solidipes.loaders.mime_types import get_extension2mime_types, get_mime_type2extensions
from solidipes.loaders.sequence import Sequence
from solidipes.plugins.discovery import loader_list, viewer_list
from solidipes.utils import logging
from solidipes.utils.utils import get_mimes, set_mimes

################################################################
from streamlit.components.v1 import html

from solidipes_core_plugin.reports.widgets.utils import FileWrapper

from .solidipes_widget import SolidipesWidget as SPW
from .validation import ValidationWidget

# import urllib.parse


################################################################

print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class DisplayFile(SPW):
    def __init__(self, filename: str, loader_name: str, paths_str: str, options_layout=None, **kwargs):
        super().__init__(**kwargs)

        self.fname = filename
        self.f = FileWrapper(self._load(filename, loader_name, paths_str))
        self.f.state.valid = self.f.is_valid
        title = self.get_file_title(self.f)

        st.markdown("<br>", unsafe_allow_html=True)
        with self.layout:
            st.markdown(title)
            self.show_file()

    def _load(self, filename: str, loader_name: str, paths_str: str):
        from solidipes.loaders.file import load_file

        group_loader_dict = {loader.__name__: loader for loader in group_loader_list}

        if loader_name in group_loader_dict:
            # dir_path = os.path.dirname(filename)
            st.warning(filename)
            # encoded_paths = paths_str.split(",")
            # paths = [urllib.parse.unquote(p) for p in encoded_paths]
            # paths = [os.path.join(dir_path, p) for p in paths]
            loader = group_loader_dict[loader_name]
            return loader(pattern=filename)

        else:
            return load_file(filename)

    def _get_jupyter_link(self):
        try:
            session = os.environ["SESSION_URL"]
            dir_path = os.getcwd()
            rel_path = os.path.relpath(dir_path, self.git_infos.root)
            if rel_path == ".":
                _link = f"{session}/lab/"
            else:
                _link = f"{session}/lab/tree/{rel_path}"
            return _link
        except Exception:
            raise RuntimeError("Not in a renku session")

    def show_file(self):
        e = self.f

        self.show_validations(e)

        self.show_metadata_editor(e)

        st.sidebar.button(
            "&#8629; Back to file list",
            on_click=lambda: html("<script>window.parent.history.back();</script>"),
            use_container_width=True,
            type="primary",
        )

        col1, col2, col3, col4 = st.columns(4)

        self.show_discussions(e)

        if e.state.adding_comment:
            from streamlit_ace import st_ace

            content = st_ace(
                theme="textmate",
                show_gutter=False,
                key=f"chat_input_{e.unique_identifier}",
            )
            if content:
                import re

                m = re.match(r"(\w+):(.*)", content)
                if m:
                    e.add_message(m[1], m[2].strip())
                else:
                    e.add_message("Unknown", content)
                e.state.adding_comment = False
                st.rerun()

        is_pyvista_sequence = False
        try:
            from solidipes_solid_mech_plugin.loaders.pyvista_mesh import PyvistaMesh

            if getattr(e.f, "sequence_type", None) == PyvistaMesh:
                is_pyvista_sequence = True
        except ModuleNotFoundError:
            pass

        if (
            isinstance(e.f, Sequence)
            and not (isinstance(e.f, FileSequence) and is_pyvista_sequence)
            and e._element_count > 1
        ):
            sequence_switcher = st.container()
            with sequence_switcher:
                st.write(f"Sequence of {e._element_count} elements.")

                selected_element = st.slider(
                    "Current element",
                    min_value=1,
                    max_value=e._element_count,
                    step=1,
                    key="sequence_switcher_" + e.unique_identifier,
                )
                e.select_element(selected_element - 1)

        file_size = e.file_info.size

        try:
            col4.download_button(
                f"Download {os.path.basename(e.file_info.path)} ({DataSize(file_size):.2a})",
                data=open(e.file_info.path, "rb"),
                file_name=os.path.basename(e.file_info.path),
                key="download_" + e.unique_identifier,
            )
        except FileNotFoundError:
            pass

        try:
            _link = self._get_jupyter_link()
            _link += "/" + os.path.dirname(e.file_info.path)
            col2.markdown(
                f"[Edit in Jupyterlab]({_link}/)",
                unsafe_allow_html=True,
            )
            _link = self._get_filebrowser_link()
            _link += "/" + os.path.dirname(e.file_info.path)
            col2.markdown(
                f"[Edit in Filebrowser]({_link}/)",
                unsafe_allow_html=True,
            )
        except RuntimeError:
            pass

        col3.button(
            ":speech_balloon: add a comment",
            on_click=lambda: setattr(e.state, "adding_comment", True),
            key=f"add_comment_button_{e.unique_identifier}",
        )

        with st.expander("Loader selection", expanded=not e.f._has_valid_extension()):
            self.loader_selection(e)

        with st.expander(
            "Viewer selection",
            expanded=e.f.preferred_viewer_name not in [v.class_path for v in e.f.compatible_viewers],
        ):
            self.viewer_selection(e)

        try:
            with st.spinner(f"Loading {e.file_info.path}..."):
                e.view()
        except Exception as err:
            container_error = st.container()
            with container_error.expander(":warning: Error trying to display file"):
                st.exception(err)
                logger.error("Error trying to display file")
                logger.error(err)
            # raise err

    def show_validations(self, e):
        ValidationWidget(e.f)

    def show_discussions(self, e):
        from solidipes_core_plugin.reports.widgets.custom_widgets import SpeechBubble

        if not e.discussions:
            return

        title = "Discussions"
        if e.archived_discussions:
            title += " (archived)"

        with st.expander("Discussions", expanded=not e.archived_discussions):
            st.markdown("### :speech_balloon: Discussions")
            for author, message in e.discussions:
                SpeechBubble(author, message)
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(2)

            cols[0].button(
                "Respond",
                on_click=lambda: setattr(e.state, "adding_comment", True),
                key=f"respond_button_{e.unique_identifier}",
            )

            if e.archived_discussions:
                cols[1].button("Unarchive messages", on_click=lambda: e.archive_discussions(False))
            else:
                cols[1].button("Mark as resolved", on_click=lambda: e.archive_discussions(True))
        st.markdown("---")

    def show_metadata_editor(self, e):
        from solidipes_core_plugin.reports.widgets.custom_widgets import EditList

        excluded_keys = ["@id", "@type", "hasPart"]
        self.rocrate_metadata = self.f.f.additional_metadata
        metadata_list = [[key, value] for key, value in self.rocrate_metadata.items() if key not in excluded_keys]
        input_params = [
            {
                "placeholder": "Key",
                "type": "text",
                "value": "",
            },
            {
                "placeholder": "Value",
                "type": "text",
                "value": "",
            },
        ]
        edit_list = EditList(metadata_list, input_params=input_params, fmt="", caption="Metadata Edition")
        new_metadata = dict(edit_list.data)
        for key in excluded_keys:
            try:
                new_metadata[key] = self.rocrate_metadata[key]
            except KeyError:
                pass
        self.rocrate_metadata.replace(new_metadata)

    def loader_selection(self, e):
        extension = e.f.file_info.extension
        extension2loaders = loader_list.get_extension2loaders()

        if extension in extension2loaders:
            loader_names = [loader.class_path for loader in extension2loaders[extension]]

        else:
            self.mime_type_selection(e)
            mime_type = e.f.file_info.type
            mime2loaders = loader_list.get_mime_type2loaders()

            if mime_type in mime2loaders:
                st.warning(
                    f'No loaders found for extension "**.{extension}**". Displaying loaders compatible with MIME type'
                    f' "**{mime_type}**".'
                )
                loader_names = [loader.class_path for loader in mime2loaders[mime_type]]
            else:
                st.warning(
                    f'No loaders found for extension "**.{extension}**" or MIME type "**{mime_type}**". Displaying all'
                    " available loaders."
                )
                loader_names = [loader.class_path for loader in loader_list]

        if e.f.preferred_loader_name not in loader_names:
            loader_names.append(e.f.preferred_loader_name)

        loader_selection_key = f"loader_selection_{e.unique_identifier}"
        if loader_selection_key not in st.session_state:
            st.session_state[loader_selection_key] = e.f.preferred_loader_name
        if st.session_state[loader_selection_key] not in loader_names:
            loader_names.append(st.session_state[loader_selection_key])

        def format_loader_name(loader_name):
            path = loader_name.split(".")
            loader_name = path[-1]
            loader_path = ".".join(path[:-1])
            if loader_path.startswith("solidipes.") or loader_path.startswith("solidipes_core_plugin."):
                return loader_name
            else:
                return f"{loader_name} ({loader_path})"

        loader_name = st.selectbox(
            "Loader",
            loader_names,
            index=loader_names.index(st.session_state[loader_selection_key]),
            format_func=format_loader_name,
        )
        if loader_name != e.f.preferred_loader_name:
            e.f.preferred_loader_name = loader_name
            viewer_selection_key = f"viewer_selection_{e.unique_identifier}"
            del st.session_state[viewer_selection_key]
            e.f.clear_cached_metadata(["file_info", "is_valid", "preferred_viewer_name"])
            st.rerun()

    def mime_type_selection(self, e):
        extension = e.f.file_info.extension
        current_mime_type = e.f.file_info.type

        show_incompatible_types = st.checkbox(
            f'Show MIME types incompatible with extension "**.{extension}**"', value=False
        )
        if show_incompatible_types:
            possible_mime_types = list(get_mime_type2extensions().keys())
        else:
            possible_mime_types = get_extension2mime_types().get(extension, [])
        if current_mime_type not in possible_mime_types:
            possible_mime_types.append(current_mime_type)

        possible_mime_types = sorted(possible_mime_types)

        def format_mime_type(mime_type):
            extensions = ", ".join(get_mime_type2extensions().get(mime_type, []))
            mime_type = mime_type.strip()
            if mime_type.endswith("/"):
                mime_type = mime_type[:-1]
            if extensions:
                extensions = " (" + extensions + ")"
            return f"{mime_type}{extensions}"

        mime_type = st.selectbox(
            "MIME type",
            possible_mime_types,
            format_func=format_mime_type,
            index=possible_mime_types.index(current_mime_type),
            accept_new_options=True,
        )

        if mime_type != current_mime_type:
            mimes = get_mimes()
            mimes[e.file_info.path] = mime_type
            set_mimes(mimes)
            e.f.clear_cached_metadata(["file_info", "is_valid", "preferred_viewer_name"])
            st.rerun()

        if st.button("Detect MIME type automatically"):
            mimes = get_mimes()
            if e.file_info.path in mimes:
                del mimes[e.file_info.path]
            set_mimes(mimes)
            e.f.clear_cached_metadata(["file_info", "is_valid"])
            st.rerun()

    def viewer_selection(self, e):
        if st.checkbox("Show incompatible viewers"):
            viewer_names = [v.class_path for v in viewer_list]
        else:
            compatible_viewers = e.f.compatible_viewers
            if isinstance(e.f, FileSequence):
                compatible_viewers.extend(e.f._current_element.compatible_viewers)

            viewer_names = [v.class_path for v in compatible_viewers]
            viewer_names = list(set(viewer_names))

        if e.f.preferred_viewer_name not in viewer_names:
            viewer_names.append(e.f.preferred_viewer_name)

        viewer_selection_key = f"viewer_selection_{e.unique_identifier}"
        if viewer_selection_key not in st.session_state:
            st.session_state[viewer_selection_key] = e.f.preferred_viewer_name
        if st.session_state[viewer_selection_key] not in viewer_names:
            viewer_names.append(st.session_state[viewer_selection_key])

        def format_viewer_name(viewer_name):
            path = viewer_name.split(".")
            viewer_name = path[-1]
            viewer_path = ".".join(path[:-1])
            if viewer_path.startswith("solidipes.") or viewer_path.startswith("solidipes_core_plugin."):
                return viewer_name
            else:
                return f"{viewer_name} ({viewer_path})"

        viewer_name = st.selectbox(
            "Viewer",
            viewer_names,
            index=viewer_names.index(st.session_state[viewer_selection_key]),
            format_func=format_viewer_name,
        )
        if viewer_name != e.f.preferred_viewer_name:
            e.f.preferred_viewer_name = viewer_name

    def get_file_title(self, e):
        path = e.file_info.path
        if isinstance(e.f, FileSequence):
            path = e.f.path

        file_title = f"{path}"

        if isinstance(e.f, FileSequence):
            file_size = e.total_size
        else:
            file_size = e.file_info.size

        file_title += f"&nbsp; &nbsp; **{e.file_info.type.strip()} {DataSize(file_size):.2a}** "
        title = file_title

        # if e.discussions or e.state.view:
        #    title += "&nbsp; :arrow_forward: &nbsp; &nbsp; "

        if e.state.view:
            title += "&nbsp; :open_book:"

        if e.discussions:
            title += "&nbsp;:e-mail: &nbsp; :arrow_forward: **You have a message**"

        return title
