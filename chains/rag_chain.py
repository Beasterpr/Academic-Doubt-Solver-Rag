from operator import itemgetter

from langchain_chroma import Chroma

from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import StrOutputParser

from prompts.rag_prompt import rag_prompt


# RAG CHAIN

def build_rag_chain(vectordb, llm):

    retriever = vectordb.as_retriever(
        search_kwargs={"k": 10}
    )

    chain = (

        RunnableParallel(

            context=itemgetter("input")
            | retriever,

            input=itemgetter("input"),

        )

        |

        RunnableParallel(

            answer=rag_prompt
            | llm
            | StrOutputParser(),

            context=itemgetter("context"),

        )

    )

    return chain
