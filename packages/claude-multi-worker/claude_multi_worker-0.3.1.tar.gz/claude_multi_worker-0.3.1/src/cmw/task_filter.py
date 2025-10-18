"""
Task Filter - タスクと非タスクを判別

実装タスクと非タスク項目（ガイドライン、要件定義など）を判別し、
適切にフィルタリングするモジュール
"""
from typing import List, Tuple, Dict
from cmw.models import Task


class TaskFilter:
    """タスク/非タスクを判別し、適切にフィルタリング"""

    # 非タスクを示すキーワード
    NON_TASK_KEYWORDS = [
        "技術スタック",
        "推奨",
        "前提条件",
        "概要",
        "非機能要件",
        "制約",
        "想定",
        "注意",
        "背景",
        "目的",
        "について",
        "とは",
        "説明",
        "紹介",
        "まとめ",
        "参考",
        "補足",
    ]

    # タスクを示す動詞
    TASK_VERBS = [
        "実装",
        "作成",
        "構築",
        "開発",
        "設計",
        "追加",
        "修正",
        "更新",
        "削除",
        "統合",
        "テスト",
        "検証",
        "デプロイ",
        "設定",
        "定義",
        "初期化",
    ]

    def is_implementation_task(self, task: Task) -> bool:
        """
        実装タスクかどうかを判定

        Args:
            task: 判定対象のタスク

        Returns:
            True: 実装タスク、False: 非タスク項目
        """
        title = task.title.lower()
        description = (task.description or "").lower()

        # 1. 非タスクキーワードチェック
        for keyword in self.NON_TASK_KEYWORDS:
            if keyword.lower() in title:
                return False

        # 2. タスク動詞チェック
        has_task_verb = any(
            verb in title or verb in description for verb in self.TASK_VERBS
        )
        if not has_task_verb:
            # 受入基準がある場合は動詞がなくても実装タスクの可能性
            if not task.acceptance_criteria:
                return False

        # 3. 受入基準チェック（具体的な基準があればタスク）
        if task.acceptance_criteria:
            if self._has_concrete_criteria(task.acceptance_criteria):
                return True

        # 4. target_filesチェック（具体的なファイルがあればタスク）
        if task.target_files and len(task.target_files) > 0:
            if self._has_concrete_files(task.target_files):
                return True

        # 5. タイトルが抽象的すぎる場合は非タスク
        if self._is_too_abstract(task.title):
            return False

        return True

    def _has_concrete_criteria(self, criteria: List[str]) -> bool:
        """
        受入基準が具体的かどうか判定

        Args:
            criteria: 受入基準のリスト

        Returns:
            True: 具体的、False: 抽象的
        """
        # 抽象的なキーワードが含まれていないか
        abstract_keywords = ["推奨", "想定", "例えば", "など", "一般的", "概要"]

        for criterion in criteria:
            # 抽象的なキーワードが多い場合
            abstract_count = sum(
                1 for kw in abstract_keywords if kw in criterion
            )
            if abstract_count > 1:
                return False

        # 少なくとも1つは具体的な動詞または技術用語を含むか
        technical_terms = [
            "API",
            "POST",
            "GET",
            "PUT",
            "DELETE",
            "JWT",
            "bcrypt",
            "SQLAlchemy",
            "FastAPI",
            "React",
            "pytest",
        ]

        has_technical = any(
            any(term in criterion for term in technical_terms)
            for criterion in criteria
        )

        has_verb = any(
            any(verb in criterion for verb in self.TASK_VERBS)
            for criterion in criteria
        )

        return has_technical or has_verb

    def _has_concrete_files(self, files: List[str]) -> bool:
        """
        ファイルパスが具体的かどうか判定

        Args:
            files: ファイルパスのリスト

        Returns:
            True: 具体的、False: 抽象的
        """
        # すべてのファイルが実在のパスっぽいか
        for file_path in files:
            # 具体的なディレクトリ構造を持つ
            if any(
                dir_name in file_path
                for dir_name in [
                    "backend/",
                    "frontend/",
                    "tests/",
                    "src/",
                    "app/",
                ]
            ):
                return True

            # 具体的な拡張子を持つ
            if any(
                file_path.endswith(ext)
                for ext in [".py", ".js", ".ts", ".tsx", ".vue", ".md"]
            ):
                return True

        return False

    def _is_too_abstract(self, title: str) -> bool:
        """
        タイトルが抽象的すぎるかどうか判定

        Args:
            title: タスクタイトル

        Returns:
            True: 抽象的すぎる、False: 適切
        """
        abstract_patterns = [
            "技術スタック",
            "推奨事項",
            "ベストプラクティス",
            "ガイドライン",
            "方針",
            "戦略",
            "アプローチ",
        ]

        title_lower = title.lower()
        return any(pattern.lower() in title_lower for pattern in abstract_patterns)

    def filter_tasks(
        self, tasks: List[Task]
    ) -> Tuple[List[Task], List[Task]]:
        """
        タスクをフィルタリング

        Args:
            tasks: タスクリスト

        Returns:
            (実装タスクのリスト, 除外された非タスクのリスト)
        """
        implementation_tasks = []
        non_tasks = []

        for task in tasks:
            if self.is_implementation_task(task):
                implementation_tasks.append(task)
            else:
                non_tasks.append(task)

        return implementation_tasks, non_tasks

    def convert_to_references(self, non_tasks: List[Task]) -> List[Dict]:
        """
        非タスクを参照情報に変換

        Args:
            non_tasks: 非タスク項目のリスト

        Returns:
            参照情報のリスト
            [
                {
                    'id': 'REF-001',
                    'title': '技術スタック',
                    'content': '...',
                    'criteria': [...],
                    'applies_to': []
                }
            ]
        """
        references = []

        for i, non_task in enumerate(non_tasks, 1):
            ref = {
                "id": f"REF-{i:03d}",
                "title": non_task.title,
                "content": non_task.description or "",
                "criteria": non_task.acceptance_criteria or [],
                "applies_to": [],  # 後で関連タスクを推論可能
            }
            references.append(ref)

        return references

    def save_references(
        self, references: List[Dict], references_path
    ) -> None:
        """
        参照情報をJSONファイルに保存

        Args:
            references: 参照情報のリスト
            references_path: 保存先パス
        """
        import json

        output = {"references": references, "generated_at": str(datetime.now())}

        references_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# datetime import for save_references
from datetime import datetime
