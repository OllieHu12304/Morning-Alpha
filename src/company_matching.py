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
    pattern = create_ticker_pattern(ticker)
    return pattern.search(str(title)) is not None


def create_ticker_pattern(ticker):
    """預先編譯股票代號邊界規則，供多篇新聞重複使用。"""
    pattern = rf"(?<![0-9A-Za-z]){re.escape(str(ticker))}(?![0-9A-Za-z])"
    return re.compile(pattern, flags=re.IGNORECASE)


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


def prepare_candidate(candidate, ambiguous_aliases):
    """預先整理一家公司不會因新聞標題改變的比對資料。"""
    company_name = str(candidate.get("name") or "").strip()
    short_name = str(candidate.get("short_name") or "").strip()
    ticker = str(candidate.get("ticker") or "").strip()
    normalized_short_name = normalize_text(short_name)
    aliases = []

    for alias_value in candidate.get("aliases", []):
        alias = str(alias_value).strip()
        normalized_alias = normalize_text(alias)

        if (
            len(normalized_alias) < MIN_ALIAS_LENGTH
            or normalized_alias in ambiguous_aliases
        ):
            continue

        aliases.append({
            "text": alias,
            "normalized_text": normalized_alias,
            "confidence": get_alias_confidence(
                normalized_alias,
                is_official_short_name=(
                    normalized_alias == normalized_short_name
                ),
            ),
        })

    return {
        "candidate": candidate,
        "company_name": company_name,
        "normalized_name": normalize_text(company_name),
        "ticker": ticker,
        "normalized_ticker": normalize_text(ticker),
        "ticker_pattern": create_ticker_pattern(ticker) if ticker else None,
        "aliases": aliases,
    }


def build_matching_context(candidates):
    """建立可供多篇新聞共同使用的公司比對 context。"""
    if not isinstance(candidates, list):
        raise ValueError("candidates 必須是 list。")

    for candidate in candidates:
        if not isinstance(candidate, dict) or not candidate.get("company_id"):
            raise ValueError("公司候選資料格式不正確。")

    ambiguous_aliases = build_ambiguous_aliases(candidates)
    return [
        prepare_candidate(candidate, ambiguous_aliases)
        for candidate in candidates
    ]


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


def find_text_spans(text, search_text):
    """找出 search_text 在 text 中每一次出現的起訖位置。"""
    spans = []
    start = 0

    while True:
        match_start = text.find(search_text, start)

        if match_start == -1:
            break

        match_end = match_start + len(search_text)
        spans.append((match_start, match_end))
        start = match_start + 1

    return spans


def spans_overlap(first_span, second_span):
    """判斷兩段文字位置是否互相重疊。"""
    return (
        first_span[0] < second_span[1]
        and second_span[0] < first_span[1]
    )


def remove_overlapping_matches(normalized_title, matches):
    """同一段文字有多個命中時，優先保留較長的公司名稱。"""
    matches_with_spans = []

    for match in matches:
        normalized_matched_text = normalize_text(match["matched_text"])
        spans = find_text_spans(normalized_title, normalized_matched_text)
        matches_with_spans.append({
            "match": match,
            "text_length": len(normalized_matched_text),
            "spans": spans,
        })

    matches_with_spans.sort(
        key=lambda item: (
            -item["text_length"],
            -item["match"]["confidence"],
            item["match"]["company_id"],
        )
    )

    kept_matches = []
    claimed_spans = []

    for item in matches_with_spans:
        independent_spans = []

        for span in item["spans"]:
            overlaps_longer_match = any(
                claimed["text_length"] > item["text_length"]
                and spans_overlap(span, claimed["span"])
                for claimed in claimed_spans
            )

            if not overlaps_longer_match:
                independent_spans.append(span)

        if not independent_spans:
            continue

        kept_matches.append(item["match"])

        for span in independent_spans:
            claimed_spans.append({
                "span": span,
                "text_length": item["text_length"],
            })

    return kept_matches


def match_prepared_candidate(title, normalized_title, prepared_candidate):
    """使用預先整理的公司資料找出最佳 match。"""
    matches = []
    candidate = prepared_candidate["candidate"]
    company_name = prepared_candidate["company_name"]
    normalized_name = prepared_candidate["normalized_name"]

    if normalized_name and normalized_name in normalized_title:
        matches.append(create_match(
            candidate,
            company_name,
            "company_name",
            1.0,
        ))

    ticker = prepared_candidate["ticker"]
    ticker_pattern = prepared_candidate["ticker_pattern"]

    if (
        ticker_pattern is not None
        and prepared_candidate["normalized_ticker"] in normalized_title
        and ticker_pattern.search(title) is not None
    ):
        matches.append(create_match(
            candidate,
            ticker,
            "ticker",
            1.0,
        ))

    for alias in prepared_candidate["aliases"]:
        if alias["normalized_text"] not in normalized_title:
            continue

        matches.append(create_match(
            candidate,
            alias["text"],
            "alias",
            alias["confidence"],
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


def match_title_companies_with_context(title, matching_context):
    """使用同一份 context 比對一篇新聞標題。"""
    normalized_title = normalize_text(title)

    if not normalized_title:
        return []

    matches = []

    for prepared_candidate in matching_context:
        match = match_prepared_candidate(
            str(title),
            normalized_title,
            prepared_candidate,
        )

        if match is not None:
            matches.append(match)

    matches = remove_overlapping_matches(normalized_title, matches)

    return sorted(
        matches,
        key=lambda match: (-match["confidence"], match["company_id"]),
    )


def match_title_companies(title, candidates):
    """建立單次 context，回傳標題中的公司 matches。"""
    if not normalize_text(title):
        return []

    matching_context = build_matching_context(candidates)
    return match_title_companies_with_context(title, matching_context)


def match_news_records(records, candidates):
    """為新聞副本加入 company_matches，不改變原始 records。"""
    if not isinstance(records, list):
        raise ValueError("records 必須是 list。")

    matching_context = build_matching_context(candidates)
    matched_records = []

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("每一筆新聞資料都必須是 object。")

        matched_record = dict(record)
        matched_record["company_matches"] = match_title_companies_with_context(
            record.get("title", ""),
            matching_context,
        )
        matched_records.append(matched_record)

    return matched_records
