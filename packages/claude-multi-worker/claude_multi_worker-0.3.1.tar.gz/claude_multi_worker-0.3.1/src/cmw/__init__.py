"""
Claude Multi-Worker Framework

Claude Codeと統合したタスク管理・メタデータフレームワーク。
requirements.mdから自動でタスクを生成し、依存関係を管理し、進捗を可視化します。
"""

__version__ = "0.3.1"

from .models import Task, TaskStatus, Worker, ExecutionResult, Priority
from .coordinator import Coordinator
from .task_provider import TaskProvider
from .state_manager import StateManager, SessionContext
from .parallel_executor import ParallelExecutor
from .error_handler import ErrorHandler, TaskFailureAction
from .feedback import FeedbackManager
from .requirements_parser import RequirementsParser
from .conflict_detector import ConflictDetector, Conflict, ConflictType, ConflictSeverity
from .progress_tracker import ProgressTracker
from .dashboard import Dashboard
from .graph_visualizer import GraphVisualizer
from .prompt_template import PromptTemplate
from .static_analyzer import StaticAnalyzer
from .interactive_fixer import InteractiveFixer
from .response_parser import ResponseParser

__all__ = [
    "Task",
    "TaskStatus",
    "Worker",
    "ExecutionResult",
    "Priority",
    "Coordinator",
    "TaskProvider",
    "StateManager",
    "SessionContext",
    "ParallelExecutor",
    "ErrorHandler",
    "TaskFailureAction",
    "FeedbackManager",
    "RequirementsParser",
    "ConflictDetector",
    "Conflict",
    "ConflictType",
    "ConflictSeverity",
    "ProgressTracker",
    "Dashboard",
    "GraphVisualizer",
    "PromptTemplate",
    "StaticAnalyzer",
    "InteractiveFixer",
    "ResponseParser",
]
