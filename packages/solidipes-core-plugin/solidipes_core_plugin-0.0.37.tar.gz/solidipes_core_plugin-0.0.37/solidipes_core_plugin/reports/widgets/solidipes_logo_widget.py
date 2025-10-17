from .plugin_management import open_plugin_dialog
from .solidipes_widget import SolidipesWidget as SPW

################################################################


class SolidipesLogoWidget(SPW):
    def __init__(self, short=False, **kwargs):
        super().__init__(**kwargs)
        if short:
            self.short(**kwargs)
        else:
            self.long(**kwargs)

    def long(self, title=None, width="30%", **kwargs):
        if self.layout.button("⚙ Manage plugins"):
            open_plugin_dialog()
        if title is None:
            title = "*Powered by* **Solidipes**"
        self.layout.markdown(title, unsafe_allow_html=True)
        self.layout.markdown(
            f'<center><img src="https://gitlab.com/solidipes/solidipes/-/raw/main/logos/solidipes.png" width="{width}"'
            ' style="border-radius:50%;" /><br><a style="font-size: 13px;"'
            ' href="https://gitlab.com/solidipes/solidipes">https://gitlab.com/solidipes/solidipes</a></center>',
            unsafe_allow_html=True,
        )
        self.layout.markdown(
            '<p style="font-size: 10px"><center><em>Software funded by</em> <img width="100px"'
            ' src="https://ethrat.ch/wp-content/uploads/2021/12/ethr_en_rgb_black.svg"'
            ' style="filter:invert(1);mix-blend-mode:difference;"/>&nbsp;<a style="font-size: 10px"'
            ' href="https://ethrat.ch/en/">https://ethrat.ch/en/</a></center></p>',
            unsafe_allow_html=True,
        )

    def short(self, width="30%", **kwargs):
        self.layout.markdown(
            '<center><a href="https://gitlab.com/solidipes/solidipes"><em><strong>Solidipes</strong></em></a><br>'
            '<a href="./" target="_self"><img'
            f' src="https://gitlab.com/solidipes/solidipes/-/raw/main/logos/solidipes.png" width="{width}"'
            ' style="border-radius:50%;" /></a></center>',
            unsafe_allow_html=True,
        )
        self.layout.markdown(
            '<center><a style="font-size: 10px" href="https://ethrat.ch/en/"><img width="100px"'
            ' src="https://ethrat.ch/wp-content/uploads/2021/12/ethr_en_rgb_black.svg"'
            ' style="filter:invert(1);mix-blend-mode:difference;"/></a></center></p>',
            unsafe_allow_html=True,
        )
