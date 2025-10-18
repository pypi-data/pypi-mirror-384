"""
Dependency Validator - 依存関係の検証と修正

循環依存の検出、分析、修正提案を行うモジュール
"""
from typing import List, Set, Tuple, Optional, Dict
import networkx as nx
import re

from cmw.models import Task


class DependencyValidator:
    """タスク依存関係の検証と修正を行うクラス"""

    def detect_cycles(self, tasks: List[Task]) -> List[List[str]]:
        """
        循環依存を検出

        Args:
            tasks: タスクリスト

        Returns:
            循環依存のリスト（各要素はタスクIDのリスト）
            例: [['TASK-004', 'TASK-005'], ['TASK-024', 'TASK-025']]
        """
        G = self._build_dependency_graph(tasks)

        try:
            # NetworkXのsimple_cyclesでサイクル検出
            cycles = list(nx.simple_cycles(G))
            return cycles
        except Exception:
            return []

    def _build_dependency_graph(self, tasks: List[Task]) -> nx.DiGraph:
        """
        依存関係グラフを構築

        Args:
            tasks: タスクリスト

        Returns:
            有向グラフ（タスクID → 依存先タスクID）
        """
        G = nx.DiGraph()

        for task in tasks:
            G.add_node(task.id)
            for dep_id in task.dependencies:
                # エッジの向き: task → dep_id（taskはdep_idに依存）
                G.add_edge(task.id, dep_id)

        return G

    def suggest_fixes(
        self, cycles: List[List[str]], tasks: List[Task]
    ) -> List[Dict]:
        """
        循環依存の修正案を提案

        Args:
            cycles: 検出された循環依存
            tasks: タスクリスト

        Returns:
            修正案のリスト
            [
                {
                    'cycle': ['TASK-004', 'TASK-005'],
                    'suggestions': [
                        {
                            'action': 'remove_dependency',
                            'from_task': 'TASK-004',
                            'to_task': 'TASK-005',
                            'reason': 'モデル定義はDB初期化の前に必要',
                            'confidence': 0.9
                        }
                    ]
                }
            ]
        """
        suggestions = []

        for cycle in cycles:
            cycle_suggestions = self._analyze_cycle(cycle, tasks)
            suggestions.append({"cycle": cycle, "suggestions": cycle_suggestions})

        return suggestions

    def _analyze_cycle(
        self, cycle: List[str], tasks: List[Task]
    ) -> List[Dict]:
        """
        循環依存を分析して修正案を生成

        Args:
            cycle: 循環依存を構成するタスクIDリスト
            tasks: 全タスクリスト

        Returns:
            修正提案のリスト（信頼度順にソート）
        """
        suggestions = []
        task_map = {t.id: t for t in tasks}

        # サイクル内の各エッジを評価
        for i in range(len(cycle)):
            from_id = cycle[i]
            to_id = cycle[(i + 1) % len(cycle)]

            from_task = task_map.get(from_id)
            to_task = task_map.get(to_id)

            if not from_task or not to_task:
                continue

            # セマンティック分析で削除すべきエッジを判定
            reason = self._should_remove_edge(from_task, to_task)

            if reason:
                confidence = self._calculate_confidence(from_task, to_task)
                suggestions.append(
                    {
                        "action": "remove_dependency",
                        "from_task": from_id,
                        "to_task": to_id,
                        "reason": reason,
                        "confidence": confidence,
                    }
                )

        # 信頼度順にソート（高い順）
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions

    def _should_remove_edge(
        self, from_task: Task, to_task: Task
    ) -> Optional[str]:
        """
        エッジを削除すべきかセマンティック分析で判定

        Args:
            from_task: 依存元タスク
            to_task: 依存先タスク

        Returns:
            削除すべき理由（削除不要ならNone）
        """
        # パターン1: 定義 → 初期化 の逆依存
        if any(
            kw in from_task.title for kw in ["定義", "モデル", "スキーマ"]
        ) and any(
            kw in to_task.title for kw in ["初期化", "セットアップ", "設定"]
        ):
            return f"{from_task.title}は{to_task.title}の前に必要"

        # パターン2: 実装 → 実装ガイドライン の依存
        if any(
            kw in to_task.title
            for kw in ["技術スタック", "推奨", "非機能要件", "制約"]
        ):
            return f"{to_task.title}は実装タスクではなくガイドライン"

        # パターン3: 番号が小さい方が先行すべき
        from_num = self._extract_section_number(from_task.title)
        to_num = self._extract_section_number(to_task.title)

        if (
            from_num is not None
            and to_num is not None
            and from_num < to_num
        ):
            return f"セクション順序: {from_num} は {to_num} より前"

        # パターン4: 基盤 → アプリケーション の逆依存
        foundation_keywords = ["データベース", "認証", "設定", "基盤"]
        app_keywords = ["エンドポイント", "API", "画面", "機能"]

        if any(
            kw in from_task.title for kw in foundation_keywords
        ) and any(kw in to_task.title for kw in app_keywords):
            return f"基盤({from_task.title})はアプリケーション層の前に必要"

        return None

    def _extract_section_number(self, title: str) -> Optional[float]:
        """
        タイトルからセクション番号を抽出

        Args:
            title: タスクタイトル

        Returns:
            セクション番号（例: "2.1 モデル定義" → 2.1）
        """
        match = re.match(r"^(\d+)\.(\d+)", title)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
        return None

    def _calculate_confidence(
        self, from_task: Task, to_task: Task
    ) -> float:
        """
        修正提案の信頼度を計算

        Args:
            from_task: 依存元タスク
            to_task: 依存先タスク

        Returns:
            信頼度（0.0-1.0）
        """
        confidence = 0.5

        # セマンティックマッチがある場合は高信頼度
        reason = self._should_remove_edge(from_task, to_task)
        if reason:
            if any(
                kw in reason
                for kw in ["定義", "初期化", "基盤", "ガイドライン"]
            ):
                confidence += 0.3  # 明確なパターン

        # セクション番号の整合性
        from_num = self._extract_section_number(from_task.title)
        to_num = self._extract_section_number(to_task.title)
        if (
            from_num is not None
            and to_num is not None
            and from_num < to_num
        ):
            confidence += 0.2  # 番号順序の確信

        return min(confidence, 1.0)

    def auto_fix_cycles(
        self,
        tasks: List[Task],
        cycles: List[List[str]],
        auto_apply: bool = True,
    ) -> List[Task]:
        """
        循環依存を自動修正

        Args:
            tasks: タスクリスト
            cycles: 検出された循環依存
            auto_apply: Trueの場合は自動適用、Falseの場合は高信頼度のみ

        Returns:
            修正後のタスクリスト
        """
        suggestions = self.suggest_fixes(cycles, tasks)
        task_map = {t.id: t for t in tasks}
        modifications = []

        for suggestion in suggestions:
            cycle = suggestion["cycle"]
            fixes = suggestion["suggestions"]

            if not fixes:
                continue

            # 最も信頼度の高い修正を適用
            best_fix = fixes[0]

            # 信頼度が低い場合はスキップ
            if not auto_apply and best_fix["confidence"] < 0.7:
                continue

            # 依存関係を削除
            from_task = task_map.get(best_fix["from_task"])
            to_task_id = best_fix["to_task"]

            if from_task and to_task_id in from_task.dependencies:
                from_task.dependencies.remove(to_task_id)
                modifications.append(
                    {
                        "from": best_fix["from_task"],
                        "to": to_task_id,
                        "reason": best_fix["reason"],
                        "confidence": best_fix["confidence"],
                    }
                )

        # 修正内容を表示
        if modifications:
            print("\n✅ 以下の依存関係を削除しました:")
            for mod in modifications:
                print(
                    f"  - {mod['from']} → {mod['to']} "
                    f"(信頼度: {mod['confidence']:.0%})"
                )
                print(f"    理由: {mod['reason']}")

        return list(task_map.values())

    def validate_dependencies(self, tasks: List[Task]) -> Dict:
        """
        依存関係全体を検証

        Args:
            tasks: タスクリスト

        Returns:
            検証結果の辞書
            {
                'has_cycles': bool,
                'cycles': List[List[str]],
                'missing_dependencies': List[str],
                'invalid_dependencies': List[str]
            }
        """
        task_ids = {t.id for t in tasks}
        result = {
            "has_cycles": False,
            "cycles": [],
            "missing_dependencies": [],
            "invalid_dependencies": [],
        }

        # 循環依存チェック
        cycles = self.detect_cycles(tasks)
        if cycles:
            result["has_cycles"] = True
            result["cycles"] = cycles

        # 存在しない依存先チェック
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    result["missing_dependencies"].append(
                        f"{task.id} → {dep_id} (存在しないタスク)"
                    )

        # 自己依存チェック
        for task in tasks:
            if task.id in task.dependencies:
                result["invalid_dependencies"].append(
                    f"{task.id} → {task.id} (自己依存)"
                )

        return result
