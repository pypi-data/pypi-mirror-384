"""
Claude Code用プロンプトテンプレート

タスク実行のための最適化されたプロンプトを生成します。
"""
from typing import List, Dict, Optional
from pathlib import Path

from .models import Task, Priority


class PromptTemplate:
    """Claude Code用のタスク実行プロンプトを生成"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = project_root or Path.cwd()

    def generate_task_prompt(
        self,
        task: Task,
        context_tasks: Optional[List[Task]] = None,
        include_instructions: bool = True
    ) -> str:
        """タスク実行用のプロンプトを生成

        Args:
            task: 実行するタスク
            context_tasks: 関連タスク（依存タスクなど）
            include_instructions: 実行手順を含めるか

        Returns:
            Claude Code用のプロンプト文字列
        """
        sections = []

        # タスク概要
        sections.append(self._build_task_overview(task))

        # 実装詳細
        if task.description:
            sections.append(self._build_implementation_details(task))

        # 対象ファイル
        if task.target_files:
            sections.append(self._build_target_files(task))

        # 依存関係
        if task.dependencies and context_tasks:
            sections.append(self._build_dependencies(task, context_tasks))

        # 受入基準
        if task.acceptance_criteria:
            sections.append(self._build_acceptance_criteria(task))

        # コンテキスト情報
        if context_tasks:
            sections.append(self._build_context(task, context_tasks))

        # 実行ステップ
        if include_instructions:
            sections.append(self._build_execution_steps(task))

        return "\n\n".join(filter(None, sections))

    def _build_task_overview(self, task: Task) -> str:
        """タスク概要セクションを構築"""
        priority_emoji = {
            Priority.HIGH: "🔴",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢"
        }
        emoji = priority_emoji.get(task.priority, "⚪")

        lines = [
            f"# {emoji} タスク: {task.id}",
            "",
            f"**タイトル:** {task.title}",
            f"**優先度:** {task.priority.value}",
            f"**担当:** {task.assigned_to}",
        ]

        return "\n".join(lines)

    def _build_implementation_details(self, task: Task) -> str:
        """実装詳細セクションを構築"""
        lines = [
            "## 📋 実装詳細",
            "",
            task.description,
        ]

        return "\n".join(lines)

    def _build_target_files(self, task: Task) -> str:
        """対象ファイルセクションを構築"""
        lines = [
            "## 📁 対象ファイル",
            "",
            "以下のファイルを作成・編集してください：",
            "",
        ]

        for file_path in task.target_files:
            lines.append(f"- `{file_path}`")

        return "\n".join(lines)

    def _build_dependencies(self, task: Task, context_tasks: List[Task]) -> str:
        """依存関係セクションを構築"""
        lines = [
            "## 🔗 依存タスク",
            "",
            "このタスクは以下のタスクに依存しています：",
            "",
        ]

        # 依存タスクの情報を取得
        dep_tasks = {t.id: t for t in context_tasks if t.id in task.dependencies}

        for dep_id in task.dependencies:
            if dep_id in dep_tasks:
                dep_task = dep_tasks[dep_id]
                lines.append(f"- **{dep_id}**: {dep_task.title}")
                if dep_task.target_files:
                    lines.append(f"  - 生成ファイル: {', '.join(f'`{f}`' for f in dep_task.target_files[:3])}")
            else:
                lines.append(f"- **{dep_id}** (詳細不明)")

        lines.append("")
        lines.append("**注意:** これらのタスクが完了していることを前提に実装してください。")

        return "\n".join(lines)

    def _build_acceptance_criteria(self, task: Task) -> str:
        """受入基準セクションを構築"""
        lines = [
            "## ✅ 受入基準",
            "",
            "以下の基準を満たすように実装してください：",
            "",
        ]

        for i, criterion in enumerate(task.acceptance_criteria, 1):
            lines.append(f"{i}. {criterion}")

        return "\n".join(lines)

    def _build_context(self, task: Task, context_tasks: List[Task]) -> str:
        """コンテキスト情報セクションを構築"""
        lines = [
            "## 🗂️ プロジェクトコンテキスト",
            "",
        ]

        # 関連する完了済みタスク
        completed_related = [
            t for t in context_tasks
            if t.id in task.dependencies and hasattr(t, 'status') and t.status.value == 'completed'
        ]

        if completed_related:
            lines.append("### 完了済みの関連タスク")
            lines.append("")
            for t in completed_related[:3]:  # 最大3件
                lines.append(f"- **{t.id}**: {t.title}")
                if t.target_files:
                    lines.append(f"  - ファイル: {', '.join(f'`{f}`' for f in t.target_files[:2])}")
            lines.append("")

        # プロジェクト構造のヒント
        if task.target_files:
            lines.append("### ファイル配置")
            lines.append("")
            lines.append("プロジェクトのディレクトリ構造に従ってファイルを配置してください。")

            # ディレクトリの推測
            dirs = set()
            for file_path in task.target_files:
                parent_dir = str(Path(file_path).parent)
                if parent_dir != '.':
                    dirs.add(parent_dir)

            if dirs:
                lines.append("")
                lines.append("主な配置先:")
                for dir_path in sorted(dirs)[:3]:
                    lines.append(f"- `{dir_path}/`")

        return "\n".join(lines)

    def _build_execution_steps(self, task: Task) -> str:
        """実行ステップセクションを構築"""
        lines = [
            "## 🚀 実装手順",
            "",
            "以下の手順で実装を進めてください：",
            "",
        ]

        steps = []

        # ステップ1: ファイル確認
        if task.dependencies:
            steps.append("1. **依存タスクの成果物を確認**")
            steps.append("   - 依存タスクで作成されたファイルを読み込み、理解する")
            steps.append("")

        # ステップ2: 実装
        step_num = len(steps) // 3 + 1
        if task.target_files:
            steps.append(f"{step_num}. **ファイルの作成/編集**")
            for file_path in task.target_files[:3]:
                steps.append(f"   - `{file_path}` を実装")
            if len(task.target_files) > 3:
                steps.append(f"   - 他 {len(task.target_files) - 3} ファイル")
            steps.append("")
            step_num += 1

        # ステップ3: テスト
        if any('test' in f.lower() for f in task.target_files):
            steps.append(f"{step_num}. **テストの実行**")
            steps.append("   - 作成したテストを実行し、全て通過することを確認")
            steps.append("")
            step_num += 1
        elif task.assigned_to != 'testing':
            steps.append(f"{step_num}. **動作確認**")
            steps.append("   - 実装した機能が正しく動作することを確認")
            steps.append("")
            step_num += 1

        # ステップ4: 受入基準チェック
        if task.acceptance_criteria:
            steps.append(f"{step_num}. **受入基準の確認**")
            steps.append("   - 全ての受入基準を満たしているか確認")
            steps.append("")
            step_num += 1

        # ステップ5: 完了報告
        steps.append(f"{step_num}. **完了報告**")
        steps.append(f"   - タスク {task.id} が完了したことを報告")
        steps.append(f"   - 作成したファイルと主な変更点を記載")

        lines.extend(steps)

        return "\n".join(lines)

    def generate_batch_prompt(
        self,
        tasks: List[Task],
        context_tasks: Optional[List[Task]] = None
    ) -> str:
        """複数タスクを一括実行するプロンプトを生成

        Args:
            tasks: 実行するタスクのリスト
            context_tasks: 関連タスク

        Returns:
            一括実行用のプロンプト文字列
        """
        lines = [
            "# 📦 一括タスク実行",
            "",
            f"以下の {len(tasks)} 個のタスクを順番に実行してください：",
            "",
        ]

        for i, task in enumerate(tasks, 1):
            priority_emoji = {
                Priority.HIGH: "🔴",
                Priority.MEDIUM: "🟡",
                Priority.LOW: "🟢"
            }.get(task.priority, "⚪")

            lines.append(f"## {i}. {priority_emoji} {task.id}: {task.title}")
            lines.append("")

            if task.description:
                # 説明を短く
                desc_lines = task.description.split('\n')
                short_desc = desc_lines[0][:100]
                if len(desc_lines[0]) > 100:
                    short_desc += "..."
                lines.append(f"**説明:** {short_desc}")
                lines.append("")

            if task.target_files:
                lines.append(f"**対象ファイル:** {', '.join(f'`{f}`' for f in task.target_files[:2])}")
                if len(task.target_files) > 2:
                    lines.append(f"  他 {len(task.target_files) - 2} ファイル")
                lines.append("")

            if task.acceptance_criteria:
                lines.append(f"**受入基準:** {len(task.acceptance_criteria)} 件")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 📝 実行方針")
        lines.append("")
        lines.append("1. 各タスクを順番に実行")
        lines.append("2. タスク間の依存関係に注意")
        lines.append("3. 各タスク完了後、簡単な動作確認を実施")
        lines.append("4. 全タスク完了後、統合テストを実行")

        return "\n".join(lines)

    def generate_review_prompt(self, task: Task, implementation_summary: str) -> str:
        """実装レビュー用のプロンプトを生成

        Args:
            task: レビュー対象のタスク
            implementation_summary: 実装の概要

        Returns:
            レビュー用のプロンプト文字列
        """
        lines = [
            f"# 🔍 タスクレビュー: {task.id}",
            "",
            f"**タスク:** {task.title}",
            "",
            "## 実装内容",
            "",
            implementation_summary,
            "",
            "## レビュー観点",
            "",
            "以下の観点でレビューしてください：",
            "",
            "### 1. 受入基準の充足",
        ]

        if task.acceptance_criteria:
            for criterion in task.acceptance_criteria:
                lines.append(f"- [ ] {criterion}")
        else:
            lines.append("- 受入基準が定義されていません")

        lines.extend([
            "",
            "### 2. コード品質",
            "- [ ] コードは読みやすく、理解しやすい",
            "- [ ] 適切なエラーハンドリングが実装されている",
            "- [ ] 必要なコメント・ドキュメントが記載されている",
            "",
            "### 3. テスト",
            "- [ ] 必要なテストが実装されている",
            "- [ ] テストが全て通過している",
            "",
            "### 4. 依存関係",
        ])

        if task.dependencies:
            lines.append("- [ ] 依存タスクの成果物を正しく利用している")
        else:
            lines.append("- 依存タスクはありません")

        lines.extend([
            "",
            "## 判定",
            "",
            "- [ ] **承認** - 全ての基準を満たしている",
            "- [ ] **条件付き承認** - 軽微な修正が必要",
            "- [ ] **却下** - 大幅な修正が必要",
        ])

        return "\n".join(lines)
