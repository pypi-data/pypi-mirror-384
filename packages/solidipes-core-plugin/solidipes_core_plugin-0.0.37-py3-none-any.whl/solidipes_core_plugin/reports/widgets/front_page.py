from solidipes.utils import get_study_metadata

from .solidipes_buttons import SolidipesButtons as SPB
from .solidipes_logo_widget import SolidipesLogoWidget as SPLW


################################################################
def side_bar(layout=None):
    zenodo_metadata = get_study_metadata()
    authors_data = zenodo_metadata["creators"]
    import streamlit as st

    if layout is None:
        layout = st.sidebar

    layout.write(
        f"""
    ### *{zenodo_metadata["title"]}*

    ####
    """,
        unsafe_allow_html=True,
    )

    orcid_img = '<img height="15" src="https://zenodo.org/static/images/orcid.svg">'
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

        authors.append(text)
    formatted = "**<center> " + ", ".join(authors) + " </center>**\n"
    layout.markdown(formatted, unsafe_allow_html=True)

    url = st.context.url

    params = [k + "=" + v for k, v in st.query_params.items()]
    params = "&".join(params)
    if params:
        url += "?" + params

    layout.markdown(f"<hr> 🔗<a href={url}> Link to this curation</a><br><br>", unsafe_allow_html=True)
    layout.code(url, language="html")


class FrontPage(SPLW):
    def __init__(self, **kwargs):
        from solidipes.utils import get_completed_stages

        side_bar()
        super().__init__(
            title="""
        <center>

# Welcome to the Solidipes Curation Tool!""",
            width="15%",
            **kwargs,
        )

        steps = [
            {
                "name": "acquisition",
                "description": (
                    "Upload any files relevant to your paper, and browse them like you would in a file browser."
                ),
            },
            {
                "name": "curation",
                "description": (
                    "Automatically verify the correct formatting of your files, review their contents, and discuss"
                    " potential issues."
                ),
            },
            {
                "name": "metadata",
                "description": (
                    "Easily edit any metadata relevant to your paper such as authors, keywords, description, and more."
                ),
            },
            {
                "name": "export",
                "description": (
                    "Once all previous steps are complete, review your work and export it to databases such as Zenodo."
                ),
            },
        ]
        completed_stages = get_completed_stages()
        incomplete_stages = set(range(len(steps))) - set(completed_stages)
        last_stage = min(incomplete_stages)

        buttons_custom_style = {
            "grid-column": 1,
            "width": "100%",
        }

        html = """
<style>
    .steps-container {
        align-items: center;
        gap: 1rem;
        grid-template-columns: 9rem 1fr;
        max-width: 55rem;
    }

    .steps-text {
        grid-column: 2;
        margin-bottom: 1rem;
        text-align: left;
    }

    @media all and (min-width: 680px) {
        .steps-container {
            display: grid;
        }

        .steps-text {
            margin-bottom: 0;
        }
    }
</style>
<center>
    <h3 style="margin-bottom: 1rem;">Here, you can prepare your paper’s data for publication in four steps:</h3>

    <div class="steps-container">
        """

        for i, step in enumerate(steps):
            name = step["name"].capitalize()
            if i in completed_stages:
                name = f"✔️ {name} &nbsp;"

            html += SPB()._html_link_button(
                name,
                f"?page={step['name']}",
                type="primary" if i == last_stage else "secondary",
                custom_style=buttons_custom_style,
            )
            html += f'<div class="steps-text">{step["description"]}</div>'

        html += """
    </div>
</center>
        """

        self.layout.html(html)
