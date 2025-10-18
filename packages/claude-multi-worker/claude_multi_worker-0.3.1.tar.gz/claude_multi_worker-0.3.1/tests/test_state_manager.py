"""
StateManagerのユニットテスト
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import time
from cmw.state_manager import StateManager, SessionContext


@pytest.fixture
def test_project():
    """テスト用プロジェクトを作成"""
    temp_dir = Path(tempfile.mkdtemp())

    # ディレクトリ構造を作成
    (temp_dir / "shared/coordination").mkdir(parents=True)

    yield temp_dir

    # クリーンアップ
    shutil.rmtree(temp_dir)


def test_acquire_and_release_lock(test_project):
    """ロックの取得と解放"""
    manager = StateManager(test_project)

    # ロック取得
    assert manager.acquire_lock()
    assert manager.is_locked()

    # ロック解放
    manager.release_lock()
    assert not manager.is_locked()


def test_cannot_acquire_lock_twice(test_project):
    """同じロックを2回取得できない"""
    manager1 = StateManager(test_project)
    manager2 = StateManager(test_project)

    # manager1がロック取得
    assert manager1.acquire_lock()

    # manager2はロック取得できない（タイムアウト1秒で試す）
    assert not manager2.acquire_lock(timeout=1)

    # manager1がロック解放
    manager1.release_lock()

    # manager2がロック取得可能に
    assert manager2.acquire_lock()
    manager2.release_lock()


def test_lock_timeout(test_project):
    """古いロックは自動的に無効化される"""
    manager = StateManager(test_project)

    # ロック取得
    manager.acquire_lock()

    # ロックファイルのタイムスタンプを古くする（6分前）
    lock_data = manager._read_lock()
    lock_data['timestamp'] = time.time() - 360  # 6分前
    manager.lock_file.write_text(
        __import__('json').dumps(lock_data, indent=2),
        encoding='utf-8'
    )

    # 古いロックは無効と判定される
    assert not manager.is_locked()

    # 新しいロックを取得できる
    assert manager.acquire_lock()
    manager.release_lock()


def test_get_lock_info(test_project):
    """ロック情報を取得できる"""
    manager = StateManager(test_project)

    # ロックがない状態
    assert manager.get_lock_info() is None

    # ロック取得
    manager.acquire_lock()

    # ロック情報を取得
    lock_info = manager.get_lock_info()
    assert lock_info is not None
    assert 'session_id' in lock_info
    assert 'timestamp' in lock_info
    assert 'hostname' in lock_info

    manager.release_lock()


def test_session_context_success(test_project):
    """SessionContextの正常動作"""
    manager = StateManager(test_project)

    # コンテキストマネージャーでロック取得
    with SessionContext(test_project) as session:
        # ロックが取得されている
        assert manager.is_locked()

    # コンテキスト終了後、ロックが解放されている
    assert not manager.is_locked()


def test_session_context_lock_failure(test_project):
    """SessionContextでロック取得失敗時に例外が発生"""
    manager1 = StateManager(test_project)

    # 先にロックを取得
    manager1.acquire_lock()

    # 別のセッションでロック取得を試みると例外
    with pytest.raises(RuntimeError, match="Could not acquire lock"):
        with SessionContext(test_project):
            pass

    manager1.release_lock()


def test_session_context_exception_handling(test_project):
    """SessionContext内で例外が発生してもロックが解放される"""
    manager = StateManager(test_project)

    try:
        with SessionContext(test_project):
            # 例外を発生させる
            raise ValueError("Test exception")
    except ValueError:
        pass

    # 例外が発生してもロックは解放される
    assert not manager.is_locked()


def test_lock_file_creation(test_project):
    """ロックファイルが正しく作成される"""
    manager = StateManager(test_project)

    # ロック取得前
    assert not manager.lock_file.exists()

    # ロック取得
    manager.acquire_lock()

    # ロックファイルが作成される
    assert manager.lock_file.exists()

    # ロック解放
    manager.release_lock()

    # ロックファイルが削除される
    assert not manager.lock_file.exists()
