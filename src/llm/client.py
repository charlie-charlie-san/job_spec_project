"""LLMクライアント（本番/モック切替対応）."""

from __future__ import annotations

import json
import os


def _get_api_key() -> str | None:
    """APIキーを取得（環境変数 or Streamlit secrets）."""
    # 環境変数から取得
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    # Streamlit Cloudのsecretsから取得
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    return None


# モック用のサンプルレスポンス
_MOCK_RESPONSE = {
    "title": "【Python】データ基盤エンジニア",
    "company": "株式会社サンプルテック",
    "role": "バックエンドエンジニア",
    "summary": "データ基盤の設計・構築を担当。既存システムのリプレイスプロジェクトに参画いただきます。",
    "must_requirements": [
        "Python 3年以上",
        "SQLを用いたデータ処理経験",
        "AWSまたはGCPの実務経験",
    ],
    "nice_to_have": [
        "Airflow/Dagsterなどワークフローツールの経験",
        "Sparkの経験",
        "チームリード経験",
    ],
    "tasks": [
        "データパイプラインの設計・実装",
        "既存バッチ処理のリファクタリング",
        "データ品質モニタリングの構築",
    ],
    "stack_keywords": [
        "Python",
        "AWS",
        "Glue",
        "Athena",
        "Airflow",
        "Terraform",
    ],
    "location": "東京都渋谷区",
    "remote_type": "hybrid",
    "rate": {
        "min": 700000,
        "max": 900000,
        "unit": "monthly",
    },
    "start_date": "2024年2月〜",
    "duration": "長期（6ヶ月以上）",
    "interview_count": 2,
    "working_hours": "週5日、140-180h/月",
    "contract_type": "業務委託",
    "notes": "服装自由、フレックス制度あり",
    "risks_or_unknowns": [
        "具体的なチーム構成が不明",
        "リプレイス完了後の体制について要確認",
    ],
}


def is_api_available() -> bool:
    """Claude APIが利用可能かチェック."""
    return bool(_get_api_key())


def call_claude(prompt: str, max_tokens: int = 4096) -> str:
    """Claude APIを呼び出す（本番/モック自動切替）.

    Args:
        prompt: プロンプト文字列
        max_tokens: 最大トークン数

    Returns:
        レスポンス文字列
    """
    api_key = _get_api_key()

    if api_key:
        # 本番モード
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except ImportError:
            # anthropicライブラリがない場合はモックにフォールバック
            pass
        except Exception:
            # API エラー時もモックにフォールバック
            pass

    # モックモード
    return json.dumps(_MOCK_RESPONSE, ensure_ascii=False)


def rewrite_text(text: str, instruction: str) -> str:
    """テキストをLLMでリライトする.

    Args:
        text: 元のテキスト
        instruction: リライト指示（例: "より丁寧に", "簡潔に"）

    Returns:
        リライト後のテキスト
    """
    api_key = _get_api_key()

    if api_key:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)

            prompt = f"""以下のテキストを「{instruction}」という指示に従ってリライトしてください。
リライト後のテキストのみを出力してください。説明や前置きは不要です。

---
{text}
---

リライト後:"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception:
            pass

    # モックモード: 簡易的なリライト
    mock_rewrites = {
        "より丁寧に": f"【丁寧版】\n{text}",
        "簡潔に": text[:len(text) // 2] + "...(以下省略)",
        "熱意を込めて": f"ぜひご検討ください！\n\n{text}\n\n何卒よろしくお願いいたします！",
        "フォーマルに": f"拝啓\n\n{text}\n\n敬具",
    }

    for key, value in mock_rewrites.items():
        if key in instruction:
            return value

    return f"【{instruction}版】\n{text}"

