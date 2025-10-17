from datasize import DataSize
from solidipes.loaders.file_sequence import FileSequence

from .solidipes_widget import SolidipesWidget as SPW


class FileButton(SPW):
    def __init__(self, e, show_only_error=False, **kwargs):
        super().__init__(**kwargs)
        self.e = e
        self.show_only_error = show_only_error

    def show(self):
        self.e.state.valid = self.e.is_valid
        if self.show_only_error and self.e.is_valid:
            return

        title = self.get_file_title(self.e)

        self.layout.link_button(f"{title}", use_container_width=True, url=f"?page=display_page&file={self.e.path}")
        self.show_discussions(self.e)

    def get_file_title(self, e):
        path = e.file_info.path
        if isinstance(e.f, FileSequence):
            path = e.f.path

        file_title = f"{path}"

        if isinstance(e.f, FileSequence):
            file_size = e.total_size
        else:
            file_size = e.file_info.size

        file_title += f"&nbsp; &nbsp; **{e.file_info.type.strip()}/{DataSize(file_size):.2a}** "
        title = file_title

        if e.state.valid and (not e.discussions or e.archived_discussions):
            title = ":white_check_mark: &nbsp; &nbsp;" + file_title
        else:
            title = ":no_entry_sign: &nbsp; &nbsp; " + file_title

        # if e.discussions or e.state.view:
        #    title += "&nbsp; :arrow_forward: &nbsp; &nbsp; "

        if e.state.view:
            title += "&nbsp; :open_book:"

        if e.discussions:
            title += "&nbsp;:e-mail: &nbsp; :arrow_forward: **You have a message**"

        return title

    def show_discussions(self, e):
        from solidipes_core_plugin.reports.widgets.custom_widgets import SpeechBubble

        if not e.discussions:
            return
        if not e.archived_discussions:
            self.layout.markdown("### :speech_balloon: Discussions")
            for author, message in e.discussions:
                SpeechBubble(author, message)
            self.layout.markdown("<br>", unsafe_allow_html=True)

            self.layout.button(
                "Respond",
                on_click=lambda: setattr(e.state, "adding_comment", True),
                key=f"respond_button_{e.unique_identifier}",
            )
            self.layout.markdown("---")

        if self.show_advanced:
            if e.discussions:
                self.layout.markdown("---")
                if not e.archived_discussions:
                    self.layout.button("Archive messages", on_click=e.archive_discussions())
                else:
                    self.layout.button("Unarchive messages", on_click=e.archive_discussions(False))

                self.layout.markdown("---")
