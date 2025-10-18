"""
Interactive Fixer - 対話的な問題修正UI

Rich UIを使用して、タスクの問題を対話的に修正する機能を提供します。
"""
from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

from .models import Task
from .dependency_validator import DependencyValidator


class InteractiveFixer:
    """対話的な問題修正機能"""

    def __init__(self):
        """初期化"""
        self.console = Console()
        self.validator = DependencyValidator()

    def fix_cycles_interactively(
        self,
        tasks: List[Task],
        cycles: List[List[str]]
    ) -> List[Task]:
        """
        循環依存を対話的に修正

        Args:
            tasks: タスクリスト
            cycles: 検出された循環依存

        Returns:
            修正後のタスクリスト
        """
        self.console.print(
            f"\n[bold yellow]⚠️  {len(cycles)}件の循環依存を検出しました[/bold yellow]"
        )

        for i, cycle in enumerate(cycles, 1):
            self.console.print(f"\n[bold]循環 {i}/{len(cycles)}:[/bold]")
            self.console.print(f"  {' ↔ '.join(cycle)}")

            # 修正提案を取得
            suggestions = self.validator.suggest_fixes([cycle], tasks)

            if not suggestions or not suggestions[0].get('suggestions'):
                self.console.print("[red]  自動修正案が見つかりません[/red]")
                continue

            fix_suggestions = suggestions[0]['suggestions']

            # 修正案を表示
            table = Table(title="修正案")
            table.add_column("番号", style="cyan", justify="center")
            table.add_column("削除する依存", style="yellow")
            table.add_column("理由", style="green")
            table.add_column("信頼度", style="magenta", justify="right")

            for j, suggestion in enumerate(fix_suggestions, 1):
                table.add_row(
                    str(j),
                    f"{suggestion['from_task']} → {suggestion['to_task']}",
                    suggestion['reason'],
                    f"{suggestion['confidence']:.0%}"
                )

            self.console.print(table)

            # ユーザーに選択を求める
            choices = [str(j) for j in range(1, len(fix_suggestions) + 1)] + ["s", "c"]
            choice = Prompt.ask(
                "どの修正案を適用しますか？ ([cyan]番号[/cyan]/[yellow]s[/yellow]=スキップ/[red]c[/red]=キャンセル)",
                choices=choices,
                default="1"
            )

            if choice == "s":
                # スキップ
                self.console.print("[yellow]この循環をスキップしました[/yellow]")
                continue
            elif choice == "c":
                # キャンセル
                self.console.print("[red]修正をキャンセルしました[/red]")
                return tasks
            else:
                # 選択した修正を適用
                selected = fix_suggestions[int(choice) - 1]
                tasks = self._apply_fix(tasks, selected)
                self.console.print(f"[green]✅ 修正を適用しました[/green]")

        return tasks

    def _apply_fix(self, tasks: List[Task], fix: dict) -> List[Task]:
        """
        修正を適用

        Args:
            tasks: タスクリスト
            fix: 修正内容

        Returns:
            修正後のタスクリスト
        """
        task_map = {t.id: t for t in tasks}
        from_task = task_map.get(fix['from_task'])
        to_task_id = fix['to_task']

        if from_task and to_task_id in from_task.dependencies:
            from_task.dependencies.remove(to_task_id)

        return tasks

    def select_tasks_interactively(
        self,
        tasks: List[Task],
        prompt_text: str = "タスクを選択してください"
    ) -> List[Task]:
        """
        タスクを対話的に選択

        Args:
            tasks: 選択肢となるタスクリスト
            prompt_text: プロンプトテキスト

        Returns:
            選択されたタスクリスト
        """
        if not tasks:
            self.console.print("[yellow]選択可能なタスクがありません[/yellow]")
            return []

        table = Table(title="タスク一覧")
        table.add_column("番号", style="cyan", justify="center")
        table.add_column("ID", style="yellow")
        table.add_column("タイトル", style="green")
        table.add_column("優先度", style="magenta")
        table.add_column("ステータス", style="blue")

        for i, task in enumerate(tasks, 1):
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(task.status.value, '?')

            table.add_row(
                str(i),
                task.id,
                task.title,
                task.priority.value,
                f"{status_icon} {task.status.value}"
            )

        self.console.print(table)

        choices_text = Prompt.ask(
            f"{prompt_text} (カンマ区切りで複数選択可、[cyan]all[/cyan]で全て選択)",
            default="all"
        )

        if choices_text == "all":
            return tasks

        try:
            selected_indices = [int(c.strip()) - 1 for c in choices_text.split(',')]
            selected = [tasks[i] for i in selected_indices if 0 <= i < len(tasks)]
            return selected
        except (ValueError, IndexError):
            self.console.print("[red]無効な選択です[/red]")
            return []

    def confirm_action(self, action: str, default: bool = True) -> bool:
        """
        アクションの確認

        Args:
            action: アクションの説明
            default: デフォルト値

        Returns:
            確認結果
        """
        return Confirm.ask(f"{action}を実行しますか？", default=default)

    def fix_missing_dependencies_interactively(
        self,
        tasks: List[Task],
        missing_deps: List[dict]
    ) -> List[Task]:
        """
        不足している依存関係を対話的に修正

        Args:
            tasks: タスクリスト
            missing_deps: 不足している依存関係のリスト

        Returns:
            修正後のタスクリスト
        """
        if not missing_deps:
            return tasks

        self.console.print(
            f"\n[bold yellow]⚠️  {len(missing_deps)}件の不足依存関係を検出しました[/bold yellow]"
        )

        task_map = {t.id: t for t in tasks}

        for i, missing in enumerate(missing_deps, 1):
            task_id = missing['task_id']
            missing_dep_id = missing['missing_dependency']

            self.console.print(f"\n[bold]不足依存 {i}/{len(missing_deps)}:[/bold]")
            self.console.print(
                f"  タスク [yellow]{task_id}[/yellow] が"
                f" [red]{missing_dep_id}[/red] に依存していますが、"
                f"このタスクは存在しません"
            )

            # 削除するか確認
            if Confirm.ask(
                f"[red]{task_id}[/red] から [red]{missing_dep_id}[/red] への依存を削除しますか？",
                default=True
            ):
                task = task_map.get(task_id)
                if task and missing_dep_id in task.dependencies:
                    task.dependencies.remove(missing_dep_id)
                    self.console.print("[green]✅ 依存を削除しました[/green]")
            else:
                self.console.print("[yellow]スキップしました[/yellow]")

        return tasks

    def show_validation_report(
        self,
        cycles: List[List[str]],
        missing_deps: List[dict],
        self_deps: List[str]
    ):
        """
        検証レポートを表示

        Args:
            cycles: 循環依存のリスト
            missing_deps: 不足依存関係のリスト
            self_deps: 自己依存のリスト
        """
        total_issues = len(cycles) + len(missing_deps) + len(self_deps)

        if total_issues == 0:
            panel = Panel(
                "[green]✅ 問題は見つかりませんでした[/green]",
                title="検証結果",
                border_style="green"
            )
            self.console.print(panel)
            return

        # 問題のサマリー
        summary_lines = [
            f"[bold]検出された問題: {total_issues}件[/bold]",
            ""
        ]

        if cycles:
            summary_lines.append(f"🔄 循環依存: {len(cycles)}件")
        if missing_deps:
            summary_lines.append(f"❌ 不足依存: {len(missing_deps)}件")
        if self_deps:
            summary_lines.append(f"⚠️  自己依存: {len(self_deps)}件")

        panel = Panel(
            "\n".join(summary_lines),
            title="検証結果",
            border_style="yellow"
        )
        self.console.print(panel)

    def confirm_save(self, file_path: str) -> bool:
        """
        保存の確認

        Args:
            file_path: 保存先ファイルパス

        Returns:
            保存するかどうか
        """
        return Confirm.ask(
            f"修正内容を [cyan]{file_path}[/cyan] に保存しますか？",
            default=True
        )
