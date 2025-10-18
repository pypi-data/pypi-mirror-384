"""
ErrorHandler - タスク失敗時の処理

役割:
- タスク失敗時の対応決定
- 部分的な成果物のロールバック
- 復旧方法の提案
"""
from pathlib import Path
from typing import Optional, List
from enum import Enum
import shutil

from .models import Task, TaskStatus


class TaskFailureAction(Enum):
    """タスク失敗時のアクション"""
    RETRY = "retry"  # リトライ
    SKIP = "skip"  # スキップ
    BLOCK = "block"  # 依存タスクをブロック
    ROLLBACK = "rollback"  # ロールバック


class ErrorHandler:
    """タスク失敗時のエラーハンドリング"""

    def __init__(self, project_path: Path):
        """
        Args:
            project_path: プロジェクトのルートパス
        """
        self.project_path = Path(project_path)
        self.artifacts_dir = project_path / "shared/artifacts"

    def handle_task_failure(
        self,
        task: Task,
        error: Exception,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> TaskFailureAction:
        """
        タスク失敗時の対応を決定

        Args:
            task: 失敗したタスク
            error: 発生したエラー
            retry_count: 現在のリトライ回数
            max_retries: 最大リトライ回数

        Returns:
            実行すべきアクション
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # リトライ可能なエラー
        if self._is_retryable_error(error_type, error_msg):
            if retry_count < max_retries:
                return TaskFailureAction.RETRY
            else:
                # リトライ上限に達した
                return TaskFailureAction.BLOCK

        # スキップ可能なエラー（オプションタスク等）
        if self._is_skippable_task(task):
            return TaskFailureAction.SKIP

        # ロールバックが必要なエラー
        if self._should_rollback(task, error):
            return TaskFailureAction.ROLLBACK

        # デフォルト: 依存タスクをブロック
        return TaskFailureAction.BLOCK

    def rollback_partial_work(self, task: Task) -> bool:
        """
        部分的な成果物を削除

        Args:
            task: ロールバック対象のタスク

        Returns:
            ロールバック成功ならTrue
        """
        if not task.artifacts:
            return True  # 成果物がない場合は成功

        success = True
        for artifact_path in task.artifacts:
            full_path = self.artifacts_dir / artifact_path

            try:
                if full_path.exists():
                    if full_path.is_file():
                        full_path.unlink()
                    elif full_path.is_dir():
                        shutil.rmtree(full_path)
            except Exception as e:
                print(f"警告: {artifact_path} の削除に失敗: {e}")
                success = False

        # タスクの成果物リストをクリア
        if success:
            task.artifacts = []

        return success

    def suggest_recovery(
        self,
        task: Task,
        error: Exception
    ) -> str:
        """
        復旧方法を提案

        Args:
            task: 失敗したタスク
            error: 発生したエラー

        Returns:
            復旧方法の提案メッセージ
        """
        error_type = type(error).__name__
        error_msg = str(error)

        suggestions = []

        # エラータイプ別の提案
        if "FileNotFoundError" in error_type:
            suggestions.append("- 依存ファイルが存在するか確認してください")
            suggestions.append("- 依存タスクが正しく完了しているか確認してください")

        elif "PermissionError" in error_type:
            suggestions.append("- ファイルの書き込み権限を確認してください")
            suggestions.append("- ファイルが他のプロセスで使用されていないか確認してください")

        elif "SyntaxError" in error_type or "ImportError" in error_type:
            suggestions.append("- 生成されたコードの構文をチェックしてください")
            suggestions.append("- 必要なパッケージがインストールされているか確認してください")

        elif "ModuleNotFoundError" in error_type:
            suggestions.append("- requirements.txt に必要なパッケージを追加してください")
            suggestions.append(f"- `pip install {self._extract_module_name(error_msg)}` を実行してください")

        elif "JSONDecodeError" in error_type:
            suggestions.append("- 設定ファイルのJSON形式を確認してください")
            suggestions.append("- ファイルが破損していないか確認してください")

        elif "ValidationError" in error_type:
            suggestions.append("- タスク定義のフィールドを確認してください")
            suggestions.append("- acceptance_criteria や target_files が正しく設定されているか確認してください")

        else:
            suggestions.append("- エラーメッセージを確認してください")
            suggestions.append("- タスクの dependencies が正しいか確認してください")

        # タスク固有の提案
        if task.dependencies:
            suggestions.append(f"- 依存タスク {', '.join(task.dependencies)} が完了しているか確認してください")

        if not suggestions:
            suggestions.append("- タスクを手動で確認し、修正してください")

        # 提案メッセージの構築
        recovery_msg = f"""
タスク {task.id} ({task.title}) が失敗しました。

エラー: {error_type}: {error_msg}

復旧方法の提案:
{chr(10).join(suggestions)}

次のアクション:
- 問題を修正後、タスクを再実行してください
- または、`cmw tasks show {task.id}` でタスク詳細を確認してください
"""
        return recovery_msg.strip()

    def get_affected_tasks(self, failed_task: Task, all_tasks: List[Task]) -> List[Task]:
        """
        失敗タスクの影響を受けるタスクを取得

        Args:
            failed_task: 失敗したタスク
            all_tasks: 全タスクのリスト

        Returns:
            影響を受けるタスクのリスト
        """
        affected = []

        def find_dependents(task_id: str):
            """再帰的に依存タスクを探索"""
            for task in all_tasks:
                if task_id in task.dependencies and task not in affected:
                    affected.append(task)
                    find_dependents(task.id)

        find_dependents(failed_task.id)
        return affected

    # === プライベートメソッド ===

    def _is_retryable_error(self, error_type: str, error_msg: str) -> bool:
        """リトライ可能なエラーか判定"""
        retryable_errors = [
            "TimeoutError",
            "ConnectionError",
            "HTTPError",
            "TemporaryError",
        ]

        # 一時的なエラーの可能性があるメッセージ
        retryable_messages = [
            "timeout",
            "connection",
            "temporary",
            "try again",
        ]

        # エラータイプチェック
        if any(err in error_type for err in retryable_errors):
            return True

        # エラーメッセージチェック
        error_msg_lower = error_msg.lower()
        if any(msg in error_msg_lower for msg in retryable_messages):
            return True

        return False

    def _is_skippable_task(self, task: Task) -> bool:
        """スキップ可能なタスクか判定"""
        # priority が "low" かつ依存タスクが少ない場合はスキップ可能
        if task.priority == "low" and len(task.dependencies) == 0:
            return True

        # タイトルに "optional" が含まれる場合
        if "optional" in task.title.lower():
            return True

        return False

    def _should_rollback(self, task: Task, error: Exception) -> bool:
        """ロールバックが必要か判定"""
        # 部分的な成果物がある場合はロールバック
        if task.artifacts and len(task.artifacts) > 0:
            return True

        # データ整合性に影響するエラー
        integrity_errors = [
            "IntegrityError",
            "UniqueViolation",
            "ForeignKeyViolation",
        ]

        error_type = type(error).__name__
        if any(err in error_type for err in integrity_errors):
            return True

        return False

    def _extract_module_name(self, error_msg: str) -> str:
        """エラーメッセージからモジュール名を抽出"""
        # "No module named 'xxx'" から 'xxx' を抽出
        if "No module named" in error_msg:
            parts = error_msg.split("'")
            if len(parts) >= 2:
                return parts[1]
        return "unknown"
