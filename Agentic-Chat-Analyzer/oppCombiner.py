import pandas as pd
import numpy as np
import re
import json

# -----------------------------------
# CONFIGURATION
# -----------------------------------
RAW_FILE_PATH = "mainData/whatsapp_professional_diverse_5000.csv"
PROCESSED_FILE_PATH = "mainData/processed_chat_dataset.csv"
TIMELINE_OUTPUT_PATH = "mainData/timelines.json"


# -----------------------------------
# CLEANING FUNCTIONS
# -----------------------------------

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r"\[id:\d+\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_chat_data():
    print("Step 1: Loading raw dataset...")

    df = pd.read_csv(RAW_FILE_PATH)
    print(f"Initial rows: {len(df)}")

    # Combine Date + Time
    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"])

    # Rename Sender column
    df.rename(columns={"Sender": "sender"}, inplace=True)

    # Clean messages
    df["message_raw"] = df["Message"]
    df["message"] = df["Message"].apply(clean_text)

    # User detection
    df["is_user_sender"] = df["sender"].str.lower() == "you"

    # Contact identification
    df["contact_name"] = np.where(
        df["is_user_sender"],
        "Other",
        df["sender"]
    )

    # Feature engineering
    df["message_length"] = df["message"].apply(len)
    df["word_count"] = df["message"].apply(lambda x: len(x.split()))
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["hour"] = df["timestamp"].dt.hour
    df["is_weekend"] = df["day_of_week"].isin(["Saturday", "Sunday"])

    # Sort and inactivity calculation
    df = df.sort_values(by=["contact_name", "timestamp"])
    df["prev_time"] = df.groupby("contact_name")["timestamp"].shift(1)
    df["inactivity_hours"] = (
        (df["timestamp"] - df["prev_time"]).dt.total_seconds() / 3600
    ).fillna(0)

    # Save processed file
    df.to_csv(PROCESSED_FILE_PATH, index=False)
    print("✅ Cleaning complete. Processed dataset saved.")

    return df


# -----------------------------------
# JSON CONVERSION
# -----------------------------------

def generate_timelines(df):
    print("🧠 Step 2: Converting to JSON timelines...")

    timelines = {}

    for contact, group in df.groupby("contact_name"):
        group = group.sort_values("timestamp")

        timelines[contact] = []

        for _, row in group.iterrows():
            timelines[contact].append({
                "timestamp": row["timestamp"],
                "sender": row["sender"],
                "message": row["message_raw"],
                "inactivity_hours": row["inactivity_hours"],
                "word_count": row["word_count"]
            })

    with open(TIMELINE_OUTPUT_PATH, "w") as f:
        json.dump(timelines, f, default=str, indent=2)

    print("🚀 JSON conversion complete.")
    print(f"Saved to: {TIMELINE_OUTPUT_PATH}")


# -----------------------------------
# MAIN PIPELINE
# -----------------------------------

def run_pipeline():
    print("🚀 Starting full relationship intelligence pipeline...\n")

    cleaned_df = clean_chat_data()
    generate_timelines(cleaned_df)

    print("\n🎉 Pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()