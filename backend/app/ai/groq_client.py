import os
from langchain_groq import ChatGroq
from pydantic import SecretStr
from app.core.config import settings

def get_groq_llm():
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    return ChatGroq(
        model=settings.GROQ_MODEL,
        temperature=0.2,
        api_key=SecretStr(api_key) if api_key else None
    )
