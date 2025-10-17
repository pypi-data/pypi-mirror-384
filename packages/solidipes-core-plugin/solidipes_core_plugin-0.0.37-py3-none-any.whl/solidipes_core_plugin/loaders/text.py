from solidipes.loaders.file import File


class Text(File):
    """Text file, potentially formatted with markdown"""

    from ..viewers.text import Text as TextViewer

    supported_mime_types = {"text/plain": "txt", "application/lammps": ["in", "data"]}
    _compatible_viewers = [TextViewer]

    @File.loadable
    def text(self):
        text = ""
        with open(self.file_info.path, "r", encoding="utf-8") as f:
            text = f.read()
        return text


class Markdown(Text):
    """Markdown file"""

    from ..viewers.text import Markdown as MarkdownViewer

    supported_mime_types = {"text/markdown": "md"}
    _compatible_viewers = [MarkdownViewer]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
