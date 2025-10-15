from framework.core.plugin import BasePlugin, PluginInfo


class ExamplePlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="example_plugin",
            version="1.0.0",
            description="An example plugin loaded from file",
            author="Framework Team",
        )
        super().__init__(info)

    def _on_start(self):
        print(f"[{self.info.name}] Example plugin started!")
