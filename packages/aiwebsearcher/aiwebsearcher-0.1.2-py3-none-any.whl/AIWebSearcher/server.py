import json
from typing import Optional

from fastmcp import FastMCP
from AIWebSearcher.FetchPage.fetchWeb import filter_extracted_text
from AIWebSearcher.WebSearch.baiduSearchTool import BaiduSearchTools
from AIWebSearcher.useAI2Search.SearchAgent import filterAnswer


mcp = FastMCP("AIWebSearcher")

# @mcp.tool
# def add(a: int, b: int) -> int:
#     """Add two numbers"""
#     return a + b

@mcp.tool
def search_baidu(query: str, max_results: int = 5, language: str = "zh") -> str:
    """Execute Baidu search and return results,
    Due to the limited amount of content returned, it is recommended to use parameters of max_results with four or more

    Args:
        query (str): Search keyword
        max_results (int, optional): Maximum number of results to return, default 5
        language (str, optional): Search language, default Chinese

    Returns:
        str: A JSON formatted string containing the search results (Title, URL, abstract).
    """
    tool = BaiduSearchTools()
    return tool.baidu_search(query, max_results=max_results, language=language)

@mcp.tool
async def AI_search_baidu(query: str, max_results: int = 5, language: str = "zh") -> str:
    """Execute Baidu search using AI and return results in order, this func time cost almost 10s,
    The AI will automatically filter and sort the search results, it is recommended to use parameters of max_results with five or more

    Args:
        query (str): Search keyword
        max_results (int, optional): Maximum number of results to return, default 5
        language (str, optional): Search language, default Chinese

    Returns:
        str: A JSON formatted string containing the search results (rank, title, url, Content).
    """
    result = await filterAnswer(query, max_results, language)
    return json.dumps(result, ensure_ascii=False, indent=2)

@mcp.tool
def extractTextFromUrl(
    url: str,
    *,
    follow_pagination: bool = True,
    pagination_limit: int = 3,
    timeout: float = 10.0,
    user_agent: Optional[str] = None,
    regular_expressions: Optional[list[str]] = None,
) -> str:
    """
    Extract and filter readable text from a webpage with optional pagination support.
    
    Uses requests to fetch HTML, trafilatura to extract clean text (falls back to raw HTML),
    and regex patterns to filter content.

    Args:
        url: Target webpage URL
        follow_pagination: Whether to follow rel="next" pagination links
        pagination_limit: Maximum pagination depth (minimum 1)
        timeout: HTTP request timeout in seconds
        user_agent: Custom User-Agent header (defaults to common browser UA)
        regular_expressions: Regex patterns to filter text; no filtering if None or empty
    """
    return filter_extracted_text(
        url,
        follow_pagination=follow_pagination,
        pagination_limit=pagination_limit,
        timeout=timeout,
        user_agent=user_agent,
        regular_expressions=regular_expressions,
    )

@mcp.tool
def extractTextFromUrls(
    urls: list[str],
    *,
    follow_pagination: bool = True,
    pagination_limit: int = 3,
    timeout: float = 10.0,
    user_agent: Optional[str] = None,
    regular_expressions: Optional[list[str]] = None,
) -> str:
    """
    Extract and filter readable text from multiple webpages with optional pagination support.
    
    Uses requests to fetch HTML, trafilatura to extract clean text (falls back to raw HTML),
    and regex patterns to filter content. Regex filtering is recommended for multiple URLs.

    Args:
        urls: List of target webpage URLs
        follow_pagination: Whether to follow rel="next" pagination links
        pagination_limit: Maximum pagination depth (minimum 1)
        timeout: HTTP request timeout in seconds
        user_agent: Custom User-Agent header (defaults to common browser UA)
        regular_expressions: Regex patterns to filter text; no filtering if None or empty
    """
    results = []
    for url in urls:
        results.append(filter_extracted_text(
        url,
        follow_pagination=follow_pagination,
        pagination_limit=pagination_limit,
        timeout=timeout,
        user_agent=user_agent,
        regular_expressions=regular_expressions,
        ))
    return "\n\n".join(results)


def main() -> None:
    """Start the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

