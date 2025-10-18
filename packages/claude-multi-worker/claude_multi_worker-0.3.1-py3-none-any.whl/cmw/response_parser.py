"""
Response Parser - Claude Code出力の自動解析

Claude Codeの応答テキストを解析して、タスク完了を自動検出します。
"""
import re
import json
from typing import List, Optional, Dict
from pathlib import Path


class ResponseParser:
    """Claude Codeの応答を解析してタスク完了を検出"""

    # ファイル作成/編集を示すパターン
    FILE_PATTERNS = [
        # 日本語パターン
        r'`([^`]+\.[a-zA-Z0-9]+)`\s*を作成',
        r'`([^`]+\.[a-zA-Z0-9]+)`\s*に.*を追加',
        r'`([^`]+\.[a-zA-Z0-9]+)`\s*を.*更新',
        r'`([^`]+\.[a-zA-Z0-9]+)`\s*を編集',
        r'`([^`]+\.[a-zA-Z0-9]+)`\s*を修正',
        r'`([^`]+\.[a-zA-Z0-9]+)`\s*に.*実装',
        # 英語パターン
        r'[Cc]reated\s+`([^`]+\.[a-zA-Z0-9]+)`',
        r'[Uu]pdated\s+`([^`]+\.[a-zA-Z0-9]+)`',
        r'[Mm]odified\s+`([^`]+\.[a-zA-Z0-9]+)`',
        r'[Ee]dited\s+`([^`]+\.[a-zA-Z0-9]+)`',
        r'[Aa]dded\s+`([^`]+\.[a-zA-Z0-9]+)`',
        r'[Ii]mplemented\s+`([^`]+\.[a-zA-Z0-9]+)`',
        # ファイルパス単独（より緩いパターン）
        r'`([a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+)`',
    ]

    # タスク完了を示すキーワード
    COMPLETION_KEYWORDS = [
        # 日本語
        '完了しました',
        '実装しました',
        '作成しました',
        '追加しました',
        '完成しました',
        '終了しました',
        # 英語
        'completed',
        'finished',
        'done',
        'implemented',
        'created',
        'added',
    ]

    # タスクIDパターン
    TASK_ID_PATTERN = r'TASK-\d{3}'

    def __init__(self):
        """初期化"""
        self.file_regex = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.FILE_PATTERNS]
        self.task_id_regex = re.compile(self.TASK_ID_PATTERN)

    def parse_response(self, response_text: str) -> Dict[str, any]:
        """
        Claude Codeの応答を解析

        Args:
            response_text: Claude Codeの出力テキスト

        Returns:
            解析結果の辞書
            {
                'artifacts': [...],  # 作成/編集されたファイル
                'task_ids': [...],   # 言及されたタスクID
                'is_completed': bool # 完了を示すキーワードがあるか
            }
        """
        artifacts = self._extract_artifacts(response_text)
        task_ids = self._extract_task_ids(response_text)
        is_completed = self._detect_completion(response_text)

        return {
            'artifacts': artifacts,
            'task_ids': task_ids,
            'is_completed': is_completed
        }

    def _extract_artifacts(self, text: str) -> List[str]:
        """
        応答からファイルパスを抽出

        Args:
            text: 解析するテキスト

        Returns:
            ファイルパスのリスト
        """
        artifacts = set()

        for regex in self.file_regex:
            matches = regex.findall(text)
            # ファイルパスのみを抽出（余分な文字を除去）
            for match in matches:
                # タプルの場合は最初の要素を取得
                if isinstance(match, tuple):
                    match = match[0]

                # ファイルパスのクリーンアップ
                cleaned = match.strip()

                # 有効なファイルパスかチェック
                if '.' in cleaned and len(cleaned) < 200:
                    # __pycache__や.pyc等は除外
                    if not any(x in cleaned for x in ['__pycache__', '.pyc', '.pyo']):
                        artifacts.add(cleaned)

        return sorted(artifacts)

    def _extract_task_ids(self, text: str) -> List[str]:
        """
        応答からタスクIDを抽出

        Args:
            text: 解析するテキスト

        Returns:
            タスクIDのリスト
        """
        matches = self.task_id_regex.findall(text)
        return sorted(set(matches))

    def _detect_completion(self, text: str) -> bool:
        """
        完了キーワードを検出

        Args:
            text: 解析するテキスト

        Returns:
            完了キーワードが含まれるか
        """
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.COMPLETION_KEYWORDS)

    def suggest_completion(self, response_text: str, task_id: str) -> Optional[str]:
        """
        タスク完了の提案を生成

        Args:
            response_text: Claude Codeの出力
            task_id: 対象タスクID

        Returns:
            完了コマンドの提案（完了していると判定されない場合はNone）
        """
        result = self.parse_response(response_text)

        # 完了していない場合はNone
        if not result['is_completed']:
            return None

        # タスクIDまたはアーティファクトが必要
        if task_id not in result['task_ids'] and not result['artifacts']:
            return None

        # 完了コマンドを生成
        if result['artifacts']:
            artifacts_str = json.dumps(result['artifacts'])
            return f"cmw task complete {task_id} --artifacts '{artifacts_str}'"
        else:
            return f"cmw task complete {task_id}"

    def auto_mark_completed(
        self,
        response_text: str,
        task_id: str,
        project_path: Path
    ) -> bool:
        """
        応答からタスク完了を自動マーク

        Args:
            response_text: Claude Codeの出力
            task_id: 対象タスクID
            project_path: プロジェクトパス

        Returns:
            タスク完了をマークしたかどうか
        """
        from .task_provider import TaskProvider

        result = self.parse_response(response_text)

        # 完了判定
        if not result['is_completed']:
            return False

        # タスクIDまたはアーティファクトが言及されているか
        if task_id not in result['task_ids'] and not result['artifacts']:
            return False

        # タスク完了をマーク
        try:
            provider = TaskProvider(project_path)
            provider.mark_completed(task_id, result['artifacts'])
            return True
        except Exception:
            return False

    def extract_summary(self, response_text: str, max_length: int = 200) -> str:
        """
        応答から要約を抽出

        Args:
            response_text: 応答テキスト
            max_length: 最大文字数

        Returns:
            要約テキスト
        """
        # 最初の段落を取得
        lines = response_text.strip().split('\n')

        summary_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                summary_lines.append(line)
                if len(' '.join(summary_lines)) > max_length:
                    break

        summary = ' '.join(summary_lines)

        # 長すぎる場合は切り詰め
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + '...'

        return summary

    def detect_errors(self, response_text: str) -> List[Dict[str, str]]:
        """
        応答からエラーを検出

        Args:
            response_text: 応答テキスト

        Returns:
            エラー情報のリスト
        """
        errors = []

        # エラーパターン
        error_patterns = [
            (r'Error:\s*(.+)', 'error'),
            (r'Exception:\s*(.+)', 'exception'),
            (r'Failed:\s*(.+)', 'failure'),
            (r'エラー:\s*(.+)', 'error'),
            (r'失敗:\s*(.+)', 'failure'),
        ]

        for pattern, error_type in error_patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                errors.append({
                    'type': error_type,
                    'message': match.group(1).strip()
                })

        return errors

    def is_asking_question(self, response_text: str) -> bool:
        """
        応答が質問を含んでいるか判定

        Args:
            response_text: 応答テキスト

        Returns:
            質問を含んでいるか
        """
        question_patterns = [
            r'\?',           # 英語の疑問符
            r'？',          # 日本語の疑問符
            r'ですか',
            r'でしょうか',
            r'よろしいですか',
            r'ますか',
            r'[Ss]hould I',
            r'[Dd]o you want',
            r'[Ww]ould you like',
        ]

        for pattern in question_patterns:
            if re.search(pattern, response_text, re.MULTILINE):
                return True

        return False
