"""
コマンドラインインターフェース (CLI)

cmw コマンドの実装
"""
import json
import click
from pathlib import Path
from typing import Optional

from .models import TaskStatus
from .coordinator import Coordinator
from .requirements_parser import RequirementsParser
from .conflict_detector import ConflictDetector
from .progress_tracker import ProgressTracker
from .dashboard import Dashboard
from .dependency_validator import DependencyValidator
from .task_filter import TaskFilter
from .git_integration import GitIntegration


@click.group()
@click.version_option(version="0.3.1")
def cli():
    """Claude Multi-Worker Framework - マルチワーカー開発フレームワーク v0.3.1"""
    pass


@cli.command()
@click.option('--name', default='new-project', help='プロジェクト名')
def init(name: str):
    """新しいプロジェクトを初期化"""
    project_path = Path.cwd() / name
    
    if project_path.exists():
        click.echo(f"❌ エラー: ディレクトリ {name} は既に存在します", err=True)
        return
    
    # ディレクトリ構造を作成
    dirs = [
        "shared/docs",
        "shared/coordination",
        "shared/artifacts/backend/core",
        "shared/artifacts/frontend",
        "shared/artifacts/tests"
    ]
    
    for dir_path in dirs:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # サンプルファイルを作成
    requirements_file = project_path / "shared" / "docs" / "requirements.md"
    requirements_file.write_text("""# プロジェクト要件書

## 概要
このプロジェクトの概要を記載してください。

## 機能要件
### 機能1:
### 機能2:

## 非機能要件
- パフォーマンス:
- セキュリティ:
""", encoding='utf-8')

    click.echo(f"✅ プロジェクト '{name}' を初期化しました")
    click.echo(f"\n次のステップ:")
    click.echo(f"  1. cd {name}")
    click.echo(f"  2. shared/docs/requirements.md を編集")
    click.echo(f"  3. cmw task generate でタスク自動生成")
    click.echo(f"  4. cmw status でプロジェクト状況を確認")


@cli.group(name='task')
def task():
    """タスク管理コマンド"""
    pass


# 後方互換性のため tasks も残す（非推奨）
@cli.group(name='tasks', hidden=True)
def tasks():
    """[非推奨] 'cmw task' を使用してください"""
    pass


@task.command('generate')
@click.option('--requirements', '-r', default='shared/docs/requirements.md',
              help='requirements.mdのパス')
@click.option('--output', '-o', default='shared/coordination/tasks.json',
              help='出力先のtasks.jsonパス')
@click.option('--force', '-f', is_flag=True,
              help='既存のtasks.jsonを上書き')
