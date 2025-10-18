"""
FeedbackManager - リアルタイムフィードバック

役割:
- 進捗状況の表示
- エラーの分かりやすい説明
- 次のアクションの提案
"""
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import Task, TaskStatus
from .coordinator import Coordinator


class FeedbackManager:
    """リアルタイムフィードバック機能"""

    def __init__(self, project_path: Path):
        """
        Args:
            project_path: プロジェクトのルートパス
        """
        self.project_path = Path(project_path)
        self.coordinator = Coordinator(project_path)

    def report_progress(self) -> str:
        """
        プロジェクト全体の進捗を表示

        Returns:
            進捗レポートの文字列
        """
        total_tasks = len(self.coordinator.tasks)
        if total_tasks == 0:
            return "タスクが見つかりません。"

        # ステータス別にカウント
        status_counts = {
            TaskStatus.PENDING: 0,
            TaskStatus.IN_PROGRESS: 0,
            TaskStatus.COMPLETED: 0,
            TaskStatus.FAILED: 0,
            TaskStatus.BLOCKED: 0,
        }

        for task in self.coordinator.tasks.values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1

        completed = status_counts[TaskStatus.COMPLETED]
        in_progress = status_counts[TaskStatus.IN_PROGRESS]
        failed = status_counts[TaskStatus.FAILED]
        blocked = status_counts[TaskStatus.BLOCKED]
        pending = status_counts[TaskStatus.PENDING]

        # 進捗率を計算
        progress_percent = (completed / total_tasks) * 100 if total_tasks > 0 else 0

        # レポート構築
        report = f"""
📊 プロジェクト進捗状況
{'=' * 50}

完了: {completed}/{total_tasks} タスク ({progress_percent:.1f}%)

ステータス別:
  ✅ 完了:     {completed}
  🔄 実行中:   {in_progress}
  ⏸️  保留:     {pending}
  ❌ 失敗:     {failed}
  🚫 ブロック: {blocked}

{'=' * 50}
"""
        return report.strip()

    def explain_error(self, task: Task, error: Exception) -> str:
        """
        エラーを分かりやすく説明

        Args:
            task: 失敗したタスク
            error: 発生したエラー

        Returns:
            エラー説明の文字列
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # エラータイプ別の説明
        explanations = {
            "FileNotFoundError": {
                "title": "ファイルが見つかりません",
                "description": "必要なファイルまたはディレクトリが存在しません。",
                "possible_causes": [
                    "依存タスクが未完了",
                    "ファイルパスが間違っている",
                    "ディレクトリが削除された",
                ],
            },
            "PermissionError": {
                "title": "権限エラー",
                "description": "ファイルまたはディレクトリへのアクセス権限がありません。",
                "possible_causes": [
                    "ファイルが読み取り専用",
                    "他のプロセスがファイルを使用中",
                    "ディレクトリへの書き込み権限がない",
                ],
            },
            "ModuleNotFoundError": {
                "title": "モジュールが見つかりません",
                "description": "必要なPythonパッケージがインストールされていません。",
                "possible_causes": [
                    "requirements.txtが更新されていない",
                    "仮想環境が有効化されていない",
                    "パッケージ名が間違っている",
                ],
            },
            "SyntaxError": {
                "title": "構文エラー",
                "description": "コードの構文に誤りがあります。",
                "possible_causes": [
                    "括弧やクォートの閉じ忘れ",
                    "インデントの誤り",
                    "予約語の誤用",
                ],
            },
            "ImportError": {
                "title": "インポートエラー",
                "description": "モジュールまたはパッケージのインポートに失敗しました。",
                "possible_causes": [
                    "モジュールが存在しない",
                    "循環インポート",
                    "パッケージ構造の誤り",
                ],
            },
            "ValueError": {
                "title": "値エラー",
                "description": "関数やメソッドに不適切な値が渡されました。",
                "possible_causes": [
                    "データ型の不一致",
                    "範囲外の値",
                    "空の値",
                ],
            },
            "KeyError": {
                "title": "キーエラー",
                "description": "辞書に存在しないキーにアクセスしようとしました。",
                "possible_causes": [
                    "キー名の誤り",
                    "データ構造の変更",
                    "初期化されていない辞書",
                ],
            },
            "TimeoutError": {
                "title": "タイムアウトエラー",
                "description": "処理が時間内に完了しませんでした。",
                "possible_causes": [
                    "ネットワーク接続の問題",
                    "処理が重すぎる",
                    "リソース不足",
                ],
            },
        }

        # デフォルトの説明
        default_explanation = {
            "title": error_type,
            "description": "予期しないエラーが発生しました。",
            "possible_causes": [
                "エラーメッセージを確認してください",
                "タスクの設定を見直してください",
            ],
        }

        explanation = explanations.get(error_type, default_explanation)

        # 説明文の構築
        error_explanation = f"""
🔴 エラー: {explanation['title']}

タスク: {task.id} - {task.title}

説明:
  {explanation['description']}

エラーメッセージ:
  {error_msg}

考えられる原因:
"""
        for cause in explanation["possible_causes"]:
            error_explanation += f"  • {cause}\n"

        return error_explanation.strip()

    def show_next_steps(self) -> str:
        """
        次に実行すべきアクションを提案

        Returns:
            次のステップの提案文字列
        """
        # 実行可能なタスクを取得
        ready_tasks = self._get_ready_tasks()

        # 失敗したタスクを取得
        failed_tasks = [
            task
            for task in self.coordinator.tasks.values()
            if task.status == TaskStatus.FAILED
        ]

        # ブロックされたタスクを取得
        blocked_tasks = [
            task
            for task in self.coordinator.tasks.values()
            if task.status == TaskStatus.BLOCKED
        ]

        # 次のステップを構築
        next_steps = f"""
