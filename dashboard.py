import streamlit as st
import pandas as pd
import requests
import time

# Configuration
API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide", page_title="Antavo AI Agent")

# --- IMPROVED CSS FOR DARK MODE VISIBILITY ---
st.markdown("""
<style>
    /* Metrics Styling */
    .big-metric {font-size: 30px; font-weight: bold; color: #4CAF50;}
    
    /* Tab Container Gap */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    /* Unselected Tabs - High Contrast for Dark Mode */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1E1E1E; /* Dark Grey Background */
        color: #FFFFFF; /* Bright White Text */
        border: 1px solid #4a4a4a; /* Subtle Border */
        border-radius: 8px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    /* Selected Tab - Bright Green */
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
        border: 1px solid #4CAF50;
    }

    /* Hover Effect */
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #4CAF50;
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar: Industry Context Switcher
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=50)
    st.title("Enterprise Loyalty Cloud")
    industry = st.selectbox("Select Industry Vertical", ["Supermarket", "Oil & Gas", "Banking"])
    st.info(f"Context loaded: **{industry}**")
    st.markdown("---")
    st.write("Logged in as: **Marketing Manager**")

st.header(f"🤖 AI Loyalty Agent - {industry} Edition")

# --- Tabs for the Workflow ---
tab1, tab2, tab3 = st.tabs(["1. AI Analysis & Proposals", "2. Validation & Launch", "3. Real-Time Monitor"])

# --- TAB 1: Analysis ---
with tab1:
    st.subheader("Detected Behavioral Segments")
    
    if st.button("🔄 Scan Customer Base"):
        try:
            # 1. Fetch Segments
            segments = requests.get(f"{API_URL}/data/segments", params={"industry": industry}).json()
            st.session_state['segments'] = segments  # Save to memory
        except:
            st.error("Backend offline. Run uvicorn api:app...")

    if 'segments' in st.session_state:
        # Display Segments in a Grid
        cols = st.columns(3)
        for i, seg in enumerate(st.session_state['segments']):
            with cols[i]:
                # Card Styling using standard markdown
                st.markdown(f"### 👥 {seg['segment_name']}")
                st.warning(f"⚠️ {seg['behavior_change']}")
                st.write(f"**Size:** {seg['size']} customers")
                st.write(f"**Avg Value:** ${seg['avg_value']}")
                
                if st.button(f"Generate Campaign for {i}", key=f"btn_{i}"):
                    with st.spinner("AI is calculating ROI and strategy..."):
                        # 2. Call AI Agent
                        response = requests.post(f"{API_URL}/agent/plan_campaign", json=seg)
                        st.session_state['draft_campaign'] = response.json()
                        st.toast("Campaign Drafted! Go to Tab 2.", icon="✅")

# --- TAB 2: Validation (Pre-filled Form) ---
with tab2:
    if 'draft_campaign' in st.session_state:
        draft = st.session_state['draft_campaign']
        
        st.subheader("📝 Validate AI Proposal")
        
        # Split into two columns: Metrics & Form
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("### AI Predictions")
            st.metric("Estimated ROI", f"{draft['estimated_roi']}x")
            st.metric("Total Cost", f"${draft['total_cost']:,}")
            st.metric("Est. Participation", f"{int(draft['estimated_participation']*100)}%")
            
        with c2:
            # --- FIX: REMOVED st.form WRAPPER TO FIX BUTTON ERROR ---
            st.markdown("### Campaign Configuration")
            
            # Helper logic to find index safely
            options = ["SMS", "Push", "Email"]
            default_idx = 0
            if draft.get("campaign_type") in options:
                default_idx = options.index(draft.get("campaign_type"))

            new_channel = st.selectbox("Channel", options, index=default_idx)
            new_incentive = st.text_input("Incentive", value=draft['incentive'])
            
            # Message + Mic Button
            st.markdown("### Message Content")
            msg_col, mic_col = st.columns([6, 1])
            with msg_col:
                new_msg = st.text_area("Edit Message", value=draft['message'], height=100, label_visibility="collapsed")
            with mic_col:
                if st.button("🎙️", help="Simulate Voice Command"):
                    st.toast("Listening... (Simulating Voice Input)", icon="🎤")
                    time.sleep(1)
                    st.toast("Voice Command Processed", icon="✅")
            
            new_duration = st.slider("Duration (Days)", 1, 30, draft['duration_days'])
            
            st.divider()
            
            # Changed to regular button (Primary Style)
            if st.button("🚀 Validate & Launch Campaign", type="primary"):
                # Update draft with edited values
                draft['campaign_type'] = new_channel
                draft['message'] = new_msg
                draft['incentive'] = new_incentive
                
                # 3. Launch
                try:
                    res = requests.post(f"{API_URL}/campaign/launch", json=draft)
                    if res.status_code == 200:
                        st.success("Campaign Successfully Launched!")
                        st.balloons()
                except Exception as e:
                    st.error(f"Launch failed: {e}")
    else:
        st.info("👈 Please select a segment in 'AI Analysis' first.")

# --- TAB 3: Real-Time Monitor ---
with tab3:
    st.subheader("📊 Live Campaign Dashboard")
    
    if st.button("Refresh Live Data"):
        try:
            live_data = requests.get(f"{API_URL}/campaign/dashboard").json()
            st.session_state['live_data'] = live_data
        except:
            st.error("No active campaigns.")

    if 'live_data' in st.session_state and st.session_state['live_data']:
        df = pd.DataFrame(st.session_state['live_data'])
        
        # Visuals
        st.dataframe(df[['segment_name', 'campaign_type', 'participants', 'revenue', 'status']], use_container_width=True)
        
        # Charts
        st.bar_chart(df, x="segment_name", y="revenue", color="#4CAF50")
    else:
        st.write("No campaigns currently active.")