def generate_tasks(requirements: str, output: str, force: bool):
    """requirements.mdからタスクを自動生成

    examples:
        cmw task generate
        cmw task generate -r docs/requirements.md
        cmw task generate --force
    """
    project_path = Path.cwd()
    requirements_path = project_path / requirements
    output_path = project_path / output

    # requirements.mdの存在確認
    if not requirements_path.exists():
        click.echo(f"❌ エラー: requirements.md が見つかりません: {requirements_path}", err=True)
        click.echo(f"\n次のステップ:")
        click.echo(f"  1. {requirements_path} を作成")
        click.echo(f"  2. プロジェクト要件を記載")
        click.echo(f"  3. cmw task generate を再実行")
        return

    # 出力先の上書き確認
    if output_path.exists() and not force:
        click.echo(f"⚠️  {output} は既に存在します")
        if not click.confirm("上書きしますか?"):
            click.echo("キャンセルしました")
            return

    try:
        # RequirementsParserでタスク生成
        click.echo(f"\n📄 {requirements} を解析中...")
        parser = RequirementsParser()
        tasks = parser.parse(requirements_path)

        click.echo(f"✅ {len(tasks)} 個のタスクを生成しました\n")

        # タスクをJSON形式に変換
        tasks_data = {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "assigned_to": task.assigned_to,
                    "dependencies": task.dependencies,
                    "target_files": task.target_files,
                    "acceptance_criteria": task.acceptance_criteria,
                    "priority": task.priority
                }
                for task in tasks
            ],
            "workers": []
        }

        # ファイルに保存
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

        click.echo(f"💾 {output} に保存しました")

        # サマリー表示
        click.echo(f"\n{'='*80}")
        click.echo("生成されたタスクのサマリー")
        click.echo(f"{'='*80}\n")

        # 優先度別カウント
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        for task in tasks:
            priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1

        click.echo(f"総タスク数: {len(tasks)}")
        click.echo(f"  🔴 高優先度: {priority_counts['high']}")
        click.echo(f"  🟡 中優先度: {priority_counts['medium']}")
        click.echo(f"  🟢 低優先度: {priority_counts['low']}")

        # 担当別カウント
        assigned_to_counts = {}
        for task in tasks:
            assigned_to_counts[task.assigned_to] = assigned_to_counts.get(task.assigned_to, 0) + 1

        click.echo(f"\n担当別:")
        for assigned_to, count in sorted(assigned_to_counts.items()):
            click.echo(f"  {assigned_to}: {count}タスク")

        click.echo(f"\n次のステップ:")
        click.echo(f"  1. タスク一覧を確認: cmw task list")
        click.echo(f"  2. プロジェクト状況を確認: cmw status")

    except FileNotFoundError as e:
        click.echo(f"❌ エラー: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"❌ タスク生成エラー: {str(e)}", err=True)
        import traceback
        traceback.print_exc()


@task.command('list')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'failed', 'blocked']),
              help='ステータスでフィルタ')
def list_tasks(status: Optional[str]):
    """タスク一覧を表示"""
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)

    if not coordinator.tasks:
        click.echo("タスクが見つかりません。'cmw task generate' を実行してください。")
        return
    
    # フィルタリング
    tasks_to_show = coordinator.tasks.values()
    if status:
        tasks_to_show = [t for t in tasks_to_show if t.status.value == status]
    
    click.echo(f"\n{'='*80}")
    click.echo(f"タスク一覧 ({len(list(tasks_to_show))} 件)")
    click.echo(f"{'='*80}\n")
    
    for task in tasks_to_show:
        status_emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.BLOCKED: "🚫"
        }
        
        emoji = status_emoji.get(task.status, "❓")
        click.echo(f"{emoji} {task.id}: {task.title}")
        click.echo(f"   ステータス: {task.status.value}")
        click.echo(f"   担当: {task.assigned_to}")
        if task.dependencies:
            click.echo(f"   依存: {', '.join(task.dependencies)}")
        click.echo()


@task.command('show')
@click.argument('task_id')
def show_task(task_id: str):
    """タスクの詳細を表示"""
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)
    
    task = coordinator.get_task(task_id)
    if not task:
        click.echo(f"❌ タスク {task_id} が見つかりません", err=True)
        return
    
    click.echo(f"\n{'='*80}")
    click.echo(f"タスク詳細: {task.id}")
    click.echo(f"{'='*80}\n")
    
    click.echo(f"タイトル: {task.title}")
    click.echo(f"説明: {task.description}")
    click.echo(f"ステータス: {task.status.value}")
    click.echo(f"優先度: {task.priority.value}")
    click.echo(f"担当ワーカー: {task.assigned_to}")
    
    if task.dependencies:
        click.echo(f"依存タスク: {', '.join(task.dependencies)}")
    
    if task.artifacts:
        click.echo(f"\n生成されたファイル:")
        for artifact in task.artifacts:
            click.echo(f"  - {artifact}")
    
    if task.error_message:
        click.echo(f"\nエラー: {task.error_message}")


