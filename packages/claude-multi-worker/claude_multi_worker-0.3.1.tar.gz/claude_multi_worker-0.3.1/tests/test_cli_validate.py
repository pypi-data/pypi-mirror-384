"""
cmw task validate コマンドのユニットテスト
"""
import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from cmw.cli import cli


@pytest.fixture
def temp_project(tmp_path):
    """テスト用のプロジェクトディレクトリを作成"""
    # ディレクトリ構造を作成
    coordination_dir = tmp_path / "shared" / "coordination"
    coordination_dir.mkdir(parents=True)

    return tmp_path


@pytest.fixture
def valid_tasks_json(temp_project):
    """正しいtasks.jsonを作成"""
    tasks_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "タスク1",
                "description": "テスト",
                "assigned_to": "backend",
                "dependencies": [],
                "target_files": ["backend/main.py"],
                "acceptance_criteria": ["実装する"],
                "priority": "medium"
            },
            {
                "id": "TASK-002",
                "title": "タスク2",
                "description": "テスト",
                "assigned_to": "backend",
                "dependencies": ["TASK-001"],
                "target_files": ["backend/utils.py"],
                "acceptance_criteria": ["実装する"],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

    return tasks_path


@pytest.fixture
def tasks_with_cycles(temp_project):
    """循環依存を含むtasks.jsonを作成"""
    tasks_data = {
        "tasks": [
            {
                "id": "TASK-004",
                "title": "2.1 モデル定義",
                "description": "モデルを定義",
                "assigned_to": "backend",
                "dependencies": ["TASK-005"],
                "target_files": ["backend/models.py"],
                "acceptance_criteria": ["モデルを実装する"],
                "priority": "high"
            },
            {
                "id": "TASK-005",
                "title": "2.2 データベース初期化",
                "description": "DBを初期化",
                "assigned_to": "backend",
                "dependencies": ["TASK-004"],
                "target_files": ["backend/database.py"],
                "acceptance_criteria": ["DBを初期化する"],
                "priority": "high"
            }
        ],
        "workers": []
    }

    tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

    return tasks_path


@pytest.fixture
def tasks_with_non_tasks(temp_project):
    """非タスク項目を含むtasks.jsonを作成"""
    tasks_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "ユーザー登録",
                "description": "ユーザー登録を実装",
                "assigned_to": "backend",
                "dependencies": [],
                "target_files": ["backend/auth.py"],
                "acceptance_criteria": ["POST /api/auth/register を実装"],
                "priority": "high"
            },
            {
                "id": "TASK-024",
                "title": "技術スタック（推奨）",
                "description": "推奨される技術スタック",
                "assigned_to": "documentation",
                "dependencies": [],
                "target_files": [],
                "acceptance_criteria": ["FastAPI", "PostgreSQL"],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

    return tasks_path


class TestValidateCommand:
    """cmw task validate コマンドのテスト"""

    def test_validate_with_no_issues(self, temp_project, valid_tasks_json, monkeypatch):
        """問題がない場合の検証"""
        runner = CliRunner()

        # カレントディレクトリを変更
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate'], catch_exceptions=False)

        # コマンドが成功
        assert result.exit_code == 0

        # 成功メッセージが表示される
        assert "循環依存は見つかりませんでした" in result.output or "PASS" in result.output
        assert "全てのタスクが実装タスクです" in result.output or "PASS" in result.output

    def test_validate_detects_cycles(self, temp_project, tasks_with_cycles, monkeypatch):
        """循環依存を検出"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate'], catch_exceptions=False)

        assert result.exit_code == 0
        assert "循環依存を検出しました" in result.output or "件" in result.output

    def test_validate_fix_cycles(self, temp_project, tasks_with_cycles, monkeypatch):
        """--fixオプションで循環依存を修正"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate', '--fix'], catch_exceptions=False)

        assert result.exit_code == 0

        # 修正メッセージが表示される
        assert "自動修正" in result.output or "を削除" in result.output

        # tasks.jsonが更新されている
        tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
        updated_data = json.loads(tasks_path.read_text(encoding='utf-8'))

        # 循環依存が解消されている
        tasks = updated_data['tasks']
        task_004 = next(t for t in tasks if t['id'] == 'TASK-004')
        task_005 = next(t for t in tasks if t['id'] == 'TASK-005')

        # TASK-004 → TASK-005 または TASK-005 → TASK-004 のいずれかが削除されている
        assert not (
            'TASK-005' in task_004['dependencies'] and
            'TASK-004' in task_005['dependencies']
        )

    def test_validate_detects_non_tasks(self, temp_project, tasks_with_non_tasks, monkeypatch):
        """非タスク項目を検出"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate'], catch_exceptions=False)

        assert result.exit_code == 0
        assert "非タスク項目を検出しました" in result.output or "TASK-024" in result.output

    def test_validate_fix_non_tasks(self, temp_project, tasks_with_non_tasks, monkeypatch):
        """--fixオプションで非タスク項目を除外"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate', '--fix'], catch_exceptions=False)

        assert result.exit_code == 0

        # 除外メッセージが表示される
        assert "非タスク項目を除外" in result.output or "除外しました" in result.output

        # tasks.jsonが更新されている
        tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
        updated_data = json.loads(tasks_path.read_text(encoding='utf-8'))

        # TASK-024が除外されている
        task_ids = [t['id'] for t in updated_data['tasks']]
        assert 'TASK-024' not in task_ids
        assert 'TASK-001' in task_ids

    def test_validate_missing_tasks_file(self, temp_project, monkeypatch):
        """tasks.jsonが存在しない場合"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate'], catch_exceptions=False)

        # エラーメッセージが表示される
        assert "が見つかりません" in result.output or "エラー" in result.output

    def test_validate_custom_tasks_file(self, temp_project, valid_tasks_json, monkeypatch):
        """カスタムtasks.jsonパスを指定"""
        monkeypatch.chdir(temp_project)

        # カスタムパスにtasks.jsonを配置
        custom_path = temp_project / "custom" / "tasks.json"
        custom_path.parent.mkdir(parents=True)

        # 既存のtasks.jsonをコピー
        tasks_data = json.loads(valid_tasks_json.read_text(encoding='utf-8'))
        custom_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

        runner = CliRunner()
        result = runner.invoke(cli, ['task', 'validate', '--tasks-file', 'custom/tasks.json'],
                               catch_exceptions=False)

        assert result.exit_code == 0
        assert "PASS" in result.output or "全ての検証項目をパス" in result.output


class TestValidateWithMissingDependencies:
    """存在しない依存先のテスト"""

    def test_validate_detects_missing_dependencies(self, temp_project, monkeypatch):
        """存在しない依存先を検出"""
        tasks_data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "タスク1",
                    "description": "テスト",
                    "assigned_to": "backend",
                    "dependencies": ["TASK-999"],  # 存在しない
                    "target_files": ["backend/main.py"],
                    "acceptance_criteria": ["実装する"],
                    "priority": "medium"
                }
            ],
            "workers": []
        }

        tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
        tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate'], catch_exceptions=False)

        assert result.exit_code == 0
        assert "存在しない依存先" in result.output or "TASK-999" in result.output


class TestValidateWithSelfDependency:
    """自己依存のテスト"""

    def test_validate_detects_self_dependency(self, temp_project, monkeypatch):
        """自己依存を検出"""
        tasks_data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "タスク1",
                    "description": "テスト",
                    "assigned_to": "backend",
                    "dependencies": ["TASK-001"],  # 自己依存
                    "target_files": ["backend/main.py"],
                    "acceptance_criteria": ["実装する"],
                    "priority": "medium"
                }
            ],
            "workers": []
        }

        tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
        tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'validate'], catch_exceptions=False)

        assert result.exit_code == 0
        assert "自己依存" in result.output or "不正な依存関係" in result.output
