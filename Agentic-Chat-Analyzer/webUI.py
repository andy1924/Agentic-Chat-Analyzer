import pandas as pd
from datetime import timedelta
from relationCalculator import calculate_scores

# ==========================================
# DATA PROCESSING BACKEND
# ==========================================

def load_data(file_obj):
    """
    Loads and validates the chat dataset.
    pure data processing, no UI elements.
    """
    try:
        if file_obj.name.endswith('.csv'):
            df = pd.read_csv(file_obj)
        else:
            raise ValueError("Unsupported format. Please upload a CSV file.")
            
        required_cols = ['date', 'time', 'sender', 'message']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")

        # Combine date + time
        df['timestamp'] = pd.to_datetime(
            df['date'] + " " + df['time'],
            format="%d/%m/%Y %I:%M %p",
            errors='coerce'
        )

        df = df.dropna(subset=['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df

    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")


def detect_main_user(df):
    """Identifies the primary user of the chat export."""
    if "You" in df['sender'].unique():
        return "You"

    # Fallback: highest frequency participant
    if 'receiver' in df.columns:
        counts = df['sender'].value_counts() + df['receiver'].value_counts()
        return counts.idxmax()
    else:
        return df['sender'].value_counts().idxmax()


def add_contact_column(df, main_user):
    """Creates a unified 'contact' column for grouping."""
    if 'receiver' in df.columns:
        df['contact'] = df.apply(
            lambda row: row['receiver'] if row['sender'] == main_user else row['sender'],
            axis=1
        )
    else:
        # Fallback if no receiver column
        df['contact'] = df['sender'].apply(lambda x: x if x != main_user else "Unknown")
    return df


def prepare_for_calculator(df, main_user):
    """
    Transforms the dataset into the format expected by relationCalculator.py.
    Also identifies valid interactions (excluding system/media).
    """
    calc_df = df.copy()
    calc_df['contact_name'] = calc_df['contact']
    calc_df['is_user_sender'] = calc_df['sender'] == main_user
    
    # Exclude system/media for valid interactions
    media_keywords = ['<Media omitted>', 'image omitted', 'audio omitted', 'video omitted', 'sticker omitted', 'null']
    calc_df['is_media'] = calc_df['message'].astype(str).apply(
        lambda m: any(kw in m for kw in media_keywords) or m.strip() == ""
    )
    
    calc_df['word_count'] = calc_df['message'].astype(str).apply(lambda m: len(m.split()) if m else 0)
    
    # Calculate inactivity hours
    calc_df = calc_df.sort_values(['contact', 'timestamp'])
    calc_df['prev_timestamp'] = calc_df.groupby('contact')['timestamp'].shift(1)
    calc_df['inactivity_hours'] = (calc_df['timestamp'] - calc_df['prev_timestamp']).dt.total_seconds() / 3600.0
    
    # Separating raw vs valid user-to-user interaction
    valid_df = calc_df[~calc_df['is_media']]
    
    return calc_df, valid_df


def analyze_contacts(df, main_user):
    """
    Analyzes each contact computationally, running the mathematically-corrected
    calculate_scores from relationCalculator dynamically on the uploaded dataset.
    """
    reference_date = df['timestamp'].max()
    contacts = df['contact'].unique()
    
    # Dynamically generate advanced scores internally instead of static JSON
    calc_df, valid_df = prepare_for_calculator(df, main_user)
    advanced_scores = calculate_scores(calc_df)
    
    results = []

    for contact in contacts:
        cdf = df[df['contact'] == contact]
        vdf = valid_df[valid_df['contact'] == contact]

        total = len(cdf)
        valid_total = len(vdf)
        
        # Interaction balance based purely on valid texts
        sent_valid = len(vdf[vdf['sender'] == main_user])
        received_valid = len(vdf[vdf['sender'] == contact])

        reply_ratio = received_valid / valid_total if valid_total else 0

        last_interaction = cdf['timestamp'].max()
        inactive_days = (reference_date - last_interaction).days

        last_week = reference_date - timedelta(days=7)
        msgs_last_week = len(cdf[cdf['timestamp'] >= last_week])

        # Consecutive initiations
        recent = cdf.tail(10)
        consecutive_you = 0

        for sender in reversed(recent['sender'].tolist()):
            if sender == main_user:
                consecutive_you += 1
            else:
                break

        # FETCH ADVANCED SCORING DATA
        if contact in advanced_scores:
            score = advanced_scores[contact].get("health_score", 0)
            risk_level = advanced_scores[contact].get("risk_level", "Unknown")
        else:
            # Fallback for minor/edge-case contacts
            score = 0.0
            risk_level = "No Data"

        results.append({
            "Contact": contact,
            "Health Score": score,
            "Risk Level": risk_level,
            "Total Messages": total,
            "Valid Interactions": valid_total,
            "Sent By You": sent_valid,
            "Received": received_valid,
            "Reply Ratio": round(reply_ratio, 2),
            "Inactive Days": inactive_days,
            "Messages Last 7 Days": msgs_last_week,
            "Consecutive You": consecutive_you,
            "Last Interaction": last_interaction.strftime("%Y-%m-%d %H:%M")
        })

    return pd.DataFrame(results)