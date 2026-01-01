"""個人情報（PII）のマスキングユーティリティ."""

import re


# メールアドレス: user@example.com 形式
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

# 電話番号: 日本の一般的な形式に対応
# - 090-1234-5678, 090_1234_5678, 09012345678
# - 03-1234-5678, 0312345678
# - +81-90-1234-5678
PHONE_PATTERN = re.compile(
    r"(?:\+81[-\s]?)?"  # 国際番号（任意）
    r"0[0-9]{1,4}"      # 市外局番 or 携帯の先頭
    r"[-\s_]?"          # 区切り（任意）
    r"[0-9]{1,4}"       # 中間
    r"[-\s_]?"          # 区切り（任意）
    r"[0-9]{3,4}"       # 末尾
)


def mask_pii(text: str) -> str:
    """テキスト内の個人情報をマスクする.

    Args:
        text: 対象テキスト

    Returns:
        マスク済みテキスト（メール→[EMAIL], 電話→[PHONE]）
    """
    # メールアドレスをマスク
    text = EMAIL_PATTERN.sub("[EMAIL]", text)

    # 電話番号をマスク
    text = PHONE_PATTERN.sub("[PHONE]", text)

    return text

