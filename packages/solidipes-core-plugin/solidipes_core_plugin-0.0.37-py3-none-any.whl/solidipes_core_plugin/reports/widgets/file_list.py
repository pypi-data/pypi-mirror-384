import os

from datasize import DataSize
from solidipes.loaders.file import File, load_file
from solidipes.loaders.file_sequence import FileSequence
from solidipes.loaders.mime_types import get_possible_extensions, get_possible_mimes

# from solidipes.loaders.virtual_file import VirtualFile
from solidipes.utils import logging, rename_file
from solidipes.utils.progress import get_progress_bar
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from solidipes_core_plugin.reports.widgets.utils import FileWrapper

from .solidipes_widget import SolidipesWidget as SPW

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################

error_cell_renderer = JsCode("""
    class ErrorCellRenderer {
        init(params) {
            if (!params.value) {
                this.eGui = document.createElement("span");
                this.eGui.innerText = "";
                return;
            }

            this.eGui = document.createElement("div");
            this.eGui.innerText = params.value;
        }

        getGui() {
            return this.eGui;
        }
    }
""")


url_cell_renderer = JsCode("""
    class UrlCellRenderer {
        init(params) {
            if (!params.value) {
                this.eGui = document.createElement("span");
                this.eGui.innerText = "";
                return;
            }

            this.eGui = document.createElement("a");
            this.eGui.innerText = "View File";
            this.eGui.setAttribute("href", "");

            let parentLocation = window.parent.location;
            let parentUrl = parentLocation.origin + parentLocation.pathname;
            let url = parentUrl + params.value;

            this.eGui.addEventListener("click", _ => {
                parent.window.open(url, "_self");
            });
            // Using href does not work because inside an iframe
            // this.eGui.setAttribute("href", url);
            // this.eGui.setAttribute("target", "_parent");
        }

        getGui() {
            return this.eGui;
        }
    }
""")


file_size_aggregator = JsCode("""
    function(params) {
        let totalSize = params.values.reduce((total, value) => total + value.value, 0);

        const units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"];
        let i = 0;
        let displaySize = totalSize;

        for (; i < units.length; i++) {
            if (displaySize < 1024) {
                break;
            }
            displaySize /= 1024;
        }

        return {
            value: totalSize,
            display: `${Math.round(displaySize * 100) / 100}${units[i]}`,
        };
    }
""")


file_size_comparator = JsCode("""
    function(value1, value2, node1, node2, isDescending) {
        return (value1?.value - value2?.value) || 1;
    }
""")


file_size_value_formatter = JsCode("""
    function(params) {
        return params.value?.display;
    }
""")


status_aggregator = JsCode("""
    function(params) {
        let valid = true;
        let message = false;

        for (let value of params.values) {
            if (value.includes("🚫")) {
                valid = false;
                // params?.rowNode?.setExpanded(true);
            }
            if (value.includes("✉️")) {
                message = true;
            }
        }

        let status = valid ? "✅" : "🚫";
        if (message) {
            status += " ✉️";
        }

        return status;
    }
""")

unique_aggregator = JsCode("""
    function(params) {

        let vals = [];
        for (let val of params.values) {
          if (!val) continue;
          if ((typeof val === "Object") && !('current' in val)) val = val.current;
          if (!(vals.includes(val))) vals.push(val);
        }
        if (vals.length != 1) return;
        return params.values[0];
    }
""")


url_aggregator = JsCode("""
    function(params) {
        let paths = [];
        let path = null;
        let loader = null;
        for (let value of params.values) {
          if (!value) continue;
          let _options = value.split('?page=display_page').pop();
          _options = _options.split('&');
          options = {};
          for (let opt of _options) {
            if (!opt){
              continue;
            }
            let key = opt.split('=')[0];
            let val = opt.split('=')[1];
            options[key] = val;
          }
          if (!('group' in options)){
            continue;
          }
          paths.push(options.path);
          path = options.group;
          loader = options.group_loader;
        }
        if (!path) return;
        let url = '?page=display_page&file=' + path + "&paths=" + paths.join(',') + '&loader=' + loader;

        return url;
    }
""")


extension_value_formatter = JsCode("""
    function(params) {
        return params.value?.current;
    }
""")


extension_cell_editor_values = JsCode("""
    function(params) {
        let initial = params.value?.initial || "";
        let possible = params.value?.possible || [];
        return possible.map(value => ({current: value, initial, possible: possible}));
    }
""")


extension_cell_editor_format_value = JsCode("""
    function(params) {
        return params?.current;
    }
""")


extension_comparator = JsCode("""
    function(value1, value2, node1, node2, isDescending) {
        return (value1?.current.localeCompare(value2?.current)) || 1;
    }
""")


