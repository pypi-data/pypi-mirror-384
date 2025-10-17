import ast
from pathlib import Path
from dataclasses import dataclass
from complexity_meter.plugins.base import Plugin


@dataclass
class FastAPIPlugin(Plugin):
    def analyze(self, node: ast.AST, metrics, file_path: Path):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                decorator_name = self.get_decorator_name(decorator)
                if decorator_name in {'get', 'post', 'put', 'delete', 'patch'}:
                    metrics.api_endpoints += 1

    def get_decorator_name(self, decorator) -> str:
        if isinstance(decorator, ast.Attribute):
            return decorator.attr
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            return decorator.func.attr
        return ''


def register_plugin():
    return FastAPIPlugin()
