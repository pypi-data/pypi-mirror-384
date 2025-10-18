"""
InteractiveFixer のユニットテスト
"""
import pytest
from unittest.mock import patch, MagicMock
from cmw.interactive_fixer import InteractiveFixer
from cmw.models import Task, Priority, TaskStatus


@pytest.fixture
def circular_tasks():
    """循環依存のあるタスク"""
    return [
        Task(
            id="TASK-001",
            title="認証API",
            description="",
            assigned_to="backend",
            dependencies=["TASK-002"],
            target_files=["backend/auth.py"],
            acceptance_criteria=[],
            priority=Priority.HIGH
        ),
        Task(
            id="TASK-002",
            title="ユーザーモデル",
            description="",
            assigned_to="backend",
            dependencies=["TASK-001"],
            target_files=["backend/models.py"],
            acceptance_criteria=[],
            priority=Priority.HIGH
        ),
    ]


@pytest.fixture
def sample_tasks():
    """サンプルタスク"""
    return [
        Task(
            id="TASK-001",
            title="認証",
            description="",
            assigned_to="backend",
            dependencies=[],
            target_files=[],
            acceptance_criteria=[],
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        ),
        Task(
            id="TASK-002",
            title="DB",
            description="",
            assigned_to="backend",
            dependencies=[],
            target_files=[],
            acceptance_criteria=[],
            priority=Priority.MEDIUM,
            status=TaskStatus.COMPLETED
        ),
    ]


class TestInteractiveFixerBasics:
    """InteractiveFixer の基本機能テスト"""

    def test_initialization(self):
        """初期化のテスト"""
        fixer = InteractiveFixer()
        assert fixer.console is not None
        assert fixer.validator is not None

    def test_confirm_action_yes(self):
        """アクション確認（Yes）"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Confirm.ask', return_value=True):
            result = fixer.confirm_action("テスト実行")
            assert result is True

    def test_confirm_action_no(self):
        """アクション確認（No）"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Confirm.ask', return_value=False):
            result = fixer.confirm_action("テスト実行")
            assert result is False


class TestFixCyclesInteractively:
    """循環依存の対話的修正テスト"""

    def test_fix_cycles_with_selection(self, circular_tasks):
        """循環依存修正（選択肢1を選択）"""
        cycles = [["TASK-001", "TASK-002"]]
        fixer = InteractiveFixer()

        # suggest_fixesをモック
        mock_suggestions = [{
            'cycle': ["TASK-001", "TASK-002"],
            'suggestions': [
                {
                    'from_task': 'TASK-001',
                    'to_task': 'TASK-002',
                    'reason': 'テスト理由',
                    'confidence': 0.85
                }
            ]
        }]

        # ユーザー入力とsugggest_fixesをモック
        with patch('rich.prompt.Prompt.ask', return_value="1"), \
             patch.object(fixer.validator, 'suggest_fixes', return_value=mock_suggestions):
            fixed_tasks = fixer.fix_cycles_interactively(circular_tasks, cycles)

        # いずれかの依存が削除されている
        task_001 = next(t for t in fixed_tasks if t.id == "TASK-001")
        task_002 = next(t for t in fixed_tasks if t.id == "TASK-002")

        # 循環が解消されているはず
        has_cycle = (
            "TASK-002" in task_001.dependencies and
            "TASK-001" in task_002.dependencies
        )
        assert not has_cycle

    def test_fix_cycles_skip(self, circular_tasks):
        """循環依存修正（スキップ）"""
        cycles = [["TASK-001", "TASK-002"]]
        fixer = InteractiveFixer()

        # スキップを選択
        with patch('rich.prompt.Prompt.ask', return_value="s"):
            fixed_tasks = fixer.fix_cycles_interactively(circular_tasks, cycles)

        # 変更されていない
        task_001 = next(t for t in fixed_tasks if t.id == "TASK-001")
        assert "TASK-002" in task_001.dependencies

    def test_fix_cycles_cancel(self, circular_tasks):
        """循環依存修正（キャンセル）"""
        cycles = [["TASK-001", "TASK-002"]]
        fixer = InteractiveFixer()

        # キャンセルを選択
        with patch('rich.prompt.Prompt.ask', return_value="c"):
            fixed_tasks = fixer.fix_cycles_interactively(circular_tasks, cycles)

        # 変更されていない
        assert fixed_tasks == circular_tasks

    def test_fix_cycles_no_suggestions(self, circular_tasks):
        """循環依存修正（修正案なし）"""
        cycles = [["TASK-001", "TASK-002"]]
        fixer = InteractiveFixer()

        # suggest_fixesが空を返すようにモック
        with patch.object(fixer.validator, 'suggest_fixes', return_value=[{'suggestions': []}]):
            fixed_tasks = fixer.fix_cycles_interactively(circular_tasks, cycles)

        # 変更されていない
        assert fixed_tasks == circular_tasks


