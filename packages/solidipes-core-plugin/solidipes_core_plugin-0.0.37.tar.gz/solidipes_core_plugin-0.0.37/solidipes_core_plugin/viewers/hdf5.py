import h5py
import matplotlib.pyplot as plt
import streamlit as st
from IPython.display import display
from solidipes.viewers import backends as viewer_backends
from solidipes.viewers.viewer import Viewer
from streamlit_tree_select import tree_select


def scan_hdf5_recursively(f):
    res = {"label": f.name}
    res["value"] = f.name

    if isinstance(f, h5py.Dataset):
        return res, [f.name]

    res["children"] = []
    labs = [f.name]
    for k, v in f.items():
        _nd, lab = scan_hdf5_recursively(v)
        res["children"].append(_nd)
        labs += lab
    return res, labs


class HDF5(Viewer):
    """Viewer for HDf5"""

    def __init__(self, data=None):
        #: Image to display
        self.datasets = None
        super().__init__(data)

    def add(self, data_container):
        """Replace the viewer's hdf5"""
        self.check_data_compatibility(data_container)
        self.datasets = data_container.datasets

    def show(self):
        if viewer_backends.current_backend == "jupyter notebook":
            display(self.datasets)

        elif viewer_backends.current_backend == "streamlit":
            col1, col2 = st.columns(2)
            nodes, labels = scan_hdf5_recursively(self.datasets)
            nodes = [nodes]
            # st.write(nodes)
            with col1:
                return_select = tree_select(
                    nodes,
                    check_model="leaf",
                    no_cascade=True,
                    expand_on_click=True,
                    only_leaf_checkboxes=True,
                    expanded=labels,
                )
            with col2:
                for e in return_select["checked"]:
                    d = self.datasets[e]
                    st.markdown(f"### {e} ({type(d).__name__})")
                    try:
                        st.markdown(f"Shape: {d.shape}")
                    except Exception:
                        pass
                    if len(d.shape) == 2 and d.shape[0] > 30 and d.shape[1] > 30:
                        div = [d.shape[i] // 2000 for i in range(len(d.shape))]
                        fig, ax = plt.subplots()
                        filtered = d[:: div[0], :: div[1]]
                        ax.imshow(filtered)
                        st.pyplot(fig)
                    elif len(d.shape) == 1:
                        div = d.shape[0] // 2000
                        if div == 0:
                            div = 1
                        fig, ax = plt.subplots()
                        filtered = d[::div]
                        ax.plot(filtered, "-o")
                        ax.set_xlabel("index")
                        st.pyplot(fig)
                    else:
                        slices = [slice(0, min(20, d.shape[i]), 1) for i in range(len(d.shape))]
                        st.dataframe(d.__getitem__(*slices))

        else:  # python
            print(self.datasets)
