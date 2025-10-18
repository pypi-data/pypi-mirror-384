"""
Requirements Generator - 対話型requirements.md生成

ユーザーとの対話を通じて、プロジェクト要件を収集し、
requirements.mdを自動生成する。
"""
from typing import List, Dict, Optional
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown


class RequirementsGenerator:
    """対話型requirements.md生成機能"""

    def __init__(self):
        self.console = Console()
        self.requirements_data = {}

    def generate_interactive(self, output_path: Path) -> bool:
        """
        対話形式でrequirements.mdを生成

        Args:
            output_path: 出力先パス

        Returns:
            生成成功したかどうか
        """
        self.console.print(Panel.fit(
            "📝 Requirements.md 対話型生成ウィザード",
            border_style="blue"
        ))
        self.console.print("\nプロジェクトに関する質問に答えてください。\n")

        # 1. プロジェクト基本情報
        self._collect_basic_info()

        # 2. 技術スタック
        self._collect_tech_stack()

        # 3. データモデル
        self._collect_data_models()

        # 4. API機能
        self._collect_api_features()

        # 5. 非機能要件
        self._collect_non_functional()

        # 6. 生成確認
        self.console.print("\n" + "="*80)
        self.console.print("[bold cyan]収集した情報:[/bold cyan]\n")
        self._show_summary()

        if not Confirm.ask("\nこの内容でrequirements.mdを生成しますか?", default=True):
            self.console.print("[yellow]生成をキャンセルしました[/yellow]")
            return False

        # 7. requirements.md生成
        content = self._generate_markdown()
        output_path.write_text(content, encoding='utf-8')

        self.console.print(f"\n[green]✅ {output_path} を生成しました[/green]")
        return True

    def _collect_basic_info(self):
        """プロジェクト基本情報を収集"""
        self.console.print("[bold]1. プロジェクト基本情報[/bold]\n")

        self.requirements_data['project_name'] = Prompt.ask(
            "プロジェクト名",
            default="新規プロジェクト"
        )

        self.requirements_data['description'] = Prompt.ask(
            "プロジェクトの説明（1行で）",
            default="RESTful APIを使用したシステム"
        )

        self.requirements_data['project_type'] = Prompt.ask(
            "プロジェクトタイプ",
            choices=["rest-api", "graphql-api", "web-app", "cli-tool", "other"],
            default="rest-api"
        )

    def _collect_tech_stack(self):
        """技術スタックを収集"""
        self.console.print("\n[bold]2. 技術スタック[/bold]\n")

        # バックエンド
        backend = Prompt.ask(
            "バックエンドフレームワーク",
            choices=["fastapi", "django", "flask", "express", "other"],
            default="fastapi"
        )

        # データベース
        database = Prompt.ask(
            "データベース",
            choices=["sqlite", "postgresql", "mysql", "mongodb", "other"],
            default="sqlite"
        )

        # ORM
        orm = Prompt.ask(
            "ORM/ODM",
            choices=["sqlalchemy", "django-orm", "prisma", "mongoose", "none"],
            default="sqlalchemy"
        )

        # 認証
        needs_auth = Confirm.ask("認証機能が必要ですか?", default=True)
        auth_method = None
        if needs_auth:
            auth_method = Prompt.ask(
                "認証方式",
                choices=["jwt", "session", "oauth2", "other"],
                default="jwt"
            )

        self.requirements_data['tech_stack'] = {
            'backend': backend,
            'database': database,
            'orm': orm,
            'auth': auth_method
        }

    def _collect_data_models(self):
        """データモデルを収集"""
        self.console.print("\n[bold]3. データモデル[/bold]\n")

        models = []

        while True:
            model_name = Prompt.ask(
                "モデル名 (完了したら空Enter)",
                default=""
            )

            if not model_name:
                break

            # フィールド収集
            fields = []
            self.console.print(f"\n[cyan]{model_name}モデルのフィールドを入力:[/cyan]")

            while True:
                field_name = Prompt.ask(
                    "  フィールド名 (完了したら空Enter)",
                    default=""
                )

                if not field_name:
                    break

                field_type = Prompt.ask(
                    f"  {field_name}の型",
                    choices=["string", "integer", "boolean", "datetime", "text", "float"],
                    default="string"
                )

                is_required = Confirm.ask(f"  {field_name}は必須?", default=True)
                is_unique = Confirm.ask(f"  {field_name}は一意?", default=False)

                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'required': is_required,
                    'unique': is_unique
                })

            models.append({
                'name': model_name,
                'fields': fields
            })

            if not Confirm.ask("\n他にモデルを追加しますか?", default=True):
                break

        self.requirements_data['models'] = models

    def _collect_api_features(self):
        """API機能を収集"""
        self.console.print("\n[bold]4. API機能[/bold]\n")

        features = []

        # 認証機能
        if self.requirements_data['tech_stack']['auth']:
            needs_register = Confirm.ask("ユーザー登録機能が必要?", default=True)
            needs_login = Confirm.ask("ログイン機能が必要?", default=True)

            if needs_register:
                features.append({
                    'name': 'ユーザー登録',
                    'endpoint': 'POST /auth/register',
                    'description': 'ユーザーアカウントの新規登録'
                })

            if needs_login:
                features.append({
                    'name': 'ログイン',
                    'endpoint': 'POST /auth/login',
                    'description': '認証してアクセストークンを取得'
                })

        # CRUD機能
        for model in self.requirements_data.get('models', []):
            model_name = model['name'].lower()

            needs_crud = Confirm.ask(
                f"\n{model['name']}のCRUD操作が必要?",
                default=True
            )

            if needs_crud:
                # 一覧取得
                features.append({
                    'name': f'{model["name"]}一覧取得',
                    'endpoint': f'GET /{model_name}s',
                    'description': f'{model["name"]}のリストを取得'
                })

                # 詳細取得
                features.append({
                    'name': f'{model["name"]}詳細取得',
                    'endpoint': f'GET /{model_name}s/{{id}}',
                    'description': f'指定した{model["name"]}を取得'
                })

                # 作成
                features.append({
                    'name': f'{model["name"]}作成',
                    'endpoint': f'POST /{model_name}s',
                    'description': f'新しい{model["name"]}を作成'
                })

                # 更新
                features.append({
                    'name': f'{model["name"]}更新',
                    'endpoint': f'PUT /{model_name}s/{{id}}',
                    'description': f'{model["name"]}情報を更新'
                })

                # 削除
                features.append({
                    'name': f'{model["name"]}削除',
                    'endpoint': f'DELETE /{model_name}s/{{id}}',
                    'description': f'{model["name"]}を削除'
                })

        self.requirements_data['features'] = features

    def _collect_non_functional(self):
        """非機能要件を収集"""
        self.console.print("\n[bold]5. 非機能要件[/bold]\n")

        # パフォーマンス
        target_response_time = Prompt.ask(
            "目標レスポンスタイム(ms)",
            default="200"
        )

        # テストカバレッジ
        test_coverage = Prompt.ask(
            "テストカバレッジ目標(%)",
            default="80"
        )

        # セキュリティ
        needs_security = Confirm.ask("セキュリティ要件を含める?", default=True)

        self.requirements_data['non_functional'] = {
            'response_time': int(target_response_time),
            'test_coverage': int(test_coverage),
            'security': needs_security
        }

    def _show_summary(self):
        """収集した情報のサマリーを表示"""
        # プロジェクト情報
        self.console.print(f"プロジェクト名: {self.requirements_data['project_name']}")
        self.console.print(f"説明: {self.requirements_data['description']}")
        self.console.print(f"タイプ: {self.requirements_data['project_type']}")

        # 技術スタック
        tech = self.requirements_data['tech_stack']
        self.console.print(f"\n技術スタック:")
        self.console.print(f"  Backend: {tech['backend']}")
        self.console.print(f"  Database: {tech['database']}")
        self.console.print(f"  ORM: {tech['orm']}")
        if tech['auth']:
            self.console.print(f"  認証: {tech['auth']}")

        # モデル数
        model_count = len(self.requirements_data.get('models', []))
        self.console.print(f"\nデータモデル: {model_count}個")

        # API機能数
        feature_count = len(self.requirements_data.get('features', []))
        self.console.print(f"API機能: {feature_count}個")

    def _generate_markdown(self) -> str:
        """requirements.mdを生成"""
        lines = []

        # タイトル
        lines.append(f"# {self.requirements_data['project_name']} - プロジェクト要件書\n")

        # 概要
        lines.append("## 概要\n")
        lines.append(f"{self.requirements_data['description']}\n")

        # 技術スタック
        lines.append("## 技術スタック\n")
        tech = self.requirements_data['tech_stack']

        backend_map = {
            'fastapi': 'Python 3.12+ with FastAPI',
            'django': 'Python 3.12+ with Django',
            'flask': 'Python 3.12+ with Flask',
            'express': 'Node.js with Express',
        }
        lines.append(f"- **Backend**: {backend_map.get(tech['backend'], tech['backend'])}")

        db_map = {
            'sqlite': 'SQLite (開発用)',
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL',
            'mongodb': 'MongoDB'
        }
        lines.append(f"- **Database**: {db_map.get(tech['database'], tech['database'])}")

        if tech['orm'] and tech['orm'] != 'none':
            lines.append(f"- **ORM**: {tech['orm'].title()}")

        if tech['auth']:
            auth_map = {
                'jwt': 'JWT (python-jose)',
                'session': 'Session認証',
                'oauth2': 'OAuth 2.0'
            }
            lines.append(f"- **認証**: {auth_map.get(tech['auth'], tech['auth'])}")

        lines.append("\n")

        # データモデル
        if self.requirements_data.get('models'):
            lines.append("## データモデル設計\n")

            for i, model in enumerate(self.requirements_data['models'], 1):
                lines.append(f"### {i}. {model['name']}モデル\n")

                for field in model['fields']:
                    type_map = {
                        'string': '文字列',
                        'integer': '整数型',
                        'boolean': 'ブール型',
                        'datetime': '日時型',
                        'text': 'テキスト',
                        'float': '浮動小数点'
                    }

                    constraints = []
                    if field['required']:
                        constraints.append('必須')
                    if field['unique']:
                        constraints.append('ユニーク制約')

                    constraint_str = f"、{', '.join(constraints)}" if constraints else ""
                    lines.append(f"- {field['name']}: {type_map[field['type']]}{constraint_str}")

                lines.append("\n")

        # API機能
        if self.requirements_data.get('features'):
            lines.append("## API機能\n")

            # 機能をグループ化
            auth_features = [f for f in self.requirements_data['features']
                           if 'auth' in f['endpoint']]
            other_features = [f for f in self.requirements_data['features']
                            if 'auth' not in f['endpoint']]

            if auth_features:
                lines.append("### 認証機能\n")
                for i, feature in enumerate(auth_features, 1):
                    lines.append(f"#### {feature['name']}\n")
                    lines.append(f"- エンドポイント: `{feature['endpoint']}`")
                    lines.append(f"- 説明: {feature['description']}\n")
                    lines.append("**受入基準:**")
                    lines.append(f"- 正常に{feature['name']}ができる")
                    lines.append(f"- 適切なバリデーションが実装されている\n")

            if other_features:
                # モデル別にグループ化
                model_features = {}
                for feature in other_features:
                    # エンドポイントからモデル名を抽出
                    parts = feature['endpoint'].split('/')
                    if len(parts) >= 2:
                        model_key = parts[1].split('s')[0] if parts[1].endswith('s') else parts[1]
                        if model_key not in model_features:
                            model_features[model_key] = []
                        model_features[model_key].append(feature)

                for model_key, features in model_features.items():
                    lines.append(f"### {model_key.title()}管理機能\n")
                    for feature in features:
                        lines.append(f"#### {feature['name']}\n")
                        lines.append(f"- エンドポイント: `{feature['endpoint']}`")
                        lines.append(f"- 説明: {feature['description']}\n")
                        lines.append("**受入基準:**")
                        lines.append(f"- 正常に{feature['name']}ができる")
                        lines.append(f"- 適切なエラーハンドリングがされている\n")

        # 非機能要件
        if self.requirements_data.get('non_functional'):
            lines.append("## 非機能要件\n")

            nfr = self.requirements_data['non_functional']

            lines.append("### パフォーマンス")
            lines.append(f"- APIレスポンスタイム: 平均{nfr['response_time']}ms以内")
            lines.append("- データベースクエリの最適化\n")

            if nfr['security']:
                lines.append("### セキュリティ")
                lines.append("- SQLインジェクション対策（ORM使用）")
                lines.append("- XSS対策（適切なエスケープ）")
                lines.append("- 入力値のバリデーション\n")

            lines.append("### テスト")
            lines.append(f"- テストカバレッジ目標: {nfr['test_coverage']}%以上")
            lines.append("- ユニットテストと統合テストの実装\n")

        # ドキュメント要件
        lines.append("## ドキュメント要件\n")
        lines.append("- OpenAPI (Swagger) 自動生成")
        lines.append("- README.md（セットアップ手順）")
        lines.append("- API使用例\n")

        return '\n'.join(lines)
