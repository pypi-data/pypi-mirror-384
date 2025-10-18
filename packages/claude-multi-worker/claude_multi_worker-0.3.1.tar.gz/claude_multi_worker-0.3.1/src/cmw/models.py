"""
データモデル定義

タスク、ワーカー、実行結果などのデータ構造を定義します。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class TaskStatus(str, Enum):
    """タスクの実行ステータス"""
    PENDING = "pending"          # 実行待機中
    IN_PROGRESS = "in_progress"  # 実行中
    COMPLETED = "completed"      # 完了
    FAILED = "failed"           # 失敗
    BLOCKED = "blocked"         # ブロック中（依存タスク未完了）


class Priority(str, Enum):
    """タスクの優先度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """タスク定義"""
    id: str
    title: str
    description: str
    assigned_to: str  # Worker ID
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # 依存タスクIDのリスト
    target_files: List[str] = field(default_factory=list)  # 対象ファイルのリスト
    acceptance_criteria: List[str] = field(default_factory=list)  # 受け入れ基準
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    started_at: Optional[str] = None  # 開始時刻（ISO形式）
    failed_at: Optional[str] = None  # 失敗時刻（ISO形式）
    artifacts: List[str] = field(default_factory=list)  # 生成されたファイルのパス
    error_message: Optional[str] = None
    error: Optional[str] = None  # エラー詳細（error_messageと互換性のため）
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "target_files": self.target_files,
            "acceptance_criteria": self.acceptance_criteria,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "started_at": self.started_at,
            "failed_at": self.failed_at,
            "artifacts": self.artifacts,
            "error_message": self.error_message,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """辞書から Task を作成"""
        # datetime文字列をパース
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            assigned_to=data["assigned_to"],
            status=TaskStatus(data.get("status", "pending")),
            priority=Priority(data.get("priority", "medium")),
            dependencies=data.get("dependencies", []),
            target_files=data.get("target_files", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            started_at=data.get("started_at"),
            failed_at=data.get("failed_at"),
            artifacts=data.get("artifacts", []),
            error_message=data.get("error_message"),
            error=data.get("error")
        )


@dataclass
class Worker:
    """ワーカー定義"""
    id: str
    name: str
    description: str
    skills: List[str] = field(default_factory=list)
    assigned_tasks: List[str] = field(default_factory=list)  # タスクIDのリスト
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "skills": self.skills,
            "assigned_tasks": self.assigned_tasks
        }


@dataclass
class ExecutionResult:
    """タスク実行結果"""
    success: bool
    task_id: str
    generated_files: List[str] = field(default_factory=list)
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None  # 実行時間（秒）
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "generated_files": self.generated_files,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time
        }
