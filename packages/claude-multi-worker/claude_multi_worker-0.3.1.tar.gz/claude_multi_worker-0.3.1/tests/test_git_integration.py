"""
GitIntegration のユニットテスト
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from cmw.git_integration import GitIntegration
from cmw.models import Task, TaskStatus, Priority


@pytest.fixture
def temp_git_repo(tmp_path):
    """テスト用のGitリポジトリを作成"""
    # .gitディレクトリを作成
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    # shared/coordination ディレクトリを作成
    coordination_dir = tmp_path / "shared" / "coordination"
    coordination_dir.mkdir(parents=True)

    # tasks.jsonを作成
    tasks_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "title": "タスク1",
                "description": "テスト",
                "assigned_to": "backend",
                "status": "pending",
                "dependencies": [],
                "target_files": [],
                "acceptance_criteria": [],
                "priority": "medium"
            },
            {
                "id": "TASK-002",
                "title": "タスク2",
                "description": "テスト",
                "assigned_to": "backend",
                "status": "pending",
                "dependencies": [],
                "target_files": [],
                "acceptance_criteria": [],
                "priority": "medium"
            },
            {
                "id": "TASK-003",
                "title": "タスク3",
                "description": "テスト",
                "assigned_to": "backend",
                "status": "completed",
                "dependencies": [],
                "target_files": [],
                "acceptance_criteria": [],
                "priority": "medium"
            }
        ],
        "workers": []
    }

    tasks_path = coordination_dir / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2), encoding='utf-8')

    return tmp_path


class TestGitIntegration:
    """GitIntegration クラスのテスト"""

    def test_is_git_repo_success(self, temp_git_repo):
        """Gitリポジトリの検出 - 成功"""
        git = GitIntegration()
        assert git._is_git_repo(temp_git_repo) is True

    def test_is_git_repo_failure(self, tmp_path):
        """Gitリポジトリの検出 - 失敗"""
        git = GitIntegration()
        assert git._is_git_repo(tmp_path) is False

    def test_extract_task_ids(self):
        """コミットメッセージからタスクIDを抽出"""
        git = GitIntegration()
        commits = [
            {'hash': 'abc123', 'message': 'feat: TASK-001 を実装'},
            {'hash': 'def456', 'message': 'fix: TASK-002 バグ修正'},
            {'hash': 'ghi789', 'message': 'docs: READMEを更新'},  # タスクIDなし
            {'hash': 'jkl012', 'message': 'test: TASK-001 と TASK-003 のテスト'},  # 複数
        ]

        task_ids = git._extract_task_ids(commits)

        assert 'TASK-001' in task_ids
        assert 'TASK-002' in task_ids
        assert 'TASK-003' in task_ids
        assert len(task_ids) == 3

    def test_extract_task_ids_no_matches(self):
        """タスクIDが含まれないコミット"""
        git = GitIntegration()
        commits = [
            {'hash': 'abc123', 'message': 'docs: READMEを更新'},
            {'hash': 'def456', 'message': 'chore: 依存関係を更新'},
        ]

        task_ids = git._extract_task_ids(commits)

        assert len(task_ids) == 0

    @patch('subprocess.run')
    def test_get_commit_log_success(self, mock_run, temp_git_repo):
        """コミットログの取得 - 成功"""
        # subprocessのモック設定
        mock_result = Mock()
        mock_result.stdout = "abc123|||feat: TASK-001 を実装\ndef456|||fix: TASK-002 バグ修正"
        mock_run.return_value = mock_result

        git = GitIntegration()
        commits = git._get_commit_log(temp_git_repo, since="1.day.ago", branch="main")

        assert len(commits) == 2
        assert commits[0]['hash'] == 'abc123'
        assert commits[0]['message'] == 'feat: TASK-001 を実装'
        assert commits[1]['hash'] == 'def456'
        assert commits[1]['message'] == 'fix: TASK-002 バグ修正'

        # git log が正しい引数で呼ばれたか確認
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert 'git' in call_args[0][0]
        assert 'log' in call_args[0][0]
        assert '--since=1.day.ago' in call_args[0][0]

    @patch('subprocess.run')
    def test_get_commit_log_empty(self, mock_run, temp_git_repo):
        """コミットログの取得 - 空"""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        git = GitIntegration()
        commits = git._get_commit_log(temp_git_repo, since=None, branch="HEAD")

        assert len(commits) == 0

    @patch('cmw.git_integration.Coordinator')
    @patch('subprocess.run')
    def test_sync_progress_from_git_success(self, mock_run, mock_coordinator_class, temp_git_repo):
        """進捗同期 - 成功"""
        # subprocessのモック設定
        mock_result = Mock()
        mock_result.stdout = "abc123|||feat: TASK-001 を実装\ndef456|||fix: TASK-002 バグ修正"
        mock_run.return_value = mock_result

        # Coordinatorのモック設定
        mock_coordinator = MagicMock()
        mock_task_001 = Mock()
        mock_task_001.status = TaskStatus.PENDING
        mock_task_002 = Mock()
        mock_task_002.status = TaskStatus.PENDING

        mock_coordinator.tasks = {
            'TASK-001': mock_task_001,
            'TASK-002': mock_task_002,
        }
        mock_coordinator_class.return_value = mock_coordinator

        # 進捗を同期
        git = GitIntegration()
        result = git.sync_progress_from_git(temp_git_repo, since="1.day.ago")

        # 結果を検証
        assert len(result['completed_tasks']) == 2
        assert 'TASK-001' in result['completed_tasks']
        assert 'TASK-002' in result['completed_tasks']
        assert result['updated_count'] == 2
        assert result['skipped_count'] == 0
        assert result['commits_analyzed'] == 2

        # mark_task_completedが呼ばれたか確認
        assert mock_coordinator.mark_task_completed.call_count == 2

    @patch('cmw.git_integration.Coordinator')
    @patch('subprocess.run')
    def test_sync_progress_from_git_skip_completed(self, mock_run, mock_coordinator_class, temp_git_repo):
        """進捗同期 - 既に完了しているタスクはスキップ"""
        mock_result = Mock()
        mock_result.stdout = "abc123|||feat: TASK-003 を実装"
        mock_run.return_value = mock_result

        # TASK-003は既に完了している
        mock_coordinator = MagicMock()
        mock_task_003 = Mock()
        mock_task_003.status = TaskStatus.COMPLETED

        mock_coordinator.tasks = {
            'TASK-003': mock_task_003,
        }
        mock_coordinator_class.return_value = mock_coordinator

        git = GitIntegration()
        result = git.sync_progress_from_git(temp_git_repo)

        # 結果を検証
        assert result['updated_count'] == 0
        assert result['skipped_count'] == 1
        assert mock_coordinator.mark_task_completed.call_count == 0

    def test_sync_progress_from_git_not_git_repo(self, tmp_path):
        """進捗同期 - Gitリポジトリではない"""
        git = GitIntegration()

        with pytest.raises(ValueError, match="Gitリポジトリではありません"):
            git.sync_progress_from_git(tmp_path)

    @patch('subprocess.run')
    def test_get_task_commits(self, mock_run, temp_git_repo):
        """特定タスクのコミット取得"""
        mock_result = Mock()
        mock_result.stdout = (
            "abc123|||feat: TASK-001 を実装\n"
            "def456|||fix: TASK-002 バグ修正\n"
            "ghi789|||test: TASK-001 テスト追加\n"
            "jkl012|||docs: README更新"
        )
        mock_run.return_value = mock_result

        git = GitIntegration()
        commits = git.get_task_commits(temp_git_repo, "TASK-001")

        assert len(commits) == 2
        assert all('TASK-001' in c['message'] for c in commits)

    @patch('subprocess.run')
    def test_get_recent_activity(self, mock_run, temp_git_repo):
        """最近のアクティビティ取得"""
        mock_result = Mock()
        mock_result.stdout = (
            "abc123|||feat: TASK-001 を実装\n"
            "def456|||fix: TASK-002 バグ修正\n"
            "ghi789|||test: TASK-001 テスト追加"
        )
        mock_run.return_value = mock_result

        git = GitIntegration()
        activity = git.get_recent_activity(temp_git_repo, days=7)

        assert 'TASK-001' in activity
        assert 'TASK-002' in activity
        assert len(activity['TASK-001']) == 2  # 2回コミット
        assert len(activity['TASK-002']) == 1  # 1回コミット

    @patch('cmw.git_integration.Coordinator')
    @patch('subprocess.run')
    def test_validate_task_references(self, mock_run, mock_coordinator_class, temp_git_repo):
        """タスク参照の検証"""
        mock_result = Mock()
        mock_result.stdout = (
            "abc123|||feat: TASK-001 を実装\n"
            "def456|||fix: TASK-999 バグ修正\n"  # 存在しないタスク
            "ghi789|||test: TASK-002 テスト追加"
        )
        mock_run.return_value = mock_result

        # Coordinatorのモック
        mock_coordinator = MagicMock()
        mock_coordinator.tasks = {
            'TASK-001': Mock(),
            'TASK-002': Mock(),
            # TASK-999 は存在しない
        }
        mock_coordinator_class.return_value = mock_coordinator

        git = GitIntegration()
        validation = git.validate_task_references(temp_git_repo)

        assert 'TASK-001' in validation['valid']
        assert 'TASK-002' in validation['valid']
        assert 'TASK-999' in validation['invalid']

        # 不正なコミットが記録されているか
        assert len(validation['invalid_commits']) == 1
        assert validation['invalid_commits'][0]['task_id'] == 'TASK-999'
        assert 'def456' in validation['invalid_commits'][0]['hash']


class TestTaskPatternMatching:
    """タスクIDパターンマッチングのテスト"""

    def test_task_pattern_basic(self):
        """基本的なタスクIDパターン"""
        git = GitIntegration()

        test_cases = [
            ("TASK-001", ["TASK-001"]),
            ("TASK-999", ["TASK-999"]),
            ("TASK-100", ["TASK-100"]),
            ("task-001", []),  # 小文字
            ("TASK-1", []),    # 2桁
            ("TASK-1234", ["TASK-123"]), # 4桁は最初の3桁にマッチ
            ("TICKET-001", []),
        ]

        for text, expected_matches in test_cases:
            matches = git.task_pattern.findall(text)
            assert matches == expected_matches, f"{text} should match {expected_matches}, got {matches}"

    def test_task_pattern_in_sentence(self):
        """文章中のタスクIDパターン"""
        git = GitIntegration()

        messages = [
            "feat: TASK-001 をTASK-002 と統合",
            "fix: TASK-100バグ修正",
            "test: [TASK-050] テスト追加",
            "実装完了: TASK-001, TASK-002, TASK-003",
        ]

        expected_counts = [2, 1, 1, 3]

        for message, expected_count in zip(messages, expected_counts):
            matches = git.task_pattern.findall(message)
            assert len(matches) == expected_count, f"{message} should have {expected_count} matches"
