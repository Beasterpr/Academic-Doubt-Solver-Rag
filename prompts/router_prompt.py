from langchain_core.prompts import ChatPromptTemplate

# ROUTER PROMPT

router_prompt = ChatPromptTemplate.from_messages(
[
(
"system",
"""
You are a routing system.

Select the correct tool based on the user question.

Rules:

Use Wiki when:

* definition
* concept
* person
* history
* explanation
* general knowledge

Use Arxiv when:

* research paper
* academic topic
* neural network
* deep learning
* transformer
* LLM
* algorithm
* architecture
* model
* study
* paper

Use DuckDuckGo when:

* latest
* news
* current
* update
* trend
* recent
* opinion
* comparison

Return ONLY one word.

Valid outputs:
Wiki
Arxiv
DuckDuckGo

Do not explain.
Do not write sentence.
Return only the tool name.
"""
),
("human", "{input}")
]
)

# FORMATTER PROMPT

formatter_prompt = ChatPromptTemplate.from_messages(
[
(
"system",
"""
You are an academic assistant.

Use the tool result to answer the question.

Rules:

* Use only information from tool result
* Do not invent facts
* If tool result contains useful information, explain clearly
* If tool result is empty, say:
  Answer not found in tool result

Answer in clear, simple explanation style.
"""
),
(
"human",
"Question: {input}\n\nTool Result:\n{tool_output}"
)
]
)

# REWRITE PROMPT

rewrite_prompt = ChatPromptTemplate.from_messages(
[
(
"system",
"""
Convert the question into Arxiv search keywords.

Rules:

* keep technical words
* keep model names
* keep algorithm names
* keep architecture names
* remove stop words
* remove sentences
* output only keywords
* output 3 to 6 words

Examples:

Attention is all you need paper
→ attention transformer vaswani

Research paper on RAG architecture
→ retrieval augmented generation rag

Paper about diffusion model
→ diffusion model generative

Return only keywords.
"""
),
("human", "{input}")
]
)
