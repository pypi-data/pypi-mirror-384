"""
Git Integration - Git連携による進捗自動更新

Gitコミットメッセージからタスク完了を自動検出し、進捗を同期します。
"""
import re
import subprocess
from pathlib import Path
from typing import List, Set, Dict, Optional
from datetime import datetime, timedelta

from .coordinator import Coordinator
from .models import TaskStatus


class GitIntegration:
    """Git連携機能を提供するクラス"""

    def __init__(self):
        """GitIntegrationを初期化"""
        self.task_pattern = re.compile(r'TASK-\d{3}')

    def sync_progress_from_git(
        self,
        project_path: Path,
        since: Optional[str] = None,
        branch: str = "HEAD"
    ) -> Dict[str, any]:
        """
        Gitコミット履歴から進捗を同期

        Args:
            project_path: プロジェクトパス
            since: コミット検索の開始時点（例: "1.day.ago", "1.week.ago", "2025-01-01"）
                   Noneの場合は全履歴を検索
            branch: ブランチ名（デフォルト: HEAD）

        Returns:
            {
                'completed_tasks': ['TASK-001', 'TASK-002'],
                'updated_count': 2,
                'skipped_count': 0,
                'commits_analyzed': 10
            }
        """
        # プロジェクトがGitリポジトリか確認
        if not self._is_git_repo(project_path):
            raise ValueError(f"{project_path} はGitリポジトリではありません")

        # コミットログを取得
        commits = self._get_commit_log(project_path, since, branch)

        # コミットメッセージからタスクIDを抽出
        completed_tasks = self._extract_task_ids(commits)

        # 進捗を更新
        coordinator = Coordinator(project_path)
        updated_count = 0
        skipped_count = 0

        for task_id in completed_tasks:
            if task_id in coordinator.tasks:
                task = coordinator.tasks[task_id]
                if task.status != TaskStatus.COMPLETED:
                    coordinator.mark_task_completed(task_id)
                    updated_count += 1
                else:
                    skipped_count += 1

        return {
            'completed_tasks': sorted(completed_tasks),
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'commits_analyzed': len(commits)
        }

    def _is_git_repo(self, path: Path) -> bool:
        """ディレクトリがGitリポジトリかチェック"""
        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def _get_commit_log(
        self,
        project_path: Path,
        since: Optional[str],
        branch: str
    ) -> List[Dict[str, str]]:
        """
        Gitコミットログを取得

        Returns:
            [
                {'hash': 'abc123', 'message': 'feat: TASK-001 実装完了'},
                {'hash': 'def456', 'message': 'fix: TASK-002 バグ修正'},
            ]
        """
        # git log コマンドを構築
        cmd = ['git', 'log', '--pretty=format:%H|||%s', branch]

        if since:
            cmd.insert(2, f'--since={since}')

        try:
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git log取得エラー: {e.stderr}")

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            try:
                commit_hash, message = line.split('|||', 1)
                commits.append({
                    'hash': commit_hash,
                    'message': message
                })
            except ValueError:
                # パースエラーは無視
                continue

        return commits

    def _extract_task_ids(self, commits: List[Dict[str, str]]) -> Set[str]:
        """
        コミットメッセージからタスクIDを抽出

        Args:
            commits: コミット情報のリスト

        Returns:
            タスクIDのセット（例: {'TASK-001', 'TASK-002'}）
        """
        task_ids = set()

        for commit in commits:
            message = commit['message']
            # TASK-XXX パターンを検索
            matches = self.task_pattern.findall(message)
            task_ids.update(matches)

        return task_ids

    def get_task_commits(
        self,
        project_path: Path,
        task_id: str,
        branch: str = "HEAD"
    ) -> List[Dict[str, str]]:
        """
        特定のタスクに関連するコミットを取得

        Args:
            project_path: プロジェクトパス
            task_id: タスクID（例: "TASK-001"）
            branch: ブランチ名

        Returns:
            コミット情報のリスト
        """
        # 全コミットを取得
        commits = self._get_commit_log(project_path, since=None, branch=branch)

        # task_idを含むコミットのみフィルタ
        task_commits = [
            commit for commit in commits
            if task_id in commit['message']
        ]

        return task_commits

    def get_recent_activity(
        self,
        project_path: Path,
        days: int = 7
    ) -> Dict[str, List[str]]:
        """
        最近のタスクアクティビティを取得

        Args:
            project_path: プロジェクトパス
            days: 過去何日分か

        Returns:
            {
                'TASK-001': ['abc123', 'def456'],
                'TASK-002': ['ghi789']
            }
        """
        since = f"{days}.days.ago"
        commits = self._get_commit_log(project_path, since, "HEAD")

        # タスクIDごとにコミットハッシュを集める
        activity = {}

        for commit in commits:
            task_ids = self.task_pattern.findall(commit['message'])
            for task_id in task_ids:
                if task_id not in activity:
                    activity[task_id] = []
                activity[task_id].append(commit['hash'])

        return activity

    def validate_task_references(
        self,
        project_path: Path
    ) -> Dict[str, List[str]]:
        """
        コミットメッセージ内のタスク参照を検証

        存在しないタスクIDを参照しているコミットを検出

        Returns:
            {
                'valid': ['TASK-001', 'TASK-002'],
                'invalid': ['TASK-999'],
                'invalid_commits': [
                    {'hash': 'abc123', 'message': 'fix: TASK-999', 'task_id': 'TASK-999'}
                ]
            }
        """
        # 全コミットを取得
        commits = self._get_commit_log(project_path, since=None, branch="HEAD")

        # コミットメッセージから全タスクIDを抽出
        referenced_tasks = self._extract_task_ids(commits)

        # 存在するタスクIDを取得
        coordinator = Coordinator(project_path)
        valid_task_ids = set(coordinator.tasks.keys())

        # 検証
        valid = referenced_tasks & valid_task_ids
        invalid = referenced_tasks - valid_task_ids

        # 不正なタスクIDを含むコミットを特定
        invalid_commits = []
        for commit in commits:
            commit_task_ids = set(self.task_pattern.findall(commit['message']))
            for task_id in commit_task_ids & invalid:
                invalid_commits.append({
                    'hash': commit['hash'][:7],
                    'message': commit['message'],
                    'task_id': task_id
                })

        return {
            'valid': sorted(valid),
            'invalid': sorted(invalid),
            'invalid_commits': invalid_commits
        }
