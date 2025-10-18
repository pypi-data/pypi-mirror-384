"""
PromptTemplate のユニットテスト
"""
import pytest
from pathlib import Path
from cmw.prompt_template import PromptTemplate
from cmw.models import Task, Priority, TaskStatus


@pytest.fixture
def simple_task():
    """シンプルなタスク"""
    return Task(
        id="TASK-001",
        title="ユーザー認証APIの実装",
        description="FastAPIでユーザー認証エンドポイントを実装する",
        assigned_to="backend",
        dependencies=[],
        target_files=["backend/api/auth.py", "backend/schemas/user.py"],
        acceptance_criteria=[
            "POST /api/auth/login が実装されている",
            "POST /api/auth/register が実装されている",
            "JWTトークンを返す"
        ],
        priority=Priority.HIGH
    )


@pytest.fixture
def dependent_task():
    """依存関係のあるタスク"""
    return Task(
        id="TASK-002",
        title="認証ミドルウェアの実装",
        description="JWTトークンを検証するミドルウェアを実装",
        assigned_to="backend",
        dependencies=["TASK-001"],
        target_files=["backend/middleware/auth.py"],
        acceptance_criteria=[
            "JWTトークンを検証する",
            "無効なトークンの場合401を返す"
        ],
        priority=Priority.MEDIUM
    )


@pytest.fixture
def context_tasks(simple_task):
    """コンテキストタスク"""
    return [
        simple_task,
        Task(
            id="TASK-000",
            title="プロジェクト設定",
            description="FastAPIプロジェクトの初期設定",
            assigned_to="backend",
            dependencies=[],
            target_files=["main.py", "requirements.txt"],
            acceptance_criteria=["FastAPIが起動する"],
            priority=Priority.HIGH,
            status=TaskStatus.COMPLETED
        )
    ]


class TestPromptTemplateBasics:
    """PromptTemplate の基本機能テスト"""

    def test_initialization(self):
        """初期化のテスト"""
        template = PromptTemplate()
        assert template.project_root == Path.cwd()

        custom_root = Path("/custom/path")
        template = PromptTemplate(project_root=custom_root)
        assert template.project_root == custom_root

    def test_generate_task_prompt_basic(self, simple_task):
        """基本的なプロンプト生成"""
        template = PromptTemplate()
        prompt = template.generate_task_prompt(simple_task)

        # タスクIDとタイトルが含まれる
        assert "TASK-001" in prompt
        assert "ユーザー認証APIの実装" in prompt

        # 説明が含まれる
        assert "FastAPIでユーザー認証エンドポイントを実装する" in prompt

        # 対象ファイルが含まれる
        assert "backend/api/auth.py" in prompt
        assert "backend/schemas/user.py" in prompt

        # 受入基準が含まれる
        assert "POST /api/auth/login" in prompt
        assert "POST /api/auth/register" in prompt
        assert "JWTトークン" in prompt

    def test_generate_task_prompt_with_context(self, dependent_task, context_tasks):
        """コンテキスト付きプロンプト生成"""
        template = PromptTemplate()
        prompt = template.generate_task_prompt(
            dependent_task,
            context_tasks=context_tasks
        )

        # 依存タスクの情報が含まれる
        assert "TASK-001" in prompt
        assert "依存" in prompt

        # コンテキスト情報が含まれる
        assert "完了済み" in prompt or "コンテキスト" in prompt


