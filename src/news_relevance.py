"""集中管理已確認不符合 Morning Alpha 目標的新聞規則。"""


CNA_EXCLUDED_TITLE_TERMS = [
    "今彩539",
    "威力彩",
    "大樂透",
    "雙贏彩",
    "3星彩",
    "4星彩",
    "39樂合彩",
    "彩券",
    "樂透",
]


def is_relevant_news(source, title):
    """判斷新聞是否應進入分析；目前只排除中央社彩券內容。"""
    if source != "cna":
        return True

    cleaned_title = str(title or "").strip()

    if not cleaned_title:
        return False

    return not any(
        term in cleaned_title
        for term in CNA_EXCLUDED_TITLE_TERMS
    )
