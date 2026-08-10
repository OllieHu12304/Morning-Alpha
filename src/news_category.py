"""集中管理 Morning Alpha 的新聞分析分類規則。"""


CATEGORY_RULES = {
    "AI 與人工智慧": ["AI", "人工智慧", "ChatGPT", "Claude", "機器學習", "生成式"],
    "半導體": ["半導體", "晶片", "台積電", "聯電", "晶圓", "記憶體", "封裝"],
    "資訊安全": ["資安", "資訊安全", "駭客", "漏洞", "網路攻擊", "詐騙"],
    "財經": ["財報", "營收", "股價", "投資", "金融", "ETF", "利率"],
    "能源": ["能源", "電力", "電池", "太陽能", "風電", "儲能"],
    "交通科技": ["電動車", "汽車", "特斯拉", "Tesla", "無人機"],
    "太空與科學": ["太空", "NASA", "天文", "衛星", "宇宙", "黑洞", "科學"],
}


def infer_category(title):
    """使用標題關鍵字推論一個統一的分析分類。"""
    normalized_title = str(title).casefold()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword.casefold() in normalized_title:
                return category

    return "其他"
