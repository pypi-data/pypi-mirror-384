"""
ParallelExecutorのユニットテスト
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import json
from cmw.parallel_executor import ParallelExecutor
from cmw.models import Task, TaskStatus


@pytest.fixture
def test_project():
    """テスト用プロジェクトを作成"""
    temp_dir = Path(tempfile.mkdtemp())

    # ディレクトリ構造を作成
    (temp_dir / "shared/coordination").mkdir(parents=True)
    (temp_dir / "shared/docs").mkdir(parents=True)
    (temp_dir / "shared/artifacts").mkdir(parents=True)

    # tasks.jsonを作成（ファイル競合のテスト用）
    tasks = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "タスク1",
                "description": "説明1",
                "assigned_to": "worker1",
                "dependencies": [],
                "target_files": ["file1.py"],
                "acceptance_criteria": [],
                "priority": "high"
            },
            {
                "id": "TASK-002",
                "title": "タスク2",
                "description": "説明2",
                "assigned_to": "worker1",
                "dependencies": [],
                "target_files": ["file2.py"],
                "acceptance_criteria": [],
                "priority": "medium"
            },
            {
                "id": "TASK-003",
                "title": "タスク3",
                "description": "説明3",
                "assigned_to": "worker1",
                "dependencies": [],
                "target_files": ["file1.py"],  # TASK-001と競合
                "acceptance_criteria": [],
                "priority": "low"
            },
            {
                "id": "TASK-004",
                "title": "タスク4",
                "description": "説明4",
                "assigned_to": "worker1",
                "dependencies": ["TASK-001"],
                "target_files": ["file4.py"],
                "acceptance_criteria": [],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    (temp_dir / "shared/coordination/tasks.json").write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    yield temp_dir

    # クリーンアップ
    shutil.rmtree(temp_dir)


def test_get_executable_tasks(test_project):
    """並列実行可能なタスクを取得できる"""
    executor = ParallelExecutor(test_project)

    executable = executor.get_executable_tasks(max_parallel=3)

    # TASK-001とTASK-002は並列実行可能（ファイルが異なる）
    # TASK-003はTASK-001と競合するので除外される
    assert len(executable) <= 3
    assert len(executable) >= 1  # 少なくとも1つは実行可能

    # ファイル競合がないことを確認
    all_files = set()
    for task in executable:
        task_files = executor._get_task_files(task)
        assert not (task_files & all_files), "ファイル競合が検出された"
        all_files.update(task_files)


def test_can_run_parallel_no_conflict(test_project):
    """ファイルが競合しないタスクは並列実行可能"""
    executor = ParallelExecutor(test_project)

    task1 = executor.provider.coordinator.get_task("TASK-001")
    task2 = executor.provider.coordinator.get_task("TASK-002")

    # TASK-001とTASK-002はファイルが異なるので並列実行可能
    assert executor.can_run_parallel(task1, task2)


def test_can_run_parallel_with_conflict(test_project):
    """ファイルが競合するタスクは並列実行不可"""
    executor = ParallelExecutor(test_project)

    task1 = executor.provider.coordinator.get_task("TASK-001")
    task3 = executor.provider.coordinator.get_task("TASK-003")

    # TASK-001とTASK-003は同じファイル（file1.py）を使用するので並列実行不可
    assert not executor.can_run_parallel(task1, task3)


def test_group_tasks_by_parallelism(test_project):
    """タスクを並列実行可能なグループに分ける"""
    executor = ParallelExecutor(test_project)

    # 全タスクを取得
    all_tasks = [
        executor.provider.coordinator.get_task("TASK-001"),
        executor.provider.coordinator.get_task("TASK-002"),
        executor.provider.coordinator.get_task("TASK-003"),
    ]

    groups = executor.group_tasks_by_parallelism(all_tasks)

    # グループが作成される
    assert len(groups) > 0

    # 各グループ内でファイル競合がないことを確認
    for group in groups:
        all_files = set()
        for task in group:
            task_files = executor._get_task_files(task)
            assert not (task_files & all_files), f"グループ内でファイル競合: {task.id}"
            all_files.update(task_files)


def test_get_all_ready_tasks(test_project):
    """実行可能な全タスクを取得できる"""
    executor = ParallelExecutor(test_project)

    ready_tasks = executor._get_all_ready_tasks()

    # 依存関係のないタスクが取得される
    # TASK-001, TASK-002, TASK-003は依存なし
    # TASK-004はTASK-001に依存しているので取得されない
    assert len(ready_tasks) >= 1

    # 全てのタスクがPENDING状態に戻っている
    for task in ready_tasks:
        assert task.status == TaskStatus.PENDING


def test_get_executable_tasks_respects_max_parallel(test_project):
    """最大並列数を尊重する"""
    executor = ParallelExecutor(test_project)

    # 最大2タスクに制限
    executable = executor.get_executable_tasks(max_parallel=2)

    assert len(executable) <= 2


def test_get_task_files(test_project):
    """タスクが扱うファイルを正しく取得できる"""
    executor = ParallelExecutor(test_project)

    task1 = executor.provider.coordinator.get_task("TASK-001")
    files = executor._get_task_files(task1)

    # TASK-001のtarget_filesが含まれる
    assert "file1.py" in files


def test_get_task_files_includes_dependencies(test_project):
    """依存タスクの成果物も含まれる"""
    executor = ParallelExecutor(test_project)

    # TASK-001を完了させる
    executor.provider.mark_completed("TASK-001", ["file1.py"])

    # TASK-004はTASK-001に依存
    task4 = executor.provider.coordinator.get_task("TASK-004")
    files = executor._get_task_files(task4)

    # TASK-004のtarget_filesとTASK-001の成果物が含まれる
    assert "file4.py" in files
    assert "file1.py" in files  # 依存タスクの成果物
