import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="RelateAI Dashboard", page_icon="⚡", layout="wide")

# --- HEADER ---
st.title("⚡ RelateAI: Relationship Intelligence System")
st.markdown("Automated social relationship management, behavioral scoring, and insights.")

# --- SIDEBAR (INPUT LAYER) ---
with st.sidebar:
    st.header("📂 1. Data Input")
    st.markdown("Upload chat export here.")

    uploaded_file = st.file_uploader("Upload WhatsApp/Telegram Chat (.txt or .csv)", type=["txt", "csv"])

    if uploaded_file:
        st.success("Chat loaded successfully!")
        st.spinner("Processing data...")

    st.divider()
    st.caption("Person 3: Wire this up to Person 1's parsing script later.")

# --- MOCK DATA TOGGLE ---
st.info("🟡 **UI Mode:** Currently displaying mock data while the backend is being connected.")

# --- TOP ROW: THE SCORECARD (HARD METRICS) ---
st.header("📊 2. Relationship Health Scorecard")
st.markdown("*Hard metrics fed by Person 1's data layer.*")

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Overall Health Score", value="78/100", delta="+5% this week")
col2.metric(label="Initiation Ratio", value="50/50", delta="Balanced", delta_color="off")
col3.metric(label="Avg Response Time", value="45 mins", delta="-10 mins (Faster)", delta_color="normal")
col4.metric(label="Sentiment Trend", value="Positive", delta="Stable", delta_color="off")

st.divider()

# --- MIDDLE ROW: AI INTELLIGENCE (BEHAVIORAL) ---
st.header("🧠 3. AI Behavioral Insights")
st.markdown("*Qualitative analysis fed by Person 2's LangChain Engine.*")

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

st.divider()

# --- BOTTOM ROW: ACTIONABLE ADVICE ---
st.header("🎯 4. Recommended Actions")
st.markdown(
    "> **AI Suggestion:** The other person responds best in the evenings. Try sending a casual check-in around 7:00 PM today referencing your last shared topic.")

if st.button("Generate Draft Message 🚀"):
    st.write("*(Draft message will appear here...)*")