class TestSelectTasksInteractively:
    """タスク選択の対話的テスト"""

    def test_select_single_task(self, sample_tasks):
        """単一タスクの選択"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Prompt.ask', return_value="1"):
            selected = fixer.select_tasks_interactively(sample_tasks)

        assert len(selected) == 1
        assert selected[0].id == "TASK-001"

    def test_select_multiple_tasks(self, sample_tasks):
        """複数タスクの選択"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Prompt.ask', return_value="1,2"):
            selected = fixer.select_tasks_interactively(sample_tasks)

        assert len(selected) == 2
        assert selected[0].id == "TASK-001"
        assert selected[1].id == "TASK-002"

    def test_select_all_tasks(self, sample_tasks):
        """全タスクの選択"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Prompt.ask', return_value="all"):
            selected = fixer.select_tasks_interactively(sample_tasks)

        assert len(selected) == 2
        assert selected == sample_tasks

    def test_select_empty_list(self):
        """空リストの選択"""
        fixer = InteractiveFixer()
        selected = fixer.select_tasks_interactively([])

        assert selected == []

    def test_select_invalid_input(self, sample_tasks):
        """無効な入力"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Prompt.ask', return_value="invalid"):
            selected = fixer.select_tasks_interactively(sample_tasks)

        assert selected == []

    def test_select_out_of_range(self, sample_tasks):
        """範囲外の選択"""
        fixer = InteractiveFixer()

        # 範囲外の番号（99）を選択
        with patch('rich.prompt.Prompt.ask', return_value="99"):
            selected = fixer.select_tasks_interactively(sample_tasks)

        # 範囲内のタスクのみが選択される
        assert len(selected) == 0


class TestFixMissingDependencies:
    """不足依存関係の修正テスト"""

    def test_fix_missing_dependencies_confirm_yes(self):
        """不足依存削除（Yes）"""
        tasks = [
            Task(
                id="TASK-001",
                title="認証",
                description="",
                assigned_to="backend",
                dependencies=["TASK-999"],  # 存在しない依存
                target_files=[],
                acceptance_criteria=[],
                priority=Priority.HIGH
            ),
        ]

        missing_deps = [
            {
                'task_id': 'TASK-001',
                'missing_dependency': 'TASK-999'
            }
        ]

        fixer = InteractiveFixer()

        with patch('rich.prompt.Confirm.ask', return_value=True):
            fixed_tasks = fixer.fix_missing_dependencies_interactively(tasks, missing_deps)

        # 依存が削除されている
        assert "TASK-999" not in fixed_tasks[0].dependencies

    def test_fix_missing_dependencies_confirm_no(self):
        """不足依存削除（No）"""
        tasks = [
            Task(
                id="TASK-001",
                title="認証",
                description="",
                assigned_to="backend",
                dependencies=["TASK-999"],
                target_files=[],
                acceptance_criteria=[],
                priority=Priority.HIGH
            ),
        ]

        missing_deps = [
            {
                'task_id': 'TASK-001',
                'missing_dependency': 'TASK-999'
            }
        ]

        fixer = InteractiveFixer()

        with patch('rich.prompt.Confirm.ask', return_value=False):
            fixed_tasks = fixer.fix_missing_dependencies_interactively(tasks, missing_deps)

        # 依存が残っている
        assert "TASK-999" in fixed_tasks[0].dependencies

    def test_fix_missing_dependencies_empty(self, sample_tasks):
        """不足依存なし"""
        fixer = InteractiveFixer()
        fixed_tasks = fixer.fix_missing_dependencies_interactively(sample_tasks, [])

        assert fixed_tasks == sample_tasks


class TestValidationReport:
    """検証レポート表示のテスト"""

    def test_show_validation_report_no_issues(self):
        """問題なしのレポート"""
        fixer = InteractiveFixer()
        # 例外が発生しないことを確認
        fixer.show_validation_report([], [], [])

    def test_show_validation_report_with_cycles(self):
        """循環依存ありのレポート"""
        fixer = InteractiveFixer()
        cycles = [["TASK-001", "TASK-002"]]
        # 例外が発生しないことを確認
        fixer.show_validation_report(cycles, [], [])

    def test_show_validation_report_with_all_issues(self):
        """全種類の問題ありのレポート"""
        fixer = InteractiveFixer()
        cycles = [["TASK-001", "TASK-002"]]
        missing_deps = [{'task_id': 'TASK-003', 'missing_dependency': 'TASK-999'}]
        self_deps = ["TASK-004"]

        # 例外が発生しないことを確認
        fixer.show_validation_report(cycles, missing_deps, self_deps)


class TestConfirmSave:
    """保存確認のテスト"""

    def test_confirm_save_yes(self):
        """保存確認（Yes）"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Confirm.ask', return_value=True):
            result = fixer.confirm_save("tasks.json")
            assert result is True

    def test_confirm_save_no(self):
        """保存確認（No）"""
        fixer = InteractiveFixer()

        with patch('rich.prompt.Confirm.ask', return_value=False):
            result = fixer.confirm_save("tasks.json")
            assert result is False


class TestApplyFix:
    """修正適用のテスト"""

    def test_apply_fix(self, circular_tasks):
        """修正の適用"""
        fixer = InteractiveFixer()

        fix = {
            'from_task': 'TASK-001',
            'to_task': 'TASK-002'
        }

        fixed_tasks = fixer._apply_fix(circular_tasks, fix)

        task_001 = next(t for t in fixed_tasks if t.id == "TASK-001")
        assert "TASK-002" not in task_001.dependencies

    def test_apply_fix_nonexistent_task(self, sample_tasks):
        """存在しないタスクへの修正適用"""
        fixer = InteractiveFixer()

        fix = {
            'from_task': 'TASK-999',  # 存在しない
            'to_task': 'TASK-001'
        }

        # 例外が発生しないことを確認
        fixed_tasks = fixer._apply_fix(sample_tasks, fix)
        assert fixed_tasks == sample_tasks
