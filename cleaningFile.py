import pandas as pd
import numpy as np
import re
from pathlib import Path

# -----------------------------------
# CONFIGURATION
# -----------------------------------
# Update this path to where your new CSV is located
RAW_FILE_PATH = "mainData/whatsapp_unique_chats_5000.csv"
OUTPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"


# -----------------------------------
# HELPER FUNCTIONS
# -----------------------------------

def clean_text(text):
    """Normalizes text and removes unique serial identifiers."""
    if pd.isna(text):
        return ""

    text = str(text).lower()

    # 1. Remove uniqueness tags like (#10000) or (#10465)
    text = re.sub(r"\(#\d+\)", "", text)

    # 2. Basic cleanup (remove extra whitespace)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# -----------------------------------
# MAIN CLEANING PIPELINE
# -----------------------------------

def clean_chat_data():
    print(f"Loading unique WhatsApp dataset from: {RAW_FILE_PATH}")

    try:
        # Loading CSV with lowercase headers as provided: date,time,sender,receiver,message
        df = pd.read_csv(RAW_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: File not found at {RAW_FILE_PATH}")
        return

    print(f"Initial Rows: {len(df)}")

    # -----------------------------------
    # TIMESTAMP PARSING
    # -----------------------------------
    # Handles "12/02/2026, 10:45 am" format
    # We strip any leading/trailing whitespace from date/time just in case
    df['timestamp'] = pd.to_datetime(
        df['date'].str.strip() + ' ' + df['time'].str.strip(),
        format='%d/%m/%Y %I:%M %p'
    )

    # -----------------------------------
    # MESSAGE CLEANING & UNIQUENESS
    # -----------------------------------
    df["message_raw"] = df["message"]  # Store original for reference
    df["message"] = df["message"].apply(clean_text)

    # Even though generated to be unique, we drop duplicates to be safe
    df = df.drop_duplicates(subset=["message_raw"]).copy()

    # -----------------------------------
    # RELATIONSHIP MAPPING
    # -----------------------------------
    # The "Contact" is the person who is NOT "You"
    df["contact_name"] = np.where(
        df["sender"].str.lower() == "you",
        df["receiver"],
        df["sender"]
    )

    # Directional flag for relationship scoring
    df["is_user_sender"] = df["sender"].str.lower() == "you"

    # -----------------------------------
    # FEATURE ENGINEERING
    # -----------------------------------
    print("Engineering features for intelligence system...")

    df["message_length"] = df["message"].apply(len)
    df["word_count"] = df["message"].apply(lambda x: len(x.split()))

    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["hour"] = df["timestamp"].dt.hour
    df["is_weekend"] = df["day_of_week"].isin(["Saturday", "Sunday"])

    # -----------------------------------
    # INACTIVITY & FLOW CALCULATION
    # -----------------------------------
    # Sort by relationship and time to see the "flow" of conversation
    df = df.sort_values(by=["contact_name", "timestamp"])

    # Calculate time gap between messages per contact (in hours)
    df["prev_time"] = df.groupby("contact_name")["timestamp"].shift(1)
    df["inactivity_hours"] = (
            (df["timestamp"] - df["prev_time"]).dt.total_seconds() / 3600
    )
    df["inactivity_hours"] = df["inactivity_hours"].fillna(0)

    # -----------------------------------
    # FINAL OUTPUT
    # -----------------------------------
    print(f"Cleaned Shape: {df.shape}")

    # Create directory if it doesn't exist
    Path(OUTPUT_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_FILE_PATH, index=False)

    print(f"Processed dataset saved to: {OUTPUT_FILE_PATH}")
    print("Pre-processing complete. Ready for Relationship Scoring.")


if __name__ == "__main__":
    clean_chat_data()