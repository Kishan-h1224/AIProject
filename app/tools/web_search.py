
from pydantic import BaseModel, ConfigDict, Field
from ddgs import DDGS

from app.tools.registry import register_tool


# ---------------------------------
# 1. Define argument schema
# ---------------------------------

class WebSearchArgs(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    query: str = Field(
        min_length=2,
        max_length=300,
        description="The search query"
    )

    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of search results"
    )


# ---------------------------------
# 2. Register Web Search Tool
# ---------------------------------

@register_tool("web_search", WebSearchArgs)
def web_search(query: str, max_results: int = 5) -> dict:

    """
    Search the internet and return relevant results.
    """

    # Initialize search provider
    search_client = DDGS(timeout=8)

    # Perform search
    raw_results = search_client.text(
        query,
        region="in-en",
        safesearch="moderate",
        max_results=max_results
    )

    # Convert results into our standard format
    formatted_results = []

    for item in raw_results:

        formatted_results.append({

            "title": item.get("title", ""),

            "url": item.get("href", ""),

            "description": item.get("body", "")[:1000]

        })

    return {

        "query": query,

        "count": len(formatted_results),

        "results": formatted_results

    }


# ---------------------------------
# 3. Test Web Search
# ---------------------------------

if __name__ == "__main__":

    query = "Python 3.10 features"

    result = web_search(
        query=query,
        max_results=5
    )

    print("\nSearch Query:", result["query"])

    print("\nNumber of Results:", result["count"])

    for index, item in enumerate(result["results"], start=1):

        print(f"\nResult {index}")

        print("Title:", item["title"])

        print("URL:", item["url"])

        print("Description:", item["description"])
