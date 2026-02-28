import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# ---------------------------------------------------------
# 1. ENVIRONMENT & OBSERVABILITY
# ---------------------------------------------------------
# Securely load API keys from a .env file
load_dotenv()

# to see exactly what went into the LLM and what came out.
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "RelateAI_Production"


# ---------------------------------------------------------
# 2. SCHEMA DEFINITION
# ---------------------------------------------------------
class RelationshipAnalysis(BaseModel):
    tone: str = Field(description="The current overall tone of the conversation.")
    relationship_type: str = Field(description="Classification of the relationship.")
    emotional_drift: str = Field(description="How the emotion has changed from beginning to end.")
    risk_of_ghosting: str = Field(description="Risk as: Low, Medium, or High, with a 1-sentence reason.")
    suggested_action: str = Field(description="One specific, actionable piece of advice for what to message next.")


# ---------------------------------------------------------
# 3. PRODUCTION CLASS (Modular & Async)
# ---------------------------------------------------------
class BehaviorAnalyzer:
    def __init__(self):
        system_prompt = """
        You are an expert behavioral analyst reading a chat history.
        Your job is to analyze the psychological subtext, tone, and emotional trajectory of the conversation.

        CRITICAL RULES:
        - Focus ONLY on context, reasoning, and behavioral suggestions.
        - Do NOT perform math, do NOT count messages, and do NOT calculate response times. 
        - Analyze the dynamic specifically from the perspective of helping 'User A'.
        """

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Chat Log:\n{chat_history}")
        ])

        # RELIABILITY Upgrade: Added max_retries to handle API network blips
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            max_retries=3,
            timeout=15
        )

        self.structured_llm = self.llm.with_structured_output(RelationshipAnalysis)
        self.chain = self.prompt | self.structured_llm

    # ASYNC Upgrade: Prevents blocking the main thread (crucial for UIs like Streamlit)
    async def analyze_chat_async(self, formatted_chat: str) -> dict:
        try:
            # ainvoke() is the asynchronous version of invoke()
            result = await self.chain.ainvoke({"chat_history": formatted_chat})

            # Return a clean Python dictionary so the UI doesn't have to deal with Pydantic objects
            return result.model_dump()

        except Exception as e:
            # ERROR HANDLING Upgrade: Never crash the frontend if the AI fails
            print(f"!Error during AI analysis: {e}")
            return {
                "tone": "Error analyzing tone.",
                "relationship_type": "Unknown",
                "emotional_drift": "Could not compute.",
                "risk_of_ghosting": "Unknown",
                "suggested_action": "System error. Please try again later."
            }


# ---------------------------------------------------------
# 4. EXECUTION (For testing standalone)
# ---------------------------------------------------------
if __name__ == "__main__":
    import json

    # Load the mock data
    with open("mockData//mockData_Arnav.json", "r") as f:
        chat_data = json.load(f)

    formatted_chat = "\n".join([f"{msg['timestamp']} | {msg['sender']}: {msg['text']}" for msg in chat_data])

    print("Analyzing conversation asynchronously...")

    # Run the async function
    analyzer = BehaviorAnalyzer()
    result = asyncio.run(analyzer.analyze_chat_async(formatted_chat))

    print(json.dumps(result, indent=2))