@task.command('analyze')
@click.option('--show-order', is_flag=True, help='推奨実行順序も表示')
def analyze_conflicts(show_order: bool):
    """タスク間のファイル競合を分析

    examples:
        cmw task analyze
        cmw task analyze --show-order
    """
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)

    if not coordinator.tasks:
        click.echo("タスクが見つかりません。'cmw task generate' を実行してください。")
        return

    # ConflictDetectorで分析
    detector = ConflictDetector()
    tasks_list = list(coordinator.tasks.values())

    # 競合レポートを生成
    report = detector.get_conflict_report(tasks_list)
    click.echo(report)

    # ファイル使用状況
    click.echo(f"\n{'='*80}")
    click.echo("ファイル使用状況")
    click.echo(f"{'='*80}\n")

    file_usage = detector.analyze_file_usage(tasks_list)

    # リスクレベル順にソート
    risk_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    sorted_files = sorted(
        file_usage.items(),
        key=lambda x: (risk_order.get(x[1]['risk_level'], 0), len(x[1]['tasks'])),
        reverse=True
    )

    for file, usage in sorted_files:
        risk_icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        icon = risk_icon.get(usage['risk_level'], '⚪')

        click.echo(f"{icon} {file}")
        click.echo(f"   リスクレベル: {usage['risk_level']}")
        click.echo(f"   関連タスク ({len(usage['tasks'])}件): {', '.join(usage['tasks'])}")
        click.echo()


@task.command('validate')
@click.option('--fix', is_flag=True, help='検出された問題を自動修正')
@click.option('--tasks-file', default='shared/coordination/tasks.json',
              help='検証するtasks.jsonのパス')
