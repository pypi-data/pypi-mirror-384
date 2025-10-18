"""
GraphVisualizer のユニットテスト
"""
import pytest
from pathlib import Path
from cmw.graph_visualizer import GraphVisualizer
from cmw.models import Task, TaskStatus, Priority


@pytest.fixture
def simple_tasks():
    """シンプルなタスクセット（依存関係あり）"""
    tasks = [
        Task(
            id="TASK-001",
            title="タスク1",
            description="基盤タスク",
            assigned_to="backend",
            dependencies=[],
            priority=Priority.HIGH
        ),
        Task(
            id="TASK-002",
            title="タスク2",
            description="TASK-001に依存",
            assigned_to="backend",
            dependencies=["TASK-001"],
            priority=Priority.MEDIUM
        ),
        Task(
            id="TASK-003",
            title="タスク3",
            description="TASK-001に依存",
            assigned_to="backend",
            dependencies=["TASK-001"],
            priority=Priority.MEDIUM
        ),
        Task(
            id="TASK-004",
            title="タスク4",
            description="TASK-002とTASK-003に依存",
            assigned_to="backend",
            dependencies=["TASK-002", "TASK-003"],
            priority=Priority.LOW
        ),
    ]
    return tasks


@pytest.fixture
def parallel_tasks():
    """並列実行可能なタスクセット"""
    tasks = [
        Task(id="TASK-001", title="基盤", description="", assigned_to="backend",
             dependencies=[], priority=Priority.HIGH),
        Task(id="TASK-002", title="並列1", description="", assigned_to="backend",
             dependencies=["TASK-001"], priority=Priority.MEDIUM),
        Task(id="TASK-003", title="並列2", description="", assigned_to="backend",
             dependencies=["TASK-001"], priority=Priority.MEDIUM),
        Task(id="TASK-004", title="並列3", description="", assigned_to="backend",
             dependencies=["TASK-001"], priority=Priority.MEDIUM),
    ]
    return tasks


@pytest.fixture
def completed_tasks():
    """ステータスが異なるタスクセット"""
    tasks = [
        Task(id="TASK-001", title="完了", description="", assigned_to="backend",
             dependencies=[], priority=Priority.HIGH, status=TaskStatus.COMPLETED),
        Task(id="TASK-002", title="進行中", description="", assigned_to="backend",
             dependencies=["TASK-001"], priority=Priority.MEDIUM, status=TaskStatus.IN_PROGRESS),
        Task(id="TASK-003", title="保留", description="", assigned_to="backend",
             dependencies=["TASK-001"], priority=Priority.MEDIUM, status=TaskStatus.PENDING),
        Task(id="TASK-004", title="失敗", description="", assigned_to="backend",
             dependencies=["TASK-002"], priority=Priority.LOW, status=TaskStatus.FAILED),
    ]
    return tasks


class TestGraphVisualizerBasics:
    """GraphVisualizer の基本機能テスト"""

    def test_initialization(self, simple_tasks):
        """初期化のテスト"""
        visualizer = GraphVisualizer(simple_tasks)

        assert len(visualizer.tasks) == 4
        assert visualizer.graph.number_of_nodes() == 4
        assert visualizer.graph.number_of_edges() == 4  # TASK-001→002, 001→003, 002→004, 003→004

    def test_build_graph(self, simple_tasks):
        """グラフ構築のテスト"""
        visualizer = GraphVisualizer(simple_tasks)

        # エッジの確認
        assert visualizer.graph.has_edge("TASK-001", "TASK-002")
        assert visualizer.graph.has_edge("TASK-001", "TASK-003")
        assert visualizer.graph.has_edge("TASK-002", "TASK-004")
        assert visualizer.graph.has_edge("TASK-003", "TASK-004")

    def test_empty_tasks(self):
        """空のタスクリストのテスト"""
        visualizer = GraphVisualizer([])

        assert len(visualizer.tasks) == 0
        assert visualizer.graph.number_of_nodes() == 0


class TestRenderAscii:
    """ASCII形式レンダリングのテスト"""

    def test_render_ascii_simple(self, simple_tasks):
        """シンプルなASCIIレンダリング"""
        visualizer = GraphVisualizer(simple_tasks)
        output = visualizer.render_ascii()

        # 全タスクが含まれているか確認
        assert "TASK-001" in output
        assert "TASK-002" in output
        assert "TASK-003" in output
        assert "TASK-004" in output

    def test_render_ascii_with_status(self, completed_tasks):
        """ステータス付きASCIIレンダリング"""
        visualizer = GraphVisualizer(completed_tasks)
        output = visualizer.render_ascii(show_status=True)

        # ステータスアイコンが含まれているか確認
        assert "✅" in output  # COMPLETED
        assert "🔄" in output  # IN_PROGRESS
        assert "⏳" in output  # PENDING
        assert "❌" in output  # FAILED

    def test_render_ascii_without_status(self, simple_tasks):
        """ステータスなしASCIIレンダリング"""
        visualizer = GraphVisualizer(simple_tasks)
        output = visualizer.render_ascii(show_status=False)

        # タスクIDとタイトルが含まれているか確認
        assert "TASK-001" in output
        assert "タスク1" in output


