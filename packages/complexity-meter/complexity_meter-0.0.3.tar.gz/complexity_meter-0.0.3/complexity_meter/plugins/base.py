import ast
import importlib.util
import logging
from pathlib import Path

from complexity_meter.structs import LogicalMetrics

logger = logging.getLogger(__name__)


class Plugin:
    def analyze(self, node: ast.AST, metrics: LogicalMetrics, file_path: Path):
        pass


class PluginLoader:
    def __init__(self, plugins_dir: Path):
        self.plugins = []
        self.load_plugins(plugins_dir)

    def load_plugins(self, plugins_dir: Path):
        for plugin_type in plugins_dir.iterdir():
            if not plugin_type.is_dir():
                continue

            for plugin_file in plugin_type.glob('*.py'):
                if plugin_file.name == '__init__.py':
                    continue

                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_type.name}.{plugin_file.stem}",
                    plugin_file
                )
                if not spec or not spec.loader:
                    continue

                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    plugin = module.register_plugin()
                    if isinstance(plugin, Plugin):
                        self.plugins.append(plugin)
                except Exception as e:
                    logger.warning(f"Plugin load error {plugin_file}: {e}")

    def analyze_node(self, node: ast.AST, metrics: LogicalMetrics, file_path: Path):
        for plugin in self.plugins:
            plugin.analyze(node, metrics, file_path)
