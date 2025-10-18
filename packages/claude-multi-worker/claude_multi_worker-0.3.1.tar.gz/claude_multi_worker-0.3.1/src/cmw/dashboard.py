"""
ターミナルダッシュボード

リアルタイムでタスク進捗を表示するターミナルダッシュボード
"""

from typing import List, Optional
from datetime import timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich import box

from .models import Task, TaskStatus
from .progress_tracker import ProgressTracker


class Dashboard:
    """ターミナルダッシュボード"""

    def __init__(self):
        self.console = Console()

    def format_duration(self, seconds: float) -> str:
        """秒数を人間が読みやすい形式に変換"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}分"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}時間{minutes}分"

    def create_summary_panel(self, tracker: ProgressTracker, tasks: List[Task]) -> Panel:
        """サマリーパネルを作成"""
        summary = tracker.get_progress_summary(tasks)

        content = f"""
📊 総タスク数: {summary['total']}

✅ 完了: {summary['completed']} ({summary['completion_rate']:.1f}%)
🔄 実行中: {summary['in_progress']}
⏳ 待機中: {summary['pending']}
❌ 失敗: {summary['failed']}
🚫 ブロック: {summary['blocked']}

📈 成功率: {summary['success_rate']:.1f}%
"""

        # 残り時間推定
        remaining = tracker.estimate_remaining_time(tasks)
        if remaining:
            content += f"\n⏱️  推定残り時間: {self.format_duration(remaining.total_seconds())}"

        return Panel(content.strip(), title="プロジェクト概要", border_style="cyan")

    def create_velocity_panel(self, tracker: ProgressTracker, tasks: List[Task]) -> Panel:
        """ベロシティパネルを作成"""
        velocity = tracker.get_velocity_metrics(tasks)

        content = f"""
🚀 タスク/時間: {velocity['tasks_per_hour']:.2f}
⏱️  平均所要時間: {self.format_duration(velocity['avg_task_duration'])}
🕐 総作業時間: {self.format_duration(velocity['total_working_time'])}
"""

        return Panel(content.strip(), title="ベロシティ", border_style="green")

    def create_priority_table(self, tracker: ProgressTracker, tasks: List[Task]) -> Table:
        """優先度別進捗テーブルを作成"""
        breakdown = tracker.get_priority_breakdown(tasks)

        table = Table(title="優先度別進捗", box=box.ROUNDED)
        table.add_column("優先度", style="cyan")
        table.add_column("総数", justify="right")
        table.add_column("完了", justify="right", style="green")
        table.add_column("実行中", justify="right", style="yellow")
        table.add_column("待機中", justify="right", style="blue")
        table.add_column("失敗", justify="right", style="red")
        table.add_column("進捗率", justify="right")

        priority_labels = {
            'high': '🔴 高',
            'medium': '🟡 中',
            'low': '🟢 低'
        }

        for priority in ['high', 'medium', 'low']:
            data = breakdown[priority]
            total = data['total']
            completed = data['completed']
            rate = (completed / total * 100) if total > 0 else 0

            table.add_row(
                priority_labels[priority],
                str(total),
                str(completed),
                str(data['in_progress']),
                str(data['pending']),
                str(data['failed']),
                f"{rate:.1f}%"
            )

        return table

    def create_worker_table(self, tracker: ProgressTracker, tasks: List[Task]) -> Table:
        """担当者別進捗テーブルを作成"""
        workers = tracker.get_worker_breakdown(tasks)

        table = Table(title="担当者別進捗", box=box.ROUNDED)
        table.add_column("担当者", style="cyan")
        table.add_column("総数", justify="right")
        table.add_column("完了", justify="right", style="green")
        table.add_column("実行中", justify="right", style="yellow")
        table.add_column("待機中", justify="right", style="blue")
        table.add_column("進捗率", justify="right")

        for worker, data in sorted(workers.items()):
            total = data['total']
            completed = data['completed']
            rate = (completed / total * 100) if total > 0 else 0

            table.add_row(
                worker,
                str(total),
                str(completed),
                str(data['in_progress']),
                str(data['pending']),
                f"{rate:.1f}%"
            )

        return table

    def create_recent_tasks_table(self, tracker: ProgressTracker, tasks: List[Task]) -> Table:
        """最近のタスクテーブルを作成"""
        timeline = tracker.get_task_timeline(tasks)
        recent = timeline[-10:] if len(timeline) > 10 else timeline

        table = Table(title="最近のアクティビティ", box=box.ROUNDED)
        table.add_column("時刻", style="cyan")
        table.add_column("タスク", style="white")
        table.add_column("イベント", style="yellow")

        event_icons = {
            'started': '▶️  開始',
            'completed': '✅ 完了',
            'failed': '❌ 失敗'
        }

        for event in reversed(recent):
            timestamp = event['timestamp'].strftime("%H:%M:%S")
            task_label = f"{event['task_id']}: {event['title']}"
            event_label = event_icons.get(event['event'], event['event'])

            table.add_row(timestamp, task_label, event_label)

        return table

    def show_dashboard(self, tracker: ProgressTracker, tasks: List[Task]) -> None:
        """ダッシュボードを表示"""
        self.console.clear()
        self.console.print("\n")
        self.console.print("=" * 80, style="bold cyan")
        self.console.print("  📊 CMW プロジェクトダッシュボード", style="bold cyan")
        self.console.print("=" * 80, style="bold cyan")
        self.console.print("\n")

        # サマリーとベロシティを横並びで表示
        from rich.columns import Columns
        self.console.print(
            Columns([
                self.create_summary_panel(tracker, tasks),
                self.create_velocity_panel(tracker, tasks)
            ])
        )
        self.console.print("\n")

        # 優先度別テーブル
        self.console.print(self.create_priority_table(tracker, tasks))
        self.console.print("\n")

        # 担当者別テーブル
        self.console.print(self.create_worker_table(tracker, tasks))
        self.console.print("\n")

        # 最近のアクティビティ
        self.console.print(self.create_recent_tasks_table(tracker, tasks))
        self.console.print("\n")

    def show_progress_bar(self, tracker: ProgressTracker, tasks: List[Task]) -> None:
        """プログレスバーを表示"""
        summary = tracker.get_progress_summary(tasks)

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task_progress = progress.add_task(
                "全体進捗",
                total=summary['total']
            )
            progress.update(task_progress, completed=summary['completed'])

            # 少し待機して表示
            import time
            time.sleep(0.1)

    def show_compact_summary(self, tracker: ProgressTracker, tasks: List[Task]) -> None:
        """コンパクトなサマリーを表示（CLIコマンド用）"""
        summary = tracker.get_progress_summary(tasks)

        self.console.print(f"\n📊 進捗: {summary['completed']}/{summary['total']} ({summary['completion_rate']:.1f}%)")

        # プログレスバー
        bar_width = 40
        completed_width = int(bar_width * summary['completion_rate'] / 100)
        bar = "█" * completed_width + "░" * (bar_width - completed_width)
        self.console.print(f"[green]{bar}[/green]")

        # ステータスカウント
        self.console.print(
            f"✅ {summary['completed']}  "
            f"🔄 {summary['in_progress']}  "
            f"⏳ {summary['pending']}  "
            f"❌ {summary['failed']}  "
            f"🚫 {summary['blocked']}"
        )

        # 残り時間
        remaining = tracker.estimate_remaining_time(tasks)
        if remaining:
            self.console.print(f"\n⏱️  推定残り時間: {self.format_duration(remaining.total_seconds())}")

        self.console.print()
