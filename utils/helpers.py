from langchain_community.utilities import (
    WikipediaAPIWrapper,
    ArxivAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
)

from langchain_community.tools import (
    WikipediaQueryRun,
    ArxivQueryRun,
    DuckDuckGoSearchRun,
)


# TOOLS

def create_tools():

    wiki = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(
            doc_content_chars_max=8000,
            top_k_results=5,
        )
    )

    arxiv = ArxivQueryRun(
        api_wrapper=ArxivAPIWrapper(
            doc_content_chars_max=8000,
            top_k_results=5,
        )
    )

    duck = DuckDuckGoSearchRun(
        api_wrapper=DuckDuckGoSearchAPIWrapper()
    )

    return wiki, arxiv, duck
