from chains.web_chain import build_web_chain


# WEB SERVICE

def run_web_search(query: str, llm) -> str:
    """Run the web search chain and return the answer string."""
    chain = build_web_chain(llm)
    answer = chain.invoke({"input": query})
    return answer if isinstance(answer, str) else str(answer)
