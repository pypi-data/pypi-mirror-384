"""
StateManager - 状態の永続化とセッション管理

役割:
- 複数セッション間での状態共有
- ロック機構による競合回避
- セッションの継続性保証
"""
from pathlib import Path
from typing import Optional
import json
import time
import os


class StateManager:
    """状態管理とロック機構"""

    LOCK_TIMEOUT = 300  # 5分

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.progress_file = project_path / "shared/coordination/progress.json"
        self.lock_file = project_path / "shared/coordination/.lock"

    def acquire_lock(self, timeout: int = 10) -> bool:
        """
        ロックを取得

        Args:
            timeout: タイムアウト秒数

        Returns:
            ロック取得成功ならTrue
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._try_acquire_lock():
                return True
            time.sleep(0.1)

        return False

    def release_lock(self):
        """ロックを解放"""
        if self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except FileNotFoundError:
                pass  # 既に削除済み

    def is_locked(self) -> bool:
        """ロックされているか確認"""
        if not self.lock_file.exists():
            return False

        lock_data = self._read_lock()
        if not lock_data:
            return False

        # タイムアウトチェック
        if time.time() - lock_data['timestamp'] > self.LOCK_TIMEOUT:
            # 古いロックは無効
            self.release_lock()
            return False

        return True

    def get_lock_info(self) -> Optional[dict]:
        """ロック情報を取得"""
        if not self.lock_file.exists():
            return None

        return self._read_lock()

    def _try_acquire_lock(self) -> bool:
        """ロック取得を試みる"""
        # 既にロックされているかチェック
        if self.is_locked():
            return False

        # ロックを作成
        lock_data = {
            'session_id': os.getpid(),
            'timestamp': time.time(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        }

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file.write_text(
            json.dumps(lock_data, indent=2),
            encoding='utf-8'
        )

        return True

    def _read_lock(self) -> Optional[dict]:
        """ロックファイルを読み込み"""
        try:
            return json.loads(self.lock_file.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError):
            return None


class SessionContext:
    """
    セッション管理のコンテキストマネージャー

    使用例:
        with SessionContext(project_path) as session:
            # ロックを取得した状態で作業
            provider = TaskProvider(project_path)
            task = provider.get_next_task()
        # ロック自動解放
    """

    def __init__(self, project_path: Path):
        self.state_manager = StateManager(project_path)

    def __enter__(self):
        if not self.state_manager.acquire_lock():
            raise RuntimeError(
                "Could not acquire lock. "
                "Another session may be running."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state_manager.release_lock()
