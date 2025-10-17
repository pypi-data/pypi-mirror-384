import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from IPython.display import display
from solidipes.loaders.data_container import DataContainer
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer, wrap_errors


class Table(Viewer):
    """Viewer for tables"""

    def __init__(self, data_container=None):
        #: Table to display
        self.data_container = None
        super().__init__(data_container)

    def add(self, data_container):
        """Replace the viewer's table"""
        self.check_data_compatibility(data_container)

        if isinstance(data_container, DataContainer):
            self.data_container = data_container

    def show_plot(self):
        if self.data_container is None:
            raise Exception("No data to show")

        table = self.data_container.table
        cols = table.columns
        colsX = [c for c in cols] + ["Row"]
        defaultX = 0
        if len(cols) == 1:
            defaultX = 1

        c1, c2 = st.columns(2)
        marker = None
        line = "-"

        with c1:
            tab_col_select, tab_advanced = st.tabs(["Column selection", "Advanced"])
            with tab_col_select:
                xaxis = st.radio(
                    "X-axis",
                    options=colsX,
                    index=defaultX,
                    horizontal=True,
                    key="xaxis_" + self.data_container.file_info.path,
                )
                yaxis = st.multiselect(
                    "Y-axis",
                    options=cols,
                    default=[c for c in cols if c != xaxis],
                    key="yaxis_" + self.data_container.file_info.path,
                )

            with tab_advanced:
                marker = st.text_input(
                    "Point marker",
                    value="o",
                    key="marker_" + self.data_container.file_info.path,
                )
                line = st.text_input(
                    "Line style",
                    value="-",
                    key="line_" + self.data_container.file_info.path,
                )

        if marker == "":
            marker = None
        if line == "":
            line = "None"

        fig = plt.figure(figsize=(7, 5))
        axe = fig.add_subplot(111)
        if xaxis != "Row" and not np.issubdtype(table[xaxis].dtype, np.number):
            st.warning(f"Cannot plot '{xaxis}' as it is of type {table[xaxis].dtype} which is not a number")
            return

        for y in yaxis:
            if not np.issubdtype(table[y].dtype, np.number):
                st.warning(f"Cannot plot '{y}' as it is of type {table[y].dtype} which is not a number")
                continue

            if xaxis == "Row":
                axe.plot(
                    table[y],
                    label=y,
                    marker=marker,
                    linestyle=line,
                )
            else:
                axe.plot(
                    table[xaxis],
                    table[y],
                    label=y,
                    marker=marker,
                    linestyle=line,
                )
        axe.set_xlabel(xaxis)
        axe.legend(loc="best")
        with c2:
            st.pyplot(fig)

    @wrap_errors
    def show(self):
        if self.data_container is None:
            raise Exception("No data to show")

        if viewer_backends.current_backend == "jupyter notebook":
            display(self.data_container.table)

        elif viewer_backends.current_backend == "streamlit":
            if self.data_container.table.shape[1] < 50:
                tab_figure, tab_raw = st.tabs(["Figure", "Raw Data"])
                with tab_figure:
                    try:
                        self.show_plot()
                    except Exception as e:
                        st.error(e)
                        st.exception(e)
                with tab_raw:
                    st.dataframe(self.data_container.table.style.format("{:e}"))
            else:
                st.dataframe(self.data_container.table.iloc[:20])
                if self.data_container.table.shape[0] > 20:
                    st.write("Truncated the long file...")

        else:  # python
            print(self.data_container.table)
