#!/bin/env python
################################################################
import os

import streamlit as st
from solidipes.utils import get_study_metadata, logging
from solidipes.utils.utils import get_zenodo_infos

from .uploader import UploaderWidget

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class DSpace7Publish(UploaderWidget):
    repo_family = "Dspace7"

    def show_submission_panel(self):
        with self.layout.expander(f"Publish in {self.repo_family}", expanded=True):
            host = st.container().selectbox(
                "Platform", ("infoscience.epfl.ch", "infoscience-sb.epfl.ch", "boris-portal.unibe.ch")
            )
            st.session_state["host"] = host
            import requests

            from solidipes_core_plugin.utils.dspace7_utils import list_collections

            try:
                collections = list_collections(host)
            except requests.exceptions.ConnectionError as e:
                st.error(e)
                st.error(f"Cannot use/connect to {host}")
                return

            collection_menu_items = []
            for idx, coll in enumerate(collections):
                collection_menu_items.append(f"{idx}.\t{coll['name']}")
            collection_item = st.container().selectbox("Collection", collection_menu_items)
            collection_id = collections[collection_menu_items.index(collection_item)]["id"]
            st.session_state["d7collection"] = collection_id
            token = st.text_input(f"{self.repo_family} token", type="password")
            zenodo_metadata = get_study_metadata()
            existing_identifier = False
            data = get_zenodo_infos()
            if "deposition_identifier" in data:
                existing_identifier = data["deposition_identifier"]
            if "doi" in zenodo_metadata:
                existing_identifier = zenodo_metadata["doi"]

            button_title = "Reuse existing deposition"
            if existing_identifier:
                button_title += f" ({existing_identifier})"
                reuse_identifier = st.checkbox(button_title, value=existing_identifier is not False)
                new_deposition = not reuse_identifier
            else:
                new_deposition = False

            col1, col2 = st.columns(2)
            title = f"Submit to {self.repo_family}"
            col2.markdown(
                "**Please push content with caution "
                f"as it may result in a permanent entry in {self.repo_family}@{host}**"
            )
            if existing_identifier and not reuse_identifier:
                existing_identifier = False

            def submit():
                st.session_state.zenodo_publish = []
                try:
                    self.upload(token, existing_identifier, new_deposition=new_deposition)
                except Exception as e:
                    self.global_message.error("upload error: " + str(e))

            col1.button(title, type="primary", on_click=submit)

    def upload(self, access_token=None, existing_identifier=None, sandbox=False, new_deposition=False):
        import argparse

        import solidipes_core_plugin.uploaders.dspace7 as d7uploader

        args = argparse.Namespace()
        args.access_token = access_token
        args.sandbox = sandbox
        args.host = st.session_state["host"]
        args.collection = st.session_state["d7collection"]
        args.directory = None
        args._print = self._print
        args.existing_identifier = existing_identifier
        args.new_deposition = new_deposition
        args.tmp_dir = "/tmp" if os.name != "nt" else os.path.expanduser(r"~\AppData\Local\Temp")
        args.no_cleanup = True
        d7uploader.main(args)
