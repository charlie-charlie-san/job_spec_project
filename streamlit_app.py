"""案件構造化 & 提案文生成 Streamlit アプリ."""

from __future__ import annotations

import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()  # .envファイルを読み込み

import streamlit as st

from src.schema import JobSpec
from src.pipeline.structure import structure_job
from src.pipeline.generate import (
    generate_internal_summary,
    generate_sales_email,
    generate_questions,
)
from src.llm.client import is_api_available, rewrite_text

# サンプル案件票テキスト
SAMPLE_JOB_TEXT = """\
【案件名】Pythonバックエンドエンジニア（データ基盤）
【企業】株式会社テックイノベーション
【単価】70〜90万円/月
【勤務地】東京都渋谷区（週2出社、それ以外リモート可）
【開始】2024年2月〜
【期間】長期（6ヶ月以上想定）
【面談】2回（1次:現場、2次:部長）
【稼働】週5日、140-180h/月
【契約】業務委託

【概要】
自社SaaSプロダクトのデータ基盤刷新プロジェクト。
既存のバッチ処理をモダンなデータパイプラインに移行。

【必須スキル】
・Python 3年以上
・SQL（複雑なクエリ経験）
・AWS or GCP の実務経験

【歓迎スキル】
・Airflow/Dagster等のワークフローツール
・Sparkでの大規模データ処理
・Terraformでのインフラ構築

【業務内容】
・データパイプラインの設計・実装
・既存バッチのリファクタリング
・データ品質モニタリング構築

【備考】
服装自由、フレックス制度あり
"""

# メールテンプレート種別
EMAIL_TEMPLATES = {
    "初回提案": {
        "prefix": "",
        "suffix": "\n\nご興味がございましたら、詳細をお伝えいたします。\nご検討のほど、よろしくお願いいたします。",
    },
    "フォローアップ": {
        "prefix": "先日ご案内した案件について、改めてご連絡いたします。\n\n",
        "suffix": "\n\nご状況いかがでしょうか。\nご不明点等ございましたら、お気軽にお申し付けください。",
    },
    "リマインド": {
        "prefix": "お忙しいところ恐れ入ります。\n先日の案件について、リマインドのご連絡です。\n\n",
        "suffix": "\n\n本案件は他候補者との調整も進んでおります。\nご興味がございましたら、お早めにご連絡いただけますと幸いです。",
    },
    "再提案": {
        "prefix": "以前ご案内した案件について、条件が更新されましたのでご連絡いたします。\n\n",
        "suffix": "\n\n前回よりも条件が改善されております。\n改めてご検討いただけますと幸いです。",
    },
}

# リライトオプション
REWRITE_OPTIONS = [
    "より丁寧に",
    "簡潔に",
    "熱意を込めて",
    "フォーマルに",
    "カジュアルに",
    "具体的に",
]

