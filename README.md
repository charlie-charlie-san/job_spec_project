# JobSpec Studio

案件票を構造化し、提案資料を自動生成するStreamlitアプリケーション。

## 機能

- **案件票の構造化**: 非構造化テキストをJSON形式に変換
- **社内要約生成**: 案件の概要をフォーマット化
- **提案メール生成**: 複数のテンプレート・トーン・角度に対応
- **ヒアリング質問生成**: 不足情報を自動抽出
- **履歴管理**: 過去の案件を保存・復元
- **類似案件サジェスト**: 技術スタックベースで類似案件を表示
- **リライト機能**: LLMで文章をブラッシュアップ

## セットアップ

```bash
# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
streamlit run streamlit_app.py
```

## 本番LLM連携

Claude APIを使用する場合:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
streamlit run streamlit_app.py
```

## プロジェクト構成

```
job_spec_project/
├── streamlit_app.py          # メインアプリ
├── src/
│   ├── schema.py             # Pydanticモデル (JobSpec)
│   ├── llm/
│   │   ├── client.py         # LLMクライアント (本番/モック)
│   │   └── prompts.py        # プロンプトテンプレート
│   ├── pipeline/
│   │   ├── structure.py      # 構造化パイプライン
│   │   └── generate.py       # テキスト生成
│   └── utils/
│       └── pii.py            # PIIマスキング
└── requirements.txt
```

## 技術スタック

- Python 3.11+
- Streamlit
- Pydantic
- Anthropic Claude API (オプション)

