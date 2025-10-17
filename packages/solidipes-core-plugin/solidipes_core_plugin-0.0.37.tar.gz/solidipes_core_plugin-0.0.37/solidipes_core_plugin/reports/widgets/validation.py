"""Widget to display validations on a DataContainer. Must be lazy-loaded to avoid loading Streamlit."""

import time
from typing import Union
from uuid import uuid4

import pandas as pd
import streamlit as st  # Cannot lazy import because of st.fragment decorator
from solidipes.loaders.data_container import DataContainer
from solidipes.validators.global_validation import DatasetProxy

from solidipes_core_plugin.reports.widgets.solidipes_widget import SolidipesWidget

VALIDATION_RELOAD_SLEEP_TIME = 1.5


class ValidationWidget(SolidipesWidget):
    def __init__(
        self,
        data_container: Union[DataContainer, DatasetProxy],
        **kwargs,
    ):
        super().__init__(**kwargs)
        if self.layout is st:
            self.layout = st.container()
        self.data_container = data_container

        with self.layout:
            self.display()

    @st.fragment
    def display(self):
        title = ":white_check_mark:" if self.data_container.is_valid else ":no_entry_sign:"
        title += " Validations"

        with st.expander(title, expanded=(not self.data_container.is_valid or len(self.data_container.errors) > 0)):
            self.display_validations()

    def display_validations(self):
        data = []
        for validation_result in self.data_container.validation_results:
            validator = validation_result.validator
            data.append({
                "name": validator.name,
                "enabled": self.data_container.validator_enabled[validator.name],
                "mandatory": validator.mandatory,
                "description": validator.description,
                "valid": validation_result.valid,
                "manually_settable": validator.manually_settable,
                "errors": "\n\n".join(validation_result.errors),
            })
        df = pd.DataFrame(data)

        if "validations_editor_key" not in st.session_state:
            st.session_state["validations_editor_key"] = uuid4()

        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_order=["enabled", "mandatory", "description", "valid", "manually_settable", "errors"],
            column_config={
                "enabled": st.column_config.CheckboxColumn("Enabled", required=False),
                "mandatory": "Mandatory",
                "description": "Description",
                "valid": "Valid",
                "manually_settable": "Manually settable",
                "errors": "Errors (double-click to expand)",
            },
            disabled=df.columns[2:],
            key=st.session_state["validations_editor_key"],
        )

        edited_lines = edited_df[df["enabled"] != edited_df["enabled"]]
        for i, row in edited_lines.iterrows():
            if row["enabled"]:
                self.data_container.enable_validator(row["name"])
                st.rerun(scope="fragment")

            else:
                try:
                    self.data_container.disable_validator(row["name"])

                except ValueError:
                    st.error(f'Cannot disable mandatory validator "{row["description"]}"')
                    st.session_state["validations_editor_key"] = uuid4()  # Force reload of data_editor
                    time.sleep(VALIDATION_RELOAD_SLEEP_TIME)

                finally:
                    st.rerun(scope="fragment")