# ページ設定
st.set_page_config(
    page_title="JobSpec Studio",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --navy-900: #0f172a;
        --navy-800: #1e293b;
        --navy-700: #334155;
        --navy-600: #475569;
        --navy-100: #f1f5f9;
        --orange-500: #f97316;
        --orange-600: #ea580c;
        --orange-100: #fff7ed;
        --white: #ffffff;
        --gray-50: #fafafa;
        --gray-100: #f4f4f5;
        --gray-200: #e4e4e7;
        --gray-400: #a1a1aa;
        --gray-600: #52525b;
        --green-500: #22c55e;
    }

    .stApp {
        background: linear-gradient(180deg, var(--gray-50) 0%, var(--white) 100%);
        font-family: 'Noto Sans JP', sans-serif;
    }

    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* サイドバー */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background: var(--navy-900) !important;
        background-color: var(--navy-900) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--white) !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: var(--white) !important;
    }

    /* サイドバーボタン - 視認性改善（通常状態） */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] button {
        background: var(--navy-700) !important;
        background-color: var(--navy-700) !important;
        color: var(--white) !important;
        border: 2px solid var(--orange-500) !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] button *,
    [data-testid="stSidebar"] .stButton button *,
    [data-testid="stSidebar"] .stButton > button *,
    section[data-testid="stSidebar"] button * {
        color: var(--white) !important;
        background: transparent !important;
    }

    /* サイドバーボタン - ホバー状態 */
    [data-testid="stSidebar"] button:hover,
    [data-testid="stSidebar"] .stButton button:hover,
    [data-testid="stSidebar"] .stButton > button:hover,
    section[data-testid="stSidebar"] button:hover {
        background: var(--orange-500) !important;
        background-color: var(--orange-500) !important;
        border-color: var(--orange-600) !important;
        color: var(--white) !important;
    }

    [data-testid="stSidebar"] button:hover *,
    section[data-testid="stSidebar"] button:hover * {
        color: var(--white) !important;
    }

    .history-item {
        background: var(--navy-800);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }

    .history-item:hover {
        background: var(--navy-700);
        border-color: var(--orange-500);
    }

    .history-item-title {
        font-weight: 500;
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .history-item-meta {
        font-size: 0.7rem;
        color: var(--gray-400) !important;
    }

    /* 類似案件カード */
    .similar-job {
        background: var(--navy-800);
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
        border-left: 3px solid var(--orange-500);
    }

    .similar-job-title {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--white) !important;
        margin-bottom: 0.2rem;
    }

    .similar-job-match {
        font-size: 0.7rem;
        color: var(--orange-500) !important;
    }

    /* APIステータスバッジ */
    .api-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
    }

    .api-badge.live {
        background: rgba(34, 197, 94, 0.2);
        color: var(--green-500) !important;
        border: 1px solid var(--green-500);
    }

    .api-badge.mock {
        background: rgba(249, 115, 22, 0.2);
        color: var(--orange-500) !important;
        border: 1px solid var(--orange-500);
    }

    h1 {
        color: var(--navy-900) !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        letter-spacing: -0.025em !important;
        border-bottom: 3px solid var(--orange-500);
        padding-bottom: 0.75rem !important;
        margin-bottom: 2rem !important;
    }

    .stSubheader, h2, h3 {
        color: var(--navy-800) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 1rem !important;
    }

    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background: var(--white);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        border: 1px solid var(--gray-200);
    }

    .stTextArea textarea {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-size: 0.9rem !important;
        color: var(--navy-900) !important;
        border: 2px solid var(--gray-200) !important;
        border-radius: 8px !important;
        background: var(--white) !important;
        transition: all 0.2s ease;
    }

    .stTextArea textarea:focus {
        border-color: var(--navy-700) !important;
        box-shadow: 0 0 0 3px rgba(30, 41, 59, 0.1) !important;
        color: var(--navy-900) !important;
    }

    .stTextArea textarea::placeholder {
        color: var(--gray-400) !important;
    }

    .stSelectbox > div > div {
        border: 2px solid var(--gray-200) !important;
        border-radius: 8px !important;
        background: var(--white) !important;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--navy-600) !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        color: var(--navy-900) !important;
    }

    .stSelectbox [data-baseweb="select"] span {
        color: var(--navy-900) !important;
    }

    .stSelectbox label {
        color: var(--navy-700) !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-baseweb="popover"] {
        background: var(--white) !important;
    }

    [data-baseweb="menu"] {
        background: var(--white) !important;
    }

    [data-baseweb="menu"] li {
        color: var(--navy-900) !important;
        background: var(--white) !important;
    }

    [data-baseweb="menu"] li:hover {
        background: var(--gray-100) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--orange-500) 0%, var(--orange-600) 100%) !important;
        color: var(--white) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(249, 115, 22, 0.25) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(249, 115, 22, 0.35) !important;
    }

    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    .stButton > button[kind="secondary"] {
        background: var(--white) !important;
        color: var(--navy-700) !important;
        border: 2px solid var(--gray-200) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: var(--navy-600) !important;
        color: var(--navy-900) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--gray-100);
        border-radius: 10px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: var(--navy-600) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        border: none !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: var(--white) !important;
        color: var(--navy-800) !important;
    }

    .stTabs [aria-selected="true"] {
        background: var(--white) !important;
        color: var(--navy-900) !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.1) !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    .stCode, code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
        border-radius: 8px !important;
    }

    pre {
        background: var(--navy-900) !important;
        border-radius: 8px !important;
        border: none !important;
    }

    .stAlert {
        border-radius: 8px !important;
        border: none !important;
    }

    [data-testid="stAlert"][data-baseweb="notification"] {
        background: var(--navy-100) !important;
        color: var(--navy-800) !important;
    }

    .stException, [data-testid="stAlert"]:has([data-testid="stErrorApiIcon"]) {
        background: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
    }

    hr {
        border-color: var(--gray-200) !important;
        margin: 1.5rem 0 !important;
    }

    .stSpinner > div {
        border-top-color: var(--orange-500) !important;
    }

    .stTextArea label, .stTextInput label {
        color: var(--navy-700) !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stMarkdown p {
        color: var(--navy-800);
        line-height: 1.7;
    }

    .stMarkdown strong {
        color: var(--navy-900);
        font-weight: 600;
    }

    [data-testid="column"]:first-child {
        border-right: 1px solid var(--gray-200);
        padding-right: 2rem !important;
    }

    [data-testid="column"]:last-child {
        padding-left: 2rem !important;
    }

    .copy-btn {
        background: var(--gray-100);
        border: 1px solid var(--gray-200);
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        font-size: 0.75rem;
        color: var(--navy-700);
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
    }

    .copy-btn:hover {
        background: var(--navy-100);
        border-color: var(--navy-600);
    }

    .copy-btn.copied {
        background: #dcfce7;
        border-color: #22c55e;
        color: #16a34a;
    }

    .char-count {
        font-size: 0.75rem;
        color: var(--gray-400);
        text-align: right;
        margin-top: 0.25rem;
    }

    .stDownloadButton > button {
        background: var(--white) !important;
        color: var(--navy-700) !important;
        border: 1px solid var(--gray-200) !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        padding: 0.4rem 0.8rem !important;
    }

    .stDownloadButton > button:hover {
        border-color: var(--navy-600) !important;
        color: var(--navy-900) !important;
    }
</style>
""", unsafe_allow_html=True)


def copy_button(text: str, button_id: str, label: str = "コピー") -> None:
    """クリップボードにコピーするボタンを表示."""
    escaped_text = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    st.markdown(
        f"""
        <button class="copy-btn" id="{button_id}" onclick="
            navigator.clipboard.writeText(`{escaped_text}`).then(() => {{
                const btn = document.getElementById('{button_id}');
                btn.innerHTML = '✓ コピー済み';
                btn.classList.add('copied');
                setTimeout(() => {{
                    btn.innerHTML = '📋 {label}';
                    btn.classList.remove('copied');
                }}, 2000);
            }});
        ">📋 {label}</button>
        """,
        unsafe_allow_html=True,
    )


def add_to_history(title: str, job: JobSpec, summary: str, email: str, questions: list[str]) -> None:
    """履歴に追加."""
    if "history" not in st.session_state:
        st.session_state["history"] = []

    entry = {
        "id": len(st.session_state["history"]),
        "title": title or "無題の案件",
        "timestamp": datetime.now().strftime("%H:%M"),
        "job": job,
        "summary": summary,
        "email": email,
        "questions": questions,
    }
    st.session_state["history"].insert(0, entry)

    if len(st.session_state["history"]) > 10:
        st.session_state["history"] = st.session_state["history"][:10]


def generate_export_markdown(job: JobSpec, summary: str, email: str, questions: list[str]) -> str:
    """Markdownエクスポート用テキストを生成."""
    questions_md = "\n".join(f"- {q}" for q in questions)
    job_json = json.dumps(job.model_dump(), ensure_ascii=False, indent=2)

    return f"""# 案件レポート: {job.title or "無題"}

生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 社内要約

{summary}

---

## 提案メール

{email}

---

## ヒアリング質問

{questions_md}

---

## 構造化データ (JSON)

```json
{job_json}
```
"""


def calculate_similarity(job1: JobSpec, job2: JobSpec) -> tuple[float, list[str]]:
    """2つの案件の類似度を計算.

    Returns:
        (類似度スコア 0-1, 共通キーワードリスト)
    """
    keywords1 = set(kw.lower() for kw in job1.stack_keywords)
    keywords2 = set(kw.lower() for kw in job2.stack_keywords)

    if not keywords1 or not keywords2:
        return 0.0, []

    common = keywords1 & keywords2
    union = keywords1 | keywords2

    score = len(common) / len(union) if union else 0.0
    return score, list(common)


def find_similar_jobs(current_job: JobSpec, history: list[dict], top_n: int = 3) -> list[dict]:
    """履歴から類似案件を検索."""
    results = []

    for entry in history:
        hist_job = entry["job"]
        if hist_job == current_job:
            continue

        score, common_keywords = calculate_similarity(current_job, hist_job)
        if score > 0:
            results.append({
                "entry": entry,
                "score": score,
                "common_keywords": common_keywords,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# セッション初期化
if "job_text_input" not in st.session_state:
    st.session_state["job_text_input"] = ""
if "history" not in st.session_state:
    st.session_state["history"] = []

# --- サイドバー ---
with st.sidebar:
    # APIステータス表示
    if is_api_available():
        st.markdown(
            '<div class="api-badge live">● Claude API 接続中</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="api-badge mock">○ モックモード</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

    # 類似案件サジェスト
    if "job" in st.session_state and st.session_state["history"]:
        similar_jobs = find_similar_jobs(
            st.session_state["job"],
            st.session_state["history"],
        )

        if similar_jobs:
            st.markdown("### 🔗 類似案件")
            for item in similar_jobs:
                entry = item["entry"]
                score = item["score"]
                common = item["common_keywords"]

                st.markdown(
                    f'<div class="similar-job">'
                    f'<div class="similar-job-title">{entry["title"][:25]}{"..." if len(entry["title"]) > 25 else ""}</div>'
                    f'<div class="similar-job-match">一致率 {score:.0%} ({", ".join(common[:3])})</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if st.button(f"📄 読み込む", key=f"similar_{entry['id']}", use_container_width=True):
                    st.session_state["job"] = entry["job"]
                    st.session_state["summary"] = entry["summary"]
                    st.session_state["email"] = entry["email"]
                    st.session_state["questions"] = entry["questions"]
                    st.rerun()

            st.divider()

    # 履歴
    st.markdown("### 📚 履歴")

    if st.session_state["history"]:
        for entry in st.session_state["history"]:
            if st.button(
                f"📄 {entry['title'][:20]}{'...' if len(entry['title']) > 20 else ''}",
                key=f"history_{entry['id']}",
                use_container_width=True,
            ):
                st.session_state["job"] = entry["job"]
                st.session_state["summary"] = entry["summary"]
                st.session_state["email"] = entry["email"]
                st.session_state["questions"] = entry["questions"]
                st.rerun()

            st.markdown(
                f'<div style="font-size: 0.7rem; color: #94a3b8; margin-top: -0.5rem; margin-bottom: 0.5rem;">'
                f'{entry["timestamp"]}</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        if st.button("🗑️ 履歴をクリア", use_container_width=True):
            st.session_state["history"] = []
            st.rerun()
    else:
        st.markdown(
            '<p style="font-size: 0.85rem; color: #94a3b8;">まだ履歴がありません</p>',
            unsafe_allow_html=True,
        )

# ヘッダー
st.markdown("# ◆ JobSpec Studio")
st.markdown(
    '<p style="color: #64748b; margin-top: -1rem; margin-bottom: 2rem; font-size: 0.9rem;">'
    '案件票を構造化し、提案資料を自動生成します'
    '</p>',
    unsafe_allow_html=True,
)

# --- 左右レイアウト ---
left_col, right_col = st.columns([1, 1.4], gap="large")

# --- 左カラム: 入力 ---
with left_col:
    st.markdown("##### INPUT")

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.button("📝 サンプル", type="secondary", use_container_width=True):
            st.session_state["job_text_input"] = SAMPLE_JOB_TEXT
            st.rerun()
    with btn_col2:
        if st.button("🗑️ クリア", type="secondary", use_container_width=True):
            st.session_state["job_text_input"] = ""
            for key in ["job", "summary", "email", "questions"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)

    job_text = st.text_area(
        "案件票テキスト",
        value=st.session_state["job_text_input"],
        height=240,
        placeholder="案件票の内容をペーストしてください...\n\n「サンプル」ボタンで例を表示できます",
        label_visibility="collapsed",
        key="job_text_area",
    )

    st.session_state["job_text_input"] = job_text

    char_count = len(job_text)
    st.markdown(
        f'<div class="char-count">{char_count:,} 文字</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        angle = st.selectbox(
            "提案角度",
            options=["採用穴埋め", "短期伴走", "まずは要件整理"],
            index=0,
        )
    with col2:
        tone = st.selectbox(
            "トーン",
            options=["丁寧", "端的"],
            index=0,
        )
    with col3:
        email_template = st.selectbox(
            "メール種別",
            options=list(EMAIL_TEMPLATES.keys()),
            index=0,
        )

    st.markdown('<div style="height: 0.75rem"></div>', unsafe_allow_html=True)

    generate_btn = st.button(
        "Generate →",
        type="primary",
        use_container_width=True,
    )

# --- 右カラム: 出力 ---
with right_col:
    st.markdown("##### OUTPUT")

    if generate_btn:
        if not job_text.strip():
            st.error("案件票テキストを入力してください。")
        else:
            try:
                with st.spinner("構造化中..."):
                    job: JobSpec = structure_job(job_text)
                    summary = generate_internal_summary(job)
                    base_email = generate_sales_email(job, tone=tone, angle=angle)

                    tmpl = EMAIL_TEMPLATES[email_template]
                    email = tmpl["prefix"] + base_email + tmpl["suffix"]

                    questions = generate_questions(job)

                st.session_state["job"] = job
                st.session_state["summary"] = summary
                st.session_state["email"] = email
                st.session_state["questions"] = questions

                add_to_history(job.title or "無題", job, summary, email, questions)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    # 結果表示
    if "job" in st.session_state:
        export_md = generate_export_markdown(
            st.session_state["job"],
            st.session_state["summary"],
            st.session_state["email"],
            st.session_state["questions"],
        )

        dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 2])
        with dl_col1:
            st.download_button(
                "📥 Markdown",
                data=export_md,
                file_name=f"jobspec_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )
        with dl_col2:
            st.download_button(
                "📥 Text",
                data=export_md.replace("```json\n", "").replace("\n```", ""),
                file_name=f"jobspec_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
            )

        tab1, tab2, tab3, tab4 = st.tabs([
            "JSON",
            "社内要約",
            "提案メール",
            "質問リスト",
        ])

        with tab1:
            job_dict = st.session_state["job"].model_dump()
            json_str = json.dumps(job_dict, ensure_ascii=False, indent=2)

            copy_button(json_str, "copy_json", "JSONをコピー")
            st.code(json_str, language="json")

        with tab2:
            summary_text = st.session_state["summary"]
            copy_button(summary_text, "copy_summary", "要約をコピー")
            st.text_area(
                "summary",
                value=summary_text,
                height=320,
                label_visibility="collapsed",
                key="summary_area",
            )

        with tab3:
            email_text = st.session_state["email"]

            # コピー & リライトボタン
            btn_row = st.columns([1, 1, 2])
            with btn_row[0]:
                copy_button(email_text, "copy_email", "メールをコピー")
            with btn_row[1]:
                rewrite_style = st.selectbox(
                    "リライト",
                    options=["選択..."] + REWRITE_OPTIONS,
                    key="rewrite_select",
                    label_visibility="collapsed",
                )

            # リライト実行
            if rewrite_style != "選択...":
                with st.spinner(f"「{rewrite_style}」でリライト中..."):
                    rewritten = rewrite_text(email_text, rewrite_style)
                    st.session_state["email"] = rewritten
                    st.rerun()

            st.text_area(
                "email",
                value=st.session_state["email"],
                height=300,
                label_visibility="collapsed",
                key="email_area",
            )

        with tab4:
            questions = st.session_state["questions"]
            questions_text = "\n".join(f"・{q}" for q in questions)

            copy_button(questions_text, "copy_questions", "質問をコピー")

            st.markdown("**確認事項**")
            for i, q in enumerate(questions, 1):
                st.markdown(
                    f'<div style="padding: 0.5rem 0; border-bottom: 1px solid #e4e4e7;">'
                    f'<span style="color: #f97316; font-weight: 600;">{i}.</span> {q}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    else:
        st.markdown(
            '<div style="display: flex; align-items: center; justify-content: center; '
            'height: 300px; color: #94a3b8; font-size: 0.9rem;">'
            '← 案件票を入力して Generate をクリック'
            '</div>',
            unsafe_allow_html=True,
        )
