"""
TaskProviderのユニットテスト
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from cmw.task_provider import TaskProvider
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
                "title": "タスク1",
                "description": "説明1",
                "assigned_to": "worker1",
                "dependencies": [],
                "target_files": ["file1.py"],
                "acceptance_criteria": ["基準1", "基準2"],
                "priority": "high"
            },
            {
                "id": "TASK-002",
                "title": "タスク2",
                "description": "説明2",
                "assigned_to": "worker1",
                "dependencies": ["TASK-001"],
                "target_files": ["file2.py"],
                "acceptance_criteria": ["基準3"],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    import json
    (temp_dir / "shared/coordination/tasks.json").write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    yield temp_dir

    # クリーンアップ
    shutil.rmtree(temp_dir)


def test_get_next_task_returns_independent_task_first(test_project):
    """依存関係のないタスクが先に返される"""
    provider = TaskProvider(test_project)

    task = provider.get_next_task()

    assert task is not None
    assert task.id == "TASK-001"
    assert len(task.dependencies) == 0


def test_get_next_task_respects_dependencies(test_project):
    """依存関係を尊重する"""
    provider = TaskProvider(test_project)

    # TASK-001を完了
    provider.mark_completed("TASK-001", ["file1.py"])

    # 次はTASK-002が返される
    task = provider.get_next_task()
    assert task.id == "TASK-002"


def test_mark_completed_updates_status(test_project):
    """完了マークでステータスが更新される"""
    provider = TaskProvider(test_project)

    task = provider.coordinator.get_task("TASK-001")
    assert task.status == TaskStatus.PENDING

    provider.mark_completed("TASK-001", ["file1.py"])

    assert task.status == TaskStatus.COMPLETED
    assert task.artifacts == ["file1.py"]
    assert task.completed_at is not None


def test_mark_failed_blocks_dependent_tasks(test_project):
    """失敗すると依存タスクがブロックされる"""
    provider = TaskProvider(test_project)

    provider.mark_failed("TASK-001", "テストエラー")

    task2 = provider.coordinator.get_task("TASK-002")
    assert task2.status == TaskStatus.BLOCKED


def test_get_task_context(test_project):
    """タスクコンテキストを正しく取得できる"""
    provider = TaskProvider(test_project)

    context = provider.get_task_context("TASK-001")

    assert context is not None
    assert context["task"]["id"] == "TASK-001"
    assert context["task"]["title"] == "タスク1"
    assert context["task"]["target_files"] == ["file1.py"]
    assert context["task"]["acceptance_criteria"] == ["基準1", "基準2"]
    assert "requirements" in context
    assert "api_spec" in context
    assert "related_files" in context
    assert "dependencies_artifacts" in context
    assert "project_structure" in context


def test_mark_started_updates_status(test_project):
    """開始マークでステータスが更新される"""
    provider = TaskProvider(test_project)

    task = provider.coordinator.get_task("TASK-001")
    assert task.status == TaskStatus.PENDING

    provider.mark_started("TASK-001")

    assert task.status == TaskStatus.IN_PROGRESS
    assert task.started_at is not None


def test_get_next_task_skips_in_progress_tasks(test_project):
    """実行中のタスクをスキップする"""
    provider = TaskProvider(test_project)

    # TASK-001を開始
    provider.mark_started("TASK-001")

    # 次のタスクを取得（TASK-001は実行中なのでNoneが返る）
    task = provider.get_next_task()
    assert task is None  # 他に実行可能なタスクがないため


def test_progress_persistence(test_project):
    """進捗情報が永続化される"""
    provider = TaskProvider(test_project)

    # タスクを完了
    provider.mark_completed("TASK-001", ["file1.py"])

    # 新しいプロバイダーを作成（進捗を読み込み）
    provider2 = TaskProvider(test_project)

    task = provider2.coordinator.get_task("TASK-001")
    assert task.status == TaskStatus.COMPLETED
    assert task.artifacts == ["file1.py"]
