import ast
import math
import logging
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Optional

try:
    import tomllib
except ImportError:
    import toml as tomllib

from complexity_meter.plugins.base import PluginLoader
from complexity_meter.structs import SizeStats, ProjectMetrics


logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    TEST_DIR_PATTERNS = ['test', 'tests']
    TEST_FILE_PATTERNS = ['test_*.py', '*_test.py']
    IGNORE_DIRS = {'.git', '.venv', 'venv', 'env', '__pycache__', 'build'}
    EXTERNAL_SERVICES = {'postgres', 'redis', 'mysql', 'mongodb', 'rabbitmq', 'kafka'}
    WEB_EXTENSIONS = {'.html', '.css', '.js', '.j2', '.jinja', '.jinja2'}

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()
        self.metrics = ProjectMetrics()
        self.inheritance_graph = defaultdict(list)
        self.all_classes = dict()
        self.imported_modules = set()
        self.plugin_loader = PluginLoader(Path(__file__).parent / 'plugins')
        self._init_metrics_containers()

    def _init_metrics_containers(self):
        self.app_class_sizes = []
        self.test_class_sizes = []
        self.app_function_sizes = []
        self.test_function_sizes = []
        self.app_import_counts = []
        self.test_import_counts = []
        self.app_depths = []
        self.test_depths = []

    def is_test_file(self, path: Path) -> bool:
        """
        Определяет, является ли файл тестовым.

        >>> ProjectAnalyzer(Path('.')).is_test_file(Path('tests/test_api.py'))
        True
        >>> ProjectAnalyzer(Path('.')).is_test_file(Path('src/main.py'))
        False
        """
        return (any(part in self.TEST_DIR_PATTERNS for part in path.parts) or any(
            path.match(pattern) for pattern in self.TEST_FILE_PATTERNS
        ))

    def should_ignore(self, path: Path) -> bool:
        """
        Проверяет, нужно ли игнорировать файл/директорию.

        >>> ProjectAnalyzer(Path('.')).should_ignore(Path('.git/config'))
        True
        >>> ProjectAnalyzer(Path('.')).should_ignore(Path('src/main.py'))
        False
        """
        # Игнорировать все файлы, которые не являются Python или веб-файлами
        if path.is_file() and path.suffix not in {'.py', *self.WEB_EXTENSIONS}:
            return True
        return any(part in self.IGNORE_DIRS for part in path.parts)

    def calculate_size_stats(self, data: List[int]) -> Optional[SizeStats]:
        """
        Вычисляет статистику размеров.

        >>> stats = ProjectAnalyzer(Path('.')).calculate_size_stats([1,2,3,4,5])
        >>> (stats.min, stats.mean, stats.p90, stats.max)
        (1, 3, 5, 5)
        """
        if not data:
            return None

        sorted_data = sorted(data)
        n = len(sorted_data)
        return SizeStats(
            min=sorted_data[0],
            mean=round(sum(sorted_data) / n),
            p90=sorted_data[min(int(0.9 * n), n - 1)],
            p95=sorted_data[min(int(0.95 * n), n - 1)],
            max=sorted_data[-1]
        )

    def analyze_directory_structure(self):
        """Анализирует физическую структуру проекта."""
        for path in self.project_path.rglob('*'):
            if self.should_ignore(path):
                continue

            if path.is_dir():
                depth = len(path.relative_to(self.project_path).parts)
                if self.is_test_file(path):
                    self.test_depths.append(depth)
                    self.metrics.tests.directories += 1
                else:
                    self.app_depths.append(depth)
                    self.metrics.app.directories += 1
            elif path.is_file():
                self.process_file(path)

    def process_file(self, path: Path):
        """Обрабатывает файл, подсчитывая LOC."""
        try:
            loc = sum(1 for line in path.read_text().splitlines() if line.strip())
        except Exception:
            logger.exception("File read error: %s", path)
            return

        # Обработка веб-файлов только для app
        if not self.is_test_file(path) and path.suffix in self.WEB_EXTENSIONS:
            self.process_web_file(path, loc)
            return

        # Обработка Python-файлов
        if path.suffix == '.py':
            metrics = self.metrics.tests if self.is_test_file(path) else self.metrics.app
            metrics.lines += loc
            metrics.files += 1

    def process_web_file(self, path: Path, loc: int):
        """Обрабатывает веб-файлы (HTML, CSS, JS)."""
        metrics = self.metrics.app.web

        if path.suffix in {'.html', '.j2', '.jinja', '.jinja2'}:
            metrics.html.lines += loc
            metrics.html.files += 1
        elif path.suffix == '.css':
            metrics.css.lines += loc
            metrics.css.files += 1
        elif path.suffix in {'.js'}:
            metrics.js.lines += loc
            metrics.js.files += 1

    def analyze_ast(self, file_path: Path, is_test: bool):
        """Анализирует AST Python-файла."""
        # Только для Python-файлов
        if file_path.suffix != '.py':
            return

        try:
            tree = ast.parse(file_path.read_text(), filename=file_path.name)
        except (SyntaxError, UnicodeDecodeError):
            logger.exception("AST parse error: %s", file_path)
            return

        imports_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports_count += 1
                self.process_import(node)

            if isinstance(node, ast.ClassDef):
                self.process_class(node, is_test)

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.process_function(node, is_test)

            self.plugin_loader.analyze_node(node, self.metrics.logical, file_path)

        if is_test:
            self.test_import_counts.append(imports_count)
            self.metrics.tests.imports.count += imports_count
        else:
            self.app_import_counts.append(imports_count)
            self.metrics.app.imports.count += imports_count

    def process_import(self, node: ast.Import | ast.ImportFrom):
        """Обрабатывает импорты."""
        module = getattr(node, 'module', '') or ''
        self.imported_modules.add(module.split('.')[0])
        for alias in node.names:
            self.imported_modules.add(alias.name.split('.')[0])

    def process_class(self, node: ast.ClassDef, is_test: bool):
        """Обрабатывает классы."""
        self.all_classes[node.name] = node
        class_size = node.end_lineno - node.lineno

        if is_test:
            self.metrics.tests.classes.count += 1
            self.test_class_sizes.append(class_size)
        else:
            self.metrics.app.classes.count += 1
            self.app_class_sizes.append(class_size)

        for base in node.bases:
            if isinstance(base, ast.Name):
                self.inheritance_graph[base.id].append(node.name)

    def process_function(self, node: ast.AST, is_test: bool):
        """Обрабатывает функции."""
        function_size = node.end_lineno - node.lineno
        if is_test:
            self.metrics.tests.functions.count += 1
            self.test_function_sizes.append(function_size)
        else:
            self.metrics.app.functions.count += 1
            self.app_function_sizes.append(function_size)

    def calculate_inheritance_depth(self) -> int:
        """Вычисляет максимальную глубину наследования."""
        depths = {}

        def dfs(cls_name: str) -> int:
            if cls_name not in self.all_classes:
                return 0
            if cls_name in depths:
                return depths[cls_name]

            max_depth = max((dfs(base) for base in self.inheritance_graph.get(cls_name, [])), default=0)
            depths[cls_name] = max_depth + 1
            return depths[cls_name]

        return max((dfs(cls_name) for cls_name in self.all_classes), default=0)

    def analyze_dependencies(self):
        """Анализирует зависимости проекта."""
        req_files = [
            self.project_path / 'requirements.txt',
            self.project_path / 'requirements-dev.txt',
            self.project_path / 'requirements-test.txt',
            self.project_path / 'pyproject.toml'
        ]

        for req_file in req_files:
            if not req_file.exists():
                continue

            if req_file.name == 'pyproject.toml':
                self.parse_pyproject(req_file)
            else:
                self.parse_requirements(req_file)

    def parse_requirements(self, file_path: Path):
        """Парсит файл requirements.txt."""
        for line in file_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if 'test' in file_path.stem or 'dev' in file_path.stem:
                self.metrics.tests.dependencies += 1
            else:
                self.metrics.app.dependencies += 1

    def parse_pyproject(self, file_path: Path):
        """Парсит файл pyproject.toml с поддержкой PEP 621 и Poetry."""
        data = tomllib.loads(file_path.read_text())
        if project := data.get('project'):
            self._parse_pyproject_pep621(project)
        if poetry := data.get('tool', {}).get('poetry', {}):
            self._parse_pyproject_poetry(poetry)

    def _parse_pyproject_pep621(self, project: dict):
        """Обрабатывает зависимости по стандарту PEP 621."""
        self.metrics.app.dependencies += len(project.get('dependencies', {}))
        for group, deps in project.get('optional-dependencies', {}).items():
            if group in ['test', 'dev']:
                self.metrics.tests.dependencies += len(deps)

    def _parse_pyproject_poetry(self, poetry: dict):
        """Обрабатывает зависимости Poetry."""
        self.metrics.app.dependencies += len(poetry.get('dependencies', {}))
        self.metrics.tests.dependencies += len(poetry.get('dev-dependencies', {}))
        for group, deps in poetry.get('optional-dependencies', {}).items():  # poetry 1.2.0?
            if group in ['test', 'dev']:
                self.metrics.tests.dependencies += len(deps.get('dependencies', {}))

    def analyze_logical_structure(self):
        """Анализирует логическую структуру проекта."""
        self.metrics.logical.integrated_systems = len({
            service for module in self.imported_modules
            for service in self.EXTERNAL_SERVICES if service in module
        })

    def calculate_complexity(self):
        """Вычисляет комплексную метрику сложности."""
        weights = {
            'loc_app': 0.15,
            'files_app': 0.1,
            'classes_app': 0.12,
            'functions_app': 0.1,
            'dependencies_app': 0.1,
            'api_endpoints': 0.1,
            'event_subscriptions': 0.08,
            'periodic_tasks': 0.07,
            'integrations': 0.1,
            'dir_depth_app': 0.08,
            # Веса для веб-метрик
            'web_html_lines': 0.02,
            'web_css_lines': 0.02,
            'web_js_lines': 0.04,
            'web_html_files': 0.01,
            'web_css_files': 0.01,
            'web_js_files': 0.02,
        }

        metrics = {
            'loc_app': self.metrics.app.lines,
            'files_app': self.metrics.app.files,
            'classes_app': self.metrics.app.classes.count,
            'functions_app': self.metrics.app.functions.count,
            'dependencies_app': self.metrics.app.dependencies,
            'api_endpoints': self.metrics.logical.api_endpoints,
            'event_subscriptions': self.metrics.logical.event_subscriptions,
            'periodic_tasks': self.metrics.logical.periodic_tasks,
            'integrations': self.metrics.logical.integrated_systems,
            'dir_depth_app': self.metrics.app.max_directory_depth,
            # Метрики для веб-ресурсов
            'web_html_lines': self.metrics.app.web.html.lines,
            'web_css_lines': self.metrics.app.web.css.lines,
            'web_js_lines': self.metrics.app.web.js.lines,
            'web_html_files': self.metrics.app.web.html.files,
            'web_css_files': self.metrics.app.web.css.files,
            'web_js_files': self.metrics.app.web.js.files,
        }

        self.metrics.complexity_score = round(sum(
            weight * math.log1p(metrics[key]) * 100
            for key, weight in weights.items()
        ))

    def finalize_metrics(self):
        """Финализирует метрики после сбора данных."""
        self.metrics.app.max_directory_depth = max(self.app_depths, default=0)
        self.metrics.tests.max_directory_depth = max(self.test_depths, default=0)

        self.metrics.app.functions.size_stats = self.calculate_size_stats(self.app_function_sizes)
        self.metrics.tests.functions.size_stats = self.calculate_size_stats(self.test_function_sizes)
        self.metrics.app.classes.size_stats = self.calculate_size_stats(self.app_class_sizes)
        self.metrics.tests.classes.size_stats = self.calculate_size_stats(self.test_class_sizes)
        self.metrics.app.imports.size_stats = self.calculate_size_stats(self.app_import_counts)
        self.metrics.tests.imports.size_stats = self.calculate_size_stats(self.test_import_counts)

    def analyze(self) -> ProjectMetrics:
        """Выполняет полный анализ проекта."""
        self.analyze_directory_structure()

        for file_path in self.project_path.rglob('*'):
            if not self.should_ignore(file_path):
                self.analyze_ast(file_path, self.is_test_file(file_path))

        self.analyze_dependencies()
        self.analyze_logical_structure()
        self.finalize_metrics()
        self.calculate_complexity()

        return self.metrics


def main():
    """Точка входа"""
    parser = argparse.ArgumentParser(description='Analyze project complexity')
    parser.add_argument('project_path', type=Path, help='Path to project directory')
    parser.add_argument(
        '--single-metric',
        action='store_true',
        default=False,
        help='Only output complexity_score value'
    )
    args = parser.parse_args()

    if not args.project_path.exists() or not args.project_path.is_dir():
        raise ValueError(f"Error: '{args.project_path}' is not a valid directory")

    analyzer = ProjectAnalyzer(args.project_path)
    metrics = analyzer.analyze()
    if args.single_metric:
        print(metrics.complexity_score)
    else:
        print(metrics)
    return 0


if __name__ == "__main__":
    exit(main())
