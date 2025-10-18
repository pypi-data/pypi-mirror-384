from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.mirai

    def get_builder(self):
        from .builder import MiraiMessageBuilder

        return MiraiMessageBuilder()

    def get_exporter(self):
        from .exporter import MiraiMessageExporter

        return MiraiMessageExporter()

    def get_fetcher(self):
        from .target import MiraiTargetFetcher

        return MiraiTargetFetcher()
