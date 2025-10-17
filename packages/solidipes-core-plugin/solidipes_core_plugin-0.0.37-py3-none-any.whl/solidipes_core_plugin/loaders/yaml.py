from .text import Text


class YAML(Text):
    supported_mime_types = {"application/yaml": ["yaml", "yml"], "text/plain": ["yaml", "yml"]}

    from ..viewers.xml import XML as XMLViewer

    _compatible_viewers = [XMLViewer]

    @Text.loadable
    def yaml(self):
        text = self.text
        import yaml as yaml_module

        yaml = yaml_module.safe_load(text)
        return yaml