class TestBuildMethods:
    """各セクション構築メソッドのテスト"""

    def test_build_task_overview(self, simple_task):
        """タスク概要の構築"""
        template = PromptTemplate()
        overview = template._build_task_overview(simple_task)

        assert "TASK-001" in overview
        assert "ユーザー認証APIの実装" in overview
        assert "high" in overview or "🔴" in overview
        assert "backend" in overview

    def test_build_implementation_details(self, simple_task):
        """実装詳細の構築"""
        template = PromptTemplate()
        details = template._build_implementation_details(simple_task)

        assert "実装詳細" in details
        assert simple_task.description in details

    def test_build_target_files(self, simple_task):
        """対象ファイルセクションの構築"""
        template = PromptTemplate()
        files_section = template._build_target_files(simple_task)

        assert "対象ファイル" in files_section
        assert "backend/api/auth.py" in files_section
        assert "backend/schemas/user.py" in files_section

    def test_build_dependencies(self, dependent_task, context_tasks):
        """依存関係セクションの構築"""
        template = PromptTemplate()
        deps_section = template._build_dependencies(dependent_task, context_tasks)

        assert "依存" in deps_section
        assert "TASK-001" in deps_section

    def test_build_acceptance_criteria(self, simple_task):
        """受入基準セクションの構築"""
        template = PromptTemplate()
        criteria_section = template._build_acceptance_criteria(simple_task)

        assert "受入基準" in criteria_section
        assert "POST /api/auth/login" in criteria_section
        assert "POST /api/auth/register" in criteria_section

    def test_build_context(self, dependent_task, context_tasks):
        """コンテキストセクションの構築"""
        template = PromptTemplate()
        context_section = template._build_context(dependent_task, context_tasks)

        assert "コンテキスト" in context_section
        # ファイル配置情報が含まれる
        assert "ファイル" in context_section or "backend" in context_section

    def test_build_execution_steps(self, simple_task):
        """実行ステップセクションの構築"""
        template = PromptTemplate()
        steps_section = template._build_execution_steps(simple_task)

        assert "実装手順" in steps_section or "手順" in steps_section
        assert "1." in steps_section
        assert "2." in steps_section


