"""
ファイル競合検出とタスク実行順序の最適化

このモジュールは、タスク間のファイル競合を検出し、
最適な実行順序を提案します。
"""

from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import networkx as nx

from .models import Task, TaskStatus


class ConflictType:
    """競合タイプの定義"""
    WRITE_WRITE = "write-write"  # 同じファイルへの書き込み
    READ_WRITE = "read-write"    # 読み込みと書き込みの競合
    DIRECTORY = "directory"       # ディレクトリレベルの競合


class ConflictSeverity:
    """競合の深刻度"""
    CRITICAL = "critical"  # 必ず順序付けが必要
    HIGH = "high"          # 推奨される順序付け
    MEDIUM = "medium"      # 並列実行可能だが注意が必要
    LOW = "low"            # ほぼ影響なし


class Conflict:
    """競合情報"""

    def __init__(self,
                 file: str,
                 tasks: List[str],
                 conflict_type: str,
                 severity: str,
                 suggestion: str = ""):
        self.file = file
        self.tasks = tasks
        self.conflict_type = conflict_type
        self.severity = severity
        self.suggestion = suggestion

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'file': self.file,
            'tasks': self.tasks,
            'conflict_type': self.conflict_type,
            'severity': self.severity,
            'suggestion': self.suggestion
        }


