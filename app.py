import streamlit as st
import pandas as pd
from webUI import load_data, detect_main_user, add_contact_column, analyze_contacts
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="RelateAI Dashboard", layout="wide")


# --- CACHED DATA PROCESSING ---
@st.cache_data
def process_uploaded_file(uploaded_file):
    """Processes the uploaded file robustly through our separated backend."""
    df = load_data(uploaded_file)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), ""

    main_user = detect_main_user(df)
    df_contacts = add_contact_column(df, main_user)
    analysis_df = analyze_contacts(df_contacts, main_user)

    return df_contacts, analysis_df, main_user


# --- HEADER ---
st.title("RelateAI: Relationship Intelligence System")
st.markdown("Automated social relationship management, behavioral scoring, and insights.")

# --- SIDEBAR (INPUT LAYER) ---
with st.sidebar:
    st.header("📂 Data Input")
    st.markdown("Upload your structured chat export (.csv) here.")

    uploaded_file = st.file_uploader("Upload Chat CSV Object", type=["csv"])

    if uploaded_file:
        # Spinner as a context manager ensures accurate feedback
        with st.spinner("Analyzing semantics and computing health matrix..."):
            try:
                df_contacts, analysis_df, main_user = process_uploaded_file(uploaded_file)
                if df_contacts.empty:
                    st.error("The uploaded file did not contain valid data or columns.")
                    st.stop()
                st.success(f"Chat loaded successfully! (Detected User: {main_user})")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.stop()
    else:
        st.info("Currently the app is set to pre-uploaded synthetic data, so upload will not work!!")
        st.info("UPLOADS WORK LOACALLY")

        import os

        demo_path = os.path.join("mainData", "whatsapp_unique_chats_5000.csv")
        try:
            with open(demo_path, "r", encoding="utf-8") as f:
                df_contacts, analysis_df, main_user = process_uploaded_file(f)
        except Exception as e:
            st.error(f"Demo file not found or invalid: {str(e)}")
            st.stop()

    st.divider()

# --- SCORECARD METRICS (Statistically Truthful Data) ---
# Ensure variables exist before rendering dashboard components
if 'analysis_df' in locals() and not analysis_df.empty:

    # Fixing the mathematical aggregation (Median avoids extreme outlier distortion)
    avg_health_score = int(analysis_df['Health Score'].median())

    total_sent_valid = analysis_df['Sent By You'].sum()
    total_received_valid = analysis_df['Received'].sum()
    total_msgs_valid = total_sent_valid + total_received_valid

    # Interaction balance logic skips system/media blank messages
    sent_pct = int((total_sent_valid / total_msgs_valid) * 100) if total_msgs_valid > 0 else 50
    recv_pct = 100 - sent_pct

    avg_inactive_days = round(analysis_df['Inactive Days'].median(), 1)
    total_contacts = len(analysis_df)

    # --- TOP ROW: THE SCORECARD (HARD METRICS) ---
    st.header("Global Relationship Health Scorecard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Overall Health Score", value=f"{avg_health_score}/100",
                help="Median relationship health across the network.")
    col2.metric(label="Network Interaction Balance", value=f"{sent_pct}% / {recv_pct}%",
                help="Percentage of valid messages sent by you vs received.")
    col3.metric(label="Avg Inactivity Gap", value=f"{avg_inactive_days} days",
                help="Median inactivity gap across all networks.")
    col4.metric(label="Valid Contacts Analyzed", value=total_contacts)

    st.divider()

    # --- NETWORK OVERVIEW ---
    st.header("Network Overview")

    st.metric(
        "Most Inactive Network Gap",
        analysis_df.sort_values("Inactive Days", ascending=False).iloc[0]['Contact'] if not analysis_df.empty else "N/A"
    )

    st.dataframe(
        analysis_df.sort_values("Health Score", ascending=False),
        use_container_width=True
    )

    st.divider()

    # --- DETAILED ANALYSIS ---
    st.header("Detailed Contact Analysis")

    selected = st.selectbox("Select Contact", analysis_df['Contact'])
    person = analysis_df[analysis_df['Contact'] == selected].iloc[0]

    colA, colB = st.columns(2)

    with colA:
        st.metric("Health Score", person["Health Score"])
        st.metric("Risk Level", person["Risk Level"])
        st.write("Total Messages (Including Media):", person["Total Messages"])
        st.write("Valid Text Interactions:", person["Valid Interactions"])
        st.write("Reply Ratio (Valid Texts):", f"{person['Reply Ratio'] * 100:.0f}%")
        st.write("Inactive Days:", person["Inactive Days"])

    with colB:
        st.write("Sent By You (Valid):", person["Sent By You"])
        st.write("Received (Valid):", person["Received"])
        st.write("Consecutive You:", person["Consecutive You"])
        st.write("Messages Last 7 Days:", person["Messages Last 7 Days"])
        st.write("Last Interaction:", person["Last Interaction"])

    st.divider()

    def load_behavioral_data():
        file_path = "mainData/analyzedResults.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return None


    data = load_behavioral_data()

    if data:
        # 1. Selection logic (since the JSON has multiple users like Alex, John, etc.)
        user_names = [user["analyzed_user"] for user in data]
        selected_user_name = st.selectbox("Select User to Analyze", user_names)

        # Get the specific data for the selected user
        user_data = next(item for item in data if item["analyzed_user"] == selected_user_name)

        if st.button("AI Behaviour Insight"):
            st.header(f"AI Behavioral Insights: {selected_user_name}")

            colA, colB = st.columns(2)

            with colA:
                st.subheader("📝 Conversation Summary")
                # Combining Style, Baseline, and Trend for a comprehensive summary
                summary_text = (
                    f"**Communication Style:** {user_data['communication_style']}.  \n"
                    f"**Emotional Baseline:** {user_data['emotional_baseline']}.  \n"
                    f"**Trend:** {user_data['engagement_trend']}.  \n\n"
                    f"**Advice:** {user_data['interaction_advice']}"
                )
                st.info(summary_text)

            with colB:
                st.subheader("🚩 Behavioral Flags")
                for flag in user_data["behavioral_flags"]:
                    st.success(f"✅ {flag}")

                # Additional metric display
                st.write(f"**Messages Analyzed:** {user_data['messages_analyzed']}")
                st.write(f"**Total Volume:** {user_data['total_messages_sent']} messages")

            # Optional: Display Reminders below
            with st.expander("📅 Suggested Reminders/Actions"):
                for reminder in user_data["suggested_reminders"][:5]:  # Show top 5
                    st.write(f"**{reminder['event_title']}** ({reminder['datetime_context']})")
                    st.caption(reminder['description'])
    else:
        st.error("Could not find analyzedResults.json in mainData folder.")

    st.subheader("Conversation History")

    chat = df_contacts[df_contacts['contact'] == selected][['timestamp', 'sender', 'message']]
    chat = chat.sort_values("timestamp", ascending=False)
    chat['timestamp'] = chat['timestamp'].dt.strftime('%b %d, %H:%M')

    st.dataframe(chat, height=400, use_container_width=True)