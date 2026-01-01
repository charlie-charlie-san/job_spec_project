"""JobSpecからテキストを生成するパイプライン（テンプレートベース）."""

from __future__ import annotations

from src.schema import JobSpec


def _format_list(items: list[str], default: str = "要確認") -> str:
    """リストをカンマ区切り文字列に変換."""
    return "、".join(items) if items else default


def _format_value(value: str | int | None, default: str = "要確認") -> str:
    """値を文字列に変換（Noneは「要確認」）."""
    return str(value) if value is not None else default


def _format_rate(job: JobSpec) -> str:
    """報酬を文字列に変換."""
    if job.rate is None:
        return "要確認"

    unit_map = {
        "hourly": "時給",
        "daily": "日給",
        "monthly": "月額",
        "yearly": "年額",
    }
    unit_str = unit_map.get(job.rate.unit or "", "")

    if job.rate.min is not None and job.rate.max is not None:
        return f"{unit_str}{int(job.rate.min):,}〜{int(job.rate.max):,}円"
    elif job.rate.min is not None:
        return f"{unit_str}{int(job.rate.min):,}円〜"
    elif job.rate.max is not None:
        return f"{unit_str}〜{int(job.rate.max):,}円"
    else:
        return "要確認"


def _format_remote(remote_type: str | None) -> str:
    """リモートタイプを日本語に変換."""
    remote_map = {
        "full_remote": "フルリモート",
        "hybrid": "一部リモート",
        "on_site": "オンサイト",
    }
    return remote_map.get(remote_type or "", "要確認")


def generate_internal_summary(job: JobSpec) -> str:
    """社内共有用のサマリを生成する.

    Args:
        job: 構造化された求人情報

    Returns:
        社内向けサマリ文字列
    """
    lines = [
        f"【案件サマリ】{_format_value(job.title)}",
        "",
        f"■ 企業: {_format_value(job.company)}",
        f"■ ポジション: {_format_value(job.role)}",
        f"■ 概要: {_format_value(job.summary)}",
        "",
        f"■ 必須スキル: {_format_list(job.must_requirements)}",
        f"■ 歓迎スキル: {_format_list(job.nice_to_have)}",
        f"■ 業務内容: {_format_list(job.tasks)}",
        f"■ 技術スタック: {_format_list(job.stack_keywords)}",
        "",
        f"■ 勤務地: {_format_value(job.location)}",
        f"■ リモート: {_format_remote(job.remote_type)}",
        f"■ 報酬: {_format_rate(job)}",
        f"■ 開始時期: {_format_value(job.start_date)}",
        f"■ 期間: {_format_value(job.duration)}",
        f"■ 稼働: {_format_value(job.working_hours)}",
        f"■ 契約形態: {_format_value(job.contract_type)}",
        f"■ 面談回数: {_format_value(job.interview_count)}",
        "",
        f"■ 備考: {_format_value(job.notes)}",
        f"■ 不明点・リスク: {_format_list(job.risks_or_unknowns, '特になし')}",
    ]
    return "\n".join(lines)


def generate_sales_email(job: JobSpec, tone: str, angle: str) -> str:
    """営業メール文面を生成する.

    Args:
        job: 構造化された求人情報
        tone: トーン（例: "丁寧", "カジュアル", "ビジネス"）
        angle: 訴求軸（例: "技術成長", "報酬", "リモート"）

    Returns:
        営業メール文字列
    """
    # トーン別の挨拶
    greeting_map = {
        "丁寧": "お世話になっております。",
        "カジュアル": "こんにちは！",
        "ビジネス": "いつもお世話になっております。",
    }
    greeting = greeting_map.get(tone, "お世話になっております。")

    # 訴求軸別のアピールポイント
    if angle == "技術成長":
        appeal = f"技術スタックは{_format_list(job.stack_keywords)}を中心としており、スキルアップにつながる環境です。"
    elif angle == "報酬":
        appeal = f"報酬は{_format_rate(job)}となっており、ご経験に見合った待遇をご用意しております。"
    elif angle == "リモート":
        appeal = f"勤務形態は{_format_remote(job.remote_type)}で、柔軟な働き方が可能です。"
    else:
        appeal = "魅力的な案件となっております。"

    lines = [
        greeting,
        "",
        f"下記案件のご紹介です。",
        "",
        f"【{_format_value(job.title)}】",
        f"企業: {_format_value(job.company)}",
        f"ポジション: {_format_value(job.role)}",
        "",
        f"概要: {_format_value(job.summary)}",
        "",
        f"必須スキル: {_format_list(job.must_requirements)}",
        f"報酬: {_format_rate(job)}",
        f"勤務地: {_format_value(job.location)}（{_format_remote(job.remote_type)}）",
        f"開始: {_format_value(job.start_date)}",
        "",
        appeal,
        "",
        "ご興味がございましたら、詳細をお伝えいたします。",
        "ご検討のほど、よろしくお願いいたします。",
    ]
    return "\n".join(lines)


def generate_questions(job: JobSpec) -> list[str]:
    """確認すべき質問リストを生成する.

    Args:
        job: 構造化された求人情報

    Returns:
        質問リスト
    """
    questions: list[str] = []

    # 基本情報の不足チェック
    if not job.company:
        questions.append("企業名を教えていただけますか？")
    if not job.summary:
        questions.append("案件の概要・背景を教えていただけますか？")

    # 必須スキルが曖昧
    if not job.must_requirements:
        questions.append("必須スキル・経験年数の目安を教えていただけますか？")

    # 報酬関連
    if job.rate is None or (job.rate.min is None and job.rate.max is None):
        questions.append("報酬レンジ（単価）を教えていただけますか？")

    # 勤務形態
    if not job.location:
        questions.append("勤務地はどちらになりますか？")
    if not job.remote_type:
        questions.append("リモートワークは可能ですか？（フル/一部/不可）")
    if not job.working_hours:
        questions.append("想定稼働時間（週何日、月何時間）を教えていただけますか？")

    # 契約関連
    if not job.start_date:
        questions.append("参画開始時期はいつ頃を想定されていますか？")
    if not job.duration:
        questions.append("契約期間の目安を教えていただけますか？")
    if job.interview_count is None:
        questions.append("面談は何回を予定されていますか？")

    # risks_or_unknownsから質問生成
    for risk in job.risks_or_unknowns:
        questions.append(f"「{risk}」について詳細を教えていただけますか？")

    # 最低限の質問を保証
    if not questions:
        questions.append("現時点で特に不明点はありませんが、進める中で確認させてください。")

    return questions

