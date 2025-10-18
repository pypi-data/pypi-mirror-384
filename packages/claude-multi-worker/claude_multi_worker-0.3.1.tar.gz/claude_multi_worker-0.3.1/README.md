# Claude Multi-Worker Framework (cmw) v0.3.1

[![Tests](https://github.com/nakishiyaman/cmw/workflows/Tests/badge.svg)](https://github.com/nakishiyaman/cmw/actions)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![codecov](https://codecov.io/gh/nakishiyaman/cmw/branch/main/graph/badge.svg)](https://codecov.io/gh/nakishiyaman/cmw)

**requirements.mdを書くだけで、大規模プロジェクトの開発を完全自動化**

Claude Codeと統合した次世代タスク管理フレームワーク。要件定義から自動的にタスクを生成し、依存関係グラフを可視化し、タスク実行プロンプトを自動生成し、Claude Codeの応答を自動解析します。開発ワークフロー全体を最適化します。

---

## 🎯 cmwはいつ必要？

| シチュエーション | Claude Code単体 | cmw併用 |
|---------------|----------------|---------|
| **プロジェクト規模** | 10タスク以下 | 30タスク以上 |
| **開発期間** | 1日で完了 | 複数日〜数週間 |
| **セッション管理** | 毎回文脈を再説明 | progress.jsonで自動継続 |
| **依存関係管理** | 手動で追跡 | NetworkXで自動管理、循環検出 |
| **ファイル競合** | 実行してみないと分からない | 事前に検出、実行順序を提案 |
| **チーム開発** | 進捗共有が困難 | Git + cmw syncで同期 |

**✅ cmwが役立つケース:**
- 30タスク以上の大規模プロジェクト
- 複数日に渡る開発（セッションを跨ぐ）
- 複雑な依存関係がある（認証→API→テストなど）
- チームで進捗を共有したい

**❌ cmwが不要なケース:**
- 10タスク以下の小規模プロジェクト
- 1セッションで完結する開発
- 単純な機能追加やバグ修正

---

## 🤔 なぜcmwが必要？

Claude Codeは強力ですが、**大規模プロジェクト**では以下の限界があります：

### 問題1: セッションを跨ぐと文脈が消える
Claude Codeは1セッションで全てを完了させることを前提としています。しかし、大規模プロジェクトでは：
- 30タスク以上の開発を1セッションで終えるのは現実的ではない
- セッションを再開すると「どこまで完了したか」を毎回説明する必要がある

**→ cmwの解決策:** `progress.json`で状態を永続化
```bash
# セッション1
cmw task complete TASK-001 TASK-002 TASK-003

# セッション2（翌日）
cmw status  # → 「3/30タスク完了、残り27タスク」と即座に把握
```

### 問題2: 依存関係の追跡が手動
Claude Codeは「どのタスクを先に実行すべきか」を自動判定できません：
- 認証→API→テストという順序を守らないとエラーになる
- 循環依存に気づかずタスクを定義してしまう

**→ cmwの解決策:** NetworkXで自動管理
```bash
cmw task graph  # → 依存関係を可視化
cmw tasks validate --fix  # → 循環依存を自動修正
```

### 問題3: ファイル競合の事前検出不可
Claude Codeは「複数タスクが同じファイルを編集する」ことを事前に検出できません：
- TASK-001とTASK-005が`auth.py`を同時に編集→競合
- 実行してみないと分からない

**→ cmwの解決策:** 事前に競合検出
```bash
cmw tasks analyze
# ⚠️  CRITICAL: auth.py (5タスク競合)
#   推奨実行順: TASK-001 → TASK-002 → TASK-005
```

---

## 📺 デモ

### クイックスタート（30秒）

requirements.mdを書くだけで、タスクが自動生成されます。

![Quick Start Demo](docs/assets/demo-quickstart.gif)

### 依存関係グラフの可視化（10秒）

タスク間の依存関係を自動で可視化し、実行順序を提案します。

![Graph Demo](docs/assets/demo-graph.gif)

### リアルタイム進捗ダッシュボード（5秒）

美しいターミナルUIで進捗を一目で把握できます。

![Dashboard Demo](docs/assets/demo-dashboard.gif)

---

## 🎯 概要

cmwは**タスク管理・メタデータ層**として機能し、Claude Codeと協調して大規模プロジェクトの開発を支援します。

### アーキテクチャ

```
ユーザー「ToDoアプリを作って」
  ↓
┌─────────────────────────────────────────┐
│ Claude Code（司令塔 + 実行層）          │
│  - 自然言語理解                          │
│  - コード生成（自身の機能）              │
│  - ファイル操作                          │
│  - テスト実行                            │
└─────────────────────────────────────────┘
  ↓ ↑ タスク情報の取得・完了報告
┌─────────────────────────────────────────┐
│ cmw（タスク管理・メタデータ層）         │
│  - requirements.md → タスク分解         │
│  - 依存関係グラフ管理                   │
│  - 進捗状態の永続化                     │
│  - ファイル配置ルール                   │
│  - 受け入れ基準                         │
└─────────────────────────────────────────┘
```

### 役割分担

**cmwが担当（WHAT/WHEN/WHERE）:**
- タスク定義と自動生成
- 依存関係管理
- 進捗状態の永続化
- ファイル配置ルール
- 受け入れ基準の提供

**Claude Codeが担当（HOW/WHY）:**
- 技術スタック選択
- 実装パターン決定
- コード生成（自身の機能で実行、API追加コストなし）
- エラー検出と修正

## ✨ 主な機能

### 🚀 実装完了（Phase 0-7 + v0.2.0）

#### 🔧 v0.2.0 新機能

##### ✅ 循環依存の自動修正（Phase 1）
- **DependencyValidator**: 循環依存の検出と自動修正
  - NetworkXによる高精度な循環検出
  - セマンティック分析による修正提案（信頼度スコアリング）
  - 自動修正機能（信頼度100%で即座に適用）
  - セクション番号・キーワードベースの判定
- **TaskFilter**: 非タスク項目の自動除外
  - 「技術スタック」「非機能要件」などを自動判定
  - 実装タスクのみを抽出
  - タスク動詞・受入基準の具体性を評価
- **成果**: blog-apiで17→15タスクに最適化、手動修正不要

##### 🔍 タスク検証コマンド（Phase 2.1）
- **CLIコマンド**: `cmw tasks validate`
  - 循環依存チェック
  - 非タスク項目チェック
  - 依存関係の妥当性チェック（存在しない依存先、自己依存）
  - `--fix`オプションで自動修正
  - Rich UIで視覚的に結果表示
- **成果**: 全検証項目を自動化、問題の早期発見

##### 🔄 Git連携による進捗自動更新（Phase 2.2）
- **GitIntegration**: Gitコミットメッセージから進捗を同期
  - コミットメッセージから`TASK-XXX`パターンを自動検出
  - 検出したタスクを自動で完了にマーク
  - タスク参照の妥当性検証
  - 最近のアクティビティ取得
- **CLIコマンド**: `cmw sync --from-git`
  - `--since`: コミット検索の開始時点（1.day.ago, 1.week.ago等）
  - `--branch`: 対象ブランチ
  - `--dry-run`: 検出のみ実行（更新なし）
- **成果**: 手動での進捗更新が不要に、Git履歴から自動同期

#### 📋 自動タスク生成（Phase 5）
- **RequirementsParser**: requirements.mdから自動でタスク生成
  - Markdown解析とセクション抽出
  - ファイルパスの自動推論（10種類のパターン対応）
  - 依存関係の自動推論（レイヤーベース + ファイルベース）
  - 優先度と担当者の自動決定
- CLIコマンド: `cmw tasks generate`

#### 🔍 ファイル競合検出（Phase 6）
- **ConflictDetector**: タスク間のファイル競合を事前検出
  - WRITE-WRITE競合の検出
  - トポロジカルソートによる最適な実行順序の提案
  - 並列実行グループの自動生成
  - 競合の深刻度判定（CRITICAL/HIGH/MEDIUM/LOW）
  - ファイル使用状況とリスク分析
- CLIコマンド: `cmw tasks analyze`

#### 📊 リアルタイム進捗UI（Phase 7）
- **ProgressTracker**: 進捗メトリクスの計算と追跡
  - 進捗サマリー（完了率、成功率）
  - 残り時間の推定（完了タスクの平均所要時間から算出）
  - タスクタイムライン
  - ベロシティメトリクス（タスク/時間、平均所要時間）
  - 優先度別・担当者別の進捗分解
- **Dashboard**: 美しいターミナルダッシュボード
  - Rich ライブラリによる視覚的なUI
  - プロジェクト概要、ベロシティ、進捗テーブル
  - 最近のアクティビティタイムライン
- CLIコマンド: `cmw status` / `cmw status --compact`

#### 🛠️ タスク管理層（Phase 1）
- **TaskProvider**: タスク情報の提供、コンテキスト構築、状態管理
- **StateManager**: ロック機構、セッション管理、進捗永続化
- **ParallelExecutor**: 並列実行判定、ファイル競合検出

#### ⚠️ エラーハンドリング（Phase 3）
- **ErrorHandler**: エラー対応決定、ロールバック、復旧提案
  - リトライ可能なエラーの自動判定
  - 部分的な成果物の自動削除
  - エラー別の復旧方法提案
  - 影響を受けるタスクの分析

#### 💬 フィードバック機能（Phase 4）
- **FeedbackManager**: リアルタイムフィードバック
  - プロジェクト全体の進捗表示
  - エラーの分かりやすい説明
  - 次のアクション提案

#### 🏗️ 基盤機能（Phase 0）
- プロジェクト初期化（`cmw init`）
- タスク定義（tasks.json）
- 依存関係管理
- 進捗管理
- CLI実装

### 🎓 実プロジェクト検証完了
- **検証プロジェクト**: [todo-api](https://github.com/nakishiyaman/todo-api)
  - 17タスク、2000行コード、106テスト
  - 全タスク完了、全テストパス
  - 9つのAPIエンドポイントが正常動作
  - ファイル競合検出: 2件（CRITICAL 1件、MEDIUM 1件）

## 📦 インストール

### 方法1: Claude Codeプラグインとして（推奨）

Claude Codeから直接インストールできます：

```bash
# Claude Codeのコマンドで
/plugin marketplace add nakishiyaman/cmw
/plugin install cmw-cli@cmw
```

インストール後、Claude Codeから`cmw`コマンドを使用できます。

### 方法2: pipで直接インストール（開発者向け）

```bash
# リポジトリをクローン
git clone https://github.com/nakishiyaman/cmw.git
cd cmw

# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存パッケージをインストール
pip install -r requirements.txt

# cmwコマンドをインストール
pip install -e .
```

## 🚀 クイックスタート

### 1. プロジェクト初期化

```bash
# 新しいプロジェクトを作成
cmw init my-project
cd my-project
```

### 2. requirements.mdを作成

#### 方法A: Claude Code統合（推奨）

`cmw requirements generate`コマンドを使用すると、Claude Codeと連携して自動でrequirements.mdを生成できます。

```bash
# 1行でプロジェクトの要望を伝えるだけ
cmw requirements generate --with-claude --prompt "ToDoアプリを作りたい"

# 次のステップが表示される:
# 1. Claude Codeを開いてください
# 2. 以下のプロンプトを Claude Code に送信してください:
#    「.cmw_prompt.md の内容に従って、requirements.mdを生成して
#     shared/docs/requirements.md に保存してください」
# 3. Claude Codeが生成完了したら:
#    cmw task generate でタスク自動生成
```

**仕組み:**
- cmwがプロンプトテンプレートを生成（`.cmw_prompt.md`）
- ユーザーがそのプロンプトをClaude Codeに渡す
- Claude Codeが詳細なrequirements.mdを生成
- 生成されたrequirements.mdから自動でタスクを生成

#### 方法B: 対話型ウィザード

対話形式で段階的にrequirements.mdを作成できます。

```bash
# 対話型ウィザードを起動
cmw requirements generate

# プロジェクト名、技術スタック、データモデル、API機能などを
# 質問に答えながら入力していく
```

#### 方法C: 手動作成

`shared/docs/requirements.md`に直接要件を記述：

```markdown
# プロジェクト要件

## 1. ユーザー認証
- ユーザー登録機能
- ログイン/ログアウト
- パスワードリセット

## 2. ToDoリスト管理
- ToDoの作成、更新、削除
- 完了/未完了の切り替え
```

### 3. タスク生成

```bash
# requirements.mdからタスクを自動生成
cmw tasks generate
```

### 4. Claude Codeから使用

Claude Codeのセッションで：

```python
from pathlib import Path
from cmw import TaskProvider

# プロジェクトパスを指定
project_path = Path.cwd()
provider = TaskProvider(project_path)

# 次のタスクを取得
task = provider.get_next_task()
print(f"次のタスク: {task.id} - {task.title}")

# タスク開始を記録
provider.mark_started(task.id)

# タスクコンテキストを取得
context = provider.get_task_context(task.id)
print(f"対象ファイル: {context['task']['target_files']}")
print(f"受け入れ基準: {context['task']['acceptance_criteria']}")

# Claude Codeがコーディング（自身の機能で実行）
# ... コード生成 ...

# 完了報告
provider.mark_completed(task.id, ["shared/artifacts/backend/auth.py"])
```

詳細は[Claude Code統合ガイド](docs/CLAUDE_CODE_INTEGRATION.md)を参照してください。

## 📂 プロジェクト構造

```
my-project/
├── shared/
│   ├── docs/                 # 設計ドキュメント
│   │   ├── requirements.md   # 要件定義
│   │   └── api-spec.md       # API仕様
│   ├── coordination/         # タスク定義と進捗
│   │   ├── tasks.json        # タスク定義
│   │   ├── progress.json     # 進捗管理
│   │   └── .lock             # セッションロック
│   └── artifacts/            # 生成されたコード
│       ├── backend/
│       ├── frontend/
│       └── tests/
```

## 🎮 CLIコマンド

### プロジェクト管理

```bash
# プロジェクト初期化
cmw init <project-name>

# プロジェクト状態表示（フルダッシュボード）
cmw status

# プロジェクト状態表示（コンパクト）
cmw status --compact
```

### Requirements管理

```bash
# requirements.md生成（Claude Code統合）
cmw requirements generate --with-claude --prompt "プロジェクトの説明"

# requirements.md生成（対話型ウィザード）
cmw requirements generate

# requirements.md生成（出力先指定）
cmw requirements generate -o custom/path/requirements.md
```

### タスク管理

```bash
# タスク生成
cmw tasks generate

# タスク一覧
cmw tasks list
cmw tasks list --status pending
cmw tasks list --status completed

# タスク詳細
cmw tasks show TASK-001

# タスク検証（v0.2.0）
cmw tasks validate              # 循環依存、非タスク項目、依存関係をチェック
cmw tasks validate --fix        # 検出した問題を自動修正

# ファイル競合分析
cmw tasks analyze

# 依存関係グラフ表示（v0.3.0）
cmw task graph                  # ASCII形式でグラフ表示
cmw task graph --format mermaid # Mermaid形式で出力
cmw task graph --stats          # 統計情報も表示

# タスク実行プロンプト生成（v0.3.0）
cmw task prompt TASK-001        # TASK-001の実行プロンプトを生成

# タスク完了マーク（v0.3.1）
cmw task complete TASK-001                                      # タスクを完了にマーク
cmw task complete TASK-001 --artifacts '["file1.py"]'         # 生成ファイルも記録
cmw task complete TASK-001 -a '["file1.py"]' -m "実装完了"   # メッセージ付き
```

### 進捗管理

```bash
# Git連携で進捗を同期（v0.2.0）
cmw sync --from-git                    # 過去1週間分のコミットから同期
cmw sync --from-git --since=1.day.ago  # 過去1日分
cmw sync --from-git --dry-run          # 検出のみ（更新なし）
```

## 📖 ドキュメント

- **[Claude Code統合ガイド](docs/CLAUDE_CODE_INTEGRATION.md)** - Claude Codeからの使用方法
- **[改善計画](docs/IMPROVEMENTS.md)** - 実プロジェクト検証結果と今後の改善計画
- **[Phase 1実装ガイド](docs/planning/phase-1-implementation-guide.md)** - タスク管理層の実装詳細
- **[アーキテクチャ設計v3.0](docs/planning/multiworker-framework-plan-v3.md)** - 全体設計と計画

## 🧪 テスト

```bash
# 全テストを実行
python -m pytest tests/ -v

# 特定のテストを実行
python -m pytest tests/test_task_provider.py -v
python -m pytest tests/test_state_manager.py -v
python -m pytest tests/test_parallel_executor.py -v
python -m pytest tests/test_error_handler.py -v
python -m pytest tests/test_feedback.py -v
python -m pytest tests/test_requirements_parser.py -v
python -m pytest tests/test_conflict_detector.py -v
python -m pytest tests/test_progress_tracker.py -v
python -m pytest tests/test_graph_visualizer.py -v      # v0.3.0
python -m pytest tests/test_prompt_template.py -v       # v0.3.0
python -m pytest tests/test_static_analyzer.py -v       # v0.3.0
python -m pytest tests/test_interactive_fixer.py -v     # v0.3.0
python -m pytest tests/test_response_parser.py -v       # v0.3.0
python -m pytest tests/test_coordinator.py -v           # v0.3.1
python -m pytest tests/test_cli_complete.py -v          # v0.3.1
```

現在291個のテストが全てパスしています（v0.3.1）。

## 📊 開発ロードマップ

### ✅ Phase 0: 基盤構築（100%）
- プロジェクト構造管理
- タスク生成機能
- Coordinator機能
- CLI基本機能

### ✅ Phase 1: タスク管理層 + 品質向上（100%）- v0.2.0
- **Phase 1.1**: TaskProvider実装（完了）
- **Phase 1.2**: StateManager実装（完了）
- **Phase 1.3**: ParallelExecutor実装（完了）
- **Phase 1.4**: DependencyValidator実装（v0.2.0）
  - 循環依存の自動検出と修正
  - セマンティック分析による高精度判定
  - 信頼度スコアリング
  - 11テスト全パス
- **Phase 1.5**: TaskFilter実装（v0.2.0）
  - 非タスク項目の自動除外
  - タスク動詞・受入基準の評価
  - blog-apiで17→15タスクに最適化

### ✅ Phase 2: Claude Code統合 + ユーザビリティ向上（100%）- v0.2.0
- **Phase 2.1**: タスク検証コマンド（v0.2.0）
  - `cmw tasks validate`実装
  - 循環依存、非タスク項目、依存関係をチェック
  - `--fix`オプションで自動修正
  - Rich UIで視覚的表示
  - 9テスト全パス
- **Phase 2.2**: Git連携による進捗自動更新（v0.2.0）
  - `cmw sync --from-git`実装
  - コミットメッセージから自動でタスク完了を検出
  - タスク参照の妥当性検証
  - 手動での進捗更新が不要に
  - 14テスト全パス
- Phase 2.3: ドキュメント作成（完了）
- Phase 2.4: MCP統合（オプション）

### ✅ Phase 3: エラーハンドリング（100%）
- **Phase 3.1**: ErrorHandler実装（完了）

### ✅ Phase 4: UX/フィードバック（100%）
- **Phase 4.1**: FeedbackManager実装（完了）

### ✅ Phase 5: 自動タスク生成（100%）
- **RequirementsParser実装完了**
  - Markdown解析とセクション抽出
  - ファイルパスの自動推論
  - 依存関係の自動推論
  - 優先度の自動決定
- **CLIコマンド追加**: `cmw tasks generate`
- **テスト**: 23テスト全パス
- **実証**: todo-api検証で手動17タスク→自動20タスク生成

### ✅ Phase 6: ファイル競合検出（100%）
- **ConflictDetector実装完了**
  - ファイル競合の事前検出（WRITE-WRITE検出）
  - 最適な実行順序の提案（トポロジカルソート）
  - 並列実行グループの自動生成
  - 競合の深刻度判定（CRITICAL/HIGH/MEDIUM/LOW）
  - ファイル使用状況とリスク分析
- **CLIコマンド追加**: `cmw tasks analyze`
- **テスト**: 19テスト全パス
- **実証**: todo-apiで2件の競合を検出、8ステップの実行順序を提案

### ✅ Phase 7: リアルタイム進捗UI（100%）
- **ProgressTracker実装完了**
  - 進捗サマリー（完了率、成功率）
  - 残り時間の推定（完了タスクの平均所要時間から算出）
  - タスクタイムライン
  - ベロシティメトリクス（タスク/時間、平均所要時間）
  - 優先度別・担当者別の進捗分解
  - メトリクスの永続化
- **Dashboard実装完了**
  - Rich ライブラリによる美しいターミナルUI
  - プロジェクト概要パネル
  - ベロシティパネル
  - 優先度別進捗テーブル
  - 担当者別進捗テーブル
  - 最近のアクティビティタイムライン
  - プログレスバー表示
- **CLIコマンド拡張**: `cmw status` にダッシュボード機能を統合
  - `cmw status`: フルダッシュボード表示
  - `cmw status --compact`: コンパクトサマリー表示
- **テスト**: 12テスト全パス
- **実証**: todo-apiで17タスクのダッシュボード表示を確認

### ✅ Phase 8: Claude Code統合最適化（100%）- v0.3.0
- **Phase 8.1**: GraphVisualizer実装（完了）
  - タスク依存関係グラフのASCII/Mermaid形式表示
  - クリティカルパスの自動計算
  - 並列実行グループの自動生成
  - グラフ統計情報（タスク数、依存関係数、最大並列度など）
  - `cmw task graph`, `cmw task graph --format mermaid`, `cmw task graph --stats`
  - 20テスト全パス
- **Phase 8.2**: PromptTemplate実装（完了）
  - タスク実行用プロンプトの自動生成
  - 依存タスク情報の自動埋め込み
  - 受入基準と実装手順の構造化
  - バッチ実行用プロンプト、レビュープロンプトの生成
  - `cmw task prompt TASK-XXX`
  - 18テスト全パス
- **Phase 8.3**: StaticAnalyzer実装（完了）
  - Pythonコードの静的解析（ASTベース）
  - ファイル依存関係の自動検出（sys.path動的変更対応）
  - タスク依存関係の自動推論
  - 循環インポート検出、API endpoint抽出、複雑度分析
  - 20テスト全パス、todo-apiで検証済み
- **Phase 8.4**: InteractiveFixer実装（完了）
  - 循環依存の対話的修正
  - タスク選択UI（Rich Table）
  - 修正提案の表示と適用
  - 23テスト全パス
- **Phase 8.5**: ResponseParser実装（完了）
  - Claude Code応答の自動解析
  - ファイルパス抽出（日英対応）
  - タスクID検出、完了キーワード検出
  - 完了コマンドの自動提案
  - エラー・質問の検出
  - 29テスト全パス、実ワークフローで検証済み
- **Phase 8.6**: TaskCompletionCommand実装（v0.3.1）
  - `cmw task complete` コマンド実装
  - `--artifacts` オプションで生成ファイルを記録
  - `--message` オプションで完了メッセージを追加
  - Coordinator進捗管理の強化（progress.json読み込み・マージ）
  - 完了状態のコマンド間永続化
  - 18テスト全パス

**全体進捗**: 100%（v0.3.1リリース完了）

**v0.3.1の新機能:**
- ✅ タスク完了コマンド（`cmw task complete`）
- ✅ 進捗状態の永続化改善
- ✅ Requirements.md自動生成（Claude Code統合）
- ✅ 288個のテスト全パス（+18テスト）

**v0.3.0の主な新機能:**
- ✅ 依存関係グラフの可視化（`cmw task graph`）
- ✅ タスク実行プロンプト自動生成（`cmw task prompt`）
- ✅ 静的コード解析とファイル依存関係検出
- ✅ 対話的な問題修正UI
- ✅ Claude Code応答の自動解析
- ✅ 273個のテスト全パス（+120テスト）
- ✅ todo-apiで実ワークフロー検証完了

---

## 🚧 次期バージョン予告（v0.4.0）

### MCP統合・Plugin化（開発予定）

Claude Codeとのシームレスな統合を実現します。

**予定機能:**
- 🔌 **Model Context Protocol (MCP)サーバー実装**
  - Claude Code内から直接cmw機能を呼び出し
  - `get_next_task()`, `complete_task()` 等のMCP Tools
  - タスク一覧、進捗状況等のMCP Resources

- 📦 **Claude Code Plugin化**
  - ワンコマンドインストール: `/plugin install cmw`
  - スラッシュコマンド: `/next-task`, `/complete-task`
  - Skills（ワークフロー指示書）の自動適用

- ⚡ **ワークフロー自動化**
  - Claude Codeが自動的にタスクを取得・完了マーク
  - 手動のコマンド実行が不要に
  - リアルタイムな進捗同期

**リリース予定:** 2025年11月中旬

**現在の使い方（v0.3.1）:**
```bash
# CLIで手動管理
cmw task list              # タスク一覧表示
cmw task prompt TASK-001   # プロンプト生成
# → Claude Codeで実装
cmw task complete TASK-001 # 完了マーク
```

**v0.4.0での使い方（予定）:**
```bash
# Claude Code内で
ユーザー: 「次のタスクを実装して」
→ Claude Codeが自動でget_next_task()呼び出し
→ 実装
→ 自動でcomplete_task()実行
```

進捗は[GitHub Issues](https://github.com/nakishiyaman/cmw/issues)で追跡できます。

---

## 💡 主な特徴

### 1. 🤖 完全自動化されたタスク生成
requirements.mdを書くだけで、タスクの分解、ファイルパスの推論、依存関係の設定まで全て自動化。手動でtasks.jsonを書く必要はありません。

### 2. 🔍 インテリジェントな競合検出
タスク間のファイル競合を事前に検出し、最適な実行順序を自動提案。並列実行の可否も自動判定します。

### 3. 📊 リアルタイム進捗可視化
美しいターミナルダッシュボードで進捗を可視化。完了率、成功率、推定残り時間、ベロシティメトリクスを一目で確認できます。

### 4. 💰 APIコストゼロ
Claude Codeが直接コードを生成するため、追加のAPI呼び出しコストはかかりません。

### 5. 🔄 セッション継続性
`progress.json`に状態を永続化するため、セッションを跨いで開発を継続できます。

### 6. 🛡️ 堅牢なエラーハンドリング
エラーの自動分類、リトライ判定、ロールバック、復旧提案まで完全自動化。

## 🔧 技術スタック

- **Python 3.12+**
- **Click**: CLIフレームワーク
- **Rich**: ターミナルUI（ダッシュボード表示）
- **NetworkX**: グラフアルゴリズム（依存関係、競合検出）
- **pytest**: テストフレームワーク
- **Pydantic**: データバリデーション（モデル定義）

## 📝 ライセンス

MIT License

## 👥 開発者

- GitHub: https://github.com/nakishiyaman/cmw

## 🤝 貢献

バグ報告や機能リクエストは、GitHubのIssuesでお願いします。

## 🔗 関連リンク

- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
