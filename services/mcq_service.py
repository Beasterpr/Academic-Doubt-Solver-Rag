from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda
from operator import itemgetter

from prompts.mcq_prompt import mcq_prompt, mcq_topic_prompt


def generate_mcqs_from_kb(vectordb, llm, topic: str, num_questions: int = 5, difficulty: str = "Mixed") -> str:
    """Generate MCQs from the indexed knowledge base (RAG)."""
    retriever = vectordb.as_retriever(search_kwargs={"k": 10})

    chain = (
        RunnableParallel(
            context=itemgetter("topic") | retriever,
            topic=itemgetter("topic"),
            num_questions=itemgetter("num_questions"),
            difficulty=itemgetter("difficulty"),
        )
        | mcq_prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke({
        "topic": topic,
        "num_questions": num_questions,
        "difficulty": difficulty,
    })


def generate_mcqs_from_topic(llm, topic: str, num_questions: int = 5, difficulty: str = "Mixed") -> str:
    """Generate MCQs from general LLM knowledge (no KB required)."""
    chain = mcq_topic_prompt | llm | StrOutputParser()

    return chain.invoke({
        "topic": topic,
        "num_questions": num_questions,
        "difficulty": difficulty,
    })


# Legacy alias kept for backward compat
def generate_mcqs(vectordb, llm, topic: str, num_questions: int = 5) -> str:
    return generate_mcqs_from_kb(vectordb, llm, topic, num_questions, "Mixed")
