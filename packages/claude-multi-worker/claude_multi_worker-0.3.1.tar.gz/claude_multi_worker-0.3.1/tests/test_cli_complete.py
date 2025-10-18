"""
cmw task complete コマンドのユニットテスト
"""
import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from cmw.cli import cli


@pytest.fixture
def temp_project(tmp_path):
    """テスト用のプロジェクトディレクトリを作成"""
    coordination_dir = tmp_path / "shared" / "coordination"
    coordination_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def tasks_json(temp_project):
    """tasks.jsonを作成"""
    tasks_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "データベース設計",
                "description": "ユーザーテーブルを設計する",
                "assigned_to": "backend",
                "dependencies": [],
                "target_files": ["backend/models.py"],
                "acceptance_criteria": ["Userモデルを作成"],
                "priority": "high"
            },
            {
                "id": "TASK-002",
                "title": "API実装",
                "description": "ユーザー登録APIを実装",
                "assigned_to": "backend",
                "dependencies": ["TASK-001"],
                "target_files": ["backend/api.py"],
                "acceptance_criteria": ["POST /users を実装"],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    tasks_path = temp_project / "shared" / "coordination" / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')
    return tasks_path


class TestCompleteCommand:
    """cmw task complete コマンドのテスト"""

    def test_complete_task_without_artifacts(self, temp_project, tasks_json, monkeypatch):
        """タスクを完了マーク（artifacts なし）"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'complete', 'TASK-001'], catch_exceptions=False)

        # コマンドが成功
        assert result.exit_code == 0

        # 成功メッセージが表示される
        assert "✅" in result.output or "完了" in result.output
        assert "TASK-001" in result.output

        # progress.jsonが作成されている
        progress_path = temp_project / "shared" / "coordination" / "progress.json"
        assert progress_path.exists()

        # progress.jsonにcompleted状態が保存されている
        progress_data = json.loads(progress_path.read_text(encoding='utf-8'))
        task_001 = next(t for t in progress_data["tasks"] if t["id"] == "TASK-001")
        assert task_001["status"] == "completed"
        assert task_001["completed_at"] is not None

    def test_complete_task_with_artifacts(self, temp_project, tasks_json, monkeypatch):
        """タスクを完了マーク（artifacts あり）"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(
            cli,
            ['task', 'complete', 'TASK-001', '--artifacts', '["backend/models.py", "tests/test_models.py"]'],
            catch_exceptions=False
        )

        # コマンドが成功
        assert result.exit_code == 0

        # 成功メッセージとアーティファクトが表示される
        assert "✅" in result.output or "完了" in result.output
        assert "backend/models.py" in result.output
        assert "tests/test_models.py" in result.output

        # progress.jsonにartifactsが保存されている
        progress_path = temp_project / "shared" / "coordination" / "progress.json"
        progress_data = json.loads(progress_path.read_text(encoding='utf-8'))
        task_001 = next(t for t in progress_data["tasks"] if t["id"] == "TASK-001")

        assert task_001["status"] == "completed"
        assert task_001["artifacts"] == ["backend/models.py", "tests/test_models.py"]

    def test_complete_task_with_message(self, temp_project, tasks_json, monkeypatch):
        """タスクを完了マーク（メッセージ付き）"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(
            cli,
            ['task', 'complete', 'TASK-001', '-m', 'モデル実装完了'],
            catch_exceptions=False
        )

        # コマンドが成功
        assert result.exit_code == 0

        # メッセージが表示される
        assert "モデル実装完了" in result.output

    def test_complete_task_with_short_option(self, temp_project, tasks_json, monkeypatch):
        """短縮オプション -a と -m をテスト"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(
            cli,
            ['task', 'complete', 'TASK-001', '-a', '["backend/models.py"]', '-m', 'Complete'],
            catch_exceptions=False
        )

        # コマンドが成功
        assert result.exit_code == 0
        assert "backend/models.py" in result.output
        assert "Complete" in result.output

    def test_complete_non_existing_task(self, temp_project, tasks_json, monkeypatch):
        """存在しないタスクを完了マーク"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ['task', 'complete', 'TASK-999'], catch_exceptions=False)

        # エラーメッセージが表示される
        assert "❌" in result.output or "見つかりません" in result.output
        assert "TASK-999" in result.output

    def test_complete_already_completed_task(self, temp_project, tasks_json, monkeypatch):
        """既に完了しているタスクを再度完了マーク"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        # 1回目の完了
        result1 = runner.invoke(cli, ['task', 'complete', 'TASK-001'], catch_exceptions=False)
        assert result1.exit_code == 0

        # 2回目の完了（既に完了している）
        result2 = runner.invoke(cli, ['task', 'complete', 'TASK-001'], catch_exceptions=False)

        # 警告メッセージが表示される
        assert "⚠️" in result2.output or "既に完了" in result2.output

    def test_complete_with_invalid_json_artifacts(self, temp_project, tasks_json, monkeypatch):
        """不正なJSON形式のartifacts"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(
            cli,
            ['task', 'complete', 'TASK-001', '--artifacts', 'invalid-json'],
            catch_exceptions=False
        )

        # エラーメッセージが表示される
        assert "❌" in result.output or "エラー" in result.output
        assert "JSON" in result.output

    def test_complete_persists_across_commands(self, temp_project, tasks_json, monkeypatch):
        """完了状態が別のコマンドでも保持される"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        # タスクを完了
        result1 = runner.invoke(
            cli,
            ['task', 'complete', 'TASK-001', '--artifacts', '["backend/models.py"]'],
            catch_exceptions=False
        )
        assert result1.exit_code == 0

        # タスク詳細を表示
        result2 = runner.invoke(cli, ['task', 'show', 'TASK-001'], catch_exceptions=False)

        # completed状態が表示される
        assert "completed" in result2.output
        assert "backend/models.py" in result2.output

        # 完了タスク一覧にも表示される
        result3 = runner.invoke(cli, ['task', 'list', '--status', 'completed'], catch_exceptions=False)
        assert "TASK-001" in result3.output

    def test_complete_enables_dependent_tasks(self, temp_project, tasks_json, monkeypatch):
        """タスク完了により依存タスクが実行可能になる"""
        runner = CliRunner()
        monkeypatch.chdir(temp_project)

        # TASK-001を完了
        result1 = runner.invoke(cli, ['task', 'complete', 'TASK-001'], catch_exceptions=False)
        assert result1.exit_code == 0

        # Coordinatorを使って実行可能タスクを確認
        from cmw.coordinator import Coordinator
        coordinator = Coordinator(temp_project)
        executable = coordinator.get_executable_tasks()

        # TASK-002が実行可能になっている
        assert len(executable) == 1
        assert executable[0].id == "TASK-002"


class TestCompleteCommandHelp:
    """cmw task complete --help のテスト"""

    def test_help_message(self):
        """ヘルプメッセージの表示"""
        runner = CliRunner()
        result = runner.invoke(cli, ['task', 'complete', '--help'])

        assert result.exit_code == 0
        assert "タスクを完了としてマーク" in result.output
        assert "--artifacts" in result.output
        assert "--message" in result.output
        assert "examples:" in result.output
