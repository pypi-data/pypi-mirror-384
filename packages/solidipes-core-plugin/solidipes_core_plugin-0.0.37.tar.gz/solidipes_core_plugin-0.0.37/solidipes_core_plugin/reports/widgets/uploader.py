#!/bin/env python
################################################################
import os
from abc import ABC, abstractmethod

import streamlit as st
import yaml
from solidipes.scanners.scanner import list_files
from solidipes.scanners.scanner_local import ExportScanner
from solidipes.utils import get_study_metadata, logging, set_study_metadata

# from solidipes.utils import get_study_metadata, logging, set_study_metadata
from solidipes.utils.git_infos import GitInfos
from solidipes.utils.metadata import lang
from solidipes.utils.metadata import licences_data_or_software as licenses
from solidipes.utils.utils import get_study_root_path
from streamlit_editable_list import editable_list

from solidipes_core_plugin.reports.widgets.file_list import FileList

from .custom_widgets import EditProgBox, EditTextBox

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class DatasetInfos(ABC):
    def __init__(self, layout):
        self.git_infos = GitInfos()
        self.layout = layout.container()
        self.repo_metadata = get_study_metadata()

        self.key = "repo_infos"

    def saveRepoEntry(self, key, value):
        self.repo_metadata[key] = value
        set_study_metadata(self.repo_metadata)

    def save_description(self, value):
        self.repo_metadata["description"] = value
        set_study_metadata(self.repo_metadata)

    def show_edit_button(self):
        st.button("Edit metadata :pencil:", on_click=lambda: setattr(self, "edit_mode", True))

    def show_title(self):
        st.markdown(f"## <center> {self.repo_metadata['title']} </center>", unsafe_allow_html=True)

    def edit_title(self):
        st.subheader("Title")
        title = st.text_input("", self.repo_metadata["title"], key=f"title_{self.key}", label_visibility="collapsed")

        if self.must_save:
            self.saveRepoEntry("title", title)

    def _create_stateful_property(self, property_key):
        streamlit_key_template = property_key + "_{self.key}"

        def getter(self):
            streamlit_key = streamlit_key_template.format(self=self)
            return getattr(st.session_state, streamlit_key, False)

        def setter(self, value):
            streamlit_key = streamlit_key_template.format(self=self)
            st.session_state[streamlit_key] = value

        return property(getter, setter)

    edit_mode = _create_stateful_property(None, "edit_mode")
    must_save = _create_stateful_property(None, "must_save")

    def format_authors(self, authors_data):
        orcid_img = (
            '<svg fill="#a6ce39" width="24px" height="24px" viewBox="0 0 32 32"><path d="M 16 3 C 8.8321388 3 3'
            " 8.832144 3 16 C 3 23.167856 8.8321388 29 16 29 C 23.167861 29 29 23.167856 29 16 C 29 8.832144 23.167861"
            " 3 16 3 z M 16 5 C 22.086982 5 27 9.9130223 27 16 C 27 22.086978 22.086982 27 16 27 C 9.9130183 27 5"
            " 22.086978 5 16 C 5 9.9130223 9.9130183 5 16 5 z M 11 8 A 1 1 0 0 0 11 10 A 1 1 0 0 0 11 8 z M 10 11 L 10"
            " 22 L 12 22 L 12 11 L 10 11 z M 14 11 L 14 12 L 14 22 L 18.5 22 C 21.525577 22 24 19.525577 24 16.5 C 24"
            " 13.474423 21.525577 11 18.5 11 L 14 11 z M 16 13 L 18.5 13 C 20.444423 13 22 14.555577 22 16.5 C 22"
            ' 18.444423 20.444423 20 18.5 20 L 16 20 L 16 13 z"/></svg>'
        )
        authors = []
        affiliations = []
        for auth in authors_data:
            if "affiliation" in auth:
                aff = auth["affiliation"].split(";")
                for e in aff:
                    if e.strip() not in affiliations:
                        affiliations.append(e.strip())

        for auth in authors_data:
            text = ""
            if "orcid" in auth:
                text += f'<a href="https://orcid.org/{auth["orcid"]}">{orcid_img}</a> '
            if "name" in auth:
                text += f"**{auth['name']}**"
            if "affiliation" in auth:
                text += "$^{"
                aff = auth["affiliation"].split(";")
                aff = [affiliations.index(e.strip()) + 1 for e in aff]
                aff = [str(e) for e in aff]
                text += f"{','.join(aff)}"
                text += "}$"

            authors.append(text)
        formatted = "**<center> " + ", ".join(authors) + " </center>**\n"
        for idx, aff in enumerate(affiliations):
            formatted += f"<center><sup>{idx + 1}</sup> <i>{aff}</i></center>\n"
        return formatted

    def format_keywords(self, keywords):
        return "<b>Keywords:</b> " + ", ".join(keywords)

    def show_keywords(self):
        st.markdown(self.format_keywords(self.repo_metadata["keywords"]), unsafe_allow_html=True)

    def edit_keywords(self):
        keywords_data = [[k] for k in self.repo_metadata["keywords"]]

        input_params = [
            {
                "placeholder": "Keyword",
                "type": "text",
                "value": "",
            },
        ]

        st.subheader("Keywords")
        keywords_data = editable_list(keywords_data, input_params, auto_save=True, key=f"keywords_{self.key}")
        keywords = [k[0] for k in keywords_data]

        if self.must_save:
            self.saveRepoEntry("keywords", keywords)

    def show_creators(self):
        st.markdown(self.format_authors(self.repo_metadata["creators"]), unsafe_allow_html=True)

    def edit_creators(self):
        creators_data = [
            [
                a.get("name", ""),
                a.get("affiliation", ""),
                a.get("orcid", ""),
            ]
            for a in self.repo_metadata["creators"]
        ]

        input_params = [
            {
                "placeholder": "Name",
                "type": "text",
                "value": "",
            },
            {
                "placeholder": "Affiliations, separated by ;",
                "type": "text",
                "value": "",
            },
            {
                "placeholder": "ORCID",
                "type": "text",
                "value": "",
            },
        ]

        st.subheader("Authors")
        creators_data = editable_list(creators_data, input_params, auto_save=True, key=f"creators_{self.key}")
        if not self.must_save:
            return

        creators = []
        for creator in creators_data:
            creator_dict = {}
            creator_dict["name"] = creator[0]
            if creator[1] != "":
                creator_dict["affiliation"] = creator[1]
            if creator[2] != "":
                creator_dict["orcid"] = creator[2]
            creators.append(creator_dict)

        for e in creators:
            if e["name"] == "":
                raise RuntimeError("An author needs mandatorily a name")

        self.saveRepoEntry("creators", creators)

    def show_general_metadata(self):
        entries = [
            f"**Upload type**: {self.repo_metadata['upload_type']}",
            f"**License**: {self.repo_metadata['license']}",
            f"**Language**: {self.repo_metadata['language']}",
        ]
        if "doi" in self.repo_metadata:
            entries.append(f"**DOI**: {self.repo_metadata['doi']}")
        st.markdown("  \n".join(entries))

    def edit_general_metadata(self):
        st.subheader("General Metadata")
        upload_type = self.edit_upload_type()
        license = self.edit_license()
        language = self.edit_language()
        doi = self.edit_doi()

        if not self.must_save:
            return

        if doi != "":
            self.saveRepoEntry("doi", doi)
        elif "doi" in self.repo_metadata:
            del self.repo_metadata["doi"]
        self.saveRepoEntry("upload_type", upload_type)
        self.saveRepoEntry("license", license)
        self.saveRepoEntry("language", language)

    def edit_upload_type(self):
        options = [
            "publication",
            "poster",
            "presentation",
            "dataset",
            "image",
            "video",
            "software",
            "lesson",
            "physicalobject",
            "text",
            "sound",
            "eventother",
        ]
        value = self.repo_metadata["upload_type"]
        return st.selectbox("Upload type", options=options, index=options.index(value))

    def edit_license(self):
        options = [_l[0] for _l in licenses]
        fmt_map = dict(licenses)

        value = self.repo_metadata["license"]
        return st.selectbox(
            "License", options=options, index=options.index(value), format_func=lambda x: fmt_map[x] + f" ({x})"
        )

    def edit_language(self):
        options = [_l[0] for _l in lang]
        fmt_map = dict(lang)

        value = self.repo_metadata["language"]
        return st.selectbox("Language", options=options, index=options.index(value), format_func=lambda x: fmt_map[x])

    def edit_doi(self):
        value = ""
        if "doi" in self.repo_metadata:
            value = self.repo_metadata["doi"]

        return st.text_input("DOI", value=value, placeholder="put a reserved doi if you have one")

    def show_related_identifiers(self):
        rels_dicts = self.repo_metadata.get("related_identifiers", [])
        if len(rels_dicts) == 0:
            return

        formatted = "**Related Identifiers**  \n"

        for r in rels_dicts:
            formatted += f"- {r['relation']} {r['identifier']} ({r['resource_type']})\n"

        st.markdown(formatted)

    def edit_related_identifiers(self):
        rels_dicts = self.repo_metadata.get("related_identifiers", [])
        rels_lists = [
            [
                r["relation"],
                r["resource_type"],
                r["identifier"],
            ]
            for r in rels_dicts
        ]

        input_params = [
            {
                "placeholder": "Relation",
                "list": "relations",
                "value": "",
                "options": [
                    "isCitedBy",
                    "cites",
                    "isSupplementTo",
                    "isSupplementedBy",
                    "isContinuedBy",
                    "continues",
                    "isDescribedBy",
                    "describes",
                    "hasMetadata",
                    "isMetadataFor",
                    "isNewVersionOf",
                    "isPreviousVersionOf",
                    "isPartOf",
                    "hasPart",
                    "isReferencedBy",
                    "references",
                    "isDocumentedBy",
                    "documents",
                    "isCompiledBy",
                    "compiles",
                    "isVariantFormOf",
                    "isOriginalFormof",
                    "isIdenticalTo",
                    "isAlternateIdentifier",
                    "isReviewedBy",
                    "reviews",
                    "isDerivedFrom",
                    "isSourceOf",
                    "requires",
                    "isRequiredBy",
                    "isObsoletedBy",
                    "obsolete",
                ],
            },
            {
                "placeholder": "Type",
                "list": "resource_types",
                "value": "",
                "options": [
                    "publication-annotationcollection",
                    "publication-book",
                    "publication-section",
                    "publication-conferencepaper",
                    "publication-datamanagementplan",
                    "publication-article",
                    "publication-patent",
                    "publication-preprint",
                    "publication-deliverable",
                    "publication-milestone",
                    "publication-proposal",
                    "publication-report",
                    "publication-softwaredocumentation",
                    "publication-taxonomictreatment",
                    "publication-technicalnote",
                    "publication-thesis",
                    "publication-workingpaper",
                    "publication-other",
                    "software",
                ],
            },
            {
                "placeholder": "Identifier",
                "type": "text",
                "value": "",
            },
        ]

        st.subheader("Additional Relations")
        rels_lists = editable_list(rels_lists, input_params, auto_save=True, key=f"related_identifiers_{self.key}")
        if not self.must_save:
            return

        rels_dicts = [
            {
                "relation": r[0],
                "resource_type": r[1],
                "identifier": r[2],
            }
            for r in rels_lists
        ]
        self.saveRepoEntry("related_identifiers", rels_dicts)

    def textbox(self, key, **kwargs):
        EditTextBox(self.repo_metadata[key], caption=key.capitalize(), key=key, **kwargs)

    def description_box(self, **kwargs):
        desc = self.repo_metadata["description"]
        with st.expander("**Description**", expanded=True):
            EditProgBox(desc, language="markdown", key="description", on_apply=self.save_description, **kwargs)

    def show(self):
        with self.layout:
            # Must show editable form temporarily to save new metadata
            erasable = st.empty()
            with erasable:
                self.show_editable()

            if not self.edit_mode:
                erasable.empty()
                self.show_formatted()

            self.description_box()
            self.raw_editor()

    def show_formatted(self):
        self.show_edit_button()
        self.show_title()
        self.show_creators()
        self.show_keywords()
        self.show_general_metadata()
        self.show_related_identifiers()

    def show_editable(self):
        with st.form(f"form_{self.key}"):
            self.edit_title()
            self.edit_creators()
            self.edit_keywords()
            self.edit_general_metadata()
            self.edit_related_identifiers()
            self.must_save = False
            st.form_submit_button("Save", on_click=self.close_editable, type="primary")

    def close_editable(self):
        self.edit_mode = False
        self.must_save = True

    def raw_editor(self):
        with self.layout.expander("**Additional Raw Metadata** (Zenodo YAML format)", expanded=False):
            st.markdown("You can edit the metadata below")
            st.markdown(
                "*Description of the Zenodo metadata can be found"
                " [here](https://github.com/zenodo/developers.zenodo.org"
                "/blob/master/source/includes/resources/deposit/"
                "_representation.md#deposit-metadata)*"
            )
            st.markdown("---")

            repo_metadata = get_study_metadata()
            metadata = repo_metadata.copy()

            for k in [
                "title",
                "creators",
                "keywords",
                "language",
                "upload_type",
                "license",
                "description",
                "related_identifiers",
            ]:
                if k in metadata:
                    del metadata[k]
            if metadata:
                repo_content = yaml.safe_dump(metadata)
            else:
                repo_content = ""

            def save(x):
                metadata = yaml.safe_load(x)
                repo_metadata.update(metadata)
                set_study_metadata(repo_metadata)

            EditProgBox(repo_content, language="yaml", disable_view=True, on_apply=lambda x: save(x), key="repo_raw")


