import requests
from html.parser import HTMLParser
from urllib.parse import urljoin
from typing import Optional

try:
    import trafilatura
except ImportError as e:
    raise ImportError(
        "This function requires 'trafilatura'. Install with: pip install trafilatura requests"
    ) from e


def extract_text_from_url(
    url: str,
    *,
    follow_pagination: bool = True,
    pagination_limit: int = 3,
    timeout: float = 10.0,
    user_agent: Optional[str] = None,
) -> str:
    """
    提取指定网址的整页可读文本（可选跟随 rel=\"next\" 分页），实现方式与项目一致：
    - 使用 requests 抓取 HTML
    - 使用 trafilatura.extract 提取纯文本，失败时回退到原始 HTML 文本

    参数:
      - url: 目标网页
      - follow_pagination: 是否跟随 rel=\"next\" 的分页链接
      - pagination_limit: 最多跟随的分页深度（至少 1）
      - timeout: 每次 HTTP 请求超时时间（秒）
      - user_agent: 自定义 UA；不提供则使用常见浏览器 UA

    返回:
      - 拼接后的纯文本，分页之间以空行分隔；无可用文本时返回空字符串
    """

    class _RelLinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.href: Optional[str] = None

        def handle_starttag(self, tag, attrs):
            if self.href:
                return
            attr = {k.lower(): v for k, v in attrs}
            rel_attr = (attr.get("rel") or "").lower().split()
            if "next" in rel_attr:
                self.href = attr.get("href")

    def _find_rel_next(html: str) -> Optional[str]:
        try:
            parser = _RelLinkParser()
            parser.feed(html)
            return parser.href
        except Exception:
            return None

    headers = {
        "User-Agent": user_agent
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }

    texts: list[str] = []
    visited = set()
    current = url

    for _ in range(max(1, int(pagination_limit))):
        if current in visited:
            break
        visited.add(current)

        resp = requests.get(current, headers=headers, timeout=timeout)
        resp.raise_for_status()
        raw_html = resp.text

        extracted = trafilatura.extract(
            raw_html,
            include_comments=False,
            include_tables=False,
        )
        clean_text = extracted.strip() if extracted else raw_html.strip()
        if clean_text:
            texts.append(clean_text)

        if not follow_pagination:
            break

        next_href = _find_rel_next(raw_html)
        if not next_href:
            break
        current = urljoin(current, next_href)

    return ("\n\n".join(texts)).strip()

def filter_extracted_text(   
    url: str,
    *,
    follow_pagination: bool = True,
    pagination_limit: int = 3,
    timeout: float = 10.0,
    user_agent: Optional[str] = None,
    regular_expressions: Optional[list[str]] = None,
) -> str:
    """
    提取并过滤指定网址的整页可读文本（可选跟随 rel=\"next\" 分页），实现方式与项目一致：
    - 使用 requests 抓取 HTML
    - 使用 trafilatura.extract 提取纯文本，失败时回退到原始 HTML 文本
    - 使用正则表达式过滤文本

    参数:
      - url: 目标网页
      - follow_pagination: 是否跟随 rel=\"next\" 的分页链接
      - pagination_limit: 最多跟随的分页深度（至少 1）
      - timeout: 每次 HTTP 请求超时时间（秒）
      - user_agent: 自定义 UA；不提供则使用常见浏览器 UA
      - regular_expressions: 用于过滤文本的正则表达式列表；如果为 None 或空列表，则不进行过滤
      """
    import re

    text = extract_text_from_url(
        url,
        follow_pagination=follow_pagination,
        pagination_limit=pagination_limit,
        timeout=timeout,
        user_agent=user_agent,
    )

    if not regular_expressions:
        return text

    patterns = [re.compile(pattern) for pattern in regular_expressions]
    filtered_lines = [
        line for line in text.splitlines()
        if any(pattern.search(line) for pattern in patterns)
    ]

    return "\n".join(filtered_lines).strip()

