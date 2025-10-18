"""
ResponseParser のユニットテスト
"""
import pytest
from pathlib import Path
from cmw.response_parser import ResponseParser


class TestResponseParserBasics:
    """ResponseParser の基本機能テスト"""

    def test_initialization(self):
        """初期化のテスト"""
        parser = ResponseParser()
        assert parser is not None
        assert len(parser.file_regex) > 0
        assert parser.task_id_regex is not None


class TestParseResponse:
    """応答解析のテスト"""

    def test_parse_response_japanese(self):
        """日本語応答の解析"""
        response = """
        TASK-001の認証機能を実装しました。

        `backend/auth.py` を作成し、以下の機能を追加しました:
        - JWT認証
        - パスワードハッシュ化

        `tests/test_auth.py` を作成し、テストを追加しました。
        """

        parser = ResponseParser()
        result = parser.parse_response(response)

        assert "backend/auth.py" in result['artifacts']
        assert "tests/test_auth.py" in result['artifacts']
        assert "TASK-001" in result['task_ids']
        assert result['is_completed'] is True

    def test_parse_response_english(self):
        """英語応答の解析"""
        response = """
        I completed TASK-002.

        Created `backend/models.py` with User model.
        Updated `backend/database.py` to add new tables.

        The implementation is finished.
        """

        parser = ResponseParser()
        result = parser.parse_response(response)

        assert "backend/models.py" in result['artifacts']
        assert "backend/database.py" in result['artifacts']
        assert "TASK-002" in result['task_ids']
        assert result['is_completed'] is True

    def test_parse_response_no_completion(self):
        """完了していない応答"""
        response = """
        I'm working on TASK-003.
        I need to modify `backend/config.py`.
        """

        parser = ResponseParser()
        result = parser.parse_response(response)

        assert "backend/config.py" in result['artifacts']
        assert "TASK-003" in result['task_ids']
        assert result['is_completed'] is False


class TestExtractArtifacts:
    """ファイル抽出のテスト"""

    def test_extract_artifacts_various_patterns(self):
        """様々なパターンのファイル抽出"""
        parser = ResponseParser()

        test_cases = [
            ("`backend/auth.py` を作成", ["backend/auth.py"]),
            ("`models.py` を更新", ["models.py"]),
            ("Created `test.py`", ["test.py"]),
            ("Updated `app/main.py` and `app/config.py`", ["app/main.py", "app/config.py"]),
            ("`src/utils/helper.ts` に関数を追加", ["src/utils/helper.ts"]),
        ]

        for text, expected in test_cases:
            artifacts = parser._extract_artifacts(text)
            for exp in expected:
                assert exp in artifacts

    def test_extract_artifacts_excludes_invalid(self):
        """無効なファイルの除外"""
        parser = ResponseParser()

        text = """
        `__pycache__/models.cpython-39.pyc` は除外
        `backend/__pycache__/` も除外
        `valid_file.py` は含める
        """

        artifacts = parser._extract_artifacts(text)

        assert "valid_file.py" in artifacts
        assert not any('__pycache__' in a for a in artifacts)
        assert not any('.pyc' in a for a in artifacts)

    def test_extract_artifacts_no_files(self):
        """ファイルなしの場合"""
        parser = ResponseParser()
        artifacts = parser._extract_artifacts("No files mentioned here.")

        assert len(artifacts) == 0


class TestExtractTaskIds:
    """タスクID抽出のテスト"""

    def test_extract_task_ids_single(self):
        """単一タスクID"""
        parser = ResponseParser()
        task_ids = parser._extract_task_ids("TASK-001を完了しました")

        assert "TASK-001" in task_ids

    def test_extract_task_ids_multiple(self):
        """複数タスクID"""
        parser = ResponseParser()
        task_ids = parser._extract_task_ids(
            "TASK-001とTASK-002、TASK-003を実装しました"
        )

        assert "TASK-001" in task_ids
        assert "TASK-002" in task_ids
        assert "TASK-003" in task_ids

    def test_extract_task_ids_duplicates(self):
        """重複したタスクID"""
        parser = ResponseParser()
        task_ids = parser._extract_task_ids(
            "TASK-001を開始しました。TASK-001を完了しました。"
        )

        # 重複が除去されている
        assert task_ids.count("TASK-001") == 1

    def test_extract_task_ids_none(self):
        """タスクIDなし"""
        parser = ResponseParser()
        task_ids = parser._extract_task_ids("No task IDs here")

        assert len(task_ids) == 0


class TestDetectCompletion:
    """完了検出のテスト"""

    def test_detect_completion_japanese(self):
        """日本語の完了キーワード"""
        parser = ResponseParser()

        test_cases = [
            "実装を完了しました",
            "タスクを完成しました",
            "ファイルを作成しました",
            "機能を追加しました",
        ]

        for text in test_cases:
            assert parser._detect_completion(text) is True

    def test_detect_completion_english(self):
        """英語の完了キーワード"""
        parser = ResponseParser()

        test_cases = [
            "Task completed successfully",
            "Implementation finished",
            "Done with the feature",
            "Created the new module",
        ]

        for text in test_cases:
            assert parser._detect_completion(text) is True

    def test_detect_completion_negative(self):
        """完了していない"""
        parser = ResponseParser()

        test_cases = [
            "Working on the task",
            "In progress",
            "Need to fix this",
        ]

        for text in test_cases:
            assert parser._detect_completion(text) is False


