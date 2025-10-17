import ast
from pathlib import Path
from dataclasses import dataclass
from complexity_meter.plugins.base import Plugin


@dataclass
class FastStreamPlugin(Plugin):
    def analyze(self, node: ast.AST, metrics, file_path: Path):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == 'subscriber':
                        metrics.event_subscriptions += 1
                    if decorator.func.attr == 'timer':
                        metrics.periodic_tasks += 1


def register_plugin():
    return FastStreamPlugin()
