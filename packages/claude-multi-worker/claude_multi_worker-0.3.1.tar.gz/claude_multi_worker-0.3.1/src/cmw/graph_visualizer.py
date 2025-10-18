"""
タスクグラフの可視化機能

タスクの依存関係をグラフとして可視化します。
"""
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import networkx as nx
from rich.tree import Tree
from rich.console import Console

from .models import Task, TaskStatus


class GraphVisualizer:
    """タスクグラフの可視化機能"""

    def __init__(self, tasks: List[Task]):
        """
        Args:
            tasks: タスクのリスト
        """
        self.tasks = {task.id: task for task in tasks}
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        """タスクの依存関係からグラフを構築"""
        G = nx.DiGraph()

        # ノードを追加
        for task_id, task in self.tasks.items():
            G.add_node(task_id, task=task)

        # エッジを追加（依存関係）
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    # dep_id → task_id の依存関係
                    G.add_edge(dep_id, task_id)

        return G

    def render_ascii(self, show_status: bool = True) -> str:
        """ASCII形式でグラフを描画

        Args:
            show_status: ステータスを表示するか

        Returns:
            ASCII形式のグラフ文字列
        """
        console = Console()

        # ルートタスク（依存関係のないタスク）を取得
        root_tasks = [
            task_id for task_id in self.tasks.keys()
            if not self.tasks[task_id].dependencies
        ]

        if not root_tasks:
            return "No tasks or circular dependencies detected"

        # Rich Treeを構築
        tree = Tree("📋 Task Graph")

        # 訪問済みタスクを追跡
        visited = set()

        def add_task_to_tree(task_id: str, parent_tree: Tree) -> None:
            """タスクをツリーに追加"""
            if task_id in visited:
                return
            visited.add(task_id)

            task = self.tasks[task_id]

            # ステータスアイコン
            status_icon = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.BLOCKED: "🚫"
            }.get(task.status, "❓")

            # ラベル作成
            if show_status:
                label = f"{status_icon} {task_id}: {task.title}"
            else:
                label = f"{task_id}: {task.title}"

            # 子ノードを追加
            task_node = parent_tree.add(label)

            # 依存先のタスク（このタスクに依存するタスク）を追加
            dependents = [
                t_id for t_id, t in self.tasks.items()
                if task_id in t.dependencies
            ]

            for dep_id in dependents:
                add_task_to_tree(dep_id, task_node)

        # ルートタスクから開始
        for root_id in sorted(root_tasks):
            add_task_to_tree(root_id, tree)

        # Rich Treeをテキストに変換
        from io import StringIO
        string_io = StringIO()
        temp_console = Console(file=string_io, force_terminal=True, width=120)
        temp_console.print(tree)
        return string_io.getvalue()

    def render_mermaid(self) -> str:
        """Mermaid形式でグラフを出力

        Returns:
            Mermaid形式のグラフ定義
        """
        lines = ["graph TD"]

        # ノード定義
        for task_id, task in self.tasks.items():
            # ステータスに応じたスタイル
            status_style = {
                TaskStatus.COMPLETED: ":::completed",
                TaskStatus.IN_PROGRESS: ":::in_progress",
                TaskStatus.FAILED: ":::failed",
                TaskStatus.BLOCKED: ":::blocked",
                TaskStatus.PENDING: ""
            }.get(task.status, "")

            # タイトルをエスケープ
            title = task.title.replace('"', "'")
            lines.append(f'    {task_id}["{task_id}: {title}"]{status_style}')

        # エッジ定義
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    lines.append(f"    {dep_id} --> {task_id}")

        # スタイル定義
        lines.extend([
            "",
            "    classDef completed fill:#90EE90,stroke:#2E8B57,stroke-width:2px",
            "    classDef in_progress fill:#FFD700,stroke:#DAA520,stroke-width:2px",
            "    classDef failed fill:#FFB6C1,stroke:#DC143C,stroke-width:2px",
            "    classDef blocked fill:#D3D3D3,stroke:#808080,stroke-width:2px"
        ])

        return "\n".join(lines)

    def export_graphviz(self, output_path: Path) -> None:
        """Graphviz形式でエクスポート

        Args:
            output_path: 出力ファイルパス (.dot)
        """
        try:
            import pygraphviz as pgv
        except ImportError:
            raise ImportError(
                "pygraphviz is not installed. "
                "Install it with: pip install pygraphviz"
            )

        # NetworkXグラフをGraphviz形式に変換
        A = nx.nx_agraph.to_agraph(self.graph)

        # スタイル設定
        A.node_attr['shape'] = 'box'
        A.node_attr['style'] = 'rounded,filled'

        # ステータスに応じた色設定
        for node in A.nodes():
            task = self.tasks.get(str(node))
            if task:
                if task.status == TaskStatus.COMPLETED:
                    A.get_node(node).attr['fillcolor'] = '#90EE90'
                elif task.status == TaskStatus.IN_PROGRESS:
                    A.get_node(node).attr['fillcolor'] = '#FFD700'
                elif task.status == TaskStatus.FAILED:
                    A.get_node(node).attr['fillcolor'] = '#FFB6C1'
                elif task.status == TaskStatus.BLOCKED:
                    A.get_node(node).attr['fillcolor'] = '#D3D3D3'
                else:
                    A.get_node(node).attr['fillcolor'] = 'white'

        # ファイルに保存
        A.write(str(output_path))

    def get_critical_path(self) -> List[str]:
        """クリティカルパスを計算

        Returns:
            クリティカルパス上のタスクIDリスト
        """
        if not self.tasks:
            return []

        # 最も長いパスを見つける（DAGの場合）
        try:
            # トポロジカルソート順でタスクを取得
            topo_order = list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            # サイクルがある場合は空リストを返す
            return []

        # 各ノードへの最長パス長を計算
        longest_path_to = {node: 0 for node in self.graph.nodes()}
        predecessor = {node: None for node in self.graph.nodes()}

        for node in topo_order:
            for successor in self.graph.successors(node):
                if longest_path_to[successor] < longest_path_to[node] + 1:
                    longest_path_to[successor] = longest_path_to[node] + 1
                    predecessor[successor] = node

        # 最長パスの終点を見つける
        end_node = max(longest_path_to, key=longest_path_to.get)

        # パスを逆順にたどる
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = predecessor[current]

        return list(reversed(path))

    def get_parallel_groups(self) -> List[List[str]]:
        """並列実行可能なタスクグループを取得

        Returns:
            並列実行可能なタスクのグループリスト
            各グループは同時に実行できるタスクIDのリスト
        """
        if not self.tasks:
            return []

        try:
            # トポロジカルソート順でレベル分け
            levels: List[List[str]] = []
            remaining = set(self.graph.nodes())

            while remaining:
                # 依存関係が全て解決されているタスクを見つける
                current_level = []
                for node in list(remaining):
                    # このノードの全ての前提条件が既に処理済みか確認
                    predecessors = set(self.graph.predecessors(node))
                    if predecessors.issubset(set().union(*levels) if levels else set()):
                        current_level.append(node)

                if not current_level:
                    # 並列実行可能なタスクがない場合（循環依存の可能性）
                    break

                levels.append(current_level)
                remaining -= set(current_level)

            return levels

        except nx.NetworkXError:
            # サイクルがある場合
            return []

    def get_statistics(self) -> Dict[str, any]:
        """グラフの統計情報を取得

        Returns:
            統計情報の辞書
        """
        stats = {
            'total_tasks': len(self.tasks),
            'total_dependencies': self.graph.number_of_edges(),
            'root_tasks': len([
                t for t in self.tasks.values()
                if not t.dependencies
            ]),
            'leaf_tasks': len([
                t_id for t_id in self.tasks.keys()
                if not list(self.graph.successors(t_id))
            ]),
            'average_dependencies': (
                sum(len(t.dependencies) for t in self.tasks.values()) / len(self.tasks)
                if self.tasks else 0
            ),
            'is_dag': nx.is_directed_acyclic_graph(self.graph),
            'has_cycles': not nx.is_directed_acyclic_graph(self.graph),
        }

        # クリティカルパス長
        if stats['is_dag']:
            critical_path = self.get_critical_path()
            stats['critical_path_length'] = len(critical_path)
            stats['critical_path'] = critical_path
        else:
            stats['critical_path_length'] = None
            stats['critical_path'] = None

        # 並列度（最大同時実行可能タスク数）
        parallel_groups = self.get_parallel_groups()
        if parallel_groups:
            stats['max_parallelism'] = max(len(group) for group in parallel_groups)
            stats['parallel_levels'] = len(parallel_groups)
        else:
            stats['max_parallelism'] = 0
            stats['parallel_levels'] = 0

        return stats

    def get_task_depth(self, task_id: str) -> int:
        """タスクの深さ（ルートからの距離）を取得

        Args:
            task_id: タスクID

        Returns:
            深さ（ルートタスクは0）
        """
        if task_id not in self.graph:
            return -1

        # 全ての前提タスクからの最長パスを計算
        max_depth = 0
        for predecessor in self.graph.predecessors(task_id):
            depth = self.get_task_depth(predecessor) + 1
            max_depth = max(max_depth, depth)

        return max_depth

    def get_dependent_tasks(self, task_id: str) -> Set[str]:
        """指定タスクに（直接・間接的に）依存するタスクを取得

        Args:
            task_id: タスクID

        Returns:
            依存するタスクIDのセット
        """
        if task_id not in self.graph:
            return set()

        # 子孫ノードを全て取得
        return set(nx.descendants(self.graph, task_id))