def validate_tasks(fix: bool, tasks_file: str):
    """タスクの品質を検証

    循環依存、非タスク項目、依存関係の妥当性をチェックします。

    examples:
        cmw task validate
        cmw task validate --fix
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console()
    project_path = Path.cwd()
    tasks_path = project_path / tasks_file

    if not tasks_path.exists():
        console.print(f"[red]❌ エラー: {tasks_file} が見つかりません[/red]")
        console.print(f"\n次のステップ:")
        console.print(f"  1. cmw task generate でタスクを生成")
        console.print(f"  2. cmw task validate で検証")
        return

    # タスクを読み込み
    tasks_data = json.loads(tasks_path.read_text(encoding='utf-8'))
    tasks_list = []

    for task_data in tasks_data.get('tasks', []):
        from .models import Task, Priority
        task = Task(
            id=task_data['id'],
            title=task_data['title'],
            description=task_data.get('description', ''),
            assigned_to=task_data.get('assigned_to', 'unknown'),
            dependencies=task_data.get('dependencies', []),
            target_files=task_data.get('target_files', []),
            acceptance_criteria=task_data.get('acceptance_criteria', []),
            priority=Priority(task_data.get('priority', 'medium'))
        )
        tasks_list.append(task)

    # 検証を実行
    validator = DependencyValidator()
    task_filter = TaskFilter()

    console.print(Panel.fit(
        "🔍 タスクの品質を検証中...",
        border_style="blue"
    ))

    # 1. 循環依存チェック
    console.print("\n[bold cyan]1. 循環依存チェック[/bold cyan]")
    cycles = validator.detect_cycles(tasks_list)

    if cycles:
        console.print(f"[yellow]⚠️  {len(cycles)}件の循環依存を検出しました:[/yellow]\n")

        for i, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
            console.print(f"  {i}. {cycle_str}")

        if fix:
            console.print(f"\n[blue]🔧 自動修正を適用中...[/blue]")
            suggestions = validator.suggest_fixes(cycles, tasks_list)

            # 修正提案を表示
            for suggestion in suggestions:
                console.print(f"\n循環: {' ↔ '.join(suggestion['cycle'])}")
                for fix_suggestion in suggestion['suggestions'][:1]:  # 最も信頼度の高い提案のみ
                    console.print(f"  ✓ {fix_suggestion['from_task']} → {fix_suggestion['to_task']} を削除")
                    console.print(f"    理由: {fix_suggestion['reason']}")
                    console.print(f"    信頼度: {fix_suggestion['confidence']*100:.0f}%")

            # 自動修正を適用
            tasks_list = validator.auto_fix_cycles(tasks_list, cycles, auto_apply=True)

            # 残りの循環をチェック
            remaining_cycles = validator.detect_cycles(tasks_list)
            if remaining_cycles:
                console.print(f"\n[yellow]⚠️  {len(remaining_cycles)}件の循環依存が残っています[/yellow]")
            else:
                console.print(f"\n[green]✅ 全ての循環依存を解決しました[/green]")

                # tasks.jsonを更新
                tasks_data['tasks'] = [
                    {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'assigned_to': task.assigned_to,
                        'dependencies': task.dependencies,
                        'target_files': task.target_files,
                        'acceptance_criteria': task.acceptance_criteria,
                        'priority': task.priority
                    }
                    for task in tasks_list
                ]
                tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')
                console.print(f"[green]💾 {tasks_file} を更新しました[/green]")
        else:
            console.print(f"\n[dim]ヒント: --fix オプションで自動修正できます[/dim]")
    else:
        console.print("[green]✅ 循環依存は見つかりませんでした[/green]")

    # 2. 非タスク項目チェック
    console.print("\n[bold cyan]2. 非タスク項目チェック[/bold cyan]")
    implementation_tasks, non_tasks = task_filter.filter_tasks(tasks_list)

    if non_tasks:
        console.print(f"[yellow]⚠️  {len(non_tasks)}件の非タスク項目を検出しました:[/yellow]\n")

        for non_task in non_tasks:
            console.print(f"  • {non_task.id}: {non_task.title}")

        console.print(f"\n[dim]これらは実装タスクではなく参照情報です[/dim]")

        if fix:
            console.print(f"\n[blue]🔧 非タスク項目を除外中...[/blue]")
            tasks_list = implementation_tasks

            # tasks.jsonを更新
            tasks_data['tasks'] = [
                {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'assigned_to': task.assigned_to,
                    'dependencies': task.dependencies,
                    'target_files': task.target_files,
                    'acceptance_criteria': task.acceptance_criteria,
                    'priority': task.priority
                }
                for task in tasks_list
            ]
            tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')
            console.print(f"[green]✅ {len(non_tasks)}件の非タスク項目を除外しました[/green]")
            console.print(f"[green]💾 {tasks_file} を更新しました[/green]")
        else:
            console.print(f"\n[dim]ヒント: --fix オプションで自動除外できます[/dim]")
    else:
        console.print("[green]✅ 全てのタスクが実装タスクです[/green]")

    # 3. 依存関係の妥当性チェック
    console.print("\n[bold cyan]3. 依存関係の妥当性チェック[/bold cyan]")
    validation_result = validator.validate_dependencies(tasks_list)

    issues_found = False

    if validation_result['missing_dependencies']:
        issues_found = True
        console.print(f"[red]❌ 存在しない依存先が見つかりました:[/red]\n")
        for issue in validation_result['missing_dependencies']:
            console.print(f"  • {issue}")

    if validation_result['invalid_dependencies']:
        issues_found = True
        console.print(f"[red]❌ 不正な依存関係が見つかりました:[/red]\n")
        for issue in validation_result['invalid_dependencies']:
            console.print(f"  • {issue}")

    if not issues_found:
        console.print("[green]✅ 全ての依存関係が正しく設定されています[/green]")

    # サマリー
    console.print("\n" + "="*80)

    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("検証項目", style="cyan")
    summary_table.add_column("結果", justify="center")
    summary_table.add_column("詳細")

    # 循環依存
    cycle_status = "✅ PASS" if not cycles else f"⚠️  {len(cycles)}件"
    cycle_detail = "循環依存なし" if not cycles else ("修正済み" if fix and not validator.detect_cycles(tasks_list) else "要修正")
    summary_table.add_row("循環依存", cycle_status, cycle_detail)

    # 非タスク項目
    non_task_status = "✅ PASS" if not non_tasks else f"⚠️  {len(non_tasks)}件"
    non_task_detail = "全て実装タスク" if not non_tasks else ("除外済み" if fix else "要除外")
    summary_table.add_row("非タスク項目", non_task_status, non_task_detail)

    # 依存関係
    dep_status = "✅ PASS" if not issues_found else "❌ FAIL"
    dep_detail = "依存関係OK" if not issues_found else "要修正"
    summary_table.add_row("依存関係の妥当性", dep_status, dep_detail)

    console.print(summary_table)
    console.print("="*80 + "\n")

    # 最終メッセージ
    if cycles or non_tasks or issues_found:
        if fix:
            console.print("[green]✅ 自動修正を完了しました[/green]")
        else:
            console.print("[yellow]💡 問題を検出しました。--fix オプションで自動修正できます[/yellow]")
    else:
        console.print("[green]🎉 全ての検証項目をパスしました！[/green]")


@task.command('graph')
@click.option('--format', type=click.Choice(['ascii', 'mermaid']), default='ascii',
              help='出力形式（ascii, mermaid）')
@click.option('--stats', is_flag=True, help='統計情報を表示')
def show_graph(format: str, stats: bool):
    """タスクの依存関係グラフを表示

    examples:
        cmw task graph
        cmw task graph --format mermaid
        cmw task graph --stats
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from .graph_visualizer import GraphVisualizer

    console = Console()
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)

    if not coordinator.tasks:
        console.print("[yellow]タスクが見つかりません。'cmw task generate' を実行してください。[/yellow]")
        return

    tasks_list = list(coordinator.tasks.values())
    visualizer = GraphVisualizer(tasks_list)

    # グラフを表示
    if format == 'ascii':
        console.print(Panel.fit(
            "📊 タスク依存関係グラフ (ASCII)",
            border_style="blue"
        ))
        console.print(visualizer.render_ascii())
    elif format == 'mermaid':
        console.print(Panel.fit(
            "📊 タスク依存関係グラフ (Mermaid)",
            border_style="blue"
        ))
        console.print("\n[cyan]以下のMermaid定義をコピーして、Mermaidビューアーで表示できます:[/cyan]\n")
        console.print(visualizer.render_mermaid())

    # 統計情報を表示
    if stats:
        console.print("\n")
        console.print(Panel.fit(
            "📈 グラフ統計情報",
            border_style="green"
        ))

        graph_stats = visualizer.get_statistics()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("項目", style="cyan")
        table.add_column("値", justify="right")

        table.add_row("総タスク数", str(graph_stats['total_tasks']))
        table.add_row("総依存関係数", str(graph_stats['total_dependencies']))
        table.add_row("ルートタスク数", str(graph_stats['root_tasks']))
        table.add_row("リーフタスク数", str(graph_stats['leaf_tasks']))
        table.add_row("平均依存数", f"{graph_stats['average_dependencies']:.2f}")
        table.add_row("DAG（非循環グラフ）", "✅ はい" if graph_stats['is_dag'] else "❌ いいえ")

        if graph_stats['is_dag']:
            table.add_row("クリティカルパス長", str(graph_stats['critical_path_length']))
            table.add_row("最大並列度", str(graph_stats['max_parallelism']))
            table.add_row("並列レベル数", str(graph_stats['parallel_levels']))

        console.print(table)

        # クリティカルパスを表示
        if graph_stats['is_dag'] and graph_stats['critical_path']:
            console.print("\n[bold cyan]🎯 クリティカルパス:[/bold cyan]")
            path_str = " → ".join(graph_stats['critical_path'])
            console.print(f"  {path_str}")

        # 並列実行グループを表示
        parallel_groups = visualizer.get_parallel_groups()
        if parallel_groups:
            console.print("\n[bold cyan]⚡ 並列実行グループ:[/bold cyan]")
            for i, group in enumerate(parallel_groups, 1):
                if len(group) == 1:
                    console.print(f"  レベル {i}: {group[0]}")
                else:
                    console.print(f"  レベル {i}: {', '.join(group)} ({len(group)}個並列)")


