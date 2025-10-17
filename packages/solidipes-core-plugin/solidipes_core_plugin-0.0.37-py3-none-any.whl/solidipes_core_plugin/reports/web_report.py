#!/bin/env python
################################################################
import argparse
import os
from typing import TYPE_CHECKING

from solidipes.plugins.discovery import uploader_list
from solidipes.reports.report import Report
from solidipes.scanners.scanner import list_files
from solidipes.utils import add_completed_stage, is_stage_completed, logging, remove_completed_stage
from solidipes.utils.git_infos import GitInfos
from solidipes.utils.progress import set_streamlit_layout as set_progress_layout
from solidipes.validators.curation import CurationValidator
from solidipes.validators.global_validation import dataset, get_global_validator

from solidipes_core_plugin.reports.widgets.solidipes_buttons import SolidipesButtons as SPB
from solidipes_core_plugin.reports.widgets.utils import FileWrapper, transform_to_subtree

################################################################

if TYPE_CHECKING:
    import streamlit as st
else:
    import lazy_loader as lazy

    st = lazy.load("streamlit")

print = logging.invalidPrint
logger = logging.getLogger()


################################################################
WebReport_pages = []


def sp_page(foo):
    WebReport_pages.append(foo.__name__)
    return foo


class WebReport:
    def __init__(self):
        self.git_infos = GitInfos()
        self.display_push_button = False
        self.file_wildcard = "*"
        self.file_error_checkbox = None
        self.scanner = get_global_validator(CurationValidator).scanner
        st.set_page_config(
            layout="wide",
            page_title="Solidipes",
            page_icon="https://gitlab.com/solidipes/solidipes/-/raw/main/logos/favicon.png",
            # initial_sidebar_state="collapsed",
        )
        if "currently_opened" not in st.session_state:
            st.session_state["currently_opened"] = None

    def createLayouts(self):
        from solidipes_core_plugin.reports.widgets.gitlab_issues import GitlabIssues
        from solidipes_core_plugin.reports.widgets.plugin_management import open_plugin_dialog
        from solidipes_core_plugin.reports.widgets.solidipes_logo_widget import SolidipesLogoWidget
        from solidipes_core_plugin.reports.widgets.uploader import DatasetInfos

        self.progress_layout = st.empty()
        set_progress_layout(self.progress_layout)
        SolidipesLogoWidget(layout=st.sidebar, short=True, width="25%")
        st.sidebar.markdown("---")
        self.info_layout = st.sidebar.container()
        st.sidebar.markdown("---")
        self.gitlab_control = st.sidebar.container()
        self.jupyter_control = st.sidebar.container()
        self.filebrowser_control = st.sidebar.container()
        self.update_buttons = st.sidebar.container()
        self.validation_layout = st.container()
        self.file_selector = st.container()
        self.path_selector = st.sidebar.container()
        if self.git_infos.repository is not None:
            self.git_control = st.sidebar.container()
        self.env_layout = st.sidebar.container()
        with st.sidebar.container():
            if st.button("⚙ Manage plugins", use_container_width=True):
                open_plugin_dialog()

        self.options = st.sidebar.expander("Options")

        self.main_layout = st.container()
        self.file_layout = self.main_layout.container()
        self.global_message = self.main_layout.container()
        self.header_layout = self.main_layout.container()
        self.tab_metadata, self.tab_files = self.main_layout.container(), self.main_layout.container()
        self.dataset_infos = DatasetInfos(self.tab_metadata)
        if self.git_infos.origin is not None:
            self.gitlab_issues = GitlabIssues(self.main_layout)
        self.files_container = self.main_layout.container()
        self.logs = self.main_layout.container()

    def scan_directories(self, dir_path):
        all_paths = []
        nodes = None
        with st.spinner("Loading directories..."):
            if "scanned_files" not in st.session_state:
                st.session_state["scanned_files"] = {}
                h = self.scanner.get_dirpath_tree()
                s_files = st.session_state["scanned_files"]
                s_files["all_paths"] = self.scanner.get_path_list()
                s_files["nodes"] = transform_to_subtree(h)
            else:
                s_files = st.session_state["scanned_files"]
            nodes = s_files["nodes"]
            all_paths = s_files["all_paths"]

        return all_paths, nodes

    def step_bar(self, page, uploader=None):
        from solidipes_core_plugin.reports.widgets.step_bar import StepBar

        if page == "display_page":
            page = "curation"

        StepBar(current_step=page, uploader=uploader)
        st.markdown("---\n\n")

    def main(self, dir_path):
        self.dir_path = dir_path
        self.scanner.root_path = self.dir_path

        if "page" in st.query_params:
            page = st.query_params["page"]
            if page not in WebReport_pages:
                st.error(f"Invalid page '{page}'")
                return
            try:
                uploader = st.query_params.get("uploader", None) if page == "export" else None
                self.step_bar(page, uploader=uploader)
                page_method = getattr(self, page)
            except AttributeError as e:
                st.write(e)
                st.error(f"Invalid page '{page}'")
                return
            return page_method()

        return self.main_page()

    @sp_page
    def display_page(self):
        from solidipes_core_plugin.reports.widgets.display_file import DisplayFile

        self.createLayouts()
        self.info_layout.write(
            "This page shows you the validation state and a visualization of one element of your dataset. You can use"
            " the “Discussions” to make any relevant comments ; this will cause the file to be tagged as erroneous"
            " until the issue is resolved."
        )

        if "file" not in st.query_params:
            st.error(f"Wrong url {[k + '=' + v for k, v in st.query_params.items()]}")
            return

        fname = st.query_params["file"]
        loader = st.query_params.get("loader", "")
        paths = st.query_params.get("paths", [])

        self.show_advanced = self.options.checkbox("Advanced", value=False)
        if self.show_advanced:
            self.logs.markdown("---")
            from solidipes_core_plugin.reports.widgets.solidipes_logs import SolidipesLogs

            SolidipesLogs(layout=self.logs)

        return DisplayFile(filename=fname, loader_name=loader, paths_str=paths, layout=self.file_layout)

    def main_page(self):
        from solidipes_core_plugin.reports.widgets.front_page import FrontPage

        FrontPage()

    @sp_page
    def metadata(self):
        self.createLayouts()
        self.info_layout.write(
            "*The goal of this step is to edit the metadata describing your dataset. This is where you add the title,"
            " authors, keywords, licence, language, and any other relevant information.*"
        )
        if is_stage_completed(2):
            self.info_layout.write(
                "*This stage has been validated. If you still need to make changes, you can **invalidate the stage**"
                " with the button below.*"
            )
            self.info_layout.button(
                "Invalidate metadata",
                on_click=lambda: remove_completed_stage(2),
                use_container_width=True,
                type="primary",
            )

        else:
            self.info_layout.write("*Once ready you can **validate the metadata** with the button below.*")

            SPB(layout=self.info_layout)._link_button(
                "Validate metadata",
                "?page=export",
                action=lambda: add_completed_stage(2),
                use_container_width=True,
                type="primary",
            )

        self.dataset_infos.show()

    @sp_page
    def export(self):
        self.createLayouts()
        self.info_layout.write(
            "*This is the final step, which allows you to publish your curated dataset to an online archive.  **Please"
            " check** that the exported archive contains all the files you wish to be published. Note that some files"
            " are added inside a .solidipes directory for forward compatibility.*"
        )

        exporter_choice = st.query_params.get("uploader", "zenodo")
        exporter_options = set()
        for u in uploader_list:
            key = u.parser_key
            if not isinstance(key, list):
                key = [key]
            if exporter_choice in key:
                exporter_choice = key[0]
            if u.report_widget_class is None:
                continue
            exporter_options.add(key[0])

        if exporter_choice not in exporter_options:
            self.tab_metadata.error(f"Widget for {exporter_choice} still needs to be written => revert to Zenodo")
            exporter_choice = "zenodo"

        from solidipes_core_plugin.reports.widgets.zenodo import ZenodoPublish

        self.exporter = ZenodoPublish
        with self.tab_metadata:
            exporter = st.segmented_control("Exporter", options=exporter_options, default=exporter_choice)

            exporter_types = {}
            for u in uploader_list:
                if u.report_widget_class is None:
                    continue
                key = u.parser_key
                if not isinstance(key, list):
                    key = [key]
                exporter_types[key[0]] = u.report_widget_class
            if exporter is not None:
                self.exporter = exporter_types[exporter]

            self.exporter(self.tab_metadata, self.global_message, self.progress_layout).show()

    @sp_page
    def acquisition(self):
        self.createLayouts()
        self.info_layout.write(
            "*Here you can acquire and organise all the files you wish to publish. Much like a regular file browser, it"
            " allows you to view and upload all files and folders in your project directory.*"
        )

        if is_stage_completed(0):
            self.info_layout.write(
                "*This stage has been validated. If you still need to make changes, you can **invalidate the stage**"
                " with the button below.*"
            )
            self.info_layout.button(
                "Invalidate acquisition",
                on_click=lambda: remove_completed_stage(0),
                use_container_width=True,
                type="primary",
            )

        else:
            self.info_layout.write("*Once ready you can **validate the acquisition** with the button below.*")
            SPB(layout=self.info_layout)._link_button(
                "Validate acquisition",
                "?page=curation",
                action=lambda: add_completed_stage(0),
                use_container_width=True,
                type="primary",
            )

        SPB()._iframe_filebrowser(self.dir_path)

    @sp_page
    def curation(self):
        self.createLayouts()
        self.info_layout.write(
            "*On this page, you can view all files in your dataset, as well as their validation state.*"
        )
        self.info_layout.write("*For an in-depth view of a given file, you can click on the “View File” button.*")
        self.info_layout.write("**Each file** *marked* 🚫 *needs to be checked to complete curation stage.*")
        self.info_layout.write("To change the extension of a file, double-click in the “extension” column.")

        if "GUI_files" not in st.session_state:
            st.session_state["GUI_files"] = {}

        self.show_advanced = False

        SPB(layout=self.update_buttons)._link_button(
            "Next (metadata)",
            "?page=metadata",
            use_container_width=True,
            type="primary",
        )

        SPB(layout=self.gitlab_control)._open_in_gitlab_button(self.git_infos.origin)
        self.show_advanced = self.options.checkbox("Advanced", value=False)
        if self.show_advanced:
            self._environment_info()

        if self.display_push_button:
            from solidipes_core_plugin.reports.widgets.git import GIT

            GIT(container_infos=self.git_infos, container_state=self.modified_state)

        if self.git_infos.origin is not None:
            self.gitlab_issues.show()

        SPB(layout=self.jupyter_control)._open_in_jupyterlab_button()
        SPB(layout=self.filebrowser_control)._open_in_filebrowser_button()

        from solidipes.loaders.cached_metadata import CachedMetadata

        with st.spinner("Unlock cache database"):
            with self.validation_layout:
                if CachedMetadata.is_cache_database_locked():
                    st.error("🔒 The cache database is currently locked")
                    if st.button("Force unlock"):
                        CachedMetadata.force_unlock()
                        st.rerun()

            while CachedMetadata.is_cache_database_locked():
                import time

                from solidipes.utils.config import cached_metadata_polling_interval

                time.sleep(cached_metadata_polling_interval)

        self.show_global_validations()

        if SPB(layout=self.file_selector)._force_rescan_button():
            clear_session_state(exclude="discussions")

        all_paths, nodes = self.scan_directories(self.dir_path)

        if "all_found_files" not in st.session_state:
            found = self.scanner.get_filtered_loader_tree([p for p in all_paths], recursive=False)
            files = list_files(found)

            files_dict = self.scanner.get_filtered_loader_dict([p for p in all_paths], recursive=False)
            files_dict = {k: FileWrapper(v) for k, v in files_dict.items()}
            st.session_state["all_found_files"] = files
            st.session_state["all_found_files_dict"] = files_dict

        all_found_files = st.session_state["all_found_files"]

        if not all_found_files:
            # st.markdown(f"#### Nothing in the paths: {all_paths}")
            st.markdown("#### Nothing in the filtered files")
            return

        with self.tab_files:
            from solidipes_core_plugin.reports.widgets.file_list import FileList

            FileList(all_found_files=all_found_files)

        with self.progress_layout:
            with st.spinner("Saving cache to YAML format"):
                from solidipes.loaders.cached_metadata import CachedMetadata

                if CachedMetadata._global_cached_metadata is not None:
                    CachedMetadata._write_cached_metadata_to_yaml()

        if self.show_advanced:
            self.logs.markdown("---")

            if SPB(layout=self.logs)._force_reset_cache():
                clear_session_state()

            from solidipes_core_plugin.reports.widgets.solidipes_logs import SolidipesLogs

            SolidipesLogs(layout=self.logs)

    def show_global_validations(self):
        from solidipes_core_plugin.reports.widgets.validation import ValidationWidget  # Keep as lazy import

        ValidationWidget(data_container=dataset, layout=self.validation_layout)

    def _environment_info(self):
        with self.env_layout.expander("Environment"):
            st.write("sh env")
            table_env = [k for k in os.environ.items()]
            st.dataframe(table_env, use_container_width=True)
            import pkg_resources

            st.write("pip packages")
            table_env = [p.project_name for p in pkg_resources.working_set]
            st.dataframe(table_env, use_container_width=True)


