"""
ProgressTrackerのテスト
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from src.cmw.progress_tracker import ProgressTracker
from src.cmw.models import Task, TaskStatus


class TestProgressTracker:
    """ProgressTrackerのテスト"""

    @pytest.fixture
    def temp_project(self):
        """一時プロジェクトディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / "shared" / "coordination").mkdir(parents=True)
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def tracker(self, temp_project):
        """ProgressTrackerインスタンス"""
        return ProgressTracker(temp_project)

    @pytest.fixture
    def sample_tasks(self):
        """サンプルタスク"""
        now = datetime.now()
        return [
            Task(
                id="TASK-001",
                title="Database Setup",
                description="Setup database",
                assigned_to="backend",
                target_files=["database.py"],
                dependencies=[],
                priority="high",
                status=TaskStatus.COMPLETED,
                started_at=now - timedelta(hours=2),
                completed_at=now - timedelta(hours=1, minutes=30)
            ),
            Task(
                id="TASK-002",
                title="Models",
                description="Create models",
                assigned_to="backend",
                target_files=["models.py"],
                dependencies=["TASK-001"],
                priority="high",
                status=TaskStatus.COMPLETED,
                started_at=now - timedelta(hours=1, minutes=30),
                completed_at=now - timedelta(hours=1)
            ),
            Task(
                id="TASK-003",
                title="Schemas",
                description="Create schemas",
                assigned_to="backend",
                target_files=["schemas.py"],
                dependencies=["TASK-002"],
                priority="medium",
                status=TaskStatus.IN_PROGRESS,
                started_at=now - timedelta(minutes=30)
            ),
            Task(
                id="TASK-004",
                title="Auth",
                description="Authentication",
                assigned_to="backend",
                target_files=["auth.py"],
                dependencies=[],
                priority="medium",
                status=TaskStatus.PENDING
            ),
            Task(
                id="TASK-005",
                title="Tests",
                description="Write tests",
                assigned_to="testing",
                target_files=["test_auth.py"],
                dependencies=["TASK-004"],
                priority="low",
                status=TaskStatus.PENDING
            )
        ]

    def test_get_progress_summary(self, tracker, sample_tasks):
        """進捗サマリーを取得"""
        summary = tracker.get_progress_summary(sample_tasks)

        assert summary['total'] == 5
        assert summary['completed'] == 2
        assert summary['in_progress'] == 1
        assert summary['pending'] == 2
        assert summary['failed'] == 0
        assert summary['blocked'] == 0
        assert summary['completion_rate'] == 40.0  # 2/5 * 100
        assert summary['success_rate'] == 100.0  # 2完了、0失敗

    def test_get_progress_summary_empty(self, tracker):
        """空のタスクリスト"""
        summary = tracker.get_progress_summary([])

        assert summary['total'] == 0
        assert summary['completion_rate'] == 0.0

    def test_get_progress_summary_with_failures(self, tracker):
        """失敗タスクを含む進捗サマリー"""
        tasks = [
            Task(
                id="TASK-001",
                title="Task 1",
                description="Test",
                assigned_to="backend",
                target_files=["test.py"],
                dependencies=[],
                priority="high",
                status=TaskStatus.COMPLETED
            ),
            Task(
                id="TASK-002",
                title="Task 2",
                description="Test",
                assigned_to="backend",
                target_files=["test2.py"],
                dependencies=[],
                priority="high",
                status=TaskStatus.FAILED
            )
        ]

        summary = tracker.get_progress_summary(tasks)
        assert summary['success_rate'] == 50.0  # 1完了 / (1完了 + 1失敗)

    def test_estimate_remaining_time(self, tracker, sample_tasks):
        """残り時間を推定"""
        remaining = tracker.estimate_remaining_time(sample_tasks)

        assert remaining is not None
        # 完了タスク2つ、平均30分
        # 残りタスク3つ（実行中1 + 待機中2）
        # 推定: 30分 * 3 = 90分
        expected_seconds = 90 * 60
        assert abs(remaining.total_seconds() - expected_seconds) < 60  # 1分の誤差許容

    def test_estimate_remaining_time_no_completed(self, tracker):
        """完了タスクがない場合"""
        tasks = [
            Task(
                id="TASK-001",
                title="Task 1",
                description="Test",
                assigned_to="backend",
                target_files=["test.py"],
                dependencies=[],
                priority="high",
                status=TaskStatus.PENDING
            )
        ]

        remaining = tracker.estimate_remaining_time(tasks)
        assert remaining is None

    def test_get_task_timeline(self, tracker, sample_tasks):
        """タスクタイムラインを取得"""
        timeline = tracker.get_task_timeline(sample_tasks)

        # TASK-001: started, completed
        # TASK-002: started, completed
        # TASK-003: started
        assert len(timeline) == 5

        # タイムスタンプでソートされている
        for i in range(len(timeline) - 1):
            assert timeline[i]['timestamp'] <= timeline[i + 1]['timestamp']

        # イベントタイプ
        events = [e['event'] for e in timeline]
        assert events.count('started') == 3
        assert events.count('completed') == 2

    def test_get_velocity_metrics(self, tracker, sample_tasks):
        """ベロシティメトリクスを取得"""
        metrics = tracker.get_velocity_metrics(sample_tasks)

        assert metrics['tasks_per_hour'] > 0
        assert metrics['avg_task_duration'] > 0
        assert metrics['total_working_time'] > 0

        # 完了タスク2つ、各30分 = 総60分
        assert abs(metrics['total_working_time'] - 3600) < 60  # 1分の誤差許容

    def test_get_velocity_metrics_no_completed(self, tracker):
        """完了タスクがない場合"""
        tasks = [
            Task(
                id="TASK-001",
                title="Task 1",
                description="Test",
                assigned_to="backend",
                target_files=["test.py"],
                dependencies=[],
                priority="high",
                status=TaskStatus.PENDING
            )
        ]

        metrics = tracker.get_velocity_metrics(tasks)
        assert metrics['tasks_per_hour'] == 0.0
        assert metrics['avg_task_duration'] == 0.0

    def test_get_priority_breakdown(self, tracker, sample_tasks):
        """優先度別の進捗を取得"""
        breakdown = tracker.get_priority_breakdown(sample_tasks)

        assert 'high' in breakdown
        assert 'medium' in breakdown
        assert 'low' in breakdown

        # high: TASK-001 (completed), TASK-002 (completed)
        assert breakdown['high']['total'] == 2
        assert breakdown['high']['completed'] == 2

        # medium: TASK-003 (in_progress), TASK-004 (pending)
        assert breakdown['medium']['total'] == 2
        assert breakdown['medium']['in_progress'] == 1
        assert breakdown['medium']['pending'] == 1

        # low: TASK-005 (pending)
        assert breakdown['low']['total'] == 1
        assert breakdown['low']['pending'] == 1

    def test_get_worker_breakdown(self, tracker, sample_tasks):
        """担当者別の進捗を取得"""
        workers = tracker.get_worker_breakdown(sample_tasks)

        assert 'backend' in workers
        assert 'testing' in workers

        # backend: 4タスク
        assert workers['backend']['total'] == 4
        assert workers['backend']['completed'] == 2
        assert workers['backend']['in_progress'] == 1
        assert workers['backend']['pending'] == 1

        # testing: 1タスク
        assert workers['testing']['total'] == 1
        assert workers['testing']['pending'] == 1

    def test_save_and_load_metrics(self, tracker, sample_tasks):
        """メトリクスの保存と読み込み"""
        # 保存
        tracker.save_metrics(sample_tasks)

        # ファイルが作成されたことを確認
        assert tracker.metrics_file.exists()

        # 読み込み
        metrics = tracker.load_metrics()
        assert metrics is not None
        assert 'summary' in metrics
        assert 'velocity' in metrics
        assert 'priority_breakdown' in metrics
        assert 'worker_breakdown' in metrics

        # サマリー内容を確認
        assert metrics['summary']['total'] == 5
        assert metrics['summary']['completed'] == 2

    def test_load_metrics_no_file(self, tracker):
        """メトリクスファイルが存在しない場合"""
        metrics = tracker.load_metrics()
        assert metrics is None