@task.command('prompt')
@click.argument('task_id')
@click.option('--output', '-o', type=click.Path(), help='プロンプトをファイルに保存')
@click.option('--review', is_flag=True, help='レビュー用プロンプトを生成')
def generate_prompt(task_id: str, output: Optional[str], review: bool):
    """タスク実行用のプロンプトを生成

    examples:
        cmw task prompt TASK-001
        cmw task prompt TASK-001 --output prompt.md
        cmw task prompt TASK-001 --review
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from .prompt_template import PromptTemplate

    console = Console()
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)

    if not coordinator.tasks:
        console.print("[yellow]タスクが見つかりません。'cmw task generate' を実行してください。[/yellow]")
        return

    # タスクを取得
    task = coordinator.get_task(task_id)
    if not task:
        console.print(f"[red]❌ タスク {task_id} が見つかりません[/red]")
        return

    # コンテキストタスク（依存タスク）を取得
    context_tasks = []
    for dep_id in task.dependencies:
        dep_task = coordinator.get_task(dep_id)
        if dep_task:
            context_tasks.append(dep_task)

    # プロンプトを生成
    template = PromptTemplate(project_root=project_path)

    if review:
        # レビュー用プロンプト
        implementation_summary = "※ 実装内容をここに記載してください"
        prompt_text = template.generate_review_prompt(task, implementation_summary)
        title = f"🔍 レビュープロンプト: {task_id}"
    else:
        # 実行用プロンプト
        prompt_text = template.generate_task_prompt(
            task,
            context_tasks=context_tasks
        )
        title = f"📝 タスク実行プロンプト: {task_id}"

    # ファイルに保存
    if output:
        output_path = Path(output)
        output_path.write_text(prompt_text, encoding='utf-8')
        console.print(f"[green]✅ プロンプトを {output} に保存しました[/green]")
        return

    # コンソールに表示
    console.print(Panel.fit(title, border_style="blue"))
    console.print("")

    # Markdown形式で表示
    md = Markdown(prompt_text)
    console.print(md)


@task.command('complete')
@click.argument('task_id')
@click.option('--artifacts', '-a', help='生成されたファイル（JSON配列形式）')
@click.option('--message', '-m', help='完了メッセージ')
def complete_task(task_id: str, artifacts: Optional[str], message: Optional[str]):
    """タスクを完了としてマーク

    examples:
        cmw task complete TASK-001
        cmw task complete TASK-001 --artifacts '["file1.py", "file2.py"]'
        cmw task complete TASK-001 -m "実装完了"
    """
    from rich.console import Console

    console = Console()
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)

    # タスクの存在確認
    task = coordinator.get_task(task_id)
    if not task:
        console.print(f"[red]❌ タスク {task_id} が見つかりません[/red]")
        return

    # すでに完了している場合
    if task.status == TaskStatus.COMPLETED:
        console.print(f"[yellow]⚠️  タスク {task_id} は既に完了しています[/yellow]")
        return

    # artifacts をパース
    artifacts_list = []
    if artifacts:
        try:
            artifacts_list = json.loads(artifacts)
        except json.JSONDecodeError:
            console.print("[red]❌ エラー: artifacts は JSON 配列形式で指定してください[/red]")
            console.print('[dim]例: --artifacts \'["file1.py", "file2.py"]\'[/dim]')
            return

    # タスクを完了マーク
    try:
        coordinator.update_task_status(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            artifacts=artifacts_list if artifacts_list else None
        )

        console.print(f"[green]✅ タスク {task_id} を完了としてマークしました[/green]")
        console.print(f"[dim]{task.title}[/dim]")

        if artifacts_list:
            console.print(f"\n[cyan]生成されたファイル:[/cyan]")
            for artifact in artifacts_list:
                console.print(f"  • {artifact}")

        if message:
            console.print(f"\n[cyan]メッセージ:[/cyan] {message}")

    except Exception as e:
        console.print(f"[red]❌ エラー: {str(e)}[/red]")


@cli.command()
@click.option('--compact', is_flag=True, help='コンパクト表示')
def status(compact: bool):
    """プロジェクトの進捗状況を表示"""
    project_path = Path.cwd()
    coordinator = Coordinator(project_path)

    if not coordinator.tasks:
        click.echo("タスクが見つかりません")
        return

    tasks_list = list(coordinator.tasks.values())
    tracker = ProgressTracker(project_path)
    dashboard = Dashboard()

    if compact:
        # コンパクト表示
        dashboard.show_compact_summary(tracker, tasks_list)
    else:
        # フルダッシュボード表示
        dashboard.show_dashboard(tracker, tasks_list)


@cli.command()
@click.option('--from-git', is_flag=True, help='Gitコミットメッセージから進捗を同期')
@click.option('--since', default='1.week.ago', help='コミット検索の開始時点（例: 1.day.ago, 2.weeks.ago, 2025-01-01）')
@click.option('--branch', default='HEAD', help='対象ブランチ（デフォルト: HEAD）')
@click.option('--dry-run', is_flag=True, help='実際には更新せず、検出結果のみ表示')
def sync(from_git: bool, since: str, branch: str, dry_run: bool):
    """進捗を同期

    examples:
        cmw sync --from-git
        cmw sync --from-git --since=1.day.ago
        cmw sync --from-git --dry-run
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    project_path = Path.cwd()

    if not from_git:
        console.print("[yellow]⚠️  同期オプションを指定してください[/yellow]")
        console.print("\n利用可能なオプション:")
        console.print("  --from-git    Gitコミットメッセージから進捗を同期")
        return

    try:
        git = GitIntegration()

        console.print(Panel.fit(
            f"🔄 Git履歴から進捗を同期中... (since: {since}, branch: {branch})",
            border_style="blue"
        ))

        if dry_run:
            # Dry-runモード: 検出のみ
            commits = git._get_commit_log(project_path, since, branch)
            task_ids = git._extract_task_ids(commits)

            console.print(f"\n[cyan]📝 検出されたタスク ({len(task_ids)}件):[/cyan]")
            for task_id in sorted(task_ids):
                console.print(f"  • {task_id}")

            console.print(f"\n[cyan]📊 分析したコミット数:[/cyan] {len(commits)}")
            console.print(f"\n[dim]ヒント: --dry-run なしで実行すると、これらのタスクが完了にマークされます[/dim]")
            return

        # 実際に同期
        result = git.sync_progress_from_git(project_path, since, branch)

        # 結果をテーブルで表示
        console.print("\n[bold green]✅ 同期完了[/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("項目", style="cyan")
        table.add_column("値", justify="right")

        table.add_row("分析したコミット数", str(result['commits_analyzed']))
        table.add_row("検出したタスク数", str(len(result['completed_tasks'])))
        table.add_row("更新したタスク数", str(result['updated_count']))
        table.add_row("スキップしたタスク数", str(result['skipped_count']))

        console.print(table)

        if result['updated_count'] > 0:
            console.print(f"\n[green]完了にマークしたタスク:[/green]")
            coordinator = Coordinator(project_path)
            for task_id in result['completed_tasks']:
                if task_id in coordinator.tasks:
                    task = coordinator.tasks[task_id]
                    if task.status == TaskStatus.COMPLETED:
                        console.print(f"  ✓ {task_id}: {task.title}")

        # タスク参照の検証
        console.print("\n[cyan]🔍 タスク参照を検証中...[/cyan]")
        validation = git.validate_task_references(project_path)

        if validation['invalid']:
            console.print(f"\n[yellow]⚠️  {len(validation['invalid'])}件の不正なタスク参照を検出:[/yellow]")
            for task_id in validation['invalid']:
                console.print(f"  • {task_id} (存在しないタスク)")

            console.print(f"\n[dim]該当するコミット:[/dim]")
            for commit in validation['invalid_commits'][:5]:  # 最大5件表示
                console.print(f"  {commit['hash']}: {commit['message'][:60]}")
        else:
            console.print("[green]✅ 全てのタスク参照が正しいです[/green]")

    except ValueError as e:
        console.print(f"[red]❌ エラー: {str(e)}[/red]")
    except RuntimeError as e:
        console.print(f"[red]❌ Git操作エラー: {str(e)}[/red]")
    except Exception as e:
        console.print(f"[red]❌ 予期しないエラー: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@cli.group(name='requirements')
def requirements():
    """Requirements.md管理コマンド"""
    pass


@requirements.command('generate')
@click.option('--output', '-o', default='shared/docs/requirements.md',
              help='出力先パス')
@click.option('--with-claude', is_flag=True,
              help='Claude Codeと統合して自動生成')
@click.option('--prompt', '-p',
              help='Claude Codeに渡すプロンプト（--with-claude使用時）')
def generate_requirements(output: str, with_claude: bool, prompt: Optional[str]):
    """対話形式でrequirements.mdを生成

    examples:
        cmw requirements generate
        cmw requirements generate -o my-requirements.md
        cmw requirements generate --with-claude --prompt "ホテル予約管理API"
    """
    project_path = Path.cwd()
    output_path = project_path / output

    # 既存ファイルの確認
    if output_path.exists():
        if not click.confirm(f"\n{output} は既に存在します。上書きしますか?"):
            click.echo("キャンセルしました")
            return

    if with_claude:
        # Claude Code統合モード
        if not prompt:
            click.echo("❌ エラー: --with-claude を使用する場合は --prompt でプロンプトを指定してください", err=True)
            click.echo("\n例:")
            click.echo('  cmw requirements generate --with-claude --prompt "ホテル予約管理APIを作成"')
            return

        # プロンプトテンプレートを読み込み
        template_path = Path(__file__).parent.parent.parent / "prompts" / "requirements_generator.md"

        if not template_path.exists():
            click.echo(f"❌ エラー: プロンプトテンプレートが見つかりません: {template_path}", err=True)
            return

        template_content = template_path.read_text(encoding='utf-8')
        final_prompt = template_content.replace('{USER_PROMPT}', prompt)

        # プロンプトを一時ファイルに保存
        prompt_file = project_path / ".cmw_prompt.md"
        prompt_file.write_text(final_prompt, encoding='utf-8')

        click.echo("\n" + "="*80)
        click.echo("🤖 Claude Code統合モード")
        click.echo("="*80)
        click.echo(f"\nユーザーの指示: {prompt}")
        click.echo(f"\nプロンプトファイル: {prompt_file}")
        click.echo(f"出力先: {output_path}")
        click.echo("\n" + "-"*80)
        click.echo("次のステップ:")
        click.echo("  1. Claude Codeを開いてください")
        click.echo(f"  2. 以下のプロンプトを Claude Code に送信してください:")
        click.echo(f"\n     「{prompt_file} の内容に従って、requirements.mdを生成して")
        click.echo(f"      {output_path} に保存してください」")
        click.echo("\n  3. Claude Codeが生成完了したら:")
        click.echo("     cmw task generate でタスク自動生成")
        click.echo("-"*80)
        return

    # 対話型生成（従来のモード）
    from .requirements_generator import RequirementsGenerator

    generator = RequirementsGenerator()
    success = generator.generate_interactive(output_path)

    if success:
        click.echo(f"\n次のステップ:")
        click.echo(f"  1. {output} を確認・編集")
        click.echo(f"  2. cmw task generate でタスク自動生成")
        click.echo(f"  3. cmw status でプロジェクト状況を確認")


# 後方互換性: task のすべてのコマンドを tasks にもコピー
for name, cmd in task.commands.items():
    tasks.add_command(cmd, name=name)


def main():
    """CLIのエントリーポイント"""
    cli()


if __name__ == '__main__':
    cli()