class TestSuggestCompletion:
    """完了提案のテスト"""

    def test_suggest_completion_with_artifacts(self):
        """成果物ありの完了提案"""
        response = """
        TASK-001を完了しました。
        `backend/auth.py` を作成しました。
        """

        parser = ResponseParser()
        suggestion = parser.suggest_completion(response, "TASK-001")

        assert suggestion is not None
        assert "cmw task complete" in suggestion
        assert "TASK-001" in suggestion
        assert "backend/auth.py" in suggestion

    def test_suggest_completion_without_artifacts(self):
        """成果物なしの完了提案"""
        response = """
        TASK-002を完了しました。
        """

        parser = ResponseParser()
        suggestion = parser.suggest_completion(response, "TASK-002")

        assert suggestion is not None
        assert "cmw task complete TASK-002" in suggestion

    def test_suggest_completion_not_completed(self):
        """完了していない場合"""
        response = """
        TASK-003を作業中です。
        """

        parser = ResponseParser()
        suggestion = parser.suggest_completion(response, "TASK-003")

        assert suggestion is None

    def test_suggest_completion_wrong_task_id(self):
        """異なるタスクID"""
        response = """
        TASK-001を完了しました。
        """

        parser = ResponseParser()
        # TASK-002を指定（応答にはTASK-001）
        suggestion = parser.suggest_completion(response, "TASK-002")

        # タスクIDが一致しないのでNone
        assert suggestion is None


class TestExtractSummary:
    """要約抽出のテスト"""

    def test_extract_summary_short(self):
        """短い要約"""
        parser = ResponseParser()
        summary = parser.extract_summary("認証機能を実装しました。")

        assert summary == "認証機能を実装しました。"

    def test_extract_summary_long(self):
        """長い要約（切り詰め）"""
        parser = ResponseParser()
        long_text = "A" * 300
        summary = parser.extract_summary(long_text, max_length=100)

        assert len(summary) <= 100
        assert summary.endswith("...")

    def test_extract_summary_skip_headers(self):
        """ヘッダーをスキップ"""
        parser = ResponseParser()
        text = """
# タイトル

認証機能を実装しました。
        """
        summary = parser.extract_summary(text)

        assert "認証機能を実装しました。" in summary
        assert "#" not in summary


class TestDetectErrors:
    """エラー検出のテスト"""

    def test_detect_errors_english(self):
        """英語のエラー検出"""
        parser = ResponseParser()
        text = """
        Error: File not found
        Exception: Invalid syntax
        """

        errors = parser.detect_errors(text)

        assert len(errors) >= 2
        assert any(e['type'] == 'error' for e in errors)
        assert any(e['type'] == 'exception' for e in errors)

    def test_detect_errors_japanese(self):
        """日本語のエラー検出"""
        parser = ResponseParser()
        text = """
        エラー: ファイルが見つかりません
        """

        errors = parser.detect_errors(text)

        assert len(errors) >= 1
        assert errors[0]['type'] == 'error'

    def test_detect_errors_none(self):
        """エラーなし"""
        parser = ResponseParser()
        errors = parser.detect_errors("Everything is working fine.")

        assert len(errors) == 0


class TestIsAskingQuestion:
    """質問検出のテスト"""

    def test_is_asking_question_japanese(self):
        """日本語の質問"""
        parser = ResponseParser()

        test_cases = [
            "これで実装しますか？",
            "続けてもよろしいですか",
            "次のタスクを実行してもいいでしょうか？",
        ]

        for text in test_cases:
            assert parser.is_asking_question(text) is True

    def test_is_asking_question_english(self):
        """英語の質問"""
        parser = ResponseParser()

        test_cases = [
            "Should I proceed with this?",
            "Do you want me to continue?",
            "Would you like me to implement this?",
        ]

        for text in test_cases:
            assert parser.is_asking_question(text) is True

    def test_is_asking_question_negative(self):
        """質問ではない"""
        parser = ResponseParser()

        test_cases = [
            "I implemented the feature.",
            "タスクを完了しました。",
        ]

        for text in test_cases:
            assert parser.is_asking_question(text) is False


class TestComplexScenarios:
    """複雑なシナリオのテスト"""

    def test_real_world_response(self):
        """実世界の応答例"""
        response = """
        TASK-005の実装を完了しました。

        以下のファイルを作成・編集しました：

        1. `backend/routers/auth.py` を作成
           - POST /auth/register エンドポイント
           - POST /auth/login エンドポイント

        2. `backend/schemas.py` を更新
           - UserCreate, UserLogin スキーマを追加

        3. `tests/test_auth.py` を作成
           - 認証エンドポイントのテストを実装

        全ての受入基準を満たしています。
        """

        parser = ResponseParser()
        result = parser.parse_response(response)

        # ファイルが抽出される
        assert "backend/routers/auth.py" in result['artifacts']
        assert "backend/schemas.py" in result['artifacts']
        assert "tests/test_auth.py" in result['artifacts']

        # タスクIDが抽出される
        assert "TASK-005" in result['task_ids']

        # 完了と判定される
        assert result['is_completed'] is True

    def test_mixed_language_response(self):
        """日英混在の応答"""
        response = """
        TASK-010を完了しました。

        Created `app.py` and updated `config.py`.
        実装した機能:
        - Authentication
        - ユーザー管理

        The implementation is finished.
        """

        parser = ResponseParser()
        result = parser.parse_response(response)

        assert "app.py" in result['artifacts']
        assert "config.py" in result['artifacts']
        assert "TASK-010" in result['task_ids']
        assert result['is_completed'] is True
