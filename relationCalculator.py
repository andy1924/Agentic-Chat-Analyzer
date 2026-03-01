import pandas as pd
import numpy as np
import json

# -----------------------------------
# CONFIG
# -----------------------------------
INPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"
OUTPUT_FILE_PATH = "mainData/relationship_health.json"


def calculate_scores(df):
    results = {}

    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Global dataset metrics for imputation (fallback for missing values)
    dataset_max_date = df["timestamp"].max()
    global_inactivity_median = df["inactivity_hours"].median()
    global_word_median = df["word_count"].median()

    contact_metrics = {}

    for contact, group in df.groupby("contact_name"):

        group = group.sort_values("timestamp")

        # -----------------------------------
        # RECENCY (Exponential decay)
        # Prevents old relationships from retaining high scores
        # -----------------------------------
        last_time = group["timestamp"].max()
        days_since_last = (dataset_max_date - last_time).days
        # Decay factor: loses ~63% power after 30 days
        recency_score = np.exp(-days_since_last / 30.0)

        # -----------------------------------
        # FREQUENCY (Log-scaled messages per day)
        # Dampens extreme outliers (e.g. 500 msgs/day) while preserving magnitude
        # -----------------------------------
        active_days = max((group["timestamp"].max() - group["timestamp"].min()).days + 1, 1)
        msgs_per_day = len(group) / active_days
        freq_score = np.log1p(msgs_per_day)

        # -----------------------------------
        # RESPONSIVENESS (Inverse scaling of median inactivity)
        # Impute missing with global median to avoid arbitrary fallback skew
        # -----------------------------------
        inactivity = group["inactivity_hours"].median()
        if pd.isnull(inactivity):
            inactivity = global_inactivity_median

        # Closer to 0 inactivity -> closer to 1 score
        resp_score = 1.0 / (1.0 + inactivity)

        # -----------------------------------
        # ENGAGEMENT (Log-scaled word count)
        # Impute missing with global median
        # -----------------------------------
        avg_word_count = group["word_count"].mean()
        if pd.isnull(avg_word_count):
            avg_word_count = global_word_median

        eng_score = np.log1p(avg_word_count)

        # -----------------------------------
        # BALANCE (Message symmetry ratio)
        # 1.0 is perfectly balanced, 0.0 is completely one-sided
        # -----------------------------------
        user_msgs = (group["is_user_sender"] == True).sum()
        other_msgs = (group["is_user_sender"] == False).sum()

        if user_msgs + other_msgs == 0:
            bal_score = 0.0
        else:
            bal_score = min(user_msgs, other_msgs) / max(user_msgs, other_msgs)

        contact_metrics[contact] = {
            "rec": recency_score,
            "freq": freq_score,
            "resp": resp_score,
            "eng": eng_score,
            "bal": bal_score
        }

    # -----------------------------------
    # NORMALIZATION (0-1 min-max scaling ON TRANSFORMED METRICS)
    # This prepares the metrics to be weighted correctly without ranking compression
    # -----------------------------------
    metrics_df = pd.DataFrame.from_dict(contact_metrics, orient="index")

    # Handle edge case where max == min by filling NaN with 0 after division
    metrics_df = (metrics_df - metrics_df.min()) / (metrics_df.max() - metrics_df.min())
    metrics_df = metrics_df.fillna(0.0)

    # -----------------------------------
    # WEIGHTING
    # Weights sum to 1.0
    # -----------------------------------
    weights = {
        "rec": 0.30,  # Recency
        "freq": 0.20,  # Frequency
        "resp": 0.15,  # Responsiveness
        "eng": 0.15,  # Engagement
        "bal": 0.20  # Balance symmetry
    }

    # Calculate final health score on a 0-100 scale
    metrics_df["health_score"] = (
                                         metrics_df["rec"] * weights["rec"] +
                                         metrics_df["freq"] * weights["freq"] +
                                         metrics_df["resp"] * weights["resp"] +
                                         metrics_df["eng"] * weights["eng"] +
                                         metrics_df["bal"] * weights["bal"]
                                 ) * 100.0

    # -----------------------------------
    # RISK CLASSIFICATION (Percentile-based purely on FINAL score)
    # This ensures relative statistical consistency
    # -----------------------------------
    final_score_percentiles = metrics_df["health_score"].rank(pct=True)

    for contact in metrics_df.index:
        score = metrics_df.at[contact, "health_score"]
        p = final_score_percentiles[contact]

        # Use percentiles to determine brackets based on aggregate population
        if p >= 0.75:
            risk = "Strong"
        elif p >= 0.50:
            risk = "Stable"
        elif p >= 0.30:
            risk = "At Risk"
        else:
            risk = "Critical"

        results[contact] = {
            "health_score": round(score, 2),
            "risk_level": risk
        }

    return results