class FileList(SPW):
    def __init__(self, all_found_files=[], show_curation_cols=True, **kwargs):
        super().__init__(**kwargs)
        cols = self.layout.columns(2)
        self.show_only_error = cols[0].checkbox("Show only files with errors")
        self.full_scan = cols[1].checkbox("Perform a full scan (slower)")
        self.display_files(all_found_files, show_curation_cols)
        self.current_dir_layout = None

    def file_as_dict(self, e, group=None, loader=None):
        path = os.path.basename(e.file_info.path)
        dir_path = os.path.dirname(e.file_info.path)
        dir_path = os.path.normpath(dir_path)
        if dir_path.startswith("." + os.sep):
            dir_path = dir_path[2:]

        dir_list = dir_path.split(os.sep)
        if dir_list == ["."]:
            dir_list = []
        dir_dict = {f"Directory_{i}": "📁 " + dir_list[i] for i in range(len(dir_list))}

        if group is not None:
            dir_dict[f"Directory_{len(dir_list)}"] = "📦 " + group

        if isinstance(e.f, FileSequence):
            path = e.f.path

        if isinstance(e.f, FileSequence):
            file_size = e.total_size
        else:
            logger.debug(e.file_info)
            file_size = e.file_info.size

        file_type = e.file_info.type.strip()
        human_readable_file_size = f"{DataSize(file_size):.2a}"

        if e.state.valid and (not e.discussions or e.archived_discussions):
            valid = "✅"
        else:
            valid = "🚫"

        if e.discussions:
            valid += " ✉️"

        current_extension = e.file_info.extension
        possible_extensions = get_possible_extensions(e.file_info.type)
        possible_mimes = get_possible_mimes(current_extension)

        if group is not None:
            url = f"?page=display_page&file={e.path}&path={path}&group={os.path.join('./', dir_path, group)}"
            url += f"&group_loader={loader}"
        elif isinstance(e.f, FileSequence):
            # p = os.path.basename(e.path)
            path = os.path.basename(path)
            url = f"?page=display_page&file={e.path}&loader=FileSequence"
            path = "📦 " + path
        else:
            url = f"?page=display_page&file={e.path}"

        file_dict = {
            "Status": valid,
            "Filename": path,
            "Path": e.file_info.path,
            "Extension": {"current": current_extension, "initial": current_extension, "possible": possible_extensions},
            "Type": {"current": file_type, "initial": file_type, "possible": possible_mimes},
            "Size": {"value": file_size, "display": human_readable_file_size},
            "Open": url,
            "Errors": "\n".join(e.errors),
        }
        if group is not None:
            file_dict["Group"] = group

        file_dict.update(dir_dict)

        return file_dict

    def display_files(self, files, show_curation_cols):
        import pandas as pd
        import streamlit as st

        n_files = len(files)
        progress_bar = get_progress_bar("Creating file list", total=n_files)

        _files = []

        for i, (full_path, f) in enumerate(files):
            progress_bar.update(1, text=f"Listing {full_path}")
            if isinstance(f, File) or isinstance(f, FileSequence):
                f = FileWrapper(f)
                f.state.valid = f.is_valid

                if self.show_only_error and f.state.valid:
                    continue

                if isinstance(f.f, FileSequence):
                    package_path = os.path.basename(f.f.path)
                    if self.full_scan:
                        for path in f.f._paths:
                            _sub_f = load_file(path)
                            _sub_f = FileWrapper(_sub_f)
                            _sub_f.state.valid = _sub_f.is_valid
                            _files.append(self.file_as_dict(_sub_f, group=package_path, loader=f.f.__class__.__name__))
                    else:
                        _files.append(self.file_as_dict(f))
                else:
                    _files.append(self.file_as_dict(f))

        _files = pd.DataFrame(_files)
        # import streamlit as st
        # st.write(_files)

        if len(_files) and _files["Status"].str.contains("🚫").any():
            from solidipes.utils import remove_completed_stage

            remove_completed_stage(1)
        else:
            from solidipes.utils import add_completed_stage

            add_completed_stage(1)

        dir_columns = [col for col in _files.columns if col.startswith("Directory")]

        grid_builder = GridOptionsBuilder.from_dataframe(_files)

        grid_builder.configure_column(
            "Status",
            aggFunc="status_aggregator",
        )
        grid_builder.configure_column(
            "Open",
            aggFunc="url_aggregator",
        )

        grid_builder.configure_column(
            "Extension",
            aggFunc="unique_aggregator",
        )

        grid_builder.configure_column(
            "Type",
            aggFunc="unique_aggregator",
        )

        grid_builder.configure_column(
            "Errors",
            aggFunc="unique_aggregator",
        )

        grid_builder.configure_column(
            "Path",
            hide=True,
        )

        grid_builder.configure_column(
            "Extension",
            cellEditor="agRichSelectCellEditor",
            cellEditorParams={
                "formatValue": extension_cell_editor_format_value,
                "values": extension_cell_editor_values,
                "allowTyping": True,
                "filterList": True,
            },
            comparator=extension_comparator,
            editable=True,
            valueFormatter=extension_value_formatter,
        )

        grid_builder.configure_column(
            "Type",
            cellEditor="agRichSelectCellEditor",
            cellEditorParams={
                "formatValue": extension_cell_editor_format_value,
                "values": extension_cell_editor_values,
                "allowTyping": True,
                "filterList": True,
            },
            comparator=extension_comparator,
            editable=True,
            valueFormatter=extension_value_formatter,
        )

        grid_builder.configure_column(
            "Size",
            # Putting aggFunc=file_size_aggregator directly fails when editing the grid
            aggFunc="file_size_aggregator",
            comparator=file_size_comparator,
            valueFormatter=file_size_value_formatter,
        )

        grid_builder.configure_column(
            "Open",
            cellRenderer=url_cell_renderer,
        )
        grid_builder.configure_column(
            "Errors",
            cellRenderer=error_cell_renderer,
        )

        for col in dir_columns:
            grid_builder.configure_column(
                col,
                hide=True,
                rowGroup=True,
            )

        grid_builder.configure_column(
            "Group",
            hide=True,
        )
        if not show_curation_cols:
            for col in ["Status", "Extension", "Type", "Open", "Errors"]:
                grid_builder.configure_column(
                    col,
                    hide=True,
                )
        grid_builder.configure_columns("Filename", wrapText=True)
        grid_builder.configure_columns("Errors", wrapText=True)
        grid_builder.configure_columns("Errors", autoHeight=True)

        grid_options = grid_builder.build()

        grid_options["aggFuncs"] = {
            "unique_aggregator": unique_aggregator,
            "status_aggregator": status_aggregator,
            "file_size_aggregator": file_size_aggregator,
            "url_aggregator": url_aggregator,
        }
        grid_options["autoGroupColumnDef"]["headerName"] = "Directory"
        if show_curation_cols:
            grid_options["autoSizeStrategy"] = {"type": "fitCellContents"}
            # grid_options["autoSizeStrategy"] = {"type": "fitGridWidth"}
        else:
            grid_options["autoSizeStrategy"] = {"type": "fitGridWidth"}
        # grid_options["domLayout"] = "autoHeight"  # Bugged: initial height is sometimes too small
        grid_options["groupAllowUnbalanced"] = True
        # grid_options["groupDefaultExpanded"] = 0
        grid_options["isGroupOpenByDefault"] = JsCode("""
        function (params){
        if (params.key.includes("📦")){
        return false;
        }
        return true;
        }
        """)
        # if self.show_only_error:
        #    grid_options["groupDefaultExpanded"] = -1
        # elif not show_curation_cols:
        #    grid_options["groupDefaultExpanded"] = 1
        # else:
        #    grid_options["groupDefaultExpanded"] = 2
        quick_filter = st.text_input("Quick filter", placeholder="Type here to filter files and directories")
        grid_options["quickFilterText"] = quick_filter
        grid_options["suppressAggFuncInHeader"] = True

        # st.write(_files)
        grid_return = AgGrid(_files, gridOptions=grid_options, allow_unsafe_jscode=True)

        new_grid_data = grid_return["data"]
        self.rename_files(new_grid_data)
        self.change_mime_files(new_grid_data)

        progress_bar.close()

    def rename_files(self, new_grid_data):
        if len(new_grid_data) == 0:
            return

        from streamlit.components.v1 import html

        from solidipes_core_plugin.reports.web_report import clear_session_state

        extensions = new_grid_data["Extension"]
        changed_extensions = extensions.apply(lambda x: x["current"] != x["initial"])
        files_to_rename = new_grid_data[changed_extensions]

        if files_to_rename.empty:
            return

        self.layout.write("Renaming files...")

        for _, file in files_to_rename.iterrows():
            current_path = file["Path"]
            new_extension = file["Extension"]["current"]
            new_path = os.path.splitext(current_path)[0] + "." + new_extension
            rename_file(current_path, new_path)

        # Reload file list
        clear_session_state()
        html("""
            <script type = "text/javascript" >
                window.parent.location.reload();
            </script >
        """)

    def change_mime_files(self, new_grid_data):
        if len(new_grid_data) == 0:
            return

        from streamlit.components.v1 import html

        from solidipes_core_plugin.reports.web_report import clear_session_state

        new_type = new_grid_data["Type"]
        changed_type = new_type.apply(lambda x: x["current"] != x["initial"])
        files_to_retype = new_grid_data[changed_type]

        if files_to_retype.empty:
            return

        self.layout.write("Renaming files...")

        for _, file in files_to_retype.iterrows():
            from solidipes.utils import get_mimes, set_mimes

            current_path = file["Path"]
            new_mime = file["Type"]["current"]
            mimes = get_mimes()
            mimes[current_path] = new_mime
            set_mimes(mimes)

        # Reload file list
        clear_session_state()
        html("""
            <script type = "text/javascript" >
                window.parent.location.reload();
            </script >
        """)
