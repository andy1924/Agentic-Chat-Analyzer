import pandas as pd
import json

# -----------------------------------
# CONFIGURATION
# -----------------------------------
INPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"
OUTPUT_FILE_PATH = "mainData/timelines.json"


# -----------------------------------
# TIMELINE GENERATOR
# -----------------------------------

def generate_timelines():

    print(f"📂 Loading processed dataset from: {INPUT_FILE_PATH}")

    try:
        df = pd.read_csv(INPUT_FILE_PATH)
    except FileNotFoundError:
        print("❌ Processed CSV not found. Run cleaning script first.")
        return

    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Sort properly
    df = df.sort_values(by=["contact_name", "timestamp"])

    timelines = {}

    print("🧠 Building timelines per contact...")

    for contact, group in df.groupby("contact_name"):

        timelines[contact] = []

        for _, row in group.iterrows():
            timelines[contact].append({
                "timestamp": row["timestamp"],
                "sender": row["sender"],
                "message": row["message_raw"],
                "inactivity_hours": row.get("inactivity_hours", 0),
                "word_count": row.get("word_count", 0),
                "message_length": row.get("message_length", 0)
            })

    # Save JSON
    with open(OUTPUT_FILE_PATH, "w") as f:
        json.dump(timelines, f, default=str, indent=2)

    print(f"🚀 Saved timelines to: {OUTPUT_FILE_PATH}")
    print("JSON conversion complete.")


# -----------------------------------
# MAIN
# -----------------------------------

if __name__ == "__main__":
    generate_timelines()