################################################################


class UploaderWidget(ABC):
    def __init__(self, layout, global_message, progress_layout):
        self.layout = layout
        self.layout = layout.container()
        self.global_message = global_message
        self.progress_layout = progress_layout

    def show(self):
        self.layout.markdown("")
        self.show_submission_panel()
        self.show_file_list()
        self.show_readme()

    def _print(self, val):
        logger.info(val)
        if "zenodo_publish" not in st.session_state:
            st.session_state.zenodo_publish = []
        st.session_state.zenodo_publish.append(val)

    @abstractmethod
    def show_submission_panel(self):
        pass

    @abstractmethod
    def upload(self, **kwargs):
        pass

    def show_file_list(self):
        self.layout.markdown("# Archive content")
        scanner = ExportScanner()
        progress_layout = self.layout.empty()
        files_layout = self.layout.container()

        found = scanner.get_loader_tree()
        files = list_files(found)

        with files_layout:
            FileList(
                all_found_files=files,
                progress_layout=progress_layout,
                show_curation_cols=False,
            )
        from solidipes_core_plugin.reports.widgets.ignore import IgnoreWidget

        IgnoreWidget(layout=self.layout)

    def show_readme(self):
        with self.layout.expander("Preview of `README.md`", expanded=True):
            readme_path = os.path.join(get_study_root_path(), "README.md")

            if not os.path.isfile(readme_path):
                st.markdown("No README.md file found!")
                return

            readme = open(readme_path, "r").read()
            st.markdown(readme)


################################################################
