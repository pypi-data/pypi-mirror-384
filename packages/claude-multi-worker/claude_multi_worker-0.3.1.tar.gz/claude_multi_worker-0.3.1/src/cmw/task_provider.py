"""
TaskProvider - Claude Codeにタスク情報を提供

役割:
- 次に実行すべきタスクを選択
- タスク実行に必要な全情報を提供
- タスク完了/失敗の記録
"""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import json

from .models import Task, TaskStatus
from .coordinator import Coordinator


class TaskProvider:
    """Claude Codeへのタスク情報提供"""

    def __init__(self, project_path: Path):
        """
        Args:
            project_path: プロジェクトのルートパス
        """
        self.project_path = Path(project_path)
        self.coordinator = Coordinator(project_path)
        self.progress_file = project_path / "shared/coordination/progress.json"

        # 進捗情報を読み込み
        self._load_progress()

    def get_next_task(self) -> Optional[Task]:
        """
        次に実行すべきタスクを取得

        依存関係を考慮し、実行可能なタスクの中から
        優先度の高いものを返す

        Returns:
            実行可能なタスク、なければNone
        """
        # 実行可能なタスクを取得（依存関係チェック済み）
        ready_tasks = self._get_ready_tasks()

        if not ready_tasks:
            return None

        # 優先度でソート
        ready_tasks.sort(key=lambda t: (
            t.priority == "high",    # 高優先度を先に
            t.priority == "medium",
            -len(t.dependencies)     # 依存が少ないものを先に
        ), reverse=True)

        return ready_tasks[0]

    def get_task_context(self, task_id: str) -> Dict:
        """
        タスク実行に必要な全コンテキストを構築

        Args:
            task_id: タスクID

        Returns:
            タスク実行に必要な情報を含む辞書
        """
        task = self.coordinator.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        return {
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "target_files": task.target_files,
                "acceptance_criteria": task.acceptance_criteria
            },
            "requirements": self._load_requirements_section(task),
            "api_spec": self._load_api_spec(task),
            "related_files": self._get_related_files(task),
            "dependencies_artifacts": self._get_dependency_artifacts(task),
            "project_structure": self._get_project_structure()
        }

    def mark_started(self, task_id: str):
        """
        タスク開始を記録

        Args:
            task_id: タスクID
        """
        task = self.coordinator.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()

        self._save_progress()

    def mark_completed(self, task_id: str, artifacts: List[str]):
        """
        タスク完了を記録

        Args:
            task_id: タスクID
            artifacts: 生成されたファイルのリスト
        """
        task = self.coordinator.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        task.artifacts = artifacts

        self._save_progress()

        # 依存タスクのブロックを解除
        self._unblock_dependent_tasks(task_id)

    def mark_failed(self, task_id: str, error: str):
        """
        タスク失敗を記録

        Args:
            task_id: タスクID
            error: エラーメッセージ
        """
        task = self.coordinator.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.FAILED
        task.error = error
        task.failed_at = datetime.now().isoformat()

        self._save_progress()

        # 依存タスクをブロック状態に
        self._block_dependent_tasks(task_id)

    # === プライベートメソッド ===

    def _get_ready_tasks(self) -> List[Task]:
        """依存関係を満たした実行可能なタスクを取得"""
        ready = []

        for task in self.coordinator.tasks.values():
            # 既に完了済みはスキップ
            if task.status == TaskStatus.COMPLETED:
                continue

            # ブロックされているタスクはスキップ
            if task.status == TaskStatus.BLOCKED:
                continue

            # 実行中のタスクはスキップ
            if task.status == TaskStatus.IN_PROGRESS:
                continue

            # 依存関係をチェック
            if self._are_dependencies_met(task):
                ready.append(task)

        return ready

    def _are_dependencies_met(self, task: Task) -> bool:
        """タスクの依存関係が満たされているか"""
        for dep_id in task.dependencies:
            dep_task = self.coordinator.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def _load_requirements_section(self, task: Task) -> str:
        """requirements.mdから関連セクションを読み込み"""
        req_file = self.project_path / "shared/docs/requirements.md"
        if not req_file.exists():
            return ""

        content = req_file.read_text(encoding='utf-8')

        # タスクに関連するセクションを抽出
        # （簡易実装: 将来的にはセクションマッピングを使用）
        return content

    def _load_api_spec(self, task: Task) -> str:
        """API仕様から関連部分を読み込み"""
        api_file = self.project_path / "shared/docs/api-spec.md"
        if not api_file.exists():
            return ""

        return api_file.read_text(encoding='utf-8')

    def _get_related_files(self, task: Task) -> List[Dict]:
        """タスクに関連する既存ファイルを取得"""
        related = []
        artifacts_dir = self.project_path / "shared/artifacts"

        # target_filesに関連するファイルを探す
        for target in task.target_files:
            target_path = artifacts_dir / target
            if target_path.exists():
                related.append({
                    "path": target,
                    "content": target_path.read_text(encoding='utf-8')
                })

        return related

    def _get_dependency_artifacts(self, task: Task) -> List[Dict]:
        """依存タスクの成果物を取得"""
        artifacts = []

        for dep_id in task.dependencies:
            dep_task = self.coordinator.get_task(dep_id)
            if dep_task and dep_task.status == TaskStatus.COMPLETED:
                for artifact_path in dep_task.artifacts:
                    full_path = self.project_path / "shared/artifacts" / artifact_path
                    if full_path.exists():
                        artifacts.append({
                            "task_id": dep_id,
                            "path": artifact_path,
                            "content": full_path.read_text(encoding='utf-8')
                        })

        return artifacts

    def _get_project_structure(self) -> Dict:
        """プロジェクト構造の情報を取得"""
        return {
            "backend_dir": "shared/artifacts/backend",
            "frontend_dir": "shared/artifacts/frontend",
            "tests_dir": "shared/artifacts/tests"
        }

    def _unblock_dependent_tasks(self, completed_task_id: str):
        """依存タスクのブロックを解除"""
        for task in self.coordinator.tasks.values():
            if completed_task_id in task.dependencies:
                if self._are_dependencies_met(task):
                    if task.status == TaskStatus.BLOCKED:
                        task.status = TaskStatus.PENDING

    def _block_dependent_tasks(self, failed_task_id: str):
        """依存タスクをブロック状態に"""
        for task in self.coordinator.tasks.values():
            if failed_task_id in task.dependencies:
                task.status = TaskStatus.BLOCKED

    def _load_progress(self):
        """進捗情報を読み込み"""
        if not self.progress_file.exists():
            self._init_progress()
            return

        progress = json.loads(self.progress_file.read_text(encoding='utf-8'))

        # タスクの状態を復元
        for task_id, task_data in progress.get("tasks", {}).items():
            task = self.coordinator.get_task(task_id)
            if task:
                task.status = TaskStatus(task_data.get("status", "pending"))
                task.started_at = task_data.get("started_at")
                task.completed_at = task_data.get("completed_at")
                task.artifacts = task_data.get("artifacts", [])
                task.error = task_data.get("error")

    def _save_progress(self):
        """進捗情報を保存"""
        progress = {
            "updated_at": datetime.now().isoformat(),
            "tasks": {}
        }

        for task_id, task in self.coordinator.tasks.items():
            progress["tasks"][task_id] = {
                "id": task.id,
                "status": task.status.value,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "artifacts": task.artifacts,
                "error": task.error
            }

        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.progress_file.write_text(
            json.dumps(progress, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def _init_progress(self):
        """進捗情報を初期化"""
        progress = {
            "created_at": datetime.now().isoformat(),
            "tasks": {}
        }

        for task_id, task in self.coordinator.tasks.items():
            progress["tasks"][task_id] = {
                "id": task.id,
                "status": TaskStatus.PENDING.value,
                "started_at": None,
                "completed_at": None,
                "artifacts": [],
                "error": None
            }

        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.progress_file.write_text(
            json.dumps(progress, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
