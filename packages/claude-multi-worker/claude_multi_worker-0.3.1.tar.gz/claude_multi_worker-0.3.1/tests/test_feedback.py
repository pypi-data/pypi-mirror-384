"""
FeedbackManagerのユニットテスト
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import json
from cmw.feedback import FeedbackManager
from cmw.models import Task, TaskStatus


@pytest.fixture
def test_project():
    """テスト用プロジェクトを作成"""
    temp_dir = Path(tempfile.mkdtemp())

    # ディレクトリ構造を作成
    (temp_dir / "shared/coordination").mkdir(parents=True)
    (temp_dir / "shared/docs").mkdir(parents=True)
    (temp_dir / "shared/artifacts").mkdir(parents=True)

    # tasks.jsonを作成
    tasks = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "認証機能実装",
                "description": "ユーザー認証を実装する",
                "assigned_to": "worker1",
                "dependencies": [],
                "target_files": ["backend/auth.py"],
                "acceptance_criteria": ["ログイン機能", "JWT発行"],
                "priority": "high",
            },
            {
                "id": "TASK-002",
                "title": "API実装",
                "description": "REST APIを実装する",
                "assigned_to": "worker1",
                "dependencies": ["TASK-001"],
                "target_files": ["backend/api.py"],
                "acceptance_criteria": ["エンドポイント作成"],
                "priority": "medium",
            },
            {
                "id": "TASK-003",
                "title": "テスト作成",
                "description": "ユニットテストを作成する",
                "assigned_to": "worker1",
                "dependencies": ["TASK-001", "TASK-002"],
                "target_files": ["tests/test_api.py"],
                "acceptance_criteria": ["全テストパス"],
                "priority": "low",
            },
        ],
        "workers": [],
    }

    (temp_dir / "shared/coordination/tasks.json").write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    yield temp_dir

    # クリーンアップ
    shutil.rmtree(temp_dir)


def test_report_progress_all_pending(test_project):
    """全タスクがPENDING状態の進捗レポート"""
    manager = FeedbackManager(test_project)

    report = manager.report_progress()

    assert "完了: 0/3" in report
    assert "0.0%" in report
    assert "保留:     3" in report


def test_report_progress_some_completed(test_project):
    """一部完了した状態の進捗レポート"""
    manager = FeedbackManager(test_project)

    # TASK-001を完了
    task1 = manager.coordinator.get_task("TASK-001")
    task1.status = TaskStatus.COMPLETED

    report = manager.report_progress()

    assert "完了: 1/3" in report
    assert "33.3%" in report
    assert "完了:     1" in report


def test_report_progress_with_failures(test_project):
    """失敗タスクがある場合の進捗レポート"""
    manager = FeedbackManager(test_project)

    # TASK-001を失敗
    task1 = manager.coordinator.get_task("TASK-001")
    task1.status = TaskStatus.FAILED

    # TASK-002をブロック
    task2 = manager.coordinator.get_task("TASK-002")
    task2.status = TaskStatus.BLOCKED

    report = manager.report_progress()

    assert "失敗:     1" in report
    assert "ブロック: 1" in report


def test_explain_error_file_not_found(test_project):
    """FileNotFoundErrorの説明"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    error = FileNotFoundError("File not found: auth.py")

    explanation = manager.explain_error(task, error)

    assert "ファイルが見つかりません" in explanation
    assert "TASK-001" in explanation
    assert "依存タスクが未完了" in explanation


def test_explain_error_permission_error(test_project):
    """PermissionErrorの説明"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    error = PermissionError("Permission denied")

    explanation = manager.explain_error(task, error)

    assert "権限エラー" in explanation
    assert "書き込み権限" in explanation or "読み取り専用" in explanation


def test_explain_error_module_not_found(test_project):
    """ModuleNotFoundErrorの説明"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    error = ModuleNotFoundError("No module named 'requests'")

    explanation = manager.explain_error(task, error)

    assert "モジュールが見つかりません" in explanation
    assert "requirements.txt" in explanation


def test_explain_error_syntax_error(test_project):
    """SyntaxErrorの説明"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    error = SyntaxError("invalid syntax")

    explanation = manager.explain_error(task, error)

    assert "構文エラー" in explanation
    assert "インデント" in explanation or "括弧" in explanation


def test_explain_error_unknown_error(test_project):
    """未知のエラーの説明"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    error = Exception("Unknown error")

    explanation = manager.explain_error(task, error)

    assert "予期しないエラー" in explanation
    assert "TASK-001" in explanation


def test_show_next_steps_with_ready_tasks(test_project):
    """実行可能なタスクがある場合の次のステップ"""
    manager = FeedbackManager(test_project)

    next_steps = manager.show_next_steps()

    assert "実行可能なタスク" in next_steps
    assert "TASK-001" in next_steps
    assert "推奨アクション" in next_steps


def test_show_next_steps_with_failed_tasks(test_project):
    """失敗タスクがある場合の次のステップ"""
    manager = FeedbackManager(test_project)

    # TASK-001を失敗
    task1 = manager.coordinator.get_task("TASK-001")
    task1.status = TaskStatus.FAILED
    task1.error = "Test error"

    next_steps = manager.show_next_steps()

    assert "失敗したタスク" in next_steps
    assert "TASK-001" in next_steps
    assert "修正してください" in next_steps


