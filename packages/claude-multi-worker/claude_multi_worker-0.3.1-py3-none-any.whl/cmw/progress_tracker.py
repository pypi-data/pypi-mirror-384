"""
リアルタイム進捗追跡とターミナルダッシュボード

このモジュールは、タスクの進捗状況をリアルタイムで追跡し、
ターミナル上に見やすいダッシュボードを表示します。
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from .models import Task, TaskStatus


class ProgressTracker:
    """進捗追跡とメトリクス計算"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.progress_file = project_path / "shared" / "coordination" / "progress.json"
        self.metrics_file = project_path / "shared" / "coordination" / "metrics.json"

    def get_progress_summary(self, tasks: List[Task]) -> Dict:
        """
        進捗サマリーを取得

        Returns:
            {
                'total': 総タスク数,
                'completed': 完了数,
                'in_progress': 実行中,
                'failed': 失敗,
                'blocked': ブロック,
                'pending': 待機中,
                'completion_rate': 完了率(0-100),
                'success_rate': 成功率(0-100)
            }
        """
        total = len(tasks)
        if total == 0:
            return {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'failed': 0,
                'blocked': 0,
                'pending': 0,
                'completion_rate': 0.0,
                'success_rate': 0.0
            }

        status_counts = {
            'completed': sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            'in_progress': sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            'failed': sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            'blocked': sum(1 for t in tasks if t.status == TaskStatus.BLOCKED),
            'pending': sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        }

        completion_rate = (status_counts['completed'] / total) * 100

        # 成功率 = 完了 / (完了 + 失敗)
        attempted = status_counts['completed'] + status_counts['failed']
        success_rate = (status_counts['completed'] / attempted * 100) if attempted > 0 else 100.0

        return {
            'total': total,
            'completion_rate': completion_rate,
            'success_rate': success_rate,
            **status_counts
        }

    def estimate_remaining_time(self, tasks: List[Task]) -> Optional[timedelta]:
        """
        残り時間を推定

        完了したタスクの平均所要時間から推定

        Returns:
            推定残り時間（timedelta）、データ不足の場合はNone
        """
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]

        if not completed_tasks:
            return None

        # 完了タスクの平均所要時間を計算
        total_duration = timedelta()
        valid_count = 0

        for task in completed_tasks:
            if task.started_at and task.completed_at:
                duration = task.completed_at - task.started_at
                total_duration += duration
                valid_count += 1

        if valid_count == 0:
            return None

        avg_duration = total_duration / valid_count

        # 残りタスク数（実行中 + 待機中）
        remaining_count = sum(
            1 for t in tasks
            if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        )

        return avg_duration * remaining_count

    def get_task_timeline(self, tasks: List[Task]) -> List[Dict]:
        """
        タスクタイムラインを取得

        Returns:
            タイムラインイベントのリスト [
                {
                    'timestamp': datetime,
                    'task_id': str,
                    'event': 'started' | 'completed' | 'failed',
                    'title': str
                }
            ]
        """
        events = []

        for task in tasks:
            if task.started_at:
                events.append({
                    'timestamp': task.started_at,
                    'task_id': task.id,
                    'event': 'started',
                    'title': task.title
                })

            if task.completed_at:
                events.append({
                    'timestamp': task.completed_at,
                    'task_id': task.id,
                    'event': 'completed',
                    'title': task.title
                })

            if task.failed_at:
                events.append({
                    'timestamp': task.failed_at,
                    'task_id': task.id,
                    'event': 'failed',
                    'title': task.title
                })

        # タイムスタンプでソート
        events.sort(key=lambda x: x['timestamp'])

        return events

    def get_velocity_metrics(self, tasks: List[Task]) -> Dict:
        """
        ベロシティメトリクスを取得

        Returns:
            {
                'tasks_per_hour': 1時間あたりの完了タスク数,
                'avg_task_duration': 平均タスク所要時間（秒）,
                'total_working_time': 総作業時間（秒）
            }
        """
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]

        if not completed_tasks:
            return {
                'tasks_per_hour': 0.0,
                'avg_task_duration': 0.0,
                'total_working_time': 0.0
            }

        # タスク所要時間を計算
        durations = []
        for task in completed_tasks:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                durations.append(duration)

        if not durations:
            return {
                'tasks_per_hour': 0.0,
                'avg_task_duration': 0.0,
                'total_working_time': 0.0
            }

        avg_duration = sum(durations) / len(durations)
        total_time = sum(durations)

        # 1時間あたりのタスク数
        tasks_per_hour = (3600 / avg_duration) if avg_duration > 0 else 0

        return {
            'tasks_per_hour': tasks_per_hour,
            'avg_task_duration': avg_duration,
            'total_working_time': total_time
        }

    def get_priority_breakdown(self, tasks: List[Task]) -> Dict[str, Dict]:
        """
        優先度別の進捗を取得

        Returns:
            {
                'high': {'total': 5, 'completed': 3, 'pending': 2, ...},
                'medium': {...},
                'low': {...}
            }
        """
        breakdown = {
            'high': {'total': 0, 'completed': 0, 'in_progress': 0, 'failed': 0, 'blocked': 0, 'pending': 0},
            'medium': {'total': 0, 'completed': 0, 'in_progress': 0, 'failed': 0, 'blocked': 0, 'pending': 0},
            'low': {'total': 0, 'completed': 0, 'in_progress': 0, 'failed': 0, 'blocked': 0, 'pending': 0}
        }

        for task in tasks:
            priority = task.priority
            if priority not in breakdown:
                continue

            breakdown[priority]['total'] += 1

            if task.status == TaskStatus.COMPLETED:
                breakdown[priority]['completed'] += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                breakdown[priority]['in_progress'] += 1
            elif task.status == TaskStatus.FAILED:
                breakdown[priority]['failed'] += 1
            elif task.status == TaskStatus.BLOCKED:
                breakdown[priority]['blocked'] += 1
            elif task.status == TaskStatus.PENDING:
                breakdown[priority]['pending'] += 1

        return breakdown

    def get_worker_breakdown(self, tasks: List[Task]) -> Dict[str, Dict]:
        """
        担当者別の進捗を取得

        Returns:
            {
                'backend': {'total': 10, 'completed': 5, ...},
                'frontend': {...},
                ...
            }
        """
        workers = {}

        for task in tasks:
            worker = task.assigned_to
            if worker not in workers:
                workers[worker] = {
                    'total': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'failed': 0,
                    'blocked': 0,
                    'pending': 0
                }

            workers[worker]['total'] += 1

            if task.status == TaskStatus.COMPLETED:
                workers[worker]['completed'] += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                workers[worker]['in_progress'] += 1
            elif task.status == TaskStatus.FAILED:
                workers[worker]['failed'] += 1
            elif task.status == TaskStatus.BLOCKED:
                workers[worker]['blocked'] += 1
            elif task.status == TaskStatus.PENDING:
                workers[worker]['pending'] += 1

        return workers

    def save_metrics(self, tasks: List[Task]) -> None:
        """
        メトリクスをファイルに保存

        Args:
            tasks: タスクリスト
        """
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_progress_summary(tasks),
            'velocity': self.get_velocity_metrics(tasks),
            'priority_breakdown': self.get_priority_breakdown(tasks),
            'worker_breakdown': self.get_worker_breakdown(tasks)
        }

        # 残り時間推定
        remaining_time = self.estimate_remaining_time(tasks)
        if remaining_time:
            metrics['estimated_remaining_seconds'] = remaining_time.total_seconds()

        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_file.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    def load_metrics(self) -> Optional[Dict]:
        """
        保存されたメトリクスを読み込み

        Returns:
            メトリクスデータ、ファイルがない場合はNone
        """
        if not self.metrics_file.exists():
            return None

        try:
            return json.loads(self.metrics_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            return None
