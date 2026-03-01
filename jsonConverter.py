import pandas as pd
import json
from pathlib import Path

# -----------------------------------
# CONFIGURATION
# -----------------------------------
# This should point to the output of your cleaning_file.py
INPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"
OUTPUT_FILE_PATH = "mainData/timelines.json"


# -----------------------------------
# TIMELINE GENERATOR
# -----------------------------------

def generate_timelines():
    print(f"Loading processed dataset from: {INPUT_FILE_PATH}")

    try:
        df = pd.read_csv(INPUT_FILE_PATH)
    except FileNotFoundError:
        print("Error: Processed CSV not found. Run your cleaning script first.")
        return

    # 1. Ensure timestamp is converted to datetime objects
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 2. Sort by contact and then chronologically
    df = df.sort_values(by=["contact_name", "timestamp"])

    timelines = {}

    print("Organizing unique chat histories per contact...")

    # Grouping by 'contact_name' (the person who is NOT 'You')
    for contact, group in df.groupby("contact_name"):

        contact_history = []

        for _, row in group.iterrows():
            # Constructing the entry for each message in the timeline
            entry = {
                "timestamp": row["timestamp"],
                "sender": row["sender"],
                "receiver": row["receiver"],
                "message": row["message_raw"],  # Keep the raw version with the (#ID)
                "metrics": {
                    "inactivity_hours": round(row.get("inactivity_hours", 0), 2),
                    "word_count": int(row.get("word_count", 0)),
                    "message_length": int(row.get("message_length", 0)),
                    "is_user_sender": bool(row.get("is_user_sender", False))
                }
            }
            contact_history.append(entry)

        timelines[contact] = contact_history

    # 3. Save as JSON with formatting
    # default=str handles the datetime objects by converting them to strings
    with open(OUTPUT_FILE_PATH, "w") as f:
        json.dump(timelines, f, default=str, indent=2)

    print(f"Successfully mapped {len(timelines)} unique relationships.")
    print(f"Saved timelines to: {OUTPUT_FILE_PATH}")


# -----------------------------------
# MAIN
# -----------------------------------

if __name__ == "__main__":
    generate_timelines()