class TestRenderMermaid:
    """Mermaid形式レンダリングのテスト"""

    def test_render_mermaid_structure(self, simple_tasks):
        """Mermaid形式の構造テスト"""
        visualizer = GraphVisualizer(simple_tasks)
        output = visualizer.render_mermaid()

        # 基本構造の確認
        assert "graph TD" in output

        # ノード定義の確認
        assert 'TASK-001["TASK-001:' in output
        assert 'TASK-002["TASK-002:' in output

        # エッジ定義の確認
        assert "TASK-001 --> TASK-002" in output
        assert "TASK-001 --> TASK-003" in output
        assert "TASK-002 --> TASK-004" in output
        assert "TASK-003 --> TASK-004" in output

        # スタイル定義の確認
        assert "classDef completed" in output
        assert "classDef in_progress" in output

    def test_render_mermaid_with_status(self, completed_tasks):
        """ステータス付きMermaid形式"""
        visualizer = GraphVisualizer(completed_tasks)
        output = visualizer.render_mermaid()

        # ステータススタイルの確認
        assert ":::completed" in output
        assert ":::in_progress" in output
        assert ":::failed" in output


class TestCriticalPath:
    """クリティカルパス計算のテスト"""

    def test_get_critical_path_simple(self, simple_tasks):
        """シンプルなクリティカルパス"""
        visualizer = GraphVisualizer(simple_tasks)
        critical_path = visualizer.get_critical_path()

        # TASK-001 → TASK-002 → TASK-004 または TASK-001 → TASK-003 → TASK-004
        assert len(critical_path) == 3
        assert critical_path[0] == "TASK-001"
        assert critical_path[-1] == "TASK-004"
        assert critical_path[1] in ["TASK-002", "TASK-003"]

    def test_get_critical_path_single_task(self):
        """単一タスクのクリティカルパス"""
        tasks = [
            Task(id="TASK-001", title="単一", description="", assigned_to="backend",
                 dependencies=[], priority=Priority.HIGH)
        ]
        visualizer = GraphVisualizer(tasks)
        critical_path = visualizer.get_critical_path()

        assert critical_path == ["TASK-001"]

    def test_get_critical_path_empty(self):
        """空のタスクリストのクリティカルパス"""
        visualizer = GraphVisualizer([])
        critical_path = visualizer.get_critical_path()

        assert critical_path == []


class TestParallelGroups:
    """並列実行グループのテスト"""

    def test_get_parallel_groups_simple(self, simple_tasks):
        """シンプルな並列グループ"""
        visualizer = GraphVisualizer(simple_tasks)
        groups = visualizer.get_parallel_groups()

        # レベル0: TASK-001
        assert len(groups) >= 3
        assert groups[0] == ["TASK-001"]

        # レベル1: TASK-002, TASK-003 (並列実行可能)
        assert set(groups[1]) == {"TASK-002", "TASK-003"}

        # レベル2: TASK-004
        assert groups[2] == ["TASK-004"]

    def test_get_parallel_groups_parallel_tasks(self, parallel_tasks):
        """並列タスクのグループ化"""
        visualizer = GraphVisualizer(parallel_tasks)
        groups = visualizer.get_parallel_groups()

        # レベル0: TASK-001
        assert groups[0] == ["TASK-001"]

        # レベル1: TASK-002, TASK-003, TASK-004 (全て並列実行可能)
        assert len(groups[1]) == 3
        assert set(groups[1]) == {"TASK-002", "TASK-003", "TASK-004"}

    def test_get_parallel_groups_empty(self):
        """空のタスクリストの並列グループ"""
        visualizer = GraphVisualizer([])
        groups = visualizer.get_parallel_groups()

        assert groups == []


class TestStatistics:
    """統計情報のテスト"""

    def test_get_statistics(self, simple_tasks):
        """統計情報の取得"""
        visualizer = GraphVisualizer(simple_tasks)
        stats = visualizer.get_statistics()

        assert stats['total_tasks'] == 4
        assert stats['total_dependencies'] == 4
        assert stats['root_tasks'] == 1
        assert stats['leaf_tasks'] == 1
        assert stats['is_dag'] is True
        assert stats['has_cycles'] is False
        assert stats['critical_path_length'] == 3
        assert stats['max_parallelism'] == 2  # TASK-002, TASK-003
        assert stats['parallel_levels'] == 3

    def test_get_statistics_empty(self):
        """空のタスクリストの統計"""
        visualizer = GraphVisualizer([])
        stats = visualizer.get_statistics()

        assert stats['total_tasks'] == 0
        assert stats['total_dependencies'] == 0
        assert stats['average_dependencies'] == 0


