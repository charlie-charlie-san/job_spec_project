"""LLM用プロンプトテンプレート."""

STRUCTURE_PROMPT_TEMPLATE = """\
あなたは求人情報を構造化するエキスパートです。
以下の求人テキストを解析し、指定されたJSON形式で出力してください。

## 入力テキスト
{job_text}

## 出力ルール（厳守）
1. JSONのみを出力すること（説明文・マークダウン記法は禁止）
2. 指定されたキー以外は絶対に追加しないこと
3. 情報が不明・欠損の場合は文字列型はnull、配列型は[]とすること
4. 値は日本語で埋めること（固有名詞・技術用語は原文のまま可）
5. enumフィールドは指定された値のみ使用すること
   - remote_type: "full_remote" | "hybrid" | "on_site" | null
   - rate.unit: "hourly" | "daily" | "monthly" | "yearly" | null

## JSON雛形（キー順序を維持すること）
{{
  "title": "案件タイトル",
  "company": "企業名",
  "role": "ポジション・役割",
  "summary": "案件概要（1〜3文）",
  "must_requirements": ["必須スキル1", "必須スキル2"],
  "nice_to_have": ["歓迎スキル1", "歓迎スキル2"],
  "tasks": ["業務内容1", "業務内容2"],
  "stack_keywords": ["技術キーワード1", "技術キーワード2"],
  "location": "勤務地",
  "remote_type": "full_remote",
  "rate": {{
    "min": 600000,
    "max": 800000,
    "unit": "monthly"
  }},
  "start_date": "開始時期（例: 2024年2月〜、即日可）",
  "duration": "期間（例: 3ヶ月〜、長期）",
  "interview_count": 2,
  "working_hours": "稼働時間（例: 週5日、140-180h/月）",
  "contract_type": "契約形態（例: 業務委託、派遣）",
  "notes": "備考・特記事項",
  "risks_or_unknowns": ["不明点1", "懸念点1"]
}}

## 出力
"""

