"""
Coordinatorクラスのユニットテスト

progress.json読み込み・マージ機能のテスト
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from cmw.coordinator import Coordinator
from cmw.models import TaskStatus


@pytest.fixture
def temp_project(tmp_path):
    """テスト用のプロジェクトディレクトリを作成"""
    coordination_dir = tmp_path / "shared" / "coordination"
    coordination_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def tasks_json(temp_project):
    """tasks.jsonを作成"""
    tasks_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "タスク1",
                "description": "テスト用タスク",
                "assigned_to": "backend",
                "dependencies": [],
                "target_files": ["backend/main.py"],
                "acceptance_criteria": ["実装する"],
                "priority": "high"
            },
            {
                "id": "TASK-002",
                "title": "タスク2",
                "description": "テスト用タスク2",
                "assigned_to": "backend",
                "dependencies": ["TASK-001"],
                "target_files": ["backend/utils.py"],
                "acceptance_criteria": ["実装する"],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')
    return tasks_path


@pytest.fixture
def progress_json(temp_project):
    """progress.jsonを作成（TASK-001が完了）"""
    now = datetime.now().isoformat()
    progress_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "タスク1",
                "description": "テスト用タスク",
                "assigned_to": "backend",
                "dependencies": [],
                "target_files": ["backend/main.py"],
                "acceptance_criteria": ["実装する"],
                "priority": "high",
                "status": "completed",
                "artifacts": ["backend/main.py", "tests/test_main.py"],
                "completed_at": now,
                "started_at": None,
                "failed_at": None,
                "error_message": None
            },
            {
                "id": "TASK-002",
                "title": "タスク2",
                "description": "テスト用タスク2",
                "assigned_to": "backend",
                "dependencies": ["TASK-001"],
                "target_files": ["backend/utils.py"],
                "acceptance_criteria": ["実装する"],
                "priority": "medium",
                "status": "pending",
                "artifacts": [],
                "completed_at": None,
                "started_at": None,
                "failed_at": None,
                "error_message": None
            }
        ]
    }

    progress_path = temp_project / "shared" / "coordination" / "progress.json"
    progress_path.write_text(json.dumps(progress_data, ensure_ascii=False, indent=2), encoding='utf-8')
    return progress_path


class TestCoordinatorProgressLoading:
    """Coordinatorのprogress.json読み込みテスト"""

    def test_load_tasks_without_progress(self, temp_project, tasks_json):
        """progress.jsonがない場合、tasks.jsonのみ読み込む"""
        coordinator = Coordinator(temp_project)

        # タスクが読み込まれている
        assert len(coordinator.tasks) == 2
        assert "TASK-001" in coordinator.tasks
        assert "TASK-002" in coordinator.tasks

        # 両方ともpending状態
        assert coordinator.tasks["TASK-001"].status == TaskStatus.PENDING
        assert coordinator.tasks["TASK-002"].status == TaskStatus.PENDING

    def test_load_tasks_with_progress(self, temp_project, tasks_json, progress_json):
        """progress.jsonがある場合、進捗状況をマージする"""
        coordinator = Coordinator(temp_project)

        # タスクが読み込まれている
        assert len(coordinator.tasks) == 2

        # TASK-001はcompleted、TASK-002はpending
        task_001 = coordinator.tasks["TASK-001"]
        assert task_001.status == TaskStatus.COMPLETED
        assert task_001.artifacts == ["backend/main.py", "tests/test_main.py"]
        assert task_001.completed_at is not None

        task_002 = coordinator.tasks["TASK-002"]
        assert task_002.status == TaskStatus.PENDING
        assert task_002.artifacts == []

    def test_update_task_status_saves_progress(self, temp_project, tasks_json):
        """update_task_statusでprogress.jsonが更新される"""
        coordinator = Coordinator(temp_project)

        # タスクを完了マーク
        coordinator.update_task_status(
            task_id="TASK-001",
            status=TaskStatus.COMPLETED,
            artifacts=["backend/main.py"]
        )

        # progress.jsonが作成されている
        progress_path = temp_project / "shared" / "coordination" / "progress.json"
        assert progress_path.exists()

        # progress.jsonに完了状態が保存されている
        progress_data = json.loads(progress_path.read_text(encoding='utf-8'))
        task_001_data = next(t for t in progress_data["tasks"] if t["id"] == "TASK-001")

        assert task_001_data["status"] == "completed"
        assert task_001_data["artifacts"] == ["backend/main.py"]
        assert task_001_data["completed_at"] is not None

    def test_progress_persists_across_instances(self, temp_project, tasks_json):
        """進捗状況が別のCoordinatorインスタンスでも保持される"""
        # 1つ目のインスタンスでタスクを完了
        coordinator1 = Coordinator(temp_project)
        coordinator1.update_task_status(
            task_id="TASK-001",
            status=TaskStatus.COMPLETED,
            artifacts=["backend/main.py"]
        )

        # 2つ目のインスタンスで進捗を読み込む
        coordinator2 = Coordinator(temp_project)

        # 進捗が保持されている
        task_001 = coordinator2.tasks["TASK-001"]
        assert task_001.status == TaskStatus.COMPLETED
        assert task_001.artifacts == ["backend/main.py"]
        assert task_001.completed_at is not None

    def test_get_executable_tasks(self, temp_project, tasks_json, progress_json):
        """依存関係を考慮した実行可能タスクの取得"""
        coordinator = Coordinator(temp_project)

        # TASK-001が完了しているので、TASK-002が実行可能
        executable = coordinator.get_executable_tasks()

        assert len(executable) == 1
        assert executable[0].id == "TASK-002"

    def test_update_with_error_message(self, temp_project, tasks_json):
        """エラーメッセージ付きでステータス更新"""
        coordinator = Coordinator(temp_project)

        coordinator.update_task_status(
            task_id="TASK-001",
            status=TaskStatus.FAILED,
            error_message="テストエラー"
        )

        # エラーメッセージが保存されている
        task_001 = coordinator.tasks["TASK-001"]
        assert task_001.status == TaskStatus.FAILED
        assert task_001.error_message == "テストエラー"

        # progress.jsonにも保存されている
        coordinator2 = Coordinator(temp_project)
        task_001_reloaded = coordinator2.tasks["TASK-001"]
        assert task_001_reloaded.status == TaskStatus.FAILED
        assert task_001_reloaded.error_message == "テストエラー"


class TestCoordinatorTaskRetrieval:
    """Coordinatorのタスク取得テスト"""

    def test_get_task_existing(self, temp_project, tasks_json):
        """存在するタスクを取得"""
        coordinator = Coordinator(temp_project)
        task = coordinator.get_task("TASK-001")

        assert task is not None
        assert task.id == "TASK-001"
        assert task.title == "タスク1"

    def test_get_task_non_existing(self, temp_project, tasks_json):
        """存在しないタスクを取得"""
        coordinator = Coordinator(temp_project)
        task = coordinator.get_task("TASK-999")

        assert task is None
