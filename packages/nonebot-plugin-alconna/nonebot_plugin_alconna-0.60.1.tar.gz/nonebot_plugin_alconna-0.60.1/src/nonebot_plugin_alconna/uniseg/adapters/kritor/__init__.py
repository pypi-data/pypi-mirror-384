from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.kritor

    def get_builder(self):
        from .builder import KritorMessageBuilder

        return KritorMessageBuilder()

    def get_exporter(self):
        from .exporter import KritorMessageExporter

        return KritorMessageExporter()

    def get_fetcher(self):
        from .target import KritorTargetFetcher

        return KritorTargetFetcher()
