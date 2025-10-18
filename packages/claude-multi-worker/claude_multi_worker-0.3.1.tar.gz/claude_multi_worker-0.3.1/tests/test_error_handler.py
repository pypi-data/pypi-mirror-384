"""
ErrorHandlerのユニットテスト
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from cmw.error_handler import ErrorHandler, TaskFailureAction
from cmw.models import Task, TaskStatus


@pytest.fixture
def test_project():
    """テスト用プロジェクトを作成"""
    temp_dir = Path(tempfile.mkdtemp())

    # ディレクトリ構造を作成
    (temp_dir / "shared/coordination").mkdir(parents=True)
    (temp_dir / "shared/artifacts/backend").mkdir(parents=True)
    (temp_dir / "shared/artifacts/tests").mkdir(parents=True)

    yield temp_dir

    # クリーンアップ
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_task():
    """テスト用のサンプルタスク"""
    return Task(
        id="TASK-001",
        title="Sample Task",
        description="Test task",
        assigned_to="worker1",
        dependencies=[],
        target_files=["backend/test.py"],
        acceptance_criteria=["基準1"],
        priority="high"
    )


def test_handle_retryable_error(test_project, sample_task):
    """リトライ可能なエラーはRETRYアクションを返す"""
    handler = ErrorHandler(test_project)

    error = TimeoutError("Connection timeout")
    action = handler.handle_task_failure(sample_task, error, retry_count=0)

    assert action == TaskFailureAction.RETRY


def test_handle_retryable_error_exceeds_max_retries(test_project, sample_task):
    """リトライ上限に達したらBLOCKアクションを返す"""
    handler = ErrorHandler(test_project)

    error = TimeoutError("Connection timeout")
    action = handler.handle_task_failure(sample_task, error, retry_count=3, max_retries=3)

    assert action == TaskFailureAction.BLOCK


def test_handle_skippable_task(test_project):
    """スキップ可能なタスクはSKIPアクションを返す"""
    handler = ErrorHandler(test_project)

    # 優先度lowのタスク
    low_priority_task = Task(
        id="TASK-002",
        title="Optional Task",
        description="Low priority task",
        assigned_to="worker1",
        dependencies=[],
        target_files=["backend/optional.py"],
        acceptance_criteria=[],
        priority="low"
    )

    error = ValueError("Some error")
    action = handler.handle_task_failure(low_priority_task, error)

    assert action == TaskFailureAction.SKIP


def test_handle_non_retryable_error(test_project, sample_task):
    """リトライ不可能なエラーはBLOCKアクションを返す"""
    handler = ErrorHandler(test_project)

    error = ValueError("Invalid value")
    action = handler.handle_task_failure(sample_task, error)

    assert action == TaskFailureAction.BLOCK


def test_rollback_partial_work_with_files(test_project, sample_task):
    """部分的な成果物を正しく削除できる"""
    handler = ErrorHandler(test_project)

    # テストファイルを作成
    test_file = test_project / "shared/artifacts/backend/test.py"
    test_file.write_text("# test file", encoding='utf-8')
    sample_task.artifacts = ["backend/test.py"]

    # ロールバック実行
    success = handler.rollback_partial_work(sample_task)

    assert success
    assert not test_file.exists()
    assert len(sample_task.artifacts) == 0


def test_rollback_partial_work_with_directories(test_project, sample_task):
    """ディレクトリも正しく削除できる"""
    handler = ErrorHandler(test_project)

    # テストディレクトリを作成
    test_dir = test_project / "shared/artifacts/backend/subdir"
    test_dir.mkdir(parents=True)
    (test_dir / "file.py").write_text("# test", encoding='utf-8')
    sample_task.artifacts = ["backend/subdir"]

    # ロールバック実行
    success = handler.rollback_partial_work(sample_task)

    assert success
    assert not test_dir.exists()
    assert len(sample_task.artifacts) == 0


def test_rollback_partial_work_no_artifacts(test_project, sample_task):
    """成果物がない場合は成功を返す"""
    handler = ErrorHandler(test_project)
    sample_task.artifacts = []

    success = handler.rollback_partial_work(sample_task)

    assert success


def test_suggest_recovery_file_not_found(test_project, sample_task):
    """FileNotFoundErrorの復旧提案を生成"""
    handler = ErrorHandler(test_project)

    error = FileNotFoundError("File not found")
    suggestion = handler.suggest_recovery(sample_task, error)

    assert "TASK-001" in suggestion
    assert "FileNotFoundError" in suggestion
    assert "依存ファイル" in suggestion


def test_suggest_recovery_permission_error(test_project, sample_task):
    """PermissionErrorの復旧提案を生成"""
    handler = ErrorHandler(test_project)

    error = PermissionError("Permission denied")
    suggestion = handler.suggest_recovery(sample_task, error)

    assert "PermissionError" in suggestion
    assert "書き込み権限" in suggestion


def test_suggest_recovery_module_not_found(test_project, sample_task):
    """ModuleNotFoundErrorの復旧提案を生成"""
    handler = ErrorHandler(test_project)

    error = ModuleNotFoundError("No module named 'requests'")
    suggestion = handler.suggest_recovery(sample_task, error)

    assert "ModuleNotFoundError" in suggestion
    assert "pip install" in suggestion
    assert "requests" in suggestion


def test_suggest_recovery_with_dependencies(test_project):
    """依存タスクがある場合の復旧提案"""
    handler = ErrorHandler(test_project)

    task_with_deps = Task(
        id="TASK-002",
        title="Dependent Task",
        description="Task with dependencies",
        assigned_to="worker1",
        dependencies=["TASK-001"],
        target_files=["backend/dependent.py"],
        acceptance_criteria=[],
        priority="high"
    )

    error = ValueError("Some error")
    suggestion = handler.suggest_recovery(task_with_deps, error)

    assert "TASK-001" in suggestion
    assert "依存タスク" in suggestion


def test_get_affected_tasks(test_project):
    """失敗タスクの影響を受けるタスクを正しく取得"""
    handler = ErrorHandler(test_project)

    # タスクツリーを作成
    task1 = Task(
        id="TASK-001",
        title="Task 1",
        description="Base task",
        assigned_to="worker1",
        dependencies=[],
        target_files=["file1.py"],
        acceptance_criteria=[],
        priority="high"
    )

    task2 = Task(
        id="TASK-002",
        title="Task 2",
        description="Depends on TASK-001",
        assigned_to="worker1",
        dependencies=["TASK-001"],
        target_files=["file2.py"],
        acceptance_criteria=[],
        priority="medium"
    )

    task3 = Task(
        id="TASK-003",
        title="Task 3",
        description="Depends on TASK-002",
        assigned_to="worker1",
        dependencies=["TASK-002"],
        target_files=["file3.py"],
        acceptance_criteria=[],
        priority="medium"
    )

    task4 = Task(
        id="TASK-004",
        title="Task 4",
        description="Independent task",
        assigned_to="worker1",
        dependencies=[],
        target_files=["file4.py"],
        acceptance_criteria=[],
        priority="low"
    )

    all_tasks = [task1, task2, task3, task4]

    # TASK-001が失敗した場合
    affected = handler.get_affected_tasks(task1, all_tasks)

    # TASK-002とTASK-003が影響を受ける
    assert len(affected) == 2
    assert task2 in affected
    assert task3 in affected
    assert task4 not in affected


def test_is_retryable_error_by_type(test_project, sample_task):
    """エラータイプによるリトライ判定"""
    handler = ErrorHandler(test_project)

    # TimeoutErrorはリトライ可能
    assert handler._is_retryable_error("TimeoutError", "")

    # ConnectionErrorはリトライ可能
    assert handler._is_retryable_error("ConnectionError", "")

    # ValueErrorはリトライ不可
    assert not handler._is_retryable_error("ValueError", "")


def test_is_retryable_error_by_message(test_project, sample_task):
    """エラーメッセージによるリトライ判定"""
    handler = ErrorHandler(test_project)

    # "timeout"を含むメッセージ
    assert handler._is_retryable_error("CustomError", "Operation timeout occurred")

    # "try again"を含むメッセージ
    assert handler._is_retryable_error("CustomError", "Please try again later")

    # リトライ不可能なメッセージ
    assert not handler._is_retryable_error("CustomError", "Invalid input")


def test_is_skippable_task(test_project):
    """スキップ可能なタスクの判定"""
    handler = ErrorHandler(test_project)

    # 優先度lowで依存なし
    low_task = Task(
        id="TASK-001",
        title="Task",
        description="desc",
        assigned_to="worker1",
        dependencies=[],
        target_files=["file.py"],
        acceptance_criteria=[],
        priority="low"
    )
    assert handler._is_skippable_task(low_task)

    # タイトルに"optional"を含む
    optional_task = Task(
        id="TASK-002",
        title="Optional Feature",
        description="desc",
        assigned_to="worker1",
        dependencies=[],
        target_files=["file.py"],
        acceptance_criteria=[],
        priority="high"
    )
    assert handler._is_skippable_task(optional_task)

    # スキップ不可能なタスク
    required_task = Task(
        id="TASK-003",
        title="Required Task",
        description="desc",
        assigned_to="worker1",
        dependencies=[],
        target_files=["file.py"],
        acceptance_criteria=[],
        priority="high"
    )
    assert not handler._is_skippable_task(required_task)


def test_should_rollback_with_artifacts(test_project, sample_task):
    """成果物がある場合はロールバックが必要"""
    handler = ErrorHandler(test_project)
    sample_task.artifacts = ["backend/test.py"]

    error = ValueError("Some error")
    should_rollback = handler._should_rollback(sample_task, error)

    assert should_rollback


def test_should_rollback_integrity_error(test_project, sample_task):
    """データ整合性エラーはロールバックが必要"""
    handler = ErrorHandler(test_project)
    sample_task.artifacts = []

    # カスタム IntegrityError を作成
    class IntegrityError(Exception):
        pass

    error = IntegrityError("Integrity constraint violated")
    should_rollback = handler._should_rollback(sample_task, error)

    assert should_rollback


def test_extract_module_name(test_project, sample_task):
    """エラーメッセージからモジュール名を抽出"""
    handler = ErrorHandler(test_project)

    # 標準的なフォーマット
    module_name = handler._extract_module_name("No module named 'requests'")
    assert module_name == "requests"

    # ネストされたモジュール
    module_name = handler._extract_module_name("No module named 'django.contrib.auth'")
    assert module_name == "django.contrib.auth"

    # 抽出できない場合
    module_name = handler._extract_module_name("Some other error")
    assert module_name == "unknown"
