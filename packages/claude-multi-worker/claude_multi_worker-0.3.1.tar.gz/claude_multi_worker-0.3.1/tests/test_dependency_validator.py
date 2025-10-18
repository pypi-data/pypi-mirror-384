"""
DependencyValidator のユニットテスト
"""
import pytest
from cmw.dependency_validator import DependencyValidator
from cmw.models import Task, Priority


class TestCycleDetection:
    """循環依存の検出テスト"""

    def test_detect_simple_cycle(self):
        """単純な循環依存の検出"""
        tasks = [
            Task(
                id="TASK-004",
                title="2.1 モデル定義",
                description="モデルを定義",
                assigned_to="backend",
                dependencies=["TASK-005"],
                priority=Priority.HIGH,
            ),
            Task(
                id="TASK-005",
                title="2.2 データベース初期化",
                description="DBを初期化",
                assigned_to="backend",
                dependencies=["TASK-004"],
                priority=Priority.HIGH,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)

        assert len(cycles) == 1
        assert set(cycles[0]) == {"TASK-004", "TASK-005"}

    def test_detect_no_cycle(self):
        """循環依存がない場合"""
        tasks = [
            Task(
                id="TASK-001",
                title="タスク1",
                description="テスト",
                assigned_to="backend",
                dependencies=[],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-002",
                title="タスク2",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-001"],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-003",
                title="タスク3",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-002"],
                priority=Priority.MEDIUM,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)

        assert len(cycles) == 0

    def test_detect_multiple_cycles(self):
        """複数の循環依存の検出"""
        tasks = [
            Task(
                id="TASK-004",
                title="モデル定義",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-005"],
                priority=Priority.HIGH,
            ),
            Task(
                id="TASK-005",
                title="DB初期化",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-004"],
                priority=Priority.HIGH,
            ),
            Task(
                id="TASK-024",
                title="技術スタック",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-025"],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-025",
                title="非機能要件",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-024"],
                priority=Priority.MEDIUM,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)

        assert len(cycles) == 2


class TestFixSuggestions:
    """修正提案のテスト"""

    def test_suggest_fixes_for_definition_initialization_cycle(self):
        """定義→初期化の循環依存の修正提案"""
        tasks = [
            Task(
                id="TASK-004",
                title="2.1 モデル定義",
                description="モデルを定義",
                assigned_to="backend",
                dependencies=["TASK-005"],
                priority=Priority.HIGH,
            ),
            Task(
                id="TASK-005",
                title="2.2 データベース初期化",
                description="DBを初期化",
                assigned_to="backend",
                dependencies=["TASK-004"],
                priority=Priority.HIGH,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)
        suggestions = validator.suggest_fixes(cycles, tasks)

        assert len(suggestions) == 1
        assert len(suggestions[0]["suggestions"]) > 0

        # 最も信頼度の高い提案
        best_fix = suggestions[0]["suggestions"][0]
        assert best_fix["from_task"] == "TASK-004"
        assert best_fix["to_task"] == "TASK-005"
        assert "定義" in best_fix["reason"] or "初期化" in best_fix["reason"]
        assert best_fix["confidence"] > 0.5

    def test_suggest_fixes_for_guideline_cycle(self):
        """ガイドライン項目の循環依存の修正提案"""
        tasks = [
            Task(
                id="TASK-024",
                title="技術スタック（推奨）",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-025"],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-025",
                title="非機能要件",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-024"],
                priority=Priority.MEDIUM,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)
        suggestions = validator.suggest_fixes(cycles, tasks)

        assert len(suggestions) == 1
        # ガイドライン項目へのエッジが削除候補
        best_fix = suggestions[0]["suggestions"][0]
        assert "ガイドライン" in best_fix["reason"] or "推奨" in best_fix["reason"]


class TestAutoFix:
    """自動修正のテスト"""

    def test_auto_fix_cycles(self):
        """循環依存の自動修正"""
        tasks = [
            Task(
                id="TASK-004",
                title="2.1 モデル定義",
                description="モデルを定義",
                assigned_to="backend",
                dependencies=["TASK-005"],
                priority=Priority.HIGH,
            ),
            Task(
                id="TASK-005",
                title="2.2 データベース初期化",
                description="DBを初期化",
                assigned_to="backend",
                dependencies=["TASK-004"],
                priority=Priority.HIGH,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)
        assert len(cycles) == 1

        # 自動修正を適用
        fixed_tasks = validator.auto_fix_cycles(tasks, cycles, auto_apply=True)

        # 修正後は循環依存がないことを確認
        remaining_cycles = validator.detect_cycles(fixed_tasks)
        assert len(remaining_cycles) == 0

    def test_auto_fix_preserves_valid_dependencies(self):
        """自動修正が正しい依存関係を保持することを確認"""
        tasks = [
            Task(
                id="TASK-001",
                title="タスク1",
                description="テスト",
                assigned_to="backend",
                dependencies=[],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-002",
                title="タスク2",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-001"],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-004",
                title="2.1 モデル定義",
                description="モデルを定義",
                assigned_to="backend",
                dependencies=["TASK-005", "TASK-001"],
                priority=Priority.HIGH,
            ),
            Task(
                id="TASK-005",
                title="2.2 データベース初期化",
                description="DBを初期化",
                assigned_to="backend",
                dependencies=["TASK-004"],
                priority=Priority.HIGH,
            ),
        ]

        validator = DependencyValidator()
        cycles = validator.detect_cycles(tasks)
        fixed_tasks = validator.auto_fix_cycles(tasks, cycles, auto_apply=True)

        # TASK-004 → TASK-001 の正しい依存関係は保持される
        task_004 = next(t for t in fixed_tasks if t.id == "TASK-004")
        assert "TASK-001" in task_004.dependencies


class TestSectionNumberExtraction:
    """セクション番号抽出のテスト"""

    def test_extract_section_number(self):
        """セクション番号の抽出"""
        validator = DependencyValidator()

        assert validator._extract_section_number("2.1 モデル定義") == 2.1
        assert validator._extract_section_number("2.2 データベース初期化") == 2.2
        assert validator._extract_section_number("10.5 テスト") == 10.5
        assert (
            validator._extract_section_number("タイトルのみ") is None
        )


class TestDependencyValidation:
    """依存関係全体の検証テスト"""

    def test_validate_missing_dependencies(self):
        """存在しない依存先の検出"""
        tasks = [
            Task(
                id="TASK-001",
                title="タスク1",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-999"],  # 存在しないタスク
                priority=Priority.MEDIUM,
            ),
        ]

        validator = DependencyValidator()
        result = validator.validate_dependencies(tasks)

        assert len(result["missing_dependencies"]) == 1
        assert "TASK-999" in result["missing_dependencies"][0]

    def test_validate_self_dependency(self):
        """自己依存の検出"""
        tasks = [
            Task(
                id="TASK-001",
                title="タスク1",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-001"],  # 自己依存
                priority=Priority.MEDIUM,
            ),
        ]

        validator = DependencyValidator()
        result = validator.validate_dependencies(tasks)

        assert len(result["invalid_dependencies"]) == 1
        assert "自己依存" in result["invalid_dependencies"][0]

    def test_validate_all_ok(self):
        """問題がない場合"""
        tasks = [
            Task(
                id="TASK-001",
                title="タスク1",
                description="テスト",
                assigned_to="backend",
                dependencies=[],
                priority=Priority.MEDIUM,
            ),
            Task(
                id="TASK-002",
                title="タスク2",
                description="テスト",
                assigned_to="backend",
                dependencies=["TASK-001"],
                priority=Priority.MEDIUM,
            ),
        ]

        validator = DependencyValidator()
        result = validator.validate_dependencies(tasks)

        assert not result["has_cycles"]
        assert len(result["cycles"]) == 0
        assert len(result["missing_dependencies"]) == 0
        assert len(result["invalid_dependencies"]) == 0
