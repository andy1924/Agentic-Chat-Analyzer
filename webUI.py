import streamlit as st
import pandas as pd
from datetime import timedelta
import os

# ==========================================
# LOAD CSV DATA
# ==========================================

def load_data():

    file_path = os.path.join("mainData", "whatsapp_unique_chats_5000.csv")

    if not os.path.exists(file_path):
        st.error("CSV file not found inside mainData/")
        return pd.DataFrame()

    df = pd.read_csv(file_path)

    # Combine date + time (DD/MM/YYYY + 12-hour time)
    df['timestamp'] = pd.to_datetime(
        df['date'] + " " + df['time'],
        format="%d/%m/%Y %I:%M %p",
        errors='coerce'
    )

    df = df.dropna(subset=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    return df


# ==========================================
# DETECT MAIN USER
# ==========================================

def detect_main_user(df):

    # If "You" exists, use it directly
    if "You" in df['sender'].unique():
        return "You"

    # Fallback: highest frequency participant
    counts = df['sender'].value_counts() + df['receiver'].value_counts()
    return counts.idxmax()


# ==========================================
# BUILD CONTACT COLUMN
# ==========================================

def add_contact_column(df, main_user):

    df['contact'] = df.apply(
        lambda row: row['receiver'] if row['sender'] == main_user else row['sender'],
        axis=1
    )

    return df


# ==========================================
# ANALYSIS ENGINE
# ==========================================

def analyze_contacts(df, main_user):

    reference_date = df['timestamp'].max()
    contacts = df['contact'].unique()
    results = []

    for contact in contacts:

        cdf = df[df['contact'] == contact]

        total = len(cdf)
        sent = len(cdf[cdf['sender'] == main_user])
        received = len(cdf[cdf['sender'] == contact])

        reply_ratio = received / total if total else 0

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

        # SCORING
        score = 100

        if inactive_days > 30:
            score -= 35
        elif inactive_days > 14:
            score -= 20

        if reply_ratio < 0.3:
            score -= 25
        elif reply_ratio < 0.5:
            score -= 15

        if msgs_last_week < 2:
            score -= 15

        if consecutive_you >= 3:
            score -= 10

        score = max(0, score)

        results.append({
            "Contact": contact,
            "Health Score": score,
            "Total Messages": total,
            "Sent By You": sent,
            "Received": received,
            "Reply Ratio": round(reply_ratio, 2),
            "Inactive Days": inactive_days,
            "Messages Last 7 Days": msgs_last_week,
            "Consecutive You": consecutive_you,
            "Last Interaction": last_interaction.strftime("%Y-%m-%d %H:%M")
        })

    return pd.DataFrame(results)


# ==========================================
# MAIN DASHBOARD
# ==========================================

def main():

    st.title("📊 Relationship Intelligence Dashboard")

    df = load_data()
    if df.empty:
        return

    main_user = detect_main_user(df)
    df = add_contact_column(df, main_user)

    st.success(f"Detected Main User: {main_user}")

    analysis_df = analyze_contacts(df, main_user)

    # NETWORK OVERVIEW
    st.header("Network Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Contacts", len(analysis_df))
    col2.metric("Average Health Score", int(analysis_df['Health Score'].mean()))
    col3.metric(
        "Most Inactive",
        analysis_df.sort_values("Inactive Days", ascending=False).iloc[0]['Contact']
    )

    st.dataframe(
        analysis_df.sort_values("Health Score", ascending=False),
        use_container_width=True
    )

    st.divider()

    # DETAILED ANALYSIS
    st.header("Detailed Contact Analysis")

    selected = st.selectbox("Select Contact", analysis_df['Contact'])
    person = analysis_df[analysis_df['Contact'] == selected].iloc[0]

    colA, colB = st.columns(2)
    # --- BOTTOM ROW: ACTIONABLE ADVICE ---
    #if st.button("Generate Draft Message"):
        #st.write("*(Draft message will appear here...)*")

    with colA:
        st.metric("Health Score", person["Health Score"])
        st.write("Total Messages:", person["Total Messages"])
        st.write("Reply Ratio:", person["Reply Ratio"])
        st.write("Inactive Days:", person["Inactive Days"])
        st.write("Messages Last 7 Days:", person["Messages Last 7 Days"])

    with colB:
        st.write("Sent By You:", person["Sent By You"])
        st.write("Received:", person["Received"])
        st.write("Consecutive You:", person["Consecutive You"])
        st.write("Last Interaction:", person["Last Interaction"])

    if st.button("AI Behaviour Insight"):
        # --- AI INTELLIGENCE (BEHAVIORAL) ---
        st.header("AI Behavioral Insights")

        colA, colB = st.columns(2)

        with colA:
            st.subheader("📝 Conversation Summary")
            st.info(
                "The conversation has been highly collaborative over the past 7 days. "
                "Both parties are actively engaging, though there was a slight drop in communication over the weekend. "
                "Overall tone remains supportive and forward-looking."
            )

        with colB:
            st.subheader("🚩 Behavioral Flags")
            st.success("✅ High reciprocal questioning (showing mutual interest).")
            st.warning("⚠️ User B has been using shorter sentences lately.")
            st.success("✅ Consistent daily check-ins.")

    st.subheader("Conversation History")

    chat = df[df['contact'] == selected][['timestamp', 'sender', 'message']]
    chat = chat.sort_values("timestamp", ascending=False)
    chat['timestamp'] = chat['timestamp'].dt.strftime('%b %d, %H:%M')

    st.dataframe(chat, height=400, use_container_width=True)



if __name__ == "__main__":
    main()