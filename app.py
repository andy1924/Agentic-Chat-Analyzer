import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="RelateAI Dashboard", layout="wide")

# --- HEADER ---
st.title("RelateAI: Relationship Intelligence System")
st.markdown("Automated social relationship management, behavioral scoring, and insights.")

# --- SIDEBAR (INPUT LAYER) ---
with st.sidebar:
    st.header("📂 Data Input")
    st.markdown("Upload chat export here.")

    uploaded_file = st.file_uploader("Upload WhatsApp/Telegram Chat (.txt or .csv)", type=["txt", "csv"])

    if uploaded_file:
        st.success("Chat loaded successfully!")
        st.spinner("Processing data...")

    st.divider()

# --- TOP ROW: THE SCORECARD (HARD METRICS) ---
st.header("Relationship Health Scorecard")

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Overall Health Score", value="78/100", delta="+5% this week")
col2.metric(label="Initiation Ratio", value="50/50", delta="Balanced", delta_color="off")
col3.metric(label="Avg Response Time", value="45 mins", delta="-10 mins (Faster)", delta_color="normal")
col4.metric(label="Sentiment Trend", value="Positive", delta="Stable", delta_color="off")

st.divider()


from webUI import main

if __name__ == "__main__":
    main()