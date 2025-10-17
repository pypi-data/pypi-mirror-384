from dataclasses import asdict, dataclass, field
from typing import Optional, Set


@dataclass
class SizeStats:
    min: int
    mean: int
    p90: int
    p95: int
    max: int


@dataclass
class CountAndSizeMetrics:
    count: int = 0
    size_stats: Optional[SizeStats] = None


@dataclass
class WebResourceMetrics:
    lines: int = 0
    files: int = 0


@dataclass
class WebMetrics:
    html: WebResourceMetrics = field(default_factory=WebResourceMetrics)
    css: WebResourceMetrics = field(default_factory=WebResourceMetrics)
    js: WebResourceMetrics = field(default_factory=WebResourceMetrics)


@dataclass
class BaseCodeMetrics:
    lines: int = 0
    files: int = 0
    dependencies: int = 0
    directories: int = 0
    max_directory_depth: int = 0
    functions: CountAndSizeMetrics = field(default_factory=CountAndSizeMetrics)
    classes: CountAndSizeMetrics = field(default_factory=CountAndSizeMetrics)
    imports: CountAndSizeMetrics = field(default_factory=CountAndSizeMetrics)


@dataclass
class CodeMetrics(BaseCodeMetrics):
    web: WebMetrics = field(default_factory=WebMetrics)


@dataclass
class LogicalMetrics:
    api_endpoints: int = 0
    event_subscriptions: int = 0
    periodic_tasks: int = 0
    integrated_systems: int = 0


@dataclass
class ProjectMetrics:
    app: CodeMetrics = field(default_factory=CodeMetrics)
    tests: BaseCodeMetrics = field(default_factory=BaseCodeMetrics)
    logical: LogicalMetrics = field(default_factory=LogicalMetrics)
    complexity_score: int = 0

    def __repr__(self):
        """Форматирует метрики в YAML-подобном виде."""

        def format_section(data, indent=0):
            lines = []
            for k, v in data.items():
                prefix = ' ' * indent
                if isinstance(v, dict):
                    lines.append(f"{prefix}{k}:")
                    lines.append(format_section(v, indent + 2))
                elif isinstance(v, (list, set)):
                    lines.append(f"{prefix}{k}: {len(v)}")
                elif hasattr(v, '__dict__'):
                    lines.append(f"{prefix}{k}:")
                    lines.append(format_section(asdict(v), indent + 2))
                elif v is None:
                    lines.append(f"{prefix}{k}: null")
                else:
                    lines.append(f"{prefix}{k}: {v}")
            return '\n'.join(lines)

        return format_section(asdict(self))