📋 次のステップ
{'=' * 50}
"""

        if failed_tasks:
            next_steps += f"\n⚠️  {len(failed_tasks)}個の失敗したタスクがあります:\n"
            for task in failed_tasks[:3]:  # 最初の3つだけ表示
                next_steps += f"  • {task.id}: {task.title}\n"
                if task.error:
                    next_steps += f"    エラー: {task.error[:50]}...\n"

        if blocked_tasks:
            next_steps += f"\n🚫 {len(blocked_tasks)}個のブロックされたタスクがあります:\n"
            for task in blocked_tasks[:3]:
                next_steps += f"  • {task.id}: {task.title}\n"
                if task.dependencies:
                    next_steps += f"    依存: {', '.join(task.dependencies)}\n"

        if ready_tasks:
            next_steps += f"\n✅ {len(ready_tasks)}個の実行可能なタスクがあります:\n"
            for task in ready_tasks[:5]:  # 最初の5つだけ表示
                next_steps += f"  • {task.id}: {task.title} (優先度: {task.priority})\n"

            # 推奨アクション
            next_task = ready_tasks[0]
            next_steps += f"\n💡 推奨アクション:\n"
            next_steps += f"  次のタスクを実行: {next_task.id} - {next_task.title}\n"
        else:
            if failed_tasks or blocked_tasks:
                next_steps += f"\n💡 推奨アクション:\n"
                next_steps += f"  失敗したタスクを修正してください\n"
            else:
                next_steps += f"\n🎉 全タスク完了！\n"

        next_steps += f"\n{'=' * 50}"
        return next_steps.strip()

    def get_task_summary(self, task: Task) -> str:
        """
        タスクの概要を取得

        Args:
            task: タスク

        Returns:
            タスク概要の文字列
        """
        status_emojis = {
            TaskStatus.PENDING: "⏸️",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.BLOCKED: "🚫",
        }

        emoji = status_emojis.get(task.status, "❓")

        summary = f"""
{emoji} {task.id}: {task.title}

ステータス: {task.status.value}
優先度: {task.priority}
依存: {', '.join(task.dependencies) if task.dependencies else 'なし'}

説明:
  {task.description}
"""

        if task.target_files:
            summary += f"\n対象ファイル:\n"
            for file in task.target_files:
                summary += f"  • {file}\n"

        if task.acceptance_criteria:
            summary += f"\n受け入れ基準:\n"
            for criteria in task.acceptance_criteria:
                summary += f"  • {criteria}\n"

        if task.status == TaskStatus.COMPLETED:
            if task.completed_at:
                summary += f"\n完了日時: {task.completed_at}\n"
            if task.artifacts:
                summary += f"成果物:\n"
                for artifact in task.artifacts:
                    summary += f"  • {artifact}\n"

        if task.status == TaskStatus.FAILED:
            if task.failed_at:
                summary += f"\n失敗日時: {task.failed_at}\n"
            if task.error:
                summary += f"エラー: {task.error}\n"

        return summary.strip()

    def estimate_remaining_time(self, avg_task_time_minutes: float = 30.0) -> str:
        """
        残り時間を見積もる

        Args:
            avg_task_time_minutes: 1タスクあたりの平均時間（分）

        Returns:
            残り時間の見積もり文字列
        """
        total_tasks = len(self.coordinator.tasks)
        completed = sum(
            1 for task in self.coordinator.tasks.values()
            if task.status == TaskStatus.COMPLETED
        )
        remaining = total_tasks - completed

        if remaining <= 0:
            return "🎉 全タスク完了！"

        # 見積もり時間を計算
        estimated_minutes = remaining * avg_task_time_minutes
        estimated_hours = estimated_minutes / 60

        estimate = f"""
⏱️  残り時間の見積もり
{'=' * 50}

残りタスク: {remaining}/{total_tasks}

見積もり時間:
  約 {estimated_minutes:.0f} 分 ({estimated_hours:.1f} 時間)

※ 1タスクあたり {avg_task_time_minutes:.0f}分として計算

{'=' * 50}
"""
        return estimate.strip()

    # === プライベートメソッド ===

    def _get_ready_tasks(self) -> List[Task]:
        """実行可能なタスクを取得"""
        ready = []

        for task in self.coordinator.tasks.values():
            # 既に完了済みはスキップ
            if task.status == TaskStatus.COMPLETED:
                continue

            # ブロックされているタスクはスキップ
            if task.status == TaskStatus.BLOCKED:
                continue

            # 失敗したタスクはスキップ
            if task.status == TaskStatus.FAILED:
                continue

            # 依存関係をチェック
            if self._are_dependencies_met(task):
                ready.append(task)

        # 優先度でソート
        ready.sort(
            key=lambda t: (
                t.priority == "high",
                t.priority == "medium",
                -len(t.dependencies),
            ),
            reverse=True,
        )

        return ready

    def _are_dependencies_met(self, task: Task) -> bool:
        """タスクの依存関係が満たされているか"""
        for dep_id in task.dependencies:
            dep_task = self.coordinator.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
