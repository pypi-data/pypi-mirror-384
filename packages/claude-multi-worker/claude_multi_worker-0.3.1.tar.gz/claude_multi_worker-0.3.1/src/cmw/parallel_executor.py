"""
ParallelExecutor - 並列実行の制御

役割:
- ファイル競合の検出
- 並列実行可能なタスクの判定
- 実行グループの管理
"""
from pathlib import Path
from typing import List, Set
from .models import Task, TaskStatus
from .task_provider import TaskProvider


class ParallelExecutor:
    """並列実行の制御"""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.provider = TaskProvider(project_path)

    def get_executable_tasks(self, max_parallel: int = 3) -> List[Task]:
        """
        並列実行可能なタスクを取得

        Args:
            max_parallel: 最大並列実行数

        Returns:
            並列実行可能なタスクのリスト
        """
        # 準備完了タスクを全て取得
        ready_tasks = self._get_all_ready_tasks()

        if not ready_tasks:
            return []

        # ファイル競合を考慮して選択
        executable = []
        used_files: Set[str] = set()

        for task in ready_tasks:
            if len(executable) >= max_parallel:
                break

            task_files = self._get_task_files(task)

            # 既に使用中のファイルと重複しないかチェック
            if not task_files & used_files:
                executable.append(task)
                used_files.update(task_files)

        return executable

    def can_run_parallel(self, task1: Task, task2: Task) -> bool:
        """
        2つのタスクが並列実行可能か判定

        Args:
            task1, task2: タスク

        Returns:
            並列実行可能ならTrue
        """
        files1 = self._get_task_files(task1)
        files2 = self._get_task_files(task2)

        # ファイルが重複していなければ並列実行可能
        return not (files1 & files2)

    def group_tasks_by_parallelism(self, tasks: List[Task]) -> List[List[Task]]:
        """
        タスクを並列実行可能なグループに分ける

        Args:
            tasks: タスクのリスト

        Returns:
            並列実行可能なグループのリスト
        """
        groups = []
        remaining = tasks.copy()

        while remaining:
            # 新しいグループを作成
            group = []
            used_files: Set[str] = set()

            # 並列実行可能なタスクをグループに追加
            for task in remaining[:]:
                task_files = self._get_task_files(task)

                if not task_files & used_files:
                    group.append(task)
                    used_files.update(task_files)
                    remaining.remove(task)

            if group:
                groups.append(group)
            else:
                # 無限ループ防止
                break

        return groups

    # === プライベートメソッド ===

    def _get_all_ready_tasks(self) -> List[Task]:
        """実行可能な全タスクを取得"""
        ready = []
        task = self.provider.get_next_task()

        # 次のタスクを順次取得
        while task:
            ready.append(task)
            # 一時的に実行中にマーク（競合チェック用）
            task.status = TaskStatus.IN_PROGRESS
            task = self.provider.get_next_task()

        # ステータスを戻す
        for t in ready:
            t.status = TaskStatus.PENDING

        return ready

    def _get_task_files(self, task: Task) -> Set[str]:
        """
        タスクが扱うファイルの集合を取得

        target_files と related_files の両方を含む
        """
        files = set(task.target_files)

        # 依存タスクの成果物も含める（読み取り専用だが念のため）
        for dep_id in task.dependencies:
            dep_task = self.provider.coordinator.get_task(dep_id)
            if dep_task and dep_task.artifacts:
                files.update(dep_task.artifacts)

        return files