################################################################


def clear_session_state(exclude=[]):
    logger.info("Clearing session state")
    clear_all_lru_caches()
    keys = [k for k in st.session_state]
    for k in keys:
        del st.session_state[k]
    from solidipes.loaders.cached_metadata import CachedMetadata

    CachedMetadata.clear_cache(exclude=exclude)
    if "all_found_files" in st.session_state:
        del st.session_state["all_found_files"]
    st.rerun()


################################################################


class WebReportSpawner(Report):
    command = "web-report"
    command_help = "Launch the web graphical interface"
    _aliases = ["web_report", "web"]

    def make(self, args: argparse.Namespace):
        import subprocess
        import sys

        if args.debug:
            os.environ["FULL_SOLIDIPES_LOG"] = "true"
        logger.debug(args.additional_arguments)

        cmd = f"streamlit run {__file__} {' '.join(args.additional_arguments)}"

        if "SOLIDIPES_DEBUGPY" in os.environ:
            cmd = f"debugpy --listen 5678 --wait-for-client -m {cmd}"

        cmd = f"{sys.executable} -m {cmd}"

        logger.info(cmd)
        subprocess.call(cmd, shell=True, cwd=args.dir_path)

    def populate_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "dir_path",
            nargs="?",
            default=".",
            help="Path to the directory to generate the report for. Defaults to current directory",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode",
        )

        parser.add_argument(
            "additional_arguments",
            nargs=argparse.REMAINDER,
            help="Additional arguments to forward to Streamlit",
        )


################################################################
def clear_all_lru_caches():
    import gc
    from functools import _lru_cache_wrapper

    for obj in gc.get_objects():
        if isinstance(obj, _lru_cache_wrapper):
            obj.cache_clear()  # Clear the cache


################################################################
if __name__ == "__main__":
    logger.info("starting web_report")
    web_report = WebReport()
    web_report.main("./")