def test_show_next_steps_with_blocked_tasks(test_project):
    """ブロックされたタスクがある場合の次のステップ"""
    manager = FeedbackManager(test_project)

    # TASK-001を完了
    task1 = manager.coordinator.get_task("TASK-001")
    task1.status = TaskStatus.COMPLETED

    # TASK-002をブロック
    task2 = manager.coordinator.get_task("TASK-002")
    task2.status = TaskStatus.BLOCKED

    next_steps = manager.show_next_steps()

    assert "ブロックされたタスク" in next_steps
    assert "TASK-002" in next_steps


def test_show_next_steps_all_completed(test_project):
    """全タスク完了時の次のステップ"""
    manager = FeedbackManager(test_project)

    # 全タスクを完了
    for task in manager.coordinator.tasks.values():
        task.status = TaskStatus.COMPLETED

    next_steps = manager.show_next_steps()

    assert "全タスク完了" in next_steps


def test_get_task_summary_pending(test_project):
    """PENDING状態のタスク概要"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    summary = manager.get_task_summary(task)

    assert "TASK-001" in summary
    assert "認証機能実装" in summary
    assert "pending" in summary
    assert "backend/auth.py" in summary
    assert "ログイン機能" in summary


def test_get_task_summary_completed(test_project):
    """COMPLETED状態のタスク概要"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    task.status = TaskStatus.COMPLETED
    task.completed_at = "2025-10-16T10:30:00Z"
    task.artifacts = ["backend/auth.py", "backend/utils.py"]

    summary = manager.get_task_summary(task)

    assert "TASK-001" in summary
    assert "completed" in summary
    assert "完了日時" in summary
    assert "backend/auth.py" in summary


def test_get_task_summary_failed(test_project):
    """FAILED状態のタスク概要"""
    manager = FeedbackManager(test_project)

    task = manager.coordinator.get_task("TASK-001")
    task.status = TaskStatus.FAILED
    task.failed_at = "2025-10-16T10:30:00Z"
    task.error = "Test error occurred"

    summary = manager.get_task_summary(task)

    assert "TASK-001" in summary
    assert "failed" in summary
    assert "失敗日時" in summary
    assert "Test error occurred" in summary


def test_estimate_remaining_time(test_project):
    """残り時間の見積もり"""
    manager = FeedbackManager(test_project)

    estimate = manager.estimate_remaining_time(avg_task_time_minutes=30.0)

    assert "残り時間の見積もり" in estimate
    assert "残りタスク: 3/3" in estimate
    assert "90 分" in estimate  # 3タスク × 30分


def test_estimate_remaining_time_partial_complete(test_project):
    """一部完了時の残り時間見積もり"""
    manager = FeedbackManager(test_project)

    # TASK-001を完了
    task1 = manager.coordinator.get_task("TASK-001")
    task1.status = TaskStatus.COMPLETED

    estimate = manager.estimate_remaining_time(avg_task_time_minutes=30.0)

    assert "残りタスク: 2/3" in estimate
    assert "60 分" in estimate  # 2タスク × 30分


def test_estimate_remaining_time_all_completed(test_project):
    """全タスク完了時の見積もり"""
    manager = FeedbackManager(test_project)

    # 全タスクを完了
    for task in manager.coordinator.tasks.values():
        task.status = TaskStatus.COMPLETED

    estimate = manager.estimate_remaining_time()

    assert "全タスク完了" in estimate


def test_get_ready_tasks(test_project):
    """実行可能なタスクの取得"""
    manager = FeedbackManager(test_project)

    ready = manager._get_ready_tasks()

    # TASK-001のみが実行可能（依存なし）
    assert len(ready) == 1
    assert ready[0].id == "TASK-001"


def test_get_ready_tasks_after_completion(test_project):
    """タスク完了後の実行可能タスク"""
    manager = FeedbackManager(test_project)

    # TASK-001を完了
    task1 = manager.coordinator.get_task("TASK-001")
    task1.status = TaskStatus.COMPLETED

    ready = manager._get_ready_tasks()

    # TASK-002が実行可能になる
    assert len(ready) == 1
    assert ready[0].id == "TASK-002"


def test_get_ready_tasks_priority_order(test_project):
    """優先度順でタスクが返される"""
    manager = FeedbackManager(test_project)

    # 全タスクの依存関係を削除
    for task in manager.coordinator.tasks.values():
        task.dependencies = []

    ready = manager._get_ready_tasks()

    # 高優先度のTASK-001が最初
    assert ready[0].id == "TASK-001"
    assert ready[0].priority == "high"


def test_are_dependencies_met(test_project):
    """依存関係が満たされているか"""
    manager = FeedbackManager(test_project)

    task1 = manager.coordinator.get_task("TASK-001")
    task2 = manager.coordinator.get_task("TASK-002")

    # TASK-001は依存なし
    assert manager._are_dependencies_met(task1)

    # TASK-002はTASK-001に依存（未完了）
    assert not manager._are_dependencies_met(task2)

    # TASK-001を完了
    task1.status = TaskStatus.COMPLETED

    # TASK-002の依存関係が満たされる
    assert manager._are_dependencies_met(task2)


def test_report_progress_no_tasks(test_project):
    """タスクがない場合の進捗レポート"""
    # 空のtasks.jsonを作成
    (test_project / "shared/coordination/tasks.json").write_text(
        json.dumps({"tasks": [], "workers": []}, indent=2), encoding="utf-8"
    )

    manager = FeedbackManager(test_project)
    report = manager.report_progress()

    assert "タスクが見つかりません" in report
