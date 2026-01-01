"""求人テキストを構造化するパイプライン."""

from __future__ import annotations

import json

from pydantic import ValidationError

from src.schema import JobSpec
from src.utils.pii import mask_pii
from src.llm.prompts import STRUCTURE_PROMPT_TEMPLATE
from src.llm.client import call_claude


def structure_job(job_text: str) -> JobSpec:
    """求人テキストを構造化してJobSpecを返す.

    Args:
        job_text: 求人の生テキスト

    Returns:
        構造化されたJobSpec

    Raises:
        ValueError: 2回リトライしてもJSONパース/バリデーションに失敗した場合
    """
    # 1. PIIマスク
    masked_text = mask_pii(job_text)

    # 2. プロンプト組み立て
    prompt = STRUCTURE_PROMPT_TEMPLATE.format(job_text=masked_text)

    # 3. LLM呼び出し（最大2回リトライ）
    last_response = ""
    last_error: Exception | None = None

    for attempt in range(2):
        if attempt == 0:
            current_prompt = prompt
        else:
            # リトライ時は修正指示を追加
            current_prompt = (
                prompt
                + f"\n\n---\n前回の出力:\n{last_response}\n\n"
                "上記の出力はJSONとして壊れています。修正してJSONのみを出力してください。"
            )

        last_response = call_claude(current_prompt)

        # 4. JSONパース & バリデーション
        try:
            data = json.loads(last_response)
            return JobSpec(**data)
        except json.JSONDecodeError as e:
            last_error = e
            continue
        except ValidationError as e:
            last_error = e
            continue

    # 2回失敗した場合
    raise ValueError(f"JSONパース/バリデーションに失敗しました: {last_error}")

