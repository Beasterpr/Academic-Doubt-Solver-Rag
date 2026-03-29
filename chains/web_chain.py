from operator import itemgetter

from pydantic import BaseModel, Field
from typing import Literal

from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
)

from langchain_core.output_parsers import StrOutputParser

from prompts.router_prompt import (
    router_prompt,
    formatter_prompt,
    rewrite_prompt,
)

from utils.helpers import create_tools


# Pydantic Models

class WebSearch(BaseModel):
    web_search_button: Literal[
        "Wiki",
        "Arxiv",
        "DuckDuckGo",
    ]

class ArxivQuery(BaseModel):
    keywords: str = Field(
        ...,
        description="short search keywords",
    )


# WEB CHAIN

def build_web_chain(llm):

    wiki_tool, arxiv_tool, duck_tool = create_tools()

    llm_router = llm.with_structured_output(WebSearch)
    llm_rewrite = llm.with_structured_output(ArxivQuery)

    # router

    router_chain = (

        RunnableParallel(
            input=itemgetter("input")
        )

        | router_prompt

        | llm_router

        | RunnableLambda(
            lambda x: x.web_search_button
        )

    )

    # formatter

    formatter_chain = (

        formatter_prompt

        | llm

        | StrOutputParser()

    )

    # rewrite

    rewrite_chain = (

        rewrite_prompt

        | llm_rewrite

        | RunnableLambda(
            lambda x: x.keywords
        )

    )

    # wiki

    wiki_chain = (

        RunnableParallel(

            tool_output=itemgetter("input")
            | wiki_tool,

            input=itemgetter("input"),

        )

        | formatter_chain

    )

    # arxiv

    arxiv_chain = (

        RunnableParallel(

            tool_output=itemgetter("input")
            | rewrite_chain
            | arxiv_tool,

            input=itemgetter("input"),

        )

        | formatter_chain

    )

    # duck

    duck_chain = (

        RunnableParallel(

            tool_output=itemgetter("input")
            | duck_tool,

            input=itemgetter("input"),

        )

        | formatter_chain

    )

    # branch

    branch = RunnableBranch(

        (
            lambda x: x["router"] == "Wiki",
            wiki_chain,
        ),

        (
            lambda x: x["router"] == "Arxiv",
            arxiv_chain,
        ),

        (
            lambda x: x["router"] == "DuckDuckGo",
            duck_chain,
        ),

        duck_chain,

    )

    # final

    final_chain = (

        RunnableParallel(

            router=router_chain,
            input=itemgetter("input"),

        )

        | branch

    )

    return final_chain
