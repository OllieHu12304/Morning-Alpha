"""以可解釋規則辨識新聞標題中的公司與股票代號。"""

import re


MIN_ALIAS_LENGTH = 2


def normalize_text(value):
    """建立適合中文字串包含比對的文字。"""
    return "".join(str(value or "").casefold().split())


def get_alias_confidence(alias, is_official_short_name=False):
    """依別名長度提供保守且可說明的 confidence。"""
    if len(alias) >= 4 or (is_official_short_name and len(alias) >= 3):
        return 0.9

    return 0.75


def ticker_appears_in_title(title, ticker):
    """只匹配獨立股票代號，避免 2330 誤中 12330。"""
    pattern = rf"(?<![0-9A-Za-z]){re.escape(str(ticker))}(?![0-9A-Za-z])"
    return re.search(pattern, str(title), flags=re.IGNORECASE) is not None


def build_ambiguous_aliases(candidates):
    """找出同時屬於多家公司的別名。"""
    company_ids_by_alias = {}

    for candidate in candidates:
        company_id = candidate.get("company_id")

        for alias in candidate.get("aliases", []):
            normalized_alias = normalize_text(alias)

            if len(normalized_alias) < MIN_ALIAS_LENGTH:
                continue

            company_ids_by_alias.setdefault(normalized_alias, set()).add(
                company_id
            )

    return {
        alias
        for alias, company_ids in company_ids_by_alias.items()
        if len(company_ids) > 1
    }


def create_match(candidate, matched_text, match_method, confidence):
    """建立 Dashboard 與 database 可共同使用的 match record。"""
    return {
        "company_id": candidate["company_id"],
        "name": candidate["name"],
        "short_name": candidate.get("short_name"),
        "industry": candidate.get("industry"),
        "ticker": candidate.get("ticker"),
        "exchange": candidate.get("exchange"),
        "matched_text": matched_text,
        "match_method": match_method,
        "confidence": confidence,
    }


def match_candidate(title, normalized_title, candidate, ambiguous_aliases):
    """找出標題對一個公司候選的最佳 match。"""
    matches = []
    company_name = str(candidate.get("name") or "").strip()
    normalized_name = normalize_text(company_name)

    if normalized_name and normalized_name in normalized_title:
        matches.append(create_match(
            candidate,
            company_name,
            "company_name",
            1.0,
        ))

    ticker = str(candidate.get("ticker") or "").strip()

    if ticker and ticker_appears_in_title(title, ticker):
        matches.append(create_match(
            candidate,
            ticker,
            "ticker",
            1.0,
        ))

    for alias_value in candidate.get("aliases", []):
        alias = str(alias_value).strip()
        normalized_alias = normalize_text(alias)
        normalized_short_name = normalize_text(candidate.get("short_name"))

        if (
            len(normalized_alias) < MIN_ALIAS_LENGTH
            or normalized_alias in ambiguous_aliases
            or normalized_alias not in normalized_title
        ):
            continue

        matches.append(create_match(
            candidate,
            alias,
            "alias",
            get_alias_confidence(
                normalized_alias,
                is_official_short_name=(
                    normalized_alias == normalized_short_name
                ),
            ),
        ))

    if not matches:
        return None

    method_priority = {"company_name": 3, "ticker": 2, "alias": 1}
    return max(
        matches,
        key=lambda match: (
            match["confidence"],
            method_priority[match["match_method"]],
            len(match["matched_text"]),
        ),
    )


def match_title_companies(title, candidates):
    """回傳標題中所有可解釋且不模糊的公司 matches。"""
    if not isinstance(candidates, list):
        raise ValueError("candidates 必須是 list。")

    normalized_title = normalize_text(title)

    if not normalized_title:
        return []

    ambiguous_aliases = build_ambiguous_aliases(candidates)
    matches = []

    for candidate in candidates:
        if not isinstance(candidate, dict) or not candidate.get("company_id"):
            raise ValueError("公司候選資料格式不正確。")

        match = match_candidate(
            str(title),
            normalized_title,
            candidate,
            ambiguous_aliases,
        )

        if match is not None:
            matches.append(match)

    return sorted(
        matches,
        key=lambda match: (-match["confidence"], match["company_id"]),
    )


def match_news_records(records, candidates):
    """為新聞副本加入 company_matches，不改變原始 records。"""
    if not isinstance(records, list):
        raise ValueError("records 必須是 list。")

    matched_records = []

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("每一筆新聞資料都必須是 object。")

        matched_record = dict(record)
        matched_record["company_matches"] = match_title_companies(
            record.get("title", ""),
            candidates,
        )
        matched_records.append(matched_record)

    return matched_records
