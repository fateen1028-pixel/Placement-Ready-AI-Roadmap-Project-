from typing import Dict, Any
from app.schemas.roadmap_state import TaskSlot
# from app.ai.gemini_client import get_gemini_llm
from app.ai.groq_client import get_groq_llm
from langchain_core.prompts import ChatPromptTemplate

class AIService:
    """
    Handles all AI-powered operations for SkillForgeAI.
    """

    def __init__(self):
        # self.llm = get_gemini_llm()
        self.llm = get_groq_llm()

    async def generate_hint(
        self,
        slot: TaskSlot,
        user_skill_vector: Dict[str, Any]
    ) -> str:
        skill = slot.skill
        difficulty = slot.difficulty
        
        # Create a concise prompt for a hint
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful coding mentor. The user is about to start a task.\n"
            "Skill: {skill}\n"
            "Difficulty: {difficulty}\n"
            "User's current skill level: {user_level}\n\n"
            "Provide a short, encouraging hint (max 2 sentences) to help them prepare. "
            "Do NOT give the answer. Focus on concepts."
        )
        
        user_level = user_skill_vector.get(skill, 0.0)
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "skill": skill,
            "difficulty": difficulty,
            "user_level": user_level
        })
        
        # Handle response content (LangChain returns an AIMessage)
        return response.content if hasattr(response, 'content') else str(response)

    async def adjust_slot_difficulty(
    self,
    slot: TaskSlot,
    user_skill_vector: Dict[str, Any]
) -> str:
        return slot.difficulty

    async def update_skill_vector(
    self,
    skill_vector: Dict[str, Any],
    slot: TaskSlot,
    success: bool
) -> Dict[str, Any]:
        skill = slot.skill

        current = skill_vector.get(skill, 0.0)

        if success:
            skill_vector[skill] = round(current + 0.1, 2)
        else:
            skill_vector[skill] = round(max(current - 0.05, 0.0), 2)

        return skill_vector

