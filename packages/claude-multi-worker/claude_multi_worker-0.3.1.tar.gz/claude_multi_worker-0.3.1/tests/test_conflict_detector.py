"""
ConflictDetectorのテスト
"""
import pytest
from pathlib import Path

from src.cmw.conflict_detector import (
    ConflictDetector,
    Conflict,
    ConflictType,
    ConflictSeverity
)
from src.cmw.models import Task, TaskStatus


class TestConflictDetector:
    """ConflictDetectorのテスト"""

    @pytest.fixture
    def detector(self):
        """ConflictDetectorインスタンス"""
        return ConflictDetector()

    @pytest.fixture
    def tasks_no_conflict(self):
        """競合のないタスク"""
        return [
            Task(
                id="TASK-001",
                title="Database Setup",
                description="Setup database",
                assigned_to="backend",
                target_files=["backend/database.py"],
                dependencies=[],
                priority="high"
            ),
            Task(
                id="TASK-002",
                title="Models",
                description="Create models",
                assigned_to="backend",
                target_files=["backend/models.py"],
                dependencies=["TASK-001"],
                priority="high"
            )
        ]

    @pytest.fixture
    def tasks_with_conflict(self):
        """競合のあるタスク"""
        return [
            Task(
                id="TASK-001",
                title="User Registration",
                description="User registration endpoint",
                assigned_to="backend",
                target_files=["backend/routers/auth.py"],
                dependencies=[],
                priority="high"
            ),
            Task(
                id="TASK-002",
                title="User Login",
                description="User login endpoint",
                assigned_to="backend",
                target_files=["backend/routers/auth.py"],
                dependencies=[],
                priority="high"
            )
        ]

    def test_detect_no_conflicts(self, detector, tasks_no_conflict):
        """競合がない場合"""
        conflicts = detector.detect_conflicts(tasks_no_conflict)
        assert len(conflicts) == 0

    def test_detect_conflicts(self, detector, tasks_with_conflict):
        """競合がある場合"""
        conflicts = detector.detect_conflicts(tasks_with_conflict)

        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert conflict.file == "backend/routers/auth.py"
        assert set(conflict.tasks) == {"TASK-001", "TASK-002"}
        assert conflict.conflict_type == ConflictType.WRITE_WRITE

    def test_conflict_severity_medium(self, detector):
        """中程度の深刻度（2タスク）"""
        tasks = [
            Task(id=f"TASK-{i:03d}", title=f"Task {i}",
                 description=f"Task {i} description",
                 assigned_to="backend",
                 target_files=["backend/test.py"],
                 dependencies=[], priority="medium")
            for i in range(1, 3)
        ]

        conflicts = detector.detect_conflicts(tasks)
        assert len(conflicts) == 1
        assert conflicts[0].severity == ConflictSeverity.MEDIUM

    def test_conflict_severity_high(self, detector):
        """高い深刻度（3-4タスク）"""
        tasks = [
            Task(id=f"TASK-{i:03d}", title=f"Task {i}",
                 description=f"Task {i} description",
                 assigned_to="backend",
                 target_files=["backend/test.py"],
                 dependencies=[], priority="medium")
            for i in range(1, 4)
        ]

        conflicts = detector.detect_conflicts(tasks)
        assert len(conflicts) == 1
        assert conflicts[0].severity == ConflictSeverity.HIGH

    def test_conflict_severity_critical(self, detector):
        """重大な深刻度（5タスク以上）"""
        tasks = [
            Task(id=f"TASK-{i:03d}", title=f"Task {i}",
                 description=f"Task {i} description",
                 assigned_to="backend",
                 target_files=["backend/test.py"],
                 dependencies=[], priority="medium")
            for i in range(1, 6)
        ]

        conflicts = detector.detect_conflicts(tasks)
        assert len(conflicts) == 1
        assert conflicts[0].severity == ConflictSeverity.CRITICAL

    def test_suggest_execution_order_no_dependencies(self, detector):
        """依存関係のないタスクの実行順序"""
        tasks = [
            Task(id="TASK-001", title="Task 1",
                 description="Task 1 description",
                 assigned_to="backend",
                 target_files=["file1.py"],
                 dependencies=[], priority="high"),
            Task(id="TASK-002", title="Task 2",
                 description="Task 2 description",
                 assigned_to="backend",
                 target_files=["file2.py"],
                 dependencies=[], priority="high")
        ]

        order = detector.suggest_execution_order(tasks)

        # 並列実行可能なので1グループ
        assert len(order) >= 1
        # 両方のタスクが含まれる
        all_tasks = [task_id for group in order for task_id in group]
        assert "TASK-001" in all_tasks
        assert "TASK-002" in all_tasks

    def test_suggest_execution_order_with_dependencies(self, detector):
        """依存関係のあるタスクの実行順序"""
        tasks = [
            Task(id="TASK-001", title="Database",
                 description="Setup database",
                 assigned_to="backend",
                 target_files=["database.py"],
                 dependencies=[], priority="high"),
            Task(id="TASK-002", title="Models",
                 description="Create models",
                 assigned_to="backend",
                 target_files=["models.py"],
                 dependencies=["TASK-001"], priority="high"),
            Task(id="TASK-003", title="Schemas",
                 description="Create schemas",
                 assigned_to="backend",
                 target_files=["schemas.py"],
                 dependencies=["TASK-002"], priority="medium")
        ]

        order = detector.suggest_execution_order(tasks)

        # 全タスクが含まれる
        all_tasks = [task_id for group in order for task_id in group]
        assert len(all_tasks) == 3

        # TASK-001が最初に来る
        first_group_tasks = set()
        for task_id in order[0]:
            first_group_tasks.add(task_id)
        assert "TASK-001" in first_group_tasks

    def test_suggest_execution_order_file_conflicts(self, detector, tasks_with_conflict):
        """ファイル競合があるタスクの実行順序"""
        order = detector.suggest_execution_order(tasks_with_conflict)

        # ファイル競合があるため、別グループになる
        assert len(order) >= 2

    def test_get_safe_parallel_tasks(self, detector):
        """安全に並列実行可能なタスクを取得"""
        tasks = [
            Task(id="TASK-001", title="Task 1",
                 description="Task 1 description",
                 assigned_to="backend",
                 target_files=["file1.py"],
                 dependencies=[], priority="high",
                 status=TaskStatus.PENDING),
            Task(id="TASK-002", title="Task 2",
                 description="Task 2 description",
                 assigned_to="backend",
                 target_files=["file2.py"],
                 dependencies=[], priority="high",
                 status=TaskStatus.PENDING),
            Task(id="TASK-003", title="Task 3",
                 description="Task 3 description",
                 assigned_to="backend",
                 target_files=["file1.py"],  # TASK-001と競合
                 dependencies=[], priority="high",
                 status=TaskStatus.PENDING)
        ]

        parallel = detector.get_safe_parallel_tasks(tasks, max_parallel=3)

        # TASK-001とTASK-003はfile1.pyで競合するため、両方は選ばれない
        assert len(parallel) >= 1
        assert not ("TASK-001" in parallel and "TASK-003" in parallel)

    def test_get_safe_parallel_tasks_with_max_limit(self, detector):
        """最大並列数の制限"""
        tasks = [
            Task(id=f"TASK-{i:03d}", title=f"Task {i}",
                 description=f"Task {i} description",
                 assigned_to="backend",
                 target_files=[f"file{i}.py"],
                 dependencies=[], priority="high",
                 status=TaskStatus.PENDING)
            for i in range(1, 6)
        ]

        parallel = detector.get_safe_parallel_tasks(tasks, max_parallel=2)

        assert len(parallel) <= 2

    def test_analyze_file_usage(self, detector):
        """ファイル使用状況の分析"""
        tasks = [
            Task(id="TASK-001", title="Task 1",
                 description="Task 1 description",
                 assigned_to="backend",
                 target_files=["backend/models.py"],
                 dependencies=[], priority="high"),
            Task(id="TASK-002", title="Task 2",
                 description="Task 2 description",
                 assigned_to="backend",
                 target_files=["backend/models.py"],
                 dependencies=[], priority="high"),
            Task(id="TASK-003", title="Task 3",
                 description="Task 3 description",
                 assigned_to="backend",
                 target_files=["backend/schemas.py"],
                 dependencies=[], priority="medium")
        ]

        usage = detector.analyze_file_usage(tasks)

        assert "backend/models.py" in usage
        assert len(usage["backend/models.py"]["tasks"]) == 2
        assert usage["backend/models.py"]["write_count"] == 2
        assert usage["backend/models.py"]["risk_level"] == ConflictSeverity.MEDIUM

        assert "backend/schemas.py" in usage
        assert len(usage["backend/schemas.py"]["tasks"]) == 1
        assert usage["backend/schemas.py"]["risk_level"] == "low"

    def test_analyze_file_usage_high_risk(self, detector):
        """高リスクファイルの検出"""
        tasks = [
            Task(id=f"TASK-{i:03d}", title=f"Task {i}",
                 description=f"Task {i} description",
                 assigned_to="backend",
                 target_files=["backend/critical.py"],
                 dependencies=[], priority="high")
            for i in range(1, 4)
        ]

        usage = detector.analyze_file_usage(tasks)

        assert usage["backend/critical.py"]["risk_level"] == ConflictSeverity.HIGH

    def test_analyze_file_usage_critical_risk(self, detector):
        """重大リスクファイルの検出"""
        tasks = [
            Task(id=f"TASK-{i:03d}", title=f"Task {i}",
                 description=f"Task {i} description",
                 assigned_to="backend",
                 target_files=["backend/critical.py"],
                 dependencies=[], priority="high")
            for i in range(1, 6)
        ]

        usage = detector.analyze_file_usage(tasks)

        assert usage["backend/critical.py"]["risk_level"] == "critical"

    def test_get_conflict_report_no_conflicts(self, detector, tasks_no_conflict):
        """競合がない場合のレポート"""
        report = detector.get_conflict_report(tasks_no_conflict)

        assert "ファイル競合レポート" in report
        assert "競合は検出されませんでした" in report

    def test_get_conflict_report_with_conflicts(self, detector, tasks_with_conflict):
        """競合がある場合のレポート"""
        report = detector.get_conflict_report(tasks_with_conflict)

        assert "ファイル競合レポート" in report
        assert "件の競合が検出されました" in report
        assert "backend/routers/auth.py" in report
        assert "推奨実行順序" in report

    def test_conflict_to_dict(self):
        """Conflictの辞書変換"""
        conflict = Conflict(
            file="test.py",
            tasks=["TASK-001", "TASK-002"],
            conflict_type=ConflictType.WRITE_WRITE,
            severity=ConflictSeverity.MEDIUM,
            suggestion="Test suggestion"
        )

        data = conflict.to_dict()

        assert data["file"] == "test.py"
        assert data["tasks"] == ["TASK-001", "TASK-002"]
        assert data["conflict_type"] == ConflictType.WRITE_WRITE
        assert data["severity"] == ConflictSeverity.MEDIUM
        assert data["suggestion"] == "Test suggestion"

    def test_get_safe_parallel_tasks_respects_dependencies(self, detector):
        """依存関係を考慮した並列タスク取得"""
        tasks = [
            Task(id="TASK-001", title="Database",
                 description="Setup database",
                 assigned_to="backend",
                 target_files=["database.py"],
                 dependencies=[], priority="high",
                 status=TaskStatus.PENDING),
            Task(id="TASK-002", title="Models",
                 description="Create models",
                 assigned_to="backend",
                 target_files=["models.py"],
                 dependencies=["TASK-001"], priority="high",
                 status=TaskStatus.PENDING)
        ]

        parallel = detector.get_safe_parallel_tasks(tasks)

        # TASK-002は依存関係が未解決なので選ばれない
        assert "TASK-001" in parallel
        assert "TASK-002" not in parallel

    def test_get_safe_parallel_tasks_after_completion(self, detector):
        """完了後の並列タスク取得"""
        tasks = [
            Task(id="TASK-001", title="Database",
                 description="Setup database",
                 assigned_to="backend",
                 target_files=["database.py"],
                 dependencies=[], priority="high",
                 status=TaskStatus.COMPLETED),
            Task(id="TASK-002", title="Models",
                 description="Create models",
                 assigned_to="backend",
                 target_files=["models.py"],
                 dependencies=["TASK-001"], priority="high",
                 status=TaskStatus.PENDING),
            Task(id="TASK-003", title="Schemas",
                 description="Create schemas",
                 assigned_to="backend",
                 target_files=["schemas.py"],
                 dependencies=["TASK-001"], priority="medium",
                 status=TaskStatus.PENDING)
        ]

        parallel = detector.get_safe_parallel_tasks(tasks)

        # TASK-001完了後、TASK-002とTASK-003が実行可能
        assert "TASK-002" in parallel or "TASK-003" in parallel
        # ファイル競合がないので両方選ばれる可能性あり
        assert len(parallel) >= 1


