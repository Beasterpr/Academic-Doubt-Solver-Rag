from langchain_core.prompts import ChatPromptTemplate

# MCQ PROMPT — Knowledge Base mode (uses retrieved context)

mcq_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an academic quiz generator.

Using ONLY the context provided, generate multiple-choice questions (MCQs).

Difficulty level: {difficulty}
- Easy:   straightforward recall questions, obvious distractors
- Medium: requires understanding, plausible distractors
- Hard:   requires deep understanding, subtle distinctions between options
- Mixed:  include a variety of easy, medium, and hard questions

Rules:
* Each question must have exactly 4 options labelled A), B), C), D)
* Only one option is correct
* Base every question strictly on the provided context
* Do not invent information outside the context
* Do NOT add any preamble or closing remarks — output ONLY the questions

Format EXACTLY as:

Q<number>. <question text>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <correct letter>

context:
{context}
""",
    ),
    ("human", "Generate {num_questions} MCQs about: {topic}"),
])


# MCQ PROMPT — General Topic mode (LLM general knowledge, no context needed)

mcq_topic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an academic quiz generator.

Generate multiple-choice questions (MCQs) based on your general knowledge about the given topic.

Difficulty level: {difficulty}
- Easy:   straightforward recall questions, obvious distractors
- Medium: requires understanding, plausible distractors
- Hard:   requires deep understanding, subtle distinctions between options
- Mixed:  include a variety of easy, medium, and hard questions

Rules:
* Each question must have exactly 4 options labelled A), B), C), D)
* Only one option is correct
* Questions must be factually accurate
* Do NOT add any preamble or closing remarks — output ONLY the questions

Format EXACTLY as:

Q<number>. <question text>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <correct letter>
""",
    ),
    ("human", "Generate {num_questions} MCQs about: {topic}"),
])
