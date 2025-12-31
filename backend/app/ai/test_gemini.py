from langchain_core.messages import HumanMessage
from gemini_client import get_gemini_llm


llm = get_gemini_llm()

response = llm.invoke([
    HumanMessage(content="Say hello in one sentence.")
])

print(response)
print("CONTENT:", response.content)
