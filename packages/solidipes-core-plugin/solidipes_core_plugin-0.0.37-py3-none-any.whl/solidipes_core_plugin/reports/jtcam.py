#!/bin/env python
################################################################
import base64
import os

import pyparsing as pp

################################################################
from solidipes_core_plugin.loaders.text import Text
from solidipes_core_plugin.reports.web_report import WebReport, WebReportSpawner

################################################################

command = "report"
command_help = "generate report for JTCAM review from a directory"
################################################################

jtcam_icon_filename = os.path.join(os.path.dirname(__file__), "jtcam_small_logo.png")
_jtcam_icon = base64.b64encode(open(jtcam_icon_filename, "rb").read()).decode("utf-8")


def jtcam_icon(size):
    _img = f'<img height="{size}" src="data:image/png;base64,{_jtcam_icon}"><br>'
    return _img


################################################################


class JTCAMReport(WebReport):
    def __init__(self):
        super().__init__()

    def main(self, dir_path):
        print(f'Generating JTCAM report for "{dir_path}"')
        self.header_layout.markdown(
            "<center>" + jtcam_icon("60em") + "</center>",
            unsafe_allow_html=True,
        )
        super().main(dir_path)

    def alternative_parser_old(self, e):
        if not isinstance(e.f, Text):
            return []
        path = e.file_info.path
        self.logger("parsing", path)

        _begin = pp.Literal("<JTCAM>").addParseAction(lambda x: "")
        _end = pp.Literal("</JTCAM>").addParseAction(lambda x: "")
        _block = pp.Combine(
            pp.SkipTo(_begin).addParseAction(lambda x: "") + _begin + pp.SkipTo(_end) + _end
        ).addParseAction(lambda x: "".join(x).strip())
        _all = pp.ZeroOrMore(_block)

        content = open(path).read()

        try:
            res = _all.parseString(content)
        except pp.ParseException:
            return []
        except KeyError:
            return []

        res = [e for e in res]
        self.logger(path, res)
        return res


################################################################


class JTCAMReportEditable(JTCAMReport):
    def __init__(self):
        super().__init__(self)

    # def display_file(self, e, readme=False):
    #     if not fnmatch.fnmatch(e.file_info.path.lower(), self.file_wildcard):
    #         return
    #
    #     path = e.file_info.path
    #     file_title = f"{path}"
    #     fname = os.path.basename(path).lower()
    #     if not readme and fname == "readme.md":
    #         return
    #
    #     state = stateWrapper(e)
    #     if not state.loaded:
    #         try:
    #             e.load_all()
    #         except Exception as err:
    #             e.errors += ["Error during import<br>" + str(err)]
    #         e.errors += selffind_jtcam_entries(e)
    #         state.valid = e.is_valid
    #         state.errors = e.errors
    #         state.loaded = True
    #
    #     if fname == "readme.md":
    #         print("readme view state:", state.view)
    #         if state.view is None:
    #             state.view = "view"
    #
    #     if self.file_error_checkbox and e.is_valid:
    #         return
    #
    #     if state.valid:
    #         title = ":white_check_mark: &nbsp; &nbsp;" + file_title
    #     else:
    #         title = ":no_entry_sign: &nbsp; &nbsp; " + file_title
    #         title += "&nbsp; &nbsp; :arrow_backward: &nbsp; &nbsp; "
    #         title += f"**{e.file_info.type.strip()}**"
    #
    #     with st.expander(
    #         f" {title}",
    #         expanded=(fname == "readme.md"),
    #     ):
    #         if not state.valid and state.errors:
    #             # st.markdown(jtcam_icon("20em"), unsafe_allow_html=True)
    #             for err in e.errors:
    #                 st.warning(err)
    #
    #         col1, col2, col3, col4 = st.columns(4)
    #         col1.download_button(
    #             f"Download {os.path.basename(e.file_info.path)}",
    #             data=open(e.file_info.path),
    #             file_name=os.path.basename(e.file_info.path),
    #             use_container_width=True,
    #             key="download_" + e.file_info.path,
    #         )
    #
    #         _path = e.file_info.path
    #         while os.path.islink(_path):
    #             dirname = os.path.dirname(path)
    #             _path = os.path.join(dirname, os.readlink(_path))
    #         url = self.git_origin + "/-/edit/master/data/" + _path
    #
    #         # edit_button = col4.button(
    #         #     f"Edit {os.path.basename(e.file_info.path)}",
    #         #     use_container_width=True,
    #         #     key="edit_" + e.file_info.path,
    #         # )
    #
    #         view_button = col2.button(
    #             f"View {os.path.basename(e.file_info.path)}",
    #             use_container_width=True,
    #             key="view_" + e.file_info.path,
    #         )
    #
    #         col3.markdown(f"[Edit on Gitlab]({url})", unsafe_allow_html=True)
    #
    #         if view_button:
    #             state.view = "view"
    #
    #         # st.markdown(f"StateView: {state.view}")
    #
    #         # if edit_button:
    #         #    state.view = "edit"
    #
    #         if state.view == "view":
    #             e.view()
    #
    #         # if state.view == "edit":
    #         #     previous_version = open(e.file_info.path).read()
    #         #     edit = st.text_area("Edition box", value=previous_version)
    #         #     save_button = st.button(
    #         # "Save", key="save_" + e.file_info.path)
    #         #     if save_button:
    #         #         state.view = "saved"
    #
    #         # if state.view == "saved":
    #         #     open(e.file_info.path, "w").write(edit)
    #         #     if update_dataset_and_push():
    #         #         st.success("Saved changes")
    #         #         state.view = "view"
    #         #         time.sleep(2)
    #         #         st.experimental_rerun()
    #         #     else:
    #         #         open(e.file_info.path, "w").write(previous_version)
    #         #         st.error("Reverted changes")


class JTCAMReportSpawner(WebReportSpawner):
    command = "jtcam"
    command_help = "Launch the web graphical interface for JTCAM curation"


################################################################
if __name__ == "__main__":
    report = JTCAMReport()
    report.main("./")
