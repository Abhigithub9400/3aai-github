CHAT_PROMPT = """
### Knowledge Base Information:
```
{CONTEXT}
```

### User Inquiry:
```
{QUERY}
```

### Response Instructions:
- Derive a precise and straightforward answer directly from the provided knowledge base.
- If information is insufficient or unavailable, inform the user that the specific answer isn't present in the current data.
- Whenever possible, point to specific sections and page numbers for additional details or related topics.

### User Experience Optimization:
- Use visual aids like graphs or charts whenever they can enhance understanding or illustrate complex points clearly.
- Ensure responses are in simple language, avoiding technical jargon to accommodate a broad range of users.
- Strive for engagement by acknowledging the user's question and showing a helpful attitude even when the answer isn't available.
- Always respond in {RESPONSE_LANGUAGE}
"""

SUGGESTED_QUESTION_PROMPT = """
You are provided with a question and its answer related to a specific topic. Your task is to generate three follow-up questions that delve deeper into the topic, explore related areas, or clarify concepts mentioned in the answer. The follow-up questions should encourage further exploration and understanding of the subject.

Question and Answer :
```
### Current Question:
{QUESTION}

### Answer:
{ANSWER}
```

** Strict Guidelines for follow-up questions:**
1. **Relevance:** Each follow-up question must directly relate to the initial question or the information provided in the answer. It should aim to expand on the topic, not deviate from it.
2. **Depth:** Aim to formulate questions that require more than a yes/no answer. The questions should encourage detailed explanations or discussions.
3. **Clarity:** Ensure that Questions should be clear and concise, avoiding ambiguity. They should be easily understood without requiring additional context.
4. **Concise:** Ensure that follow-up questions should be short and concise not more than 10 words
5. **ResponseLanguage:** Always respond in {RESPONSE_LANGUAGE}
"""
