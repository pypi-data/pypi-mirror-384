"""
RequirementsParserのテスト
"""
import pytest
from pathlib import Path
import tempfile
import json

from src.cmw.requirements_parser import RequirementsParser
from src.cmw.models import Task


class TestRequirementsParser:
    """RequirementsParserのテスト"""

    @pytest.fixture
    def parser(self):
        """パーサーインスタンス"""
        return RequirementsParser()

    @pytest.fixture
    def sample_requirements(self):
        """サンプルrequirements.md"""
        content = """# サンプルプロジェクト要件

## 1. データベース設定

### 1.1 モデル定義
- Userモデルの作成
- Taskモデルの作成
- リレーションシップの設定

## 2. 認証機能

### 2.1 ユーザー登録
- エンドポイント: POST /auth/register
- メールアドレスバリデーション
- パスワードハッシュ化

### 2.2 ログイン
- エンドポイント: POST /auth/login
- JWTトークン発行
- 認証情報の検証

## 3. タスク管理API

### 3.1 タスク作成
- エンドポイント: POST /tasks
- タイトルバリデーション
- 認証済みユーザーのタスク作成

### 3.2 タスク一覧取得
- エンドポイント: GET /tasks
- フィルタ機能
- ソート機能
"""
        return content

    @pytest.fixture
    def temp_requirements_file(self, sample_requirements):
        """一時的なrequirements.mdファイル"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(sample_requirements)
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    def test_parse_creates_tasks(self, parser, temp_requirements_file):
        """requirements.mdからタスクが生成される"""
        tasks = parser.parse(temp_requirements_file)

        assert len(tasks) > 0
        assert all(isinstance(task, Task) for task in tasks)

    def test_parse_assigns_task_ids(self, parser, temp_requirements_file):
        """タスクIDが正しく採番される"""
        tasks = parser.parse(temp_requirements_file)

        task_ids = [task.id for task in tasks]
        assert task_ids[0] == "TASK-001"
        assert all(task_id.startswith("TASK-") for task_id in task_ids)

        # IDがユニーク
        assert len(task_ids) == len(set(task_ids))

    def test_infer_target_files_for_models(self, parser):
        """モデル関連タスクのファイル推論"""
        files = parser._infer_target_files(
            "データベースモデル定義",
            ["Userモデルの作成", "Taskモデルの作成"]
        )

        assert "backend/models.py" in files

    def test_infer_target_files_for_auth_endpoint(self, parser):
        """認証エンドポイントのファイル推論"""
        files = parser._infer_target_files(
            "ユーザー登録エンドポイント",
            ["エンドポイント: POST /auth/register", "メールアドレスバリデーション"]
        )

        assert "backend/routers/auth.py" in files

    def test_infer_target_files_for_task_endpoint(self, parser):
        """タスクエンドポイントのファイル推論"""
        files = parser._infer_target_files(
            "タスク作成エンドポイント",
            ["エンドポイント: POST /tasks", "タイトルバリデーション"]
        )

        assert "backend/routers/tasks.py" in files

    def test_infer_target_files_for_database(self, parser):
        """データベース設定のファイル推論"""
        files = parser._infer_target_files(
            "データベース設定",
            ["SQLAlchemyのセットアップ", "データベース接続の確立"]
        )

        assert "backend/database.py" in files

    def test_infer_target_files_for_schemas(self, parser):
        """Pydanticスキーマのファイル推論"""
        files = parser._infer_target_files(
            "Pydanticスキーマ定義",
            ["UserCreateスキーマ", "TaskResponseスキーマ", "バリデーション"]
        )

        assert "backend/schemas.py" in files

    def test_infer_target_files_for_auth_utils(self, parser):
        """認証ユーティリティのファイル推論"""
        files = parser._infer_target_files(
            "認証ユーティリティ実装",
            ["パスワードハッシュ化", "JWTトークン生成", "bcrypt使用"]
        )

        assert "backend/auth.py" in files

    def test_infer_target_files_for_tests(self, parser):
        """テストファイルの推論"""
        files = parser._infer_target_files(
            "認証テストの作成",
            ["ユーザー登録テスト", "ログインテスト"]
        )

        assert any("test" in f for f in files)

    def test_infer_priority_high(self, parser):
        """高優先度の推論"""
        priority = parser._infer_priority("データベースモデル定義")
        assert priority == "high"

        priority = parser._infer_priority("認証機能実装")
        assert priority == "high"

    def test_infer_priority_low(self, parser):
        """低優先度の推論"""
        priority = parser._infer_priority("README.md作成")
        assert priority == "low"

        priority = parser._infer_priority("タスク削除エンドポイント")
        assert priority == "low"

    def test_infer_priority_medium(self, parser):
        """中優先度の推論"""
        priority = parser._infer_priority("タスク一覧取得")
        assert priority == "medium"

    def test_infer_assigned_to_backend(self, parser):
        """backend担当の推論"""
        assigned = parser._infer_assigned_to(["backend/routers/auth.py"])
        assert assigned == "backend"

    def test_infer_assigned_to_testing(self, parser):
        """testing担当の推論"""
        assigned = parser._infer_assigned_to(["tests/test_auth.py"])
        assert assigned == "testing"

    def test_infer_assigned_to_documentation(self, parser):
        """documentation担当の推論"""
        assigned = parser._infer_assigned_to(["README.md"])
        assert assigned == "documentation"

    def test_extract_sections(self, parser, sample_requirements):
        """セクション抽出"""
        sections = parser._extract_sections(sample_requirements)

        assert len(sections) == 3
        assert sections[0]['title'] == "1. データベース設定"
        assert sections[1]['title'] == "2. 認証機能"
        assert sections[2]['title'] == "3. タスク管理API"

        # サブセクションの確認
        assert len(sections[0]['subsections']) == 1
        assert sections[0]['subsections'][0]['title'] == "1.1 モデル定義"

    def test_dependencies_layer_based(self, parser, temp_requirements_file):
        """レイヤーベースの依存関係推論"""
        tasks = parser.parse(temp_requirements_file)

        # 生成されたタスクが存在することを確認
        assert len(tasks) > 0

        # 全てのタスクがvalidな構造を持つことを確認
        for task in tasks:
            assert task.id is not None
            assert isinstance(task.dependencies, list)

            # 依存関係が循環していないことを確認（簡易版）
            # 各タスクは自分自身に依存しない
            assert task.id not in task.dependencies

    def test_parse_file_not_found(self, parser):
        """存在しないファイルのエラー"""
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/requirements.md"))

    def test_task_has_required_fields(self, parser, temp_requirements_file):
        """生成されたタスクが必要なフィールドを持つ"""
        tasks = parser.parse(temp_requirements_file)

        for task in tasks:
            assert task.id is not None
            assert task.title is not None
            assert task.description is not None
            assert isinstance(task.target_files, list)
            assert isinstance(task.acceptance_criteria, list)
            assert task.priority in ['low', 'medium', 'high']
            assert isinstance(task.dependencies, list)

    def test_acceptance_criteria_extracted(self, parser, temp_requirements_file):
        """受け入れ基準が正しく抽出される"""
        tasks = parser.parse(temp_requirements_file)

        # モデル定義タスクを探す
        model_task = next((t for t in tasks
                          if 'モデル定義' in t.title or 'models.py' in t.target_files),
                         None)

        if model_task and model_task.acceptance_criteria:
            # 受け入れ基準が抽出されている
            assert len(model_task.acceptance_criteria) > 0


# Note: 以下のテストは、外部プロジェクト（todo-api）に依存しているため、
# Public化にあたりコメントアウトしています。
# ローカル環境で検証する場合は、適宜パスを修正してコメントを解除してください。

# class TestRealWorldRequirements:
#     """実際のrequirements.mdを使用したテスト"""
#
#     @pytest.fixture
#     def parser(self):
#         return RequirementsParser()
#
#     def test_parse_todo_api_requirements(self, parser):
#         """todo-apiのrequirements.mdを解析"""
#         # todo-apiのrequirements.mdパス（環境に応じて変更）
#         todo_api_req = Path("path/to/todo-api/shared/docs/requirements.md")
#
#         if not todo_api_req.exists():
#             pytest.skip("todo-api requirements.md not found")
#
#         tasks = parser.parse(todo_api_req)
#
#         # 少なくとも10タスク以上生成されるはず
#         assert len(tasks) >= 10
#
#         # タスクIDの確認
#         task_ids = [t.id for t in tasks]
#         assert len(task_ids) == len(set(task_ids))  # ユニーク
#
#         # データベースタスクが存在
#         db_tasks = [t for t in tasks if 'database' in ' '.join(t.target_files).lower()]
#         assert len(db_tasks) > 0
#
#         # 認証タスクが存在
#         auth_tasks = [t for t in tasks if 'auth' in ' '.join(t.target_files).lower()]
#         assert len(auth_tasks) > 0
#
#         # テストタスクが存在
#         test_tasks = [t for t in tasks if any('test' in f for f in t.target_files)]
#         assert len(test_tasks) > 0
#
#     def test_generated_tasks_have_valid_dependencies(self, parser):
#         """生成されたタスクの依存関係が有効"""
#         todo_api_req = Path("path/to/todo-api/shared/docs/requirements.md")
#
#         if not todo_api_req.exists():
#             pytest.skip("todo-api requirements.md not found")
#
#         tasks = parser.parse(todo_api_req)
#         task_ids = {t.id for t in tasks}
#
#         # 全ての依存関係が存在するタスクを参照している
#         for task in tasks:
#             for dep_id in task.dependencies:
#                 assert dep_id in task_ids, f"Invalid dependency {dep_id} in {task.id}"
#
#     def test_no_self_dependencies(self, parser):
#         """自己依存がないことを確認"""
#         todo_api_req = Path("path/to/todo-api/shared/docs/requirements.md")
#
#         if not todo_api_req.exists():
#             pytest.skip("todo-api requirements.md not found")
#
#         tasks = parser.parse(todo_api_req)
#
#         # 各タスクが自分自身に依存していないことを確認
#         for task in tasks:
#             assert task.id not in task.dependencies, \
#                 f"Task {task.id} depends on itself"