class ConflictDetector:
    """ファイル競合の検出と解決提案"""

    def __init__(self):
        pass

    def detect_conflicts(self, tasks: List[Task]) -> List[Conflict]:
        """
        ファイル競合を検出

        Args:
            tasks: タスクのリスト

        Returns:
            競合情報のリスト
        """
        conflicts = []
        file_to_tasks = self._group_by_file(tasks)

        for file, task_ids in file_to_tasks.items():
            if len(task_ids) > 1:
                # 複数のタスクが同じファイルを扱う
                conflict_type = ConflictType.WRITE_WRITE
                severity = self._determine_severity(task_ids, tasks)
                suggestion = self._generate_suggestion(file, task_ids, tasks)

                conflict = Conflict(
                    file=file,
                    tasks=task_ids,
                    conflict_type=conflict_type,
                    severity=severity,
                    suggestion=suggestion
                )
                conflicts.append(conflict)

        return conflicts

    def suggest_execution_order(self, tasks: List[Task]) -> List[List[str]]:
        """
        競合を避ける実行順序を提案

        Returns:
            並列実行グループのリスト [
                ['TASK-001', 'TASK-002'],  # グループ1: 並列実行可能
                ['TASK-003'],               # グループ2: 依存あり
                ['TASK-004', 'TASK-005']    # グループ3: 並列実行可能
            ]
        """
        # 依存関係グラフを構築
        G = self._build_dependency_graph(tasks)

        # トポロジカルソート
        try:
            sorted_tasks = list(nx.topological_sort(G))
        except nx.NetworkXError:
            # 循環依存がある場合は、IDでソート
            sorted_tasks = sorted([t.id for t in tasks])

        # レベルごとにグループ化（並列実行可能なタスク）
        groups = self._group_by_execution_level(sorted_tasks, tasks)

        return groups

    def get_safe_parallel_tasks(self, tasks: List[Task], max_parallel: int = 3) -> List[str]:
        """
        安全に並列実行可能なタスクを取得

        Args:
            tasks: タスクのリスト
            max_parallel: 最大並列実行数

        Returns:
            並列実行可能なタスクIDのリスト
        """
        # 実行可能なタスク（依存関係が解決済み）を取得
        ready_tasks = []
        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue

            # 依存関係チェック
            if task.dependencies:
                deps_met = all(
                    any(t.id == dep_id and t.status == TaskStatus.COMPLETED for t in tasks)
                    for dep_id in task.dependencies
                )
                if deps_met:
                    ready_tasks.append(task)
            else:
                # 依存関係がない
                ready_tasks.append(task)

        if not ready_tasks:
            return []

        # ファイル競合をチェック
        parallel_tasks = []
        used_files = set()

        for task in ready_tasks:
            # このタスクのファイルが既に使用されているかチェック
            task_files = set(task.target_files)
            if not (task_files & used_files):
                # 競合なし
                parallel_tasks.append(task.id)
                used_files.update(task_files)

                if len(parallel_tasks) >= max_parallel:
                    break

        return parallel_tasks

    def analyze_file_usage(self, tasks: List[Task]) -> Dict[str, Dict]:
        """
        ファイル使用状況を分析

        Returns:
            ファイルごとの使用状況 {
                'backend/models.py': {
                    'tasks': ['TASK-001', 'TASK-002'],
                    'read_count': 5,
                    'write_count': 2,
                    'risk_level': 'high'
                }
            }
        """
        file_usage = {}

        for task in tasks:
            for file in task.target_files:
                if file not in file_usage:
                    file_usage[file] = {
                        'tasks': [],
                        'read_count': 0,
                        'write_count': 0,
                        'risk_level': 'low'
                    }

                file_usage[file]['tasks'].append(task.id)
                file_usage[file]['write_count'] += 1

        # リスクレベルを計算
        for file, usage in file_usage.items():
            task_count = len(usage['tasks'])
            if task_count >= 5:
                usage['risk_level'] = 'critical'
            elif task_count >= 3:
                usage['risk_level'] = 'high'
            elif task_count >= 2:
                usage['risk_level'] = 'medium'
            else:
                usage['risk_level'] = 'low'

        return file_usage

    def _group_by_file(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """ファイルごとにタスクをグループ化"""
        file_to_tasks = {}

        for task in tasks:
            for file in task.target_files:
                if file not in file_to_tasks:
                    file_to_tasks[file] = []
                file_to_tasks[file].append(task.id)

        return file_to_tasks

    def _determine_severity(self, task_ids: List[str], tasks: List[Task]) -> str:
        """競合の深刻度を判定"""
        task_count = len(task_ids)

        if task_count >= 5:
            return ConflictSeverity.CRITICAL
        elif task_count >= 3:
            return ConflictSeverity.HIGH
        elif task_count >= 2:
            return ConflictSeverity.MEDIUM
        else:
            return ConflictSeverity.LOW

    def _generate_suggestion(self, file: str, task_ids: List[str], tasks: List[Task]) -> str:
        """競合解決の提案を生成"""
        task_count = len(task_ids)

        if task_count == 2:
            return f"タスク {task_ids[0]} を先に実行し、その後 {task_ids[1]} を実行してください"
        elif task_count >= 3:
            return f"{task_count}個のタスクが {file} を編集します。順次実行を推奨します"
        else:
            return "順次実行を推奨"

    def _build_dependency_graph(self, tasks: List[Task]) -> nx.DiGraph:
        """依存関係グラフを構築"""
        G = nx.DiGraph()

        for task in tasks:
            G.add_node(task.id)
            for dep in task.dependencies:
                G.add_edge(dep, task.id)

        return G

    def _group_by_execution_level(self, sorted_tasks: List[str], tasks: List[Task]) -> List[List[str]]:
        """実行レベルごとにタスクをグループ化"""
        tasks_by_id = {t.id: t for t in tasks}
        groups = []
        remaining = set(sorted_tasks)

        while remaining:
            # 依存が全て解決済みのタスクを取得
            ready = []
            for task_id in remaining:
                task = tasks_by_id.get(task_id)
                if not task:
                    continue

                # 依存関係をチェック
                deps_met = all(dep not in remaining for dep in task.dependencies)
                if deps_met:
                    ready.append(task_id)

            if not ready:
                # デッドロック回避：残りのタスクを全て追加
                ready = list(remaining)

            # ファイル競合を考慮してグループ化
            parallel_group = self._filter_by_file_conflicts(ready, tasks_by_id)

            if parallel_group:
                groups.append(parallel_group)
                remaining -= set(parallel_group)

        return groups

    def _filter_by_file_conflicts(self, task_ids: List[str], tasks_by_id: Dict[str, Task]) -> List[str]:
        """ファイル競合を考慮してタスクをフィルタリング"""
        selected = []
        used_files = set()

        for task_id in task_ids:
            task = tasks_by_id.get(task_id)
            if not task:
                continue

            task_files = set(task.target_files)

            # ファイル競合チェック
            if not (task_files & used_files):
                selected.append(task_id)
                used_files.update(task_files)

        # 選択されなかったタスクも含める（次のグループで処理）
        # ただし、最低1つは選択
        if not selected and task_ids:
            selected = [task_ids[0]]

        return selected

    def get_conflict_report(self, tasks: List[Task]) -> str:
        """
        競合レポートを生成

        Args:
            tasks: タスクのリスト

        Returns:
            人間が読みやすい競合レポート
        """
        conflicts = self.detect_conflicts(tasks)
        file_usage = self.analyze_file_usage(tasks)

        report = []
        report.append("=" * 80)
        report.append("ファイル競合レポート")
        report.append("=" * 80)
        report.append("")

        if not conflicts:
            report.append("✅ ファイル競合は検出されませんでした")
            return "\n".join(report)

        report.append(f"⚠️  {len(conflicts)} 件の競合が検出されました")
        report.append("")

        # 深刻度別にグループ化
        by_severity = {}
        for conflict in conflicts:
            severity = conflict.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(conflict)

        # 深刻度順に表示
        for severity in [ConflictSeverity.CRITICAL, ConflictSeverity.HIGH,
                        ConflictSeverity.MEDIUM, ConflictSeverity.LOW]:
            if severity not in by_severity:
                continue

            severity_conflicts = by_severity[severity]
            severity_icon = {
                ConflictSeverity.CRITICAL: "🔴",
                ConflictSeverity.HIGH: "🟠",
                ConflictSeverity.MEDIUM: "🟡",
                ConflictSeverity.LOW: "🟢"
            }

            report.append(f"{severity_icon[severity]} {severity.upper()} ({len(severity_conflicts)}件)")
            report.append("-" * 80)

            for conflict in severity_conflicts:
                report.append(f"  ファイル: {conflict.file}")
                report.append(f"  タスク: {', '.join(conflict.tasks)}")
                report.append(f"  提案: {conflict.suggestion}")
                report.append("")

        # 推奨実行順序
        report.append("=" * 80)
        report.append("推奨実行順序")
        report.append("=" * 80)
        report.append("")

        execution_order = self.suggest_execution_order(tasks)
        for i, group in enumerate(execution_order, 1):
            if len(group) == 1:
                report.append(f"ステップ {i}: {group[0]}")
            else:
                report.append(f"ステップ {i}: {', '.join(group)} (並列実行可能)")

        return "\n".join(report)
