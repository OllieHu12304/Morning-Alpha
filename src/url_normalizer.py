"""將新聞 URL 轉成適合比較重複文章的標準格式。"""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETER_NAMES = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def is_tracking_parameter(name):
    """判斷 query parameter 是否只用於追蹤。"""
    normalized_name = name.casefold()
    return (
        normalized_name.startswith("utm_")
        or normalized_name in TRACKING_PARAMETER_NAMES
    )


def get_parameter_sort_key(parameter):
    """提供 query parameters 穩定且不分大小寫的排序依據。"""
    name, value = parameter
    return name.casefold(), value


def normalize_url(url):
    """保守地正規化 HTTP／HTTPS URL，不移除未知參數。"""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("新聞 URL 必須是非空白文字。")

    parsed_url = urlsplit(url.strip())
    scheme = parsed_url.scheme.casefold()

    if scheme not in {"http", "https"}:
        raise ValueError("新聞 URL 只支援 http 或 https。")

    hostname = parsed_url.hostname

    if not hostname:
        raise ValueError("新聞 URL 缺少 hostname。")

    hostname = hostname.casefold()

    if hostname.startswith("www."):
        hostname = hostname.removeprefix("www.")

    try:
        port = parsed_url.port
    except ValueError as error:
        raise ValueError("新聞 URL 的 port 格式不正確。") from error

    is_default_port = (
        scheme == "http" and port == 80
    ) or (
        scheme == "https" and port == 443
    )

    if port is None or is_default_port:
        network_location = hostname
    else:
        network_location = f"{hostname}:{port}"

    query_parameters = parse_qsl(
        parsed_url.query,
        keep_blank_values=True,
    )
    meaningful_parameters = []

    for name, value in query_parameters:
        if not is_tracking_parameter(name):
            meaningful_parameters.append((name, value))

    meaningful_parameters.sort(key=get_parameter_sort_key)
    normalized_query = urlencode(meaningful_parameters, doseq=True)

    return urlunsplit((
        scheme,
        network_location,
        parsed_url.path,
        normalized_query,
        "",
    ))