# -----------------------------------
# MAIN EXECUTION
# -----------------------------------
if __name__ == "__main__":
    print("📂 Loading processed dataset...")
    df = pd.read_csv(INPUT_FILE_PATH)

    print("🧠 Computing mathematically-corrected relationship health scores...")
    results = calculate_scores(df)

    with open(OUTPUT_FILE_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("🚀 Relationship health scoring complete.")
    print(f"Saved to {OUTPUT_FILE_PATH}")
import pandas as pd
import numpy as np
import json

# -----------------------------------
# CONFIG
# -----------------------------------
INPUT_FILE_PATH = "mainData/processed_chat_dataset.csv"
OUTPUT_FILE_PATH = "mainData/relationship_health.json"


def calculate_scores(df):

    results = {}

    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Global dataset metrics for imputation (fallback for missing values)
    dataset_max_date = df["timestamp"].max()
    global_inactivity_median = df["inactivity_hours"].median()
    global_word_median = df["word_count"].median()

    contact_metrics = {}

    for contact, group in df.groupby("contact_name"):

        group = group.sort_values("timestamp")

        # -----------------------------------
        # RECENCY (Exponential decay)
        # Prevents old relationships from retaining high scores
        # -----------------------------------
        last_time = group["timestamp"].max()
        days_since_last = (dataset_max_date - last_time).days
        # Decay factor: loses ~63% power after 30 days
        recency_score = np.exp(-days_since_last / 30.0)

        # -----------------------------------
        # FREQUENCY (Log-scaled messages per day)
        # Dampens extreme outliers (e.g. 500 msgs/day) while preserving magnitude
        # -----------------------------------
        active_days = max((group["timestamp"].max() - group["timestamp"].min()).days + 1, 1)
        msgs_per_day = len(group) / active_days
        freq_score = np.log1p(msgs_per_day)

        # -----------------------------------
        # RESPONSIVENESS (Inverse scaling of median inactivity)
        # Impute missing with global median to avoid arbitrary fallback skew
        # -----------------------------------
        inactivity = group["inactivity_hours"].median()
        if pd.isnull(inactivity):
            inactivity = global_inactivity_median

        # Closer to 0 inactivity -> closer to 1 score
        resp_score = 1.0 / (1.0 + inactivity)

        # -----------------------------------
        # ENGAGEMENT (Log-scaled word count)
        # Impute missing with global median
        # -----------------------------------
        avg_word_count = group["word_count"].mean()
        if pd.isnull(avg_word_count):
            avg_word_count = global_word_median

        eng_score = np.log1p(avg_word_count)

        # -----------------------------------
        # BALANCE (Message symmetry ratio)
        # 1.0 is perfectly balanced, 0.0 is completely one-sided
        # -----------------------------------
        user_msgs = (group["is_user_sender"] == True).sum()
        other_msgs = (group["is_user_sender"] == False).sum()

        if user_msgs + other_msgs == 0:
            bal_score = 0.0
        else:
            bal_score = min(user_msgs, other_msgs) / max(user_msgs, other_msgs)

        contact_metrics[contact] = {
            "rec": recency_score,
            "freq": freq_score,
            "resp": resp_score,
            "eng": eng_score,
            "bal": bal_score
        }

    # -----------------------------------
    # NORMALIZATION (0-1 min-max scaling ON TRANSFORMED METRICS)
    # This prepares the metrics to be weighted correctly without ranking compression
    # -----------------------------------
    metrics_df = pd.DataFrame.from_dict(contact_metrics, orient="index")

    # Handle edge case where max == min by filling NaN with 0 after division
    metrics_df = (metrics_df - metrics_df.min()) / (metrics_df.max() - metrics_df.min())
    metrics_df = metrics_df.fillna(0.0)

    # -----------------------------------
    # WEIGHTING
    # Weights sum to 1.0
    # -----------------------------------
    weights = {
        "rec": 0.30,   # Recency
        "freq": 0.20,  # Frequency
        "resp": 0.15,  # Responsiveness
        "eng": 0.15,   # Engagement
        "bal": 0.20    # Balance symmetry
    }

    # Calculate final health score on a 0-100 scale
    metrics_df["health_score"] = (
        metrics_df["rec"] * weights["rec"] +
        metrics_df["freq"] * weights["freq"] +
        metrics_df["resp"] * weights["resp"] +
        metrics_df["eng"] * weights["eng"] +
        metrics_df["bal"] * weights["bal"]
    ) * 100.0

    # -----------------------------------
    # RISK CLASSIFICATION (Percentile-based purely on FINAL score)
    # This ensures relative statistical consistency
    # -----------------------------------
    final_score_percentiles = metrics_df["health_score"].rank(pct=True)

    for contact in metrics_df.index:
        score = metrics_df.at[contact, "health_score"]
        p = final_score_percentiles[contact]

        # Use percentiles to determine brackets based on aggregate population
        if p >= 0.75:
            risk = "Strong"
        elif p >= 0.50:
            risk = "Stable"
        elif p >= 0.30:
            risk = "At Risk"
        else:
            risk = "Critical"

        results[contact] = {
            "health_score": round(score, 2),
            "risk_level": risk
        }

    return results


# -----------------------------------
# MAIN EXECUTION
# -----------------------------------
if __name__ == "__main__":

    print("📂 Loading processed dataset...")
    df = pd.read_csv(INPUT_FILE_PATH)

    print("🧠 Computing mathematically-corrected relationship health scores...")
    results = calculate_scores(df)

    with open(OUTPUT_FILE_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("🚀 Relationship health scoring complete.")
    print(f"Saved to {OUTPUT_FILE_PATH}")