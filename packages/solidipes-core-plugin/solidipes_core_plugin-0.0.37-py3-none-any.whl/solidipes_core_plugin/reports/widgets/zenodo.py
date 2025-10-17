#!/bin/env python
################################################################
import os
import time

import streamlit as st

################################################################
from solidipes.utils import get_study_metadata, logging
from solidipes.utils.utils import get_zenodo_infos

from solidipes_core_plugin.utils.zenodo_utils import get_existing_deposition_identifier

from .uploader import UploaderWidget

################################################################

DELAY_FIX_BUTTONS = 0.5

print = logging.invalidPrint
logger = logging.getLogger()


################################################################


class ZenodoPublish(UploaderWidget):
    def __init__(self, *args):
        super().__init__(*args)

    def show_submission_panel(self):
        with self.layout.expander("Publish in Zenodo/InvenioRDM", expanded=True):
            token = st.text_input("Zenodo token", type="password", on_change=self.ensure_submit_detection)
            st.markdown(
                "[[Create a Zenodo"
                " token]](https://zenodo.org/account/settings/applications/tokens/new/)&nbsp;&nbsp;[[Create a"
                " Zenodo-Sandbox"
                " token]](https://sandbox.zenodo.org/account/settings/applications/tokens/new/)&nbsp;&nbsp;[[Zenodo"
                " token documentation]](https://developers.zenodo.org/#creating-a-personal-access-token)",
                unsafe_allow_html=True,
            )
            zenodo_metadata = get_study_metadata()
            cached_zenodo_info = get_zenodo_infos()

            existing_identifier = ""
            if "deposition_identifier" in cached_zenodo_info:
                existing_identifier = cached_zenodo_info["deposition_identifier"]
            if "doi" in zenodo_metadata and not existing_identifier:
                existing_identifier = zenodo_metadata["doi"]

            if st.checkbox("Use existing identifier", value=bool(existing_identifier)):
                new_deposition = False
                existing_identifier = st.text_input(
                    "Identifier (URL or DOI)", value=existing_identifier, on_change=self.ensure_submit_detection
                )
            else:
                new_deposition = True
                existing_identifier = ""

            if new_deposition:
                sandbox = st.checkbox('Publish in "Sandbox"', value=True)
            else:
                sandbox = bool(existing_identifier) and "sandbox" in existing_identifier

            col1, col2 = st.columns(2)
            if not sandbox:
                col2.markdown(
                    "**Not using Sandbox will submit to the main "
                    "Zenodo website. Please push content with caution "
                    "as it may result in a permanent entry**"
                )

            if "zenodo_publish" not in st.session_state:
                st.session_state.zenodo_publish = []

            if col1.button("Submit draft", type="primary"):
                st.session_state.zenodo_publish = []
                try:
                    self.upload(token, existing_identifier, sandbox=sandbox, new_deposition=new_deposition)
                except Exception as e:
                    self.global_message.error("upload error: " + str(e))

            st.markdown(
                "<span style='font-size:0.85em;'>Note: After sending a draft on Zenodo, the dataset can still be"
                ' modified until the "Publish" button is pressed on Zenodo. Metadata can always be modified, even'
                " after publication.</span>",
                unsafe_allow_html=True,
            )

            if st.session_state.zenodo_publish:
                url = get_existing_deposition_identifier(".")
                st.markdown(f"**Deposition url**: {url}")
                logger.info(st.session_state.zenodo_publish)
                st.code("\n".join(st.session_state.zenodo_publish).replace("[94m", "").replace("[0m", ""))

    def ensure_submit_detection(self):
        """Ensure that clicking on the submit button after editing a text field triggers the button.
        Bug seems to happen because of the st.empty call on the progress bar showing loading files."""

        time.sleep(DELAY_FIX_BUTTONS)

    def upload(self, access_token=None, existing_identifier=None, sandbox=True, new_deposition=False):
        import argparse

        import solidipes_core_plugin.uploaders.zenodo as zenodo_upload

        args = argparse.Namespace()
        args.access_token = access_token
        args.sandbox = sandbox
        args.directory = None
        args._print = self._print
        args.existing_identifier = existing_identifier
        args.new_deposition = new_deposition
        args.tmp_dir = "/tmp" if os.name != "nt" else os.path.expanduser(r"~\AppData\Local\Temp")
        args.no_cleanup = True
        zenodo_upload.main(args)
