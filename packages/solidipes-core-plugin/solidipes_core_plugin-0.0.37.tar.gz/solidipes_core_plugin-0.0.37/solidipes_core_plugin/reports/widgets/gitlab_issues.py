#!/bin/env python
################################################################
import os

import gitlab
import streamlit as st
from solidipes.utils.git_infos import GitInfos

################################################################


class GitlabIssues:
    def __init__(self, layout):
        self.git_infos = GitInfos()
        self.layout = layout
        self.layout_container = layout.container()

        if "PROJECT_NAME" not in os.environ:
            split = self.git_infos.origin.split("/")
            project_name = split[-1]
            user_name = split[-2]
            repo_uri = self.git_infos.origin.split(user_name + "/" + project_name)[0]
            os.environ["REPO_URI"] = repo_uri
            os.environ["USER_NAME"] = user_name
            os.environ["PROJECT_NAME"] = project_name
        else:
            project_name = os.environ["PROJECT_NAME"]
            repo_uri_and_user_name = self.git_infos.origin.split("/" + project_name)[0]
            user_name = repo_uri_and_user_name.split("/")[-1]
            repo_uri = repo_uri_and_user_name.split("/" + user_name)[0]
            os.environ["USER_NAME"] = user_name
            os.environ["REPO_URI"] = repo_uri

        project_name = os.environ["PROJECT_NAME"]
        repo_uri = os.environ["REPO_URI"]
        gl = gitlab.Gitlab(repo_uri)
        try:
            self.project = gl.projects.get(user_name + "/" + project_name)
        except gitlab.GitlabGetError:
            self.project = None
        except Exception as err:
            print(err)
            self.project = None

    def show(self):
        if self.project is None:
            return

        issues = self.project.issues.list(state="opened")
        if len(issues) == 0:
            return
        opened_issues = 0
        for issue in issues:
            if issue.state == "open":
                opened_issues
            if len(issues) == 0:
                return

        self.layout_container.markdown("## Reviews & Issues")
        for issue in issues:
            with self.layout_container.expander(issue.title, expanded=True):
                col1, col2 = st.columns(2)

                col1.image(f"{issue.author['avatar_url']}")
                col2.markdown(f"### {issue.title}")
                col2.markdown(f"*Author: {issue.author['name']}*")
                st.markdown(issue.description)
                st.markdown("---")
                st.markdown(f"### :speech_balloon: &nbsp; &nbsp;[**Please reply to the requests**]({issue.web_url})")
