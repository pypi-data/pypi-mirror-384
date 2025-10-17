import os

import streamlit as st
from solidipes.utils import get_git_repository, get_git_root, get_study_metadata, logging
from solidipes.utils.git_infos import GitInfos

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class GIT:
    def __init__(self, container=None):
        # to repair
        # if self.git_infos.repository is not None:
        #    self._git_info()

        if container is None:
            container = st
        self.container = container
        self.git_infos = GitInfos()

        changed_files = self.git_get_changed_files()
        if changed_files:
            self.container.button(
                "Dataset in a modified state: Push Modifications ?",
                on_click=self.git_push,
                type="primary",
                use_container_width=True,
            )
        else:
            self.container.empty()

    def git_get_changed_files(self):
        changed_files = []
        if self.git_infos.repository:
            changed_files = [item.a_path for item in self.git_infos.repository.index.diff(None)]
        return changed_files

    def git_push(self):
        import subprocess

        import git

        save_cwd = os.getcwd()
        try:
            os.chdir(get_git_root())
            changed_files = self.git_get_changed_files()
            # changed_files = [os.path.relpath(e, os.getcwd()) for e in changed_files]
            for e in changed_files:
                ret = self.git_infos.repository.git.add(e)
            if ret != "":
                logger.info(ret)

            ret = self.git_infos.repository.git.commit('-m "Automatic update from solidipes interface"')
            if ret != "":
                logger.info(ret)

        except git.GitCommandError as err:
            logger.error(err)
            os.chdir(save_cwd)
            return

        os.chdir(save_cwd)

        p = subprocess.Popen(
            "renku dataset update --delete -c --all --no-remote",
            shell=True,
            stdout=subprocess.PIPE,
        )
        p.wait()
        out, err = p.communicate()

        if not p.returncode == 0:
            self.global_message.error("renku update failed")
            if out is not None:
                self.global_message.error(out.decode())
            if err is not None:
                self.global_message.error(err.decode())
        else:
            logger.info(out.decode())

        try:
            origin = self.git_infos.repository.remotes.origin
            origin.push("master")

        except git.GitCommandError as err:
            logger.error(err)
            return

        logger.success("Update repository complete")

        # self.clear_session_state()

    def _git_info(self):
        with self.git_control.container():
            changed_files = self.git_get_changed_files()
            changed_files = [e for e in changed_files if not e.startswith(".solidipes/cloud/")]
            if changed_files:
                with st.expander("Modified Files", expanded=False):
                    for p in changed_files:
                        st.markdown(f"- {p}")

                    st.button(
                        "Revert Modifications",
                        type="primary",
                        use_container_width=True,
                        on_click=self.git_revert,
                    )

    def git_revert(self):
        repo = get_git_repository()
        ret = repo.git.reset("--hard")
        logger.info("git revert", ret)
        logger.info("git revert", type(ret))
        logger.info("git revert return", ret)
        logger.info("git revert", ret)
        logger.info("git revert", type(ret))
        logger.info("git revert return", ret)
        zenodo_metadata = get_study_metadata()
        import yaml

        zenodo_content = yaml.safe_dump(zenodo_metadata)
        st.session_state["zenodo_metadata_editor"] = zenodo_content
        logger.info(
            "st.session_state['zenodo_metadata_editor']",
            st.session_state["zenodo_metadata_editor"],
        )
        st.session_state["rewrote_zenodo_content"] = True
        # self.clear_session_state()
