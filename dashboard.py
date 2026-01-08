import streamlit as st
import pandas as pd
import requests
import time

API_URL = "http://127.0.0.1:8000"
st.set_page_config(layout="wide", page_title="Unified Loyalty Agent")

# CSS for Enterprise UI
st.markdown("""
<style>
    .big-metric {font-size: 26px; font-weight: bold; color: #4CAF50;}
    .step-header {font-size: 20px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🛡️ Loyalty Command Center")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    
    app_mode = st.radio("Select Module:", [
        "🚀 Campaign Launchpad", 
        "📊 Live Monitoring", 
        "🕵️ Customer 360°"
    ])
    st.divider()

# ==========================================
# MODULE 1: CAMPAIGN LAUNCHPAD
# ==========================================
if app_mode == "🚀 Campaign Launchpad":
    st.title("🚀 Campaign Orchestrator")
    
    if 'camp_step' not in st.session_state: st.session_state['camp_step'] = 1
    if 'selected_seg' not in st.session_state: st.session_state['selected_seg'] = None
    if 'proposal' not in st.session_state: st.session_state['proposal'] = None

    # --- STEP 1: ANALYSIS ---
    if st.session_state['camp_step'] == 1:
        st.markdown("<div class='step-header'>1. AI Analysis & Segmentation</div>", unsafe_allow_html=True)
        st.info("The AI is continuously analyzing purchase history for behavioral anomalies.")
        
        uploaded_file = st.file_uploader("Upload Transaction Data (CSV)", type=["csv"], key="camp_upload")
        if uploaded_file:
            files = {"file": uploaded_file.getvalue()}
            try:
                requests.post(f"{API_URL}/upload_data", files=files)
                segments = requests.get(f"{API_URL}/analyze_segments").json()
                
                st.subheader("⚠️ Detected Behavioral Groups")
                cols = st.columns(2)
                
                for i, seg in enumerate(segments):
                    with cols[i]:
                        with st.container(border=True):
                            st.markdown(f"### {seg['name']}")
                            st.warning(f"**Trigger:** {seg['behavior_change']}")
                            st.write(f"**Audience:** {seg['size']} Customers")
                            st.write(f"**Avg Basket:** {seg['avg_basket']} MAD")
                            
                            if st.button(f"✨ Draft Strategy", key=f"btn_{i}"):
                                with st.spinner("🤖 CFO & Strategy Agents working..."):
                                    res = requests.post(f"{API_URL}/generate_campaign_proposal", json=seg).json()
                                    st.session_state['selected_seg'] = seg
                                    st.session_state['proposal'] = res
                                    st.session_state['camp_step'] = 2
                                    st.rerun()
            except Exception as e:
                st.error(f"Connection Error: {e}")

    # --- STEP 2: POST-VALIDATION FORM ---
    elif st.session_state['camp_step'] == 2:
        st.markdown("<div class='step-header'>2. Post-Validation & Edit</div>", unsafe_allow_html=True)
        
        prop = st.session_state['proposal']
        strat = prop['strategy']
        fin = prop['financials']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 Est. Participation", fin['est_participation_rate'])
        c2.metric("💰 Total Cost", f"{fin['total_campaign_cost']} MAD")
        c3.metric("📈 Est. ROI", f"{fin['estimated_roi']}x")
        
        st.divider()
        
        with st.container(border=True):
            st.subheader("📝 Campaign Configuration")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                msg = st.text_area("Message Content", value=strat['message'], height=120)
                vc1, vc2 = st.columns([1, 4])
                if vc1.button("🎙️ Voice"):
                    st.toast("Listening...")
                    time.sleep(1)
                    st.info("🗣️ Voice Command: 'Change incentive to 20% discount'")
                vc2.caption("Use voice to edit parameters.")

            with col2:
                ctype = st.selectbox("Channel", ["SMS", "Email", "Push"], index=0 if st.session_state['selected_seg']['recommended_channel'] == "SMS" else 1)
                incentive = st.text_input("Incentive", value=strat['incentive'])
                duration = st.number_input("Duration (Days)", value=strat.get('duration_days', 7))
            
            if st.button("🚀 Validate & Launch Campaign", type="primary"):
                payload = {
                    "segment_name": st.session_state['selected_seg']['name'],
                    "campaign_type": ctype,
                    "message": msg,
                    "incentive": incentive,
                    "duration": duration,
                    "est_roi": fin['estimated_roi'],
                    "total_cost": fin['total_campaign_cost']
                }
                requests.post(f"{API_URL}/launch_campaign", json=payload)
                st.session_state['camp_step'] = 1 
                st.balloons()
                st.success("Campaign Launched! Redirecting to Monitor...")
                time.sleep(2)
                st.rerun()

# ==========================================
# MODULE 2: LIVE MONITORING (FIXED CHART)
# ==========================================
elif app_mode == "📊 Live Monitoring":
    st.title("📊 Real-Time Campaign Monitor")
    
    if st.button("🔄 Refresh Live Data"):
        st.toast("Syncing with POS System...")
    
    try:
        campaigns = requests.get(f"{API_URL}/monitor_campaigns").json()
        
        if not campaigns:
            st.info("No active campaigns. Go to 'Campaign Launchpad' to start one.")
        else:
            camp_names = [f"ID {c['id']}: {c['config']['segment_name']}" for c in campaigns]
            selected_camp_str = st.selectbox("Select Active Campaign:", camp_names, index=len(camp_names)-1)
            
            selected_id = int(selected_camp_str.split(":")[0].replace("ID ", ""))
            c = next(item for item in campaigns if item["id"] == selected_id)
            live = c['live_data']
            
            st.divider()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Participants", live['participants'], delta="Active")
            m2.metric("Transactions", live['transactions'])
            m3.metric("Points Given", live['points_distributed'])
            
            st.divider()
            
            f1, f2, f3 = st.columns(3)
            f1.metric("Revenue Generated", f"{live['revenue']} MAD")
            f2.metric("Actual Cost", f"{live['actual_cost']} MAD")
            
            delta_roi = round(live['actual_roi'] - c['config']['est_roi'], 2)
            f3.metric("Actual ROI", f"{live['actual_roi']}x", delta=f"{delta_roi}x variance")
            
            # --- CHART FIX: WIDE FORMAT ---
            st.markdown("### 📈 ROI Trend: Forecast vs Reality")
            
            # Creating 2 columns instead of 2 rows ensures Streamlit applies 2 colors correctly
            chart_data = pd.DataFrame({
                "Estimated ROI": [c['config']['est_roi']],
                "Actual ROI": [live['actual_roi']]
            })
            st.bar_chart(chart_data, color=["#FF4B4B", "#4CAF50"])

    except Exception as e:
        st.error(f"Monitoring Unavailable: {e}")

# ==========================================
# MODULE 3: CUSTOMER 360
# ==========================================
elif app_mode == "🕵️ Customer 360°":
    st.title("🕵️ Individual Customer Detective")
    
    uploaded_file = st.file_uploader("Upload Customer DB (CSV)", type=["csv"], key="indiv_upload")
    if uploaded_file:
        if st.button("Process Database"):
            files = {"file": uploaded_file.getvalue()}
            requests.post(f"{API_URL}/upload_data", files=files)
            st.success("Database Indexed!")
            st.session_state['db_loaded'] = True
            
    if st.session_state.get('db_loaded'):
        st.divider()
        c1, c2 = st.columns(2)
        
        churn_ids = requests.get(f"{API_URL}/get_ids_by_status/Churned").json()
        active_ids = requests.get(f"{API_URL}/get_ids_by_status/Active").json()
        
        cid = None
        with c1:
            sel_churn = st.selectbox("🚨 Churned List", ["Select..."] + churn_ids)
            if sel_churn != "Select...": cid = sel_churn
        with c2:
            sel_active = st.selectbox("✅ Active List", ["Select..."] + active_ids)
            if sel_active != "Select...": cid = sel_active
            
        if cid:
            c = requests.get(f"{API_URL}/get_customer_details/{cid}").json()
            
            st.markdown(f"### Client #{c['ClientID']}")
            s1, s2, s3 = st.columns(3)
            s1.metric("Status", c['Status'])
            s2.metric("Total Spend", f"{c['Total_Spend']} MAD")
            s3.metric("Sentiment", c.get('Sentiment', 'Unknown'))
            st.info(f"📝 Feedback: {c.get('Feedback', 'None')}")
            
            if st.button("⚡ Generate Solution"):
                with st.spinner("Analyzing..."):
                    sol = requests.post(f"{API_URL}/agent/individual_solution", json={"customer_data": c}).json()
                    st.success("Solution Generated!")
                    
                    k1, k2 = st.columns(2)
                    k1.markdown(f"**Root Cause:** {sol['root_cause']}")
                    k1.markdown(f"**Strategy:** {sol['solution_strategy']}")
                    
                    k2.text_area("Draft Message", sol['drafted_message'], height=100)
                    k2.success(f"Incentive: {sol['recommended_incentive']}")