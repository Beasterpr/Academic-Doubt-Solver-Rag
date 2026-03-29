import time
import concurrent.futures

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate


# CONFIG

CHUNK_SIZE      = 8000
CHUNK_OVERLAP   = 200
MAX_CHUNKS      = 18
MAX_WORKERS     = 4
RETRY_ATTEMPTS  = 3
RETRY_BASE_WAIT = 5

# PROMPTS

MAP_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=(
        "You are a research assistant. Extract and summarize the key points from "
        "the section below into 4–6 concise bullet points. Be factual and specific.\n\n"
        "Text:\n{text}\n\n"
        "Key Points:"
    ),
)

COMBINE_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=(
        "You are an expert academic report writer. Using the bullet-point summaries "
        "below (each from a different section of the same source), write a single, "
        "well-structured, professional report with the following sections:\n\n"
        "## Executive Summary\n"
        "A 3–4 sentence overview of the entire content.\n\n"
        "## Main Findings\n"
        "Organised by theme. Use sub-headings where appropriate.\n\n"
        "## Key Takeaways\n"
        "3–5 actionable or memorable points.\n\n"
        "## Conclusion\n"
        "A brief closing paragraph.\n\n"
        "Write in clear, professional English. Do NOT invent information beyond "
        "what is present in the summaries.\n\n"
        "Summaries:\n{text}\n\n"
        "Report:"
    ),
)

# HELPERS

def _split_docs(docs) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(docs)


def _smart_truncate(chunks: list) -> tuple:
    """Cap to MAX_CHUNKS using evenly-spaced sampling."""
    if len(chunks) <= MAX_CHUNKS:
        return chunks, False
    step = len(chunks) / MAX_CHUNKS
    selected = [chunks[int(i * step)] for i in range(MAX_CHUNKS)]
    return selected, True


def _summarize_chunk(llm, chunk_text: str, idx: int) -> tuple:
    """Summarize one chunk with retry on rate-limit errors."""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = llm.invoke(MAP_PROMPT.format(text=chunk_text))
            return idx, response.content
        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                time.sleep(RETRY_BASE_WAIT * (attempt + 1))
            else:
                return idx, f"[Error on chunk {idx+1}: {e}]"
    return idx, f"[Chunk {idx+1}: failed after {RETRY_ATTEMPTS} retries]"


# MAIN PIPELINE

def generate_report(docs, llm, on_chunk_done=None) -> dict:
    """
    Full pipeline: split → truncate → parallel map → combine.

    on_chunk_done(completed: int, total: int) is called after each chunk finishes.

    Returns:
        {
            "report":        str,
            "total_chunks":  int,
            "used_chunks":   int,
            "truncated":     bool,
            "elapsed":       float,
        }
    """
    start = time.time()

    # 1. Split
    all_chunks = _split_docs(docs)

    # 2. Truncate
    chunks, truncated = _smart_truncate(all_chunks)
    total = len(chunks)

    # 3. Parallel map
    summaries = [None] * total
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {
            ex.submit(_summarize_chunk, llm, c.page_content, i): i
            for i, c in enumerate(chunks)
        }
        for future in concurrent.futures.as_completed(futures):
            idx, summary = future.result()
            summaries[idx] = summary
            completed += 1
            if on_chunk_done:
                on_chunk_done(completed, total)

    # 4. Combine
    combined = "\n\n".join(
        f"[Section {i+1}]\n{s}" for i, s in enumerate(summaries)
    )
    final = llm.invoke(COMBINE_PROMPT.format(text=combined))

    return {
        "report":       final.content,
        "total_chunks": len(all_chunks),
        "used_chunks":  total,
        "truncated":    truncated,
        "elapsed":      time.time() - start,
    }
