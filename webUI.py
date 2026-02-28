import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION & STYLING
# ==========================================

def get_risk_styling(score):
    """Returns the label and hex color based on the health score."""
    if score >= 80:
        return "Healthy", "#10B981" # Green
    elif score >= 60:
        return "Cooling", "#F59E0B" # Yellow
    elif score >= 40:
        return "At Risk", "#F97316" # Orange
    else:
        return "Critical", "#EF4444" # Red

def create_badge(text, color):
    """Generates HTML for a colored SaaS-style badge."""
    return f"""
    <div style="background-color: {color}20; color: {color}; 
                padding: 4px 12px; border-radius: 9999px; 
                display: inline-block; font-weight: 600; font-size: 0.85rem; 
                border: 1px solid {color}50;">
        {text}
    </div>
    """

# ==========================================
# DATA PROCESSING
# ==========================================

@st.cache_data(show_spinner=False)
def load_data(uploaded_file=None):
    """Loads JSON chat data from upload or default local file."""
    data = None
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
        except Exception as e:
            st.error(f"Error parsing uploaded JSON: {e}")
            return pd.DataFrame()
    else:
        # File path for your specific dataset
        file_path = os.path.join("mockData", "mockdata_Devaansh.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
        else:
            return pd.DataFrame() # Empty dataframe if no file found

    if data:
        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            # FIX APPLIED HERE: Safely parse dates and ignore bad formats
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Fill any unparseable dates with the current time to prevent crashes
            if df['timestamp'].isna().any():
                df['timestamp'] = df['timestamp'].fillna(pd.Timestamp.now())
                
            # Sort chronologically
            df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    return pd.DataFrame()

def compute_contact_metrics(df_contact, reference_date):
    """Computes base metrics for a single contact."""
    if df_contact.empty:
        return None
    
    last_interaction = df_contact['timestamp'].max()
    inactive_days = (reference_date - last_interaction).days
    
    total_msgs = len(df_contact)
    # Assuming 'me' is the primary user. Any other sender is a reply.
    replies = len(df_contact[df_contact['sender'] != 'me'])
    reply_ratio = replies / total_msgs if total_msgs > 0 else 0
    
    seven_days_ago = reference_date - timedelta(days=7)
    msgs_last_7_days = len(df_contact[df_contact['timestamp'] >= seven_days_ago])
    
    # Calculate consecutive initiations (approximation: trailing messages by 'me')
    recent_msgs = df_contact.tail(5)
    consecutive_me = 0
    for sender in reversed(recent_msgs['sender'].tolist()):
        if sender == 'me':
            consecutive_me += 1
        else:
            break

    return {
        "Last Interaction": last_interaction,
        "Inactive Days": max(0, inactive_days),
        "Reply Ratio": round(reply_ratio, 2),
        "Messages Last 7 Days": msgs_last_7_days,
        "Consecutive Initiations": consecutive_me
    }

def compute_all_scores(df):
    """Aggregates metrics and applies rule-based risk scoring."""
    if df.empty:
        return pd.DataFrame()

    # Use the latest message in the entire dataset as "today" to ensure 
    # metrics work cleanly with static/historical mock data.
    reference_date = df['timestamp'].max()
    
    contacts = df['contact'].unique()
    metrics_list = []

    for contact in contacts:
        contact_df = df[df['contact'] == contact]
        metrics = compute_contact_metrics(contact_df, reference_date)
        
        if metrics:
            score = 100
            if metrics["Inactive Days"] > 14:
                score -= 25
            if metrics["Reply Ratio"] < 0.4:
                score -= 20
            if metrics["Messages Last 7 Days"] < 3:
                score -= 15
            
            score = max(0, score) # Floor at 0
            risk_level, _ = get_risk_styling(score)
            
            metrics_list.append({
                "Contact": contact,
                "Health Score": score,
                "Risk Level": risk_level,
                "Last Interaction": metrics["Last Interaction"].strftime("%Y-%m-%d %H:%M"),
                "Reply Ratio": metrics["Reply Ratio"],
                "Inactive Days": metrics["Inactive Days"],
                "Messages Last 7 Days": metrics["Messages Last 7 Days"],
                "Consecutive Initiations": metrics["Consecutive Initiations"]
            })
            
    return pd.DataFrame(metrics_list)

# ==========================================
# UI COMPONENTS
# ==========================================

def render_dashboard():
    """Main rendering loop for the Streamlit UI."""
    st.set_page_config(
        page_title="Relationship Health Monitor", 
        page_icon="⚡", 
        layout="wide"
    )

    # 1. Header
    st.title("Agentic Chat Analyzer")
    st.markdown("### Relationship Health Monitor", unsafe_allow_html=True)
    st.divider()

    # 2. Sidebar Filters & Upload
    with st.sidebar:
        st.header("Settings & Filters")
        uploaded_file = st.file_uploader("Override Mock Data (JSON)", type=["json"])
        
        with st.spinner("Loading chat data..."):
            raw_df = load_data(uploaded_file)
            
        if raw_df.empty:
            st.warning("No data found. Please upload a JSON file or ensure `mockData/mockdata_Devaansh.json` exists.")
            return

        metrics_df = compute_all_scores(raw_df)
        
        st.divider()
        st.subheader("Filters")
        
        all_contacts = ["All"] + list(metrics_df['Contact'].unique())
        selected_contact_filter = st.selectbox("Select Contact", all_contacts)
        
        risk_options = ["All", "Healthy", "Cooling", "At Risk", "Critical"]
        selected_risk = st.selectbox("Risk Level", risk_options)
        
        min_date = raw_df['timestamp'].min().date()
        max_date = raw_df['timestamp'].max().date()
        
        # Safe Date Range handling in case all dates evaluate to the exact same day
        if min_date == max_date:
            date_range = st.date_input("Date Range", [min_date, max_date + timedelta(days=1)], min_value=min_date, max_value=max_date + timedelta(days=1))
        else:
            date_range = st.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Apply Filters to DataFrames
    filtered_metrics = metrics_df.copy()
    filtered_raw = raw_df.copy()

    if selected_contact_filter != "All":
        filtered_metrics = filtered_metrics[filtered_metrics['Contact'] == selected_contact_filter]
        filtered_raw = filtered_raw[filtered_raw['contact'] == selected_contact_filter]
        
    if selected_risk != "All":
        filtered_metrics = filtered_metrics[filtered_metrics['Risk Level'] == selected_risk]
        # Only keep raw messages for contacts that match the risk filter
        filtered_raw = filtered_raw[filtered_raw['contact'].isin(filtered_metrics['Contact'])]

    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (filtered_raw['timestamp'].dt.date >= start_date) & (filtered_raw['timestamp'].dt.date <= end_date)
        filtered_raw = filtered_raw.loc[mask]

    # Stop rendering if filters result in empty data
    if filtered_metrics.empty:
        st.info("No contacts match the current filter criteria.")
        return

    # 3. Top Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Contacts", len(filtered_metrics))
    with m2:
        avg_health = int(filtered_metrics['Health Score'].mean())
        st.metric("Average Health Score", avg_health)
    with m3:
        high_risk = len(filtered_metrics[filtered_metrics['Risk Level'].isin(['At Risk', 'Critical'])])
        st.metric("High Risk Contacts", high_risk)
    with m4:
        most_inactive = filtered_metrics.loc[filtered_metrics['Inactive Days'].idxmax()]
        st.metric("Most Inactive", f"{most_inactive['Contact']} ({most_inactive['Inactive Days']}d)")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Main Dashboard Layout (Sections A & B)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### Section A: Overview Table")
        # Format dataframe for display
        display_df = filtered_metrics[['Contact', 'Health Score', 'Risk Level', 'Last Interaction', 'Reply Ratio']].copy()
        st.dataframe(
            display_df.sort_values('Health Score', ascending=False),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown("#### Section B: Trend Chart")
        if not filtered_raw.empty:
            # Group by week and count messages
            trend_data = filtered_raw.copy()
            trend_data['Week'] = trend_data['timestamp'].dt.to_period('W').apply(lambda r: r.start_time)
            weekly_counts = trend_data.groupby('Week').size().reset_index(name='Message Count')
            
            # Using Streamlit's native line chart instead of Plotly
            chart_data = weekly_counts.set_index('Week')
            st.line_chart(chart_data, y='Message Count', color="#3B82F6")
        else:
            st.info("No timeline data available for the selected filters.")

    st.divider()

    # 5. Detail Views (Sections C & D)
    st.markdown("#### Focus View")
    
    # Default to the selected contact or the first one in the filtered list
    focus_contact = selected_contact_filter if selected_contact_filter != "All" else filtered_metrics.iloc[0]['Contact']
    
    contact_stats = filtered_metrics[filtered_metrics['Contact'] == focus_contact].iloc[0]
    contact_chat = filtered_raw[filtered_raw['contact'] == focus_contact].copy()

    detail_col, chat_col = st.columns([1, 2], gap="large")

    with detail_col:
        st.markdown(f"##### Section C: {focus_contact}'s Details")
        
        score = contact_stats['Health Score']
        label, color = get_risk_styling(score)
        
        st.markdown(f"<h1 style='color:{color}; margin-bottom: 0;'>{score}</h1>", unsafe_allow_html=True)
        st.markdown(create_badge(label, color), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write(f"**Last Interaction:** {contact_stats['Last Interaction']}")
        st.write(f"**Reply Ratio:** {contact_stats['Reply Ratio']}")
        st.write(f"**Messages Last 7 Days:** {contact_stats['Messages Last 7 Days']}")
        
        with st.expander("🔍 Explainability Metrics", expanded=False):
            st.write(f"**Days Inactive:** {contact_stats['Inactive Days']}")
            st.write(f"**Consecutive Initiations by You:** {contact_stats['Consecutive Initiations']}")
            st.write(f"**Sentiment Profile:** Neutral (Placeholder)")
            
            st.caption("Score Calculation:")
            st.caption("- Base: 100")
            if contact_stats['Inactive Days'] > 14: st.caption("- Inactive > 14 days: -25")
            if contact_stats['Reply Ratio'] < 0.4: st.caption("- Low reply ratio: -20")
            if contact_stats['Messages Last 7 Days'] < 3: st.caption("- Low recent volume: -15")

    with chat_col:
        st.markdown("##### Section D: Raw Chat Preview")
        if not contact_chat.empty:
            last_10 = contact_chat.tail(10)[['timestamp', 'sender', 'message']].copy()
            last_10['timestamp'] = last_10['timestamp'].dt.strftime('%b %d, %H:%M')
            st.dataframe(last_10, use_container_width=True, hide_index=True)
        else:
            st.info("No chat history found in the selected date range.")

    # 6. Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
        "Built for Hackathon Demo – Agentic Relationship Intelligence"
        "</p>", 
        unsafe_allow_html=True
    )

def main():
    render_dashboard()

if __name__ == "__main__":
    main()