class TestRealWorldScenario:
    """実際のプロジェクトでのシナリオテスト"""

    @pytest.fixture
    def detector(self):
        return ConflictDetector()

    def test_todo_api_like_tasks(self, detector):
        """todo-apiのようなタスクセット"""
        tasks = [
            Task(id="TASK-001", title="Database Setup",
                 description="Setup database",
                 assigned_to="backend",
                 target_files=["backend/database.py"],
                 dependencies=[], priority="high"),
            Task(id="TASK-002", title="User Model",
                 description="Create user model",
                 assigned_to="backend",
                 target_files=["backend/models.py"],
                 dependencies=["TASK-001"], priority="high"),
            Task(id="TASK-003", title="Task Model",
                 description="Create task model",
                 assigned_to="backend",
                 target_files=["backend/models.py"],
                 dependencies=["TASK-001"], priority="high"),
            Task(id="TASK-004", title="User Registration",
                 description="User registration endpoint",
                 assigned_to="backend",
                 target_files=["backend/routers/auth.py"],
                 dependencies=["TASK-002"], priority="medium"),
            Task(id="TASK-005", title="User Login",
                 description="User login endpoint",
                 assigned_to="backend",
                 target_files=["backend/routers/auth.py"],
                 dependencies=["TASK-002"], priority="medium")
        ]

        # 競合検出
        conflicts = detector.detect_conflicts(tasks)

        # models.pyとrouters/auth.pyで競合があるはず
        conflict_files = [c.file for c in conflicts]
        assert "backend/models.py" in conflict_files
        assert "backend/routers/auth.py" in conflict_files

        # 実行順序
        order = detector.suggest_execution_order(tasks)

        # 全タスクが含まれる
        all_tasks = [task_id for group in order for task_id in group]
        assert len(all_tasks) == 5

        # TASK-001が最初
        assert "TASK-001" in order[0]
