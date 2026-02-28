import pandas as pd
import numpy as np
import json

# -----------------------------------
# CONFIG
# -----------------------------------
INPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"
OUTPUT_FILE_PATH = "mainData/relationship_health.json"


def normalize(value, min_val, max_val):
    if max_val == min_val:
        return 0
    return (value - min_val) / (max_val - min_val)


def calculate_scores(df):

    results = {}

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Dataset-wide stats
    dataset_max_date = df["timestamp"].max()
    dataset_min_date = df["timestamp"].min()

    global_avg_word_count = df["word_count"].mean()
    global_median_inactivity = df["inactivity_hours"].median()

    # For normalization
    recency_values = []
    freq_values = []
    inactivity_values = []
    engagement_values = []
    balance_values = []

    contact_metrics = {}

    for contact, group in df.groupby("contact_name"):

        group = group.sort_values("timestamp")

        # RECENCY
        last_time = group["timestamp"].max()
        days_since_last = (dataset_max_date - last_time).days

        # FREQUENCY
        active_days = (group["timestamp"].max() - group["timestamp"].min()).days + 1
        total_msgs = len(group)
        msgs_per_day = total_msgs / max(active_days, 1)

        # RESPONSIVENESS
        avg_inactivity = group["inactivity_hours"].mean()

        # ENGAGEMENT
        avg_word_count = group["word_count"].mean()

        # BALANCE
        user_msgs = group[group["is_user_sender"] == True].shape[0]
        other_msgs = group[group["is_user_sender"] == False].shape[0]

        if user_msgs + other_msgs == 0:
            balance_ratio = 0
        else:
            balance_ratio = min(user_msgs, other_msgs) / max(user_msgs, other_msgs)

        contact_metrics[contact] = {
            "days_since_last": days_since_last,
            "msgs_per_day": msgs_per_day,
            "avg_inactivity": avg_inactivity,
            "avg_word_count": avg_word_count,
            "balance_ratio": balance_ratio
        }

        recency_values.append(days_since_last)
        freq_values.append(msgs_per_day)
        inactivity_values.append(avg_inactivity)
        engagement_values.append(avg_word_count)
        balance_values.append(balance_ratio)

    # Normalization ranges
    rec_min, rec_max = min(recency_values), max(recency_values)
    freq_min, freq_max = min(freq_values), max(freq_values)
    inact_min, inact_max = min(inactivity_values), max(inactivity_values)
    eng_min, eng_max = min(engagement_values), max(engagement_values)
    bal_min, bal_max = min(balance_values), max(balance_values)

    # Calculate normalized health score
    for contact, metrics in contact_metrics.items():

        rec_score = 1 - normalize(metrics["days_since_last"], rec_min, rec_max)
        freq_score = normalize(metrics["msgs_per_day"], freq_min, freq_max)
        resp_score = 1 - normalize(metrics["avg_inactivity"], inact_min, inact_max)
        eng_score = normalize(metrics["avg_word_count"], eng_min, eng_max)
        bal_score = normalize(metrics["balance_ratio"], bal_min, bal_max)

        health_score = np.mean([
            rec_score,
            freq_score,
            resp_score,
            eng_score,
            bal_score
        ]) * 100

        # Risk classification based on dataset percentile
        if health_score >= 75:
            risk = "Strong"
        elif health_score >= 55:
            risk = "Stable"
        elif health_score >= 35:
            risk = "At Risk"
        else:
            risk = "Critical"

        results[contact] = {
            "health_score": round(health_score, 2),
            "risk_level": risk
        }

    return results


if __name__ == "__main__":

    print("📂 Loading processed dataset...")
    df = pd.read_csv(INPUT_FILE_PATH)

    print("🧠 Computing data-driven relationship health...")
    results = calculate_scores(df)

    with open(OUTPUT_FILE_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("🚀 Relationship health scoring complete.")
    print("Saved to mainData/relationship_health.json")