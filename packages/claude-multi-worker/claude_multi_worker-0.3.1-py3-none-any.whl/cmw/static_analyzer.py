"""
Pythonコードの静的解析機能

ASTを使用してファイルの依存関係を解析し、タスク間の依存関係を推論します。
"""
import ast
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import re

from .models import Task


class StaticAnalyzer:
    """Pythonコードの静的解析機能"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = project_root or Path.cwd()

    def analyze_file_dependencies(self, file_path: str) -> Set[str]:
        """ファイルの依存関係を解析（AST使用）

        Args:
            file_path: 解析するファイルのパス（プロジェクトルートからの相対パス）

        Returns:
            依存ファイルのセット（プロジェクトルートからの相対パス）
        """
        full_path = self.project_root / file_path

        if not full_path.exists():
            return set()

        if not full_path.suffix == '.py':
            return set()

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(full_path))
            dependencies = set()

            # sys.pathの変更を検出
            extra_paths = self._detect_sys_path_changes(tree, file_path)

            # Import文を検出
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep_files = self._module_to_file(alias.name, file_path, extra_paths)
                        dependencies.update(dep_files)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # from X import Y の場合、XとX.Yの両方を試す
                        dep_files = self._module_to_file(node.module, file_path, extra_paths)
                        dependencies.update(dep_files)

                        # Yがモジュールである場合も考慮（from routers import auth など）
                        for alias in node.names:
                            submodule = f"{node.module}.{alias.name}"
                            sub_dep_files = self._module_to_file(submodule, file_path, extra_paths)
                            # 自分自身を除外
                            sub_dep_files.discard(file_path)
                            dependencies.update(sub_dep_files)
                    else:
                        # from . import Y の場合
                        for alias in node.names:
                            dep_files = self._module_to_file(f".{alias.name}", file_path, extra_paths)
                            # 自分自身を除外
                            dep_files.discard(file_path)
                            dependencies.update(dep_files)

            return dependencies

        except (SyntaxError, UnicodeDecodeError):
            # 構文エラーやエンコーディングエラーは無視
            return set()

    def _detect_sys_path_changes(self, tree: ast.AST, current_file: str) -> List[Path]:
        """sys.pathの変更を検出

        Args:
            tree: ASTツリー
            current_file: 現在のファイルパス

        Returns:
            追加されたパスのリスト
        """
        extra_paths = []

        for node in ast.walk(tree):
            # sys.path.insert(0, ...) や sys.path.append(...) を検出
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute):
                    # sys.path.insert や sys.path.append
                    if (isinstance(call.func.value, ast.Attribute) and
                        isinstance(call.func.value.value, ast.Name) and
                        call.func.value.value.id == 'sys' and
                        call.func.value.attr == 'path' and
                        call.func.attr in ['insert', 'append']):

                        # 引数を解析（簡易版 - str(Path(__file__).parent.parent) など）
                        # 一般的なパターン: parent や parent.parent
                        for arg in call.args:
                            path = self._evaluate_path_expr(arg, current_file)
                            if path:
                                extra_paths.append(path)

        return extra_paths

    def _evaluate_path_expr(self, node: ast.AST, current_file: str) -> Optional[Path]:
        """パス式を評価（簡易版）

        Args:
            node: AST ノード
            current_file: 現在のファイルパス

        Returns:
            評価されたパス
        """
        # str(Path(__file__).parent) や str(Path(__file__).parent.parent) を検出
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'str':
            if len(node.args) > 0:
                arg = node.args[0]
                # Path(__file__).parent.parent などを解析
                parent_count = 0
                current = arg

                while isinstance(current, ast.Attribute) and current.attr == 'parent':
                    parent_count += 1
                    current = current.value

                # Path(__file__) の部分を確認
                if isinstance(current, ast.Call):
                    if (isinstance(current.func, ast.Name) and current.func.id == 'Path' and
                        len(current.args) > 0 and isinstance(current.args[0], ast.Name) and
                        current.args[0].id == '__file__'):

                        # current_fileから parent_count 分上のディレクトリを取得
                        # current_fileはプロジェクトルートからの相対パスなので、
                        # Path(current_file)の親ディレクトリをparent_count回取得
                        current_path = Path(current_file)

                        # ファイル自体は含めず、parent_count回親ディレクトリに移動
                        # Path(__file__).parent は1回、.parent.parent は2回
                        result = current_path
                        for _ in range(parent_count):
                            result = result.parent

                        # 絶対パスに変換
                        return self.project_root / result

        return None

    def _module_to_file(self, module_name: str, current_file: str, extra_paths: List[Path] = None) -> Set[str]:
        """モジュール名をファイルパスに変換

        Args:
            module_name: モジュール名（例: "backend.api.auth"）
            current_file: 現在のファイルパス
            extra_paths: sys.pathに追加されたパス

        Returns:
            ファイルパスのセット（プロジェクトルートからの相対パス）
        """
        if extra_paths is None:
            extra_paths = []

        results = set()

        # 相対インポート（.module）は現在のディレクトリからの相対パス
        if module_name.startswith('.'):
            current_dir = Path(current_file).parent
            # . の数だけ上のディレクトリに移動
            level = len(module_name) - len(module_name.lstrip('.'))
            for _ in range(level - 1):
                current_dir = current_dir.parent

            # 残りのモジュール名をパスに変換
            remaining = module_name.lstrip('.')
            if remaining:
                module_path = current_dir / remaining.replace('.', '/')
            else:
                module_path = current_dir

            # __init__.py または .py を試す
            for suffix in ['__init__.py', '.py']:
                candidate = self.project_root / f"{module_path}{suffix}"
                if candidate.exists():
                    results.add(str(candidate.relative_to(self.project_root)))

            return results

        # 絶対インポートの場合
        module_path = module_name.replace('.', '/')

        # 現在のファイルのディレクトリを検索パスに追加
        current_file_dir = self.project_root / Path(current_file).parent

        # extra_paths（sys.pathで追加されたパス）を優先し、次にプロジェクトルート、最後に現在のディレクトリ
        search_bases = extra_paths + [self.project_root, current_file_dir]

        for base in search_bases:
            # __init__.py を試す
            candidate = base / module_path / '__init__.py'
            if candidate.exists() and candidate.is_relative_to(self.project_root):
                results.add(str(candidate.relative_to(self.project_root)))

            # .py を試す
            candidate = base / f"{module_path}.py"
            if candidate.exists() and candidate.is_relative_to(self.project_root):
                results.add(str(candidate.relative_to(self.project_root)))

        return results

    def infer_task_dependencies(
        self,
        tasks: List[Task],
        existing_dependencies: bool = True
    ) -> List[Task]:
        """タスク間の依存関係を静的解析で推論

        Args:
            tasks: タスクのリスト
            existing_dependencies: 既存の依存関係を保持するか

        Returns:
            依存関係が更新されたタスクのリスト
        """
        # タスクIDとtarget_filesのマッピングを作成
        task_files = {}
        file_to_task = {}

        for task in tasks:
            task_files[task.id] = set(task.target_files)
            for file in task.target_files:
                if file not in file_to_task:
                    file_to_task[file] = []
                file_to_task[file].append(task.id)

        # 各タスクの依存関係を推論
        updated_tasks = []

        for task in tasks:
            # 既存の依存関係を保持
            if existing_dependencies:
                inferred_deps = set(task.dependencies)
            else:
                inferred_deps = set()

            # 各target_fileの依存関係を解析
            for target_file in task.target_files:
                file_deps = self.analyze_file_dependencies(target_file)

                # 依存ファイルがどのタスクに属するか確認
                for dep_file in file_deps:
                    if dep_file in file_to_task:
                        for dep_task_id in file_to_task[dep_file]:
                            if dep_task_id != task.id:
                                inferred_deps.add(dep_task_id)

            # 依存関係を更新
            updated_task = Task(
                id=task.id,
                title=task.title,
                description=task.description,
                assigned_to=task.assigned_to,
                dependencies=list(inferred_deps),
                target_files=task.target_files,
                acceptance_criteria=task.acceptance_criteria,
                priority=task.priority,
                status=task.status
            )
            updated_tasks.append(updated_task)

        return updated_tasks

    def detect_circular_imports(self, tasks: List[Task]) -> List[List[str]]:
        """インポートの循環を検出

        Args:
            tasks: タスクのリスト

        Returns:
            循環インポートのリスト（各要素は循環するファイルパスのリスト）
        """
        # まず全てのファイルを収集
        all_files = set()
        for task in tasks:
            for file in task.target_files:
                all_files.add(file)

        # ファイル間の依存関係グラフを構築
        file_graph = {}
        for file in all_files:
            file_graph[file] = set()
            deps = self.analyze_file_dependencies(file)
            file_graph[file].update(deps & all_files)

        # DFSで循環を検出
        visited = set()
        rec_stack = []  # Use list to track the path
        cycles = []

        def dfs(node: str) -> None:
            """深さ優先探索で循環を検出"""
            visited.add(node)
            rec_stack.append(node)

            for neighbor in file_graph.get(node, set()):
                if neighbor in rec_stack:
                    # 循環を発見
                    cycle_start = rec_stack.index(neighbor)
                    cycle = rec_stack[cycle_start:]
                    if cycle not in cycles:
                        cycles.append(cycle)
                elif neighbor not in visited:
                    dfs(neighbor)

            rec_stack.remove(node)

        for file in all_files:
            if file not in visited:
                dfs(file)

        return cycles

    def analyze_import_patterns(self, tasks: List[Task]) -> Dict[str, any]:
        """インポートパターンを分析

        Args:
            tasks: タスクのリスト

        Returns:
            インポートパターンの統計情報
        """
        stats = {
            'total_files': 0,
            'total_imports': 0,
            'circular_imports': [],
            'most_imported_files': [],
            'files_with_most_imports': [],
        }

        # ファイルごとのインポート数と被インポート数をカウント
        import_counts = {}  # ファイル -> インポートしているファイル数
        imported_counts = {}  # ファイル -> インポートされている回数

        all_files = []
        for task in tasks:
            all_files.extend(task.target_files)

        stats['total_files'] = len(all_files)

        for file in all_files:
            deps = self.analyze_file_dependencies(file)
            import_counts[file] = len(deps)
            stats['total_imports'] += len(deps)

            for dep in deps:
                if dep not in imported_counts:
                    imported_counts[dep] = 0
                imported_counts[dep] += 1

        # 最もインポートされているファイル（上位5件）
        sorted_imported = sorted(
            imported_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        stats['most_imported_files'] = [
            {'file': file, 'count': count}
            for file, count in sorted_imported[:5]
        ]

        # 最も多くインポートしているファイル（上位5件）
        sorted_imports = sorted(
            import_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        stats['files_with_most_imports'] = [
            {'file': file, 'count': count}
            for file, count in sorted_imports[:5]
        ]

        # 循環インポート
        stats['circular_imports'] = self.detect_circular_imports(tasks)

        return stats

    def suggest_file_organization(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """ファイル構成の提案

        Args:
            tasks: タスクのリスト

        Returns:
            ディレクトリごとのファイルリスト
        """
        organization = {}

        for task in tasks:
            for file in task.target_files:
                # ディレクトリを取得
                directory = str(Path(file).parent)
                if directory == '.':
                    directory = 'root'

                if directory not in organization:
                    organization[directory] = []

                organization[directory].append(file)

        return organization

    def extract_api_endpoints(self, file_path: str) -> List[Dict[str, str]]:
        """FastAPIのエンドポイントを抽出（簡易版）

        Args:
            file_path: 解析するファイルのパス

        Returns:
            エンドポイント情報のリスト
        """
        full_path = self.project_root / file_path

        if not full_path.exists():
            return []

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()

            endpoints = []

            # 正規表現でHTTPメソッドデコレータを検出
            patterns = [
                (r'@\w+\.get\(["\']([^"\']+)["\']\)', 'GET'),
                (r'@\w+\.post\(["\']([^"\']+)["\']\)', 'POST'),
                (r'@\w+\.put\(["\']([^"\']+)["\']\)', 'PUT'),
                (r'@\w+\.delete\(["\']([^"\']+)["\']\)', 'DELETE'),
                (r'@\w+\.patch\(["\']([^"\']+)["\']\)', 'PATCH'),
            ]

            for pattern, method in patterns:
                for match in re.finditer(pattern, source):
                    path = match.group(1)
                    endpoints.append({
                        'method': method,
                        'path': path,
                        'file': file_path
                    })

            return endpoints

        except (UnicodeDecodeError, FileNotFoundError):
            return []

    def analyze_complexity(self, file_path: str) -> Dict[str, any]:
        """ファイルの複雑度を分析

        Args:
            file_path: 解析するファイルのパス

        Returns:
            複雑度の情報
        """
        full_path = self.project_root / file_path

        if not full_path.exists():
            return {}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(full_path))

            stats = {
                'lines_of_code': len(source.split('\n')),
                'num_functions': 0,
                'num_classes': 0,
                'num_imports': 0,
                'max_nesting_depth': 0,
            }

            # ASTを走査
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    stats['num_functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    stats['num_classes'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    stats['num_imports'] += 1

            # ネストの深さを計算（簡易版）
            def get_max_depth(node: ast.AST, current_depth: int = 0) -> int:
                max_depth = current_depth
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        child_depth = get_max_depth(child, current_depth + 1)
                        max_depth = max(max_depth, child_depth)
                return max_depth

            stats['max_nesting_depth'] = get_max_depth(tree)

            return stats

        except (SyntaxError, UnicodeDecodeError):
            return {}
