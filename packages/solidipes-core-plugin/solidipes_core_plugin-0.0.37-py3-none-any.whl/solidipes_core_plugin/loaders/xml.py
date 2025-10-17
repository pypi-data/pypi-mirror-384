import xmltodict

from .text import Text


class XML(Text):
    supported_mime_types = {"text/xml": "xml", "application/xml": "xml", "application/paraview/state": "xml"}

    from ..viewers.xml import XML as XMLViewer

    _compatible_viewers = [XMLViewer]

    @Text.loadable
    def xml(self):
        text = self.text
        xml = xmltodict.parse(text)
        return xml
