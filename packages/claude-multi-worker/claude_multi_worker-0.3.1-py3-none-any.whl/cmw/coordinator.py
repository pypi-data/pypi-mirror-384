"""
コーディネーター機能

タスクの管理、依存関係の解決を行います。
"""
import json
from pathlib import Path
from typing import Optional, List, Dict
from .models import Task, TaskStatus, Worker


class Coordinator:
    """タスクの管理と調整を行うコーディネーター"""
    
    def __init__(self, project_path: Path):
        """
        コーディネーターを初期化
        
        Args:
            project_path: プロジェクトのルートパス
        """
        self.project_path = project_path
        self.tasks_file = project_path / "shared" / "coordination" / "tasks.json"
        self.progress_file = project_path / "shared" / "coordination" / "progress.json"
        self.tasks: Dict[str, Task] = {}
        self.workers: Dict[str, Worker] = {}
        
        # タスクとワーカーを読み込む
        self._load_tasks()
    
    def _load_tasks(self):
        """tasks.json からタスクを読み込み、progress.json で進捗状況をマージ"""
        if not self.tasks_file.exists():
            return

        with open(self.tasks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # タスクを読み込む
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                self.tasks[task.id] = task

            # ワーカーを読み込む
            for worker_data in data.get("workers", []):
                worker = Worker(
                    id=worker_data["id"],
                    name=worker_data["name"],
                    description=worker_data["description"],
                    skills=worker_data.get("skills", []),
                    assigned_tasks=worker_data.get("assigned_tasks", [])
                )
                self.workers[worker.id] = worker

        # progress.json が存在する場合、進捗状況をマージ
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)

                for task_data in progress_data.get("tasks", []):
                    # task_dataが辞書でない場合はスキップ（古い形式対応）
                    if not isinstance(task_data, dict):
                        continue
                    task_id = task_data.get("id")
                    if task_id in self.tasks:
                        # 進捗状況のみをマージ（status, artifacts, completed_at, error_message など）
                        task = self.tasks[task_id]
                        if "status" in task_data:
                            task.status = TaskStatus(task_data["status"])
                        if "artifacts" in task_data:
                            task.artifacts = task_data["artifacts"]
                        if "completed_at" in task_data and task_data["completed_at"]:
                            from datetime import datetime
                            task.completed_at = datetime.fromisoformat(task_data["completed_at"])
                        if "started_at" in task_data and task_data["started_at"]:
                            from datetime import datetime
                            task.started_at = datetime.fromisoformat(task_data["started_at"])
                        if "failed_at" in task_data and task_data["failed_at"]:
                            from datetime import datetime
                            task.failed_at = datetime.fromisoformat(task_data["failed_at"])
                        if "error_message" in task_data:
                            task.error_message = task_data["error_message"]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        タスクを取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク（存在しない場合はNone）
        """
        return self.tasks.get(task_id)
    
    def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus,
        error_message: Optional[str] = None,
        artifacts: Optional[List[str]] = None
    ):
        """
        タスクのステータスを更新
        
        Args:
            task_id: タスクID
            status: 新しいステータス
            error_message: エラーメッセージ（任意）
            artifacts: 生成されたファイルのリスト（任意）
        """
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = status
        task.error_message = error_message
        
        if artifacts:
            task.artifacts = artifacts
        
        if status == TaskStatus.COMPLETED:
            from datetime import datetime
            task.completed_at = datetime.now()
        
        # progress.json を更新
        self._save_progress()
    
    def _save_progress(self):
        """進捗状況を保存"""
        progress_data = {
            "tasks": [task.to_dict() for task in self.tasks.values()]
        }
        
        # ディレクトリが存在しない場合は作成
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def get_executable_tasks(self) -> List[Task]:
        """
        実行可能なタスクのリストを取得
        
        Returns:
            依存タスクが完了しており実行可能なタスクのリスト
        """
        executable = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # 依存タスクがすべて完了しているか確認
            dependencies_met = True
            for dep_id in task.dependencies:
                dep_task = self.tasks.get(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                executable.append(task)
        
        return executable