class TestTaskDepth:
    """タスク深さのテスト"""

    def test_get_task_depth(self, simple_tasks):
        """タスク深さの取得"""
        visualizer = GraphVisualizer(simple_tasks)

        assert visualizer.get_task_depth("TASK-001") == 0
        assert visualizer.get_task_depth("TASK-002") == 1
        assert visualizer.get_task_depth("TASK-003") == 1
        assert visualizer.get_task_depth("TASK-004") == 2

    def test_get_task_depth_invalid(self, simple_tasks):
        """存在しないタスクの深さ"""
        visualizer = GraphVisualizer(simple_tasks)

        assert visualizer.get_task_depth("TASK-999") == -1


class TestDependentTasks:
    """依存タスクのテスト"""

    def test_get_dependent_tasks(self, simple_tasks):
        """依存タスクの取得"""
        visualizer = GraphVisualizer(simple_tasks)

        # TASK-001に依存するタスク
        dependents = visualizer.get_dependent_tasks("TASK-001")
        assert dependents == {"TASK-002", "TASK-003", "TASK-004"}

        # TASK-002に依存するタスク
        dependents = visualizer.get_dependent_tasks("TASK-002")
        assert dependents == {"TASK-004"}

        # TASK-004に依存するタスク（なし）
        dependents = visualizer.get_dependent_tasks("TASK-004")
        assert dependents == set()

    def test_get_dependent_tasks_invalid(self, simple_tasks):
        """存在しないタスクの依存タスク"""
        visualizer = GraphVisualizer(simple_tasks)

        dependents = visualizer.get_dependent_tasks("TASK-999")
        assert dependents == set()


class TestGraphvizExport:
    """Graphvizエクスポートのテスト"""

    def test_export_graphviz_missing_library(self, simple_tasks, tmp_path):
        """pygraphvizがない場合のエラー"""
        visualizer = GraphVisualizer(simple_tasks)
        output_path = tmp_path / "graph.dot"

        # pygraphvizがインストールされていない場合、ImportErrorが発生する
        try:
            visualizer.export_graphviz(output_path)
        except ImportError as e:
            assert "pygraphviz" in str(e)


class TestComplexScenarios:
    """複雑なシナリオのテスト"""

    def test_large_graph(self):
        """大規模グラフのテスト"""
        # 10個のタスクを生成
        tasks = []
        for i in range(10):
            task_id = f"TASK-{i:03d}"
            dependencies = [f"TASK-{j:03d}" for j in range(max(0, i-2), i)]
            tasks.append(
                Task(
                    id=task_id,
                    title=f"タスク{i}",
                    description="",
                    assigned_to="backend",
                    dependencies=dependencies,
                    priority=Priority.MEDIUM
                )
            )

        visualizer = GraphVisualizer(tasks)
        stats = visualizer.get_statistics()

        assert stats['total_tasks'] == 10
        assert stats['is_dag'] is True

    def test_multiple_root_tasks(self):
        """複数のルートタスク"""
        tasks = [
            Task(id="ROOT-1", title="ルート1", description="", assigned_to="backend",
                 dependencies=[], priority=Priority.HIGH),
            Task(id="ROOT-2", title="ルート2", description="", assigned_to="backend",
                 dependencies=[], priority=Priority.HIGH),
            Task(id="CHILD-1", title="子1", description="", assigned_to="backend",
                 dependencies=["ROOT-1"], priority=Priority.MEDIUM),
            Task(id="CHILD-2", title="子2", description="", assigned_to="backend",
                 dependencies=["ROOT-2"], priority=Priority.MEDIUM),
        ]

        visualizer = GraphVisualizer(tasks)
        stats = visualizer.get_statistics()

        assert stats['root_tasks'] == 2
        assert stats['leaf_tasks'] == 2

    def test_diamond_dependency(self):
        """ダイヤモンド型依存関係"""
        tasks = [
            Task(id="A", title="A", description="", assigned_to="backend",
                 dependencies=[], priority=Priority.HIGH),
            Task(id="B", title="B", description="", assigned_to="backend",
                 dependencies=["A"], priority=Priority.MEDIUM),
            Task(id="C", title="C", description="", assigned_to="backend",
                 dependencies=["A"], priority=Priority.MEDIUM),
            Task(id="D", title="D", description="", assigned_to="backend",
                 dependencies=["B", "C"], priority=Priority.LOW),
        ]

        visualizer = GraphVisualizer(tasks)
        critical_path = visualizer.get_critical_path()

        # A → B → D または A → C → D
        assert len(critical_path) == 3
        assert critical_path[0] == "A"
        assert critical_path[-1] == "D"

        # 並列グループ
        groups = visualizer.get_parallel_groups()
        assert len(groups) == 3
        assert groups[0] == ["A"]
        assert set(groups[1]) == {"B", "C"}
        assert groups[2] == ["D"]