class TestPromptGeneration:
    """プロンプト生成の総合テスト"""

    def test_prompt_without_instructions(self, simple_task):
        """実行手順なしのプロンプト"""
        template = PromptTemplate()
        prompt = template.generate_task_prompt(
            simple_task,
            include_instructions=False
        )

        # 基本情報は含まれる
        assert "TASK-001" in prompt

        # 実行手順は含まれない
        assert "実装手順" not in prompt

    def test_prompt_with_empty_fields(self):
        """空フィールドを含むタスクのプロンプト"""
        task = Task(
            id="TASK-003",
            title="シンプルタスク",
            description="",
            assigned_to="backend",
            dependencies=[],
            target_files=[],
            acceptance_criteria=[],
            priority=Priority.LOW
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        # タスクIDとタイトルは必須
        assert "TASK-003" in prompt
        assert "シンプルタスク" in prompt

    def test_prompt_with_many_target_files(self):
        """多数の対象ファイルを持つタスク"""
        task = Task(
            id="TASK-004",
            title="多数ファイル",
            description="テスト",
            assigned_to="backend",
            dependencies=[],
            target_files=[f"file{i}.py" for i in range(10)],
            acceptance_criteria=["実装する"],
            priority=Priority.MEDIUM
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        # 全ファイルが含まれるか、または省略表示
        assert "file0.py" in prompt
        assert "file1.py" in prompt


class TestBatchPrompt:
    """一括プロンプト生成のテスト"""

    def test_generate_batch_prompt(self, simple_task, dependent_task):
        """一括プロンプトの生成"""
        template = PromptTemplate()
        tasks = [simple_task, dependent_task]
        prompt = template.generate_batch_prompt(tasks)

        # 両方のタスクが含まれる
        assert "TASK-001" in prompt
        assert "TASK-002" in prompt

        # タスク数が記載される
        assert "2" in prompt

        # 実行方針が含まれる
        assert "実行方針" in prompt or "順番" in prompt

    def test_generate_batch_prompt_with_context(self, simple_task, dependent_task, context_tasks):
        """コンテキスト付き一括プロンプト"""
        template = PromptTemplate()
        tasks = [simple_task, dependent_task]
        prompt = template.generate_batch_prompt(tasks, context_tasks=context_tasks)

        assert "TASK-001" in prompt
        assert "TASK-002" in prompt

    def test_generate_batch_prompt_single_task(self, simple_task):
        """単一タスクの一括プロンプト"""
        template = PromptTemplate()
        prompt = template.generate_batch_prompt([simple_task])

        assert "TASK-001" in prompt
        assert "1" in prompt


class TestReviewPrompt:
    """レビュープロンプト生成のテスト"""

    def test_generate_review_prompt(self, simple_task):
        """レビュープロンプトの生成"""
        template = PromptTemplate()
        implementation = "認証APIを実装しました。JWTトークンを使用しています。"
        prompt = template.generate_review_prompt(simple_task, implementation)

        # タスク情報が含まれる
        assert "TASK-001" in prompt
        assert "ユーザー認証APIの実装" in prompt

        # 実装内容が含まれる
        assert implementation in prompt

        # レビュー観点が含まれる
        assert "レビュー" in prompt
        assert "受入基準" in prompt
        assert "コード品質" in prompt
        assert "テスト" in prompt

        # 受入基準がチェックリスト形式
        assert "[ ]" in prompt

    def test_generate_review_prompt_without_criteria(self):
        """受入基準なしのレビュープロンプト"""
        task = Task(
            id="TASK-005",
            title="テストタスク",
            description="テスト",
            assigned_to="backend",
            dependencies=[],
            target_files=["test.py"],
            acceptance_criteria=[],
            priority=Priority.LOW
        )

        template = PromptTemplate()
        prompt = template.generate_review_prompt(task, "実装完了")

        assert "TASK-005" in prompt
        assert "レビュー" in prompt


class TestPriorityEmoji:
    """優先度の絵文字表示テスト"""

    def test_high_priority_emoji(self):
        """高優先度の絵文字"""
        task = Task(
            id="TASK-H",
            title="高優先度",
            description="",
            assigned_to="backend",
            dependencies=[],
            target_files=[],
            acceptance_criteria=[],
            priority=Priority.HIGH
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        assert "🔴" in prompt

    def test_medium_priority_emoji(self):
        """中優先度の絵文字"""
        task = Task(
            id="TASK-M",
            title="中優先度",
            description="",
            assigned_to="backend",
            dependencies=[],
            target_files=[],
            acceptance_criteria=[],
            priority=Priority.MEDIUM
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        assert "🟡" in prompt

    def test_low_priority_emoji(self):
        """低優先度の絵文字"""
        task = Task(
            id="TASK-L",
            title="低優先度",
            description="",
            assigned_to="backend",
            dependencies=[],
            target_files=[],
            acceptance_criteria=[],
            priority=Priority.LOW
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        assert "🟢" in prompt


class TestComplexScenarios:
    """複雑なシナリオのテスト"""

    def test_task_with_multiple_dependencies(self):
        """複数の依存関係を持つタスク"""
        task = Task(
            id="TASK-100",
            title="統合タスク",
            description="複数の依存タスクを統合",
            assigned_to="backend",
            dependencies=["TASK-001", "TASK-002", "TASK-003"],
            target_files=["integration.py"],
            acceptance_criteria=["全て統合する"],
            priority=Priority.HIGH
        )

        context = [
            Task(
                id="TASK-001",
                title="タスク1",
                description="",
                assigned_to="backend",
                dependencies=[],
                target_files=["file1.py"],
                acceptance_criteria=[],
                priority=Priority.HIGH
            ),
            Task(
                id="TASK-002",
                title="タスク2",
                description="",
                assigned_to="backend",
                dependencies=[],
                target_files=["file2.py"],
                acceptance_criteria=[],
                priority=Priority.MEDIUM
            ),
        ]

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task, context_tasks=context)

        # 全ての依存タスクが言及される
        assert "TASK-001" in prompt
        assert "TASK-002" in prompt
        assert "TASK-003" in prompt

    def test_test_task_prompt(self):
        """テストタスクのプロンプト"""
        task = Task(
            id="TASK-TEST",
            title="ユニットテスト作成",
            description="認証APIのテストを作成",
            assigned_to="testing",
            dependencies=["TASK-001"],
            target_files=["tests/test_auth.py"],
            acceptance_criteria=[
                "全エンドポイントをテスト",
                "カバレッジ80%以上"
            ],
            priority=Priority.MEDIUM
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        assert "test" in prompt.lower()
        assert "TASK-TEST" in prompt

    def test_documentation_task_prompt(self):
        """ドキュメントタスクのプロンプト"""
        task = Task(
            id="TASK-DOC",
            title="API仕様書作成",
            description="OpenAPI仕様を作成",
            assigned_to="documentation",
            dependencies=[],
            target_files=["docs/openapi.yaml"],
            acceptance_criteria=["全エンドポイントを記載"],
            priority=Priority.LOW
        )

        template = PromptTemplate()
        prompt = template.generate_task_prompt(task)

        assert "TASK-DOC" in prompt
        assert "openapi.yaml" in prompt
