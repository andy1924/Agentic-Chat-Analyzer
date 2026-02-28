import pandas as pd
import numpy as np
import re
from pathlib import Path

# -----------------------------------
# CONFIGURATION
# -----------------------------------
RAW_FILE_PATH = "mainData/whatsapp_professional_diverse_5000.csv"
OUTPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"


# -----------------------------------
# HELPER FUNCTIONS
# -----------------------------------

def clean_text(text):
    """Normalizes text for processing."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r"\[id:\d+\]", "", text)  # remove id tags
    return re.sub(r"\s+", " ", text).strip()


# -----------------------------------
# MAIN CLEANING PIPELINE
# -----------------------------------

def clean_chat_data():
    print(f"📂 Loading dataset from: {RAW_FILE_PATH}")

    try:
        df = pd.read_csv(RAW_FILE_PATH)
    except FileNotFoundError:
        print("❌ Error: CSV file not found. Check your path.")
        return

    print(f"Initial Rows: {len(df)}")

    # -----------------------------------
    # 1️⃣ CREATE TIMESTAMP
    # -----------------------------------
    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"])

    # -----------------------------------
    # 2️⃣ CLEAN MESSAGE TEXT
    # -----------------------------------
    df["message_raw"] = df["Message"]
    df["message"] = df["Message"].apply(clean_text)

    # Drop duplicates
    df = df.drop_duplicates(subset=["message_raw"]).copy()

    # -----------------------------------
    # 3️⃣ STANDARDIZE COLUMN NAMES
    # -----------------------------------
    df.rename(columns={
        "Sender": "sender"
    }, inplace=True)

    # If you want contact_name separate (assuming one-to-one chats)
    df["contact_name"] = df["sender"].apply(lambda x: "You" if x.lower() != "you" else "Self")

    # -----------------------------------
    # 4️⃣ FEATURE ENGINEERING
    # -----------------------------------
    print("🛠️ Engineering features...")

    df["message_length"] = df["message"].apply(len)
    df["word_count"] = df["message"].apply(lambda x: len(x.split()))

    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["hour"] = df["timestamp"].dt.hour
    df["is_weekend"] = df["day_of_week"].isin(["Saturday", "Sunday"])

    # -----------------------------------
    # 5️⃣ INACTIVITY CALCULATION
    # -----------------------------------
    df = df.sort_values(by=["timestamp"])

    df["is_user_sender"] = df["sender"].str.lower() == "you"

    df["prev_time"] = df.groupby("sender")["timestamp"].shift(1)

    df["inactivity_hours"] = (
        (df["timestamp"] - df["prev_time"]).dt.total_seconds() / 3600
    )

    df["inactivity_hours"] = df["inactivity_hours"].fillna(0)

    # -----------------------------------
    # 6️⃣ SAVE OUTPUT
    # -----------------------------------
    print(f"✅ Cleaned Shape: {df.shape}")

    df.to_csv(OUTPUT_FILE_PATH, index=False)

    print(f"🚀 Processed dataset saved to: {OUTPUT_FILE_PATH}")
    print("Dataset is now ready for Relationship Scoring.")


if __name__ == "__main__":
    clean_chat_data()