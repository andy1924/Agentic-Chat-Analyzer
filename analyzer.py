import os
import asyncio
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# ---------------------------------------------------------
# 1. ENVIRONMENT & OBSERVABILITY
# ---------------------------------------------------------
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_PROJECT"] = "RelateAI_Production"

# ---------------------------------------------------------
# 2. UPDATED SCHEMA: PROFILES & REMINDERS
# ---------------------------------------------------------
# --- NEW: Nested Schema for Reminders ---
class Reminder(BaseModel):
    event_title: str = Field(description="A short, actionable title for the calendar event (e.g., 'Coffee with Alex', 'Send Invoice').")
    datetime_context: str = Field(description="The exact date or time mentioned, converted to ISO 8601 format if possible, or a descriptive string like 'Tomorrow afternoon'. Leave as 'None' if no time is mentioned.")
    description: str = Field(description="A brief context of the reminder based on the chat.")

# --- UPDATED: Main Profile Schema ---
class IndividualProfile(BaseModel):
    communication_style: str = Field(description="The user's core texting style (e.g., Direct & analytical, enthusiastic, passive, brief).")
    emotional_baseline: str = Field(description="The general emotional state or mood of this user across these messages.")
    engagement_trend: str = Field(description="How their effort or length of messages is trending over time (e.g., Becoming more invested, pulling away, consistent).")
    behavioral_flags: list[str] = Field(description="A list of 1-3 specific communication quirks, green flags, or red flags (e.g., 'Uses demanding language', 'Highly supportive').")
    interaction_advice: str = Field(description="Actionable advice on how others should communicate with this person to get the best response.")
    suggested_reminders: list[Reminder] = Field(description="A list of any commitments, meetings, or tasks mentioned by either person in this chat that require a calendar reminder. Return an empty list [] if none exist.")

# ---------------------------------------------------------
# 3. PRODUCTION CLASS (Modular & Async)
# ---------------------------------------------------------
class BehaviorAnalyzer:
    def __init__(self):
        system_prompt = """
        You are an expert behavioral and linguistic analyst.
        Your job is to profile an individual's communication style based purely on a timeline of their isolated messages.

        CRITICAL RULES:
        - You are ONLY seeing messages from ONE person. You do not see the replies.
        - Focus on psychological profiling, tone, vocabulary, and emotional consistency.
        - Extract ANY commitments, plans, or deadlines mentioned into the 'suggested_reminders' list.
        - Assume the current date is March 1, 2026, and the timezone is Asia/Kolkata (IST) when calculating dates.
        - Do NOT perform math, do NOT count messages, and do NOT calculate response times. 
        - Provide highly actionable advice on how someone else should adapt their communication to match this user's style.
        """

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "User's Message Log:\n{chat_history}")
        ])

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            max_retries=3,
            timeout=15
        )

        self.structured_llm = self.llm.with_structured_output(IndividualProfile)
        self.chain = self.prompt | self.structured_llm

    async def analyze_chat_async(self, formatted_chat: str) -> dict:
        try:
            result = await self.chain.ainvoke({"chat_history": formatted_chat})
            return result.model_dump()

        except Exception as e:
            print(f"Error during AI analysis: {e}")
            return {
                "communication_style": "Error analyzing style.",
                "emotional_baseline": "Unknown",
                "engagement_trend": "Unknown",
                "behavioral_flags": ["System error."],
                "interaction_advice": "Please try again later.",
                "suggested_reminders": [] # Added this so UI doesn't crash on error
            }

# ---------------------------------------------------------
# 4. EXECUTION PIPELINE
# ---------------------------------------------------------
async def process_and_save_real_data(input_file_path: str, output_file_name: str):
    save_directory = "mainData"
    os.makedirs(save_directory, exist_ok=True)
    output_path = os.path.join(save_directory, output_file_name)

    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            real_chat_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {input_file_path}.")
        return

    print("Extracting messages from conversations...")
    flat_messages = []

    if isinstance(real_chat_data, dict):
        for conversation_name, message_list in real_chat_data.items():
            if isinstance(message_list, list):
                flat_messages.extend(message_list)
    elif isinstance(real_chat_data, list):
        flat_messages = real_chat_data

    if not flat_messages:
        print("Error: No valid messages found to process.")
        return

    print("Grouping messages by sender...")
    grouped_messages = {}

    for msg in flat_messages:
        sender = msg.get('sender', 'Unknown')
        timestamp = msg.get('timestamp', 'Unknown Time')
        text = msg.get('message', '')

        if sender not in grouped_messages:
            grouped_messages[sender] = []

        grouped_messages[sender].append(f"[{timestamp}] {text}")

    print(f"Found {len(grouped_messages)} unique users. Building behavioral profiles & extracting reminders...")

    analyzer = BehaviorAnalyzer()
    all_user_profiles = []

    for user, messages in grouped_messages.items():
        print(f"Processing analysis for: {user}...")

        user_chat_block = "\n".join(messages[-50:])
        ai_insight = await analyzer.analyze_chat_async(user_chat_block)

        ai_insight["analyzed_user"] = user
        ai_insight["messages_analyzed"] = len(messages[-50:])
        ai_insight["total_messages_sent"] = len(messages)

        all_user_profiles.append(ai_insight)

        await asyncio.sleep(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_user_profiles, f, indent=4)

    print(f"Success! {len(all_user_profiles)} user profiles securely saved to: {output_path}")

if __name__ == "__main__":
    INPUT_FILE = "mainData//timelines.json"
    OUTPUT_FILE = "analyzedResults.json"
    asyncio.run(process_and_save_real_data(INPUT_FILE, OUTPUT_FILE))