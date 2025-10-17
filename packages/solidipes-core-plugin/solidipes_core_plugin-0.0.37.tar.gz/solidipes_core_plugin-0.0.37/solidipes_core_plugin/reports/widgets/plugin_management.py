import time

import pandas as pd
import solidipes as sp
import streamlit as st
from solidipes.plugins.management import get_installed_plugins_info, install_plugin, remove_plugin, reset_plugins

SUCESS_SLEEP_TIME = 2


@st.dialog("Plugin Management", width="large")
def open_plugin_dialog():
    st.write("## Installed plugins")

    plugin_info = get_installed_plugins_info()
    df = pd.DataFrame(plugin_info)
    df.insert(0, "selected", False)
    df_selected = st.data_editor(
        df,
        hide_index=True,
        column_order=["selected", "package", "loaded", "version", "url", "editable"],
        column_config={
            "selected": st.column_config.CheckboxColumn("Select", required=True),
            "package": "Name",
            "loaded": "Version (memory)",
            "version": "Version (disk)",
            "url": "URL",
            "editable": "Editable",
        },
        disabled=df.columns[1:],
    )
    df_selected = df_selected[df_selected["selected"]]

    if len(df_selected) == 0:
        st.write("To update or remove plugins, select them using the leftmost column.")

    else:
        if st.checkbox("Use custom Python Package Index URL", key="custom_index_url_update"):
            index_url = st.text_input("Index URL (optional)")
        else:
            index_url = None

        col1, col2 = st.columns(2)

        if col1.button("Update selected plugins", type="primary", use_container_width=True):
            any_success = False

            for plugin_url, editable in zip(df_selected["url"], df_selected["editable"]):
                success = False
                with st.spinner(f"Installing {plugin_url}"):
                    try:
                        install_plugin(plugin_url, index_url=index_url, editable=editable, update=True)
                        success = True
                        any_success = True
                    except Exception as e:
                        st.error(e)

                if success:
                    st.success(f"Plugin {plugin_url} installed successfully!")

            if any_success:
                st.success("Reloading...")
                time.sleep(SUCESS_SLEEP_TIME)
                sp.close_cached_metadata()
                st.rerun()

        elif col2.button("Remove selected plugins", type="primary", use_container_width=True):
            any_success = False

            for package_name in df_selected["package"]:
                success = False
                with st.spinner(f"Removing {package_name}"):
                    try:
                        remove_plugin(package_name)
                        success = True
                        any_success = True
                    except Exception as e:
                        st.error(e)

                if success:
                    st.success(f"Plugin {package_name} removed successfully!")

            if any_success:
                st.success("Reloading...")
                time.sleep(SUCESS_SLEEP_TIME)
                sp.close_cached_metadata()
                st.rerun()

    if st.button("Reload all plugins", type="primary"):
        versions = reset_plugins()
        st.success("Reloading...")
        st.write(versions)
        time.sleep(SUCESS_SLEEP_TIME)
        st.rerun()

    st.write("## Install plugin")
    with st.expander("Show"):
        plugin_url = st.text_input("Plugin name, path, or URL (git+https://...)")

        if st.checkbox("Use custom Python Package Index URL", key="custom_index_url_install"):
            index_url = st.text_input("Index URL (optional)")
        else:
            index_url = None

        editable = st.checkbox("Editable mode (for local development)")
        if st.button("Install", type="primary"):
            if not plugin_url:
                st.error("Please provide a plugin name, path, or URL.")
                return

            success = False
            with st.spinner(f"Installing {plugin_url}"):
                try:
                    install_plugin(plugin_url, index_url=index_url, editable=editable)
                    success = True
                except Exception as e:
                    st.error(e)

            if success:
                st.success(f"Plugin {plugin_url} installed successfully! Reloading...")
                time.sleep(SUCESS_SLEEP_TIME)
                sp.close_cached_metadata()
                st.rerun()
