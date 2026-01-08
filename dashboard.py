import streamlit as st
import pandas as pd
import requests
import time

API_URL = "http://127.0.0.1:8000"
st.set_page_config(layout="wide", page_title="Customer 360 AI")

# CSS
st.markdown("""
<style>
    .customer-card {background-color: #262730; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;}
    .stat-box {text-align: center; background: #1e1e1e; padding: 10px; border-radius: 5px; margin: 5px;}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("👥 Customer Database")
    uploaded_file = st.file_uploader("Upload 'customer_360_data.csv'", type=["csv"])
    
    if uploaded_file:
        if st.button("🔄 Process Database"):
            files = {"file": uploaded_file.getvalue()}
            res = requests.post(f"{API_URL}/upload_data", files=files)
            if res.status_code == 200:
                st.success(f"Indexed {res.json()['count']} Profiles")
                st.session_state['data_loaded'] = True
    
    st.divider()
    
    selected_id = None
    
    if st.session_state.get('data_loaded'):
        # SEPARATE DROPDOWNS
        st.markdown("### 🔍 Quick Filter")
        
        # 1. Churned List
        churned_list = requests.get(f"{API_URL}/get_ids_by_status/Churned").json()
        churn_select = st.selectbox(
            "🚨 Churned (Crisis)", 
            options=["Select..."] + churned_list,
            index=0
        )
        
        # 2. Active List
        active_list = requests.get(f"{API_URL}/get_ids_by_status/Active").json()
        active_select = st.selectbox(
            "✅ Active (Positive)", 
            options=["Select..."] + active_list,
            index=0
        )
        
        # Logic to handle selection priority
        if churn_select != "Select...":
            selected_id = churn_select
        elif active_select != "Select...":
            selected_id = active_select

# Main Screen
st.title("🕵️ Individual Customer Detective")

if selected_id:
    # 1. Fetch Details
    c = requests.get(f"{API_URL}/get_customer_details/{selected_id}").json()
    
    # Top Row: The Profile
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
        st.markdown(f"### Client #{c['ClientID']}")
        
        status_color = "red" if c['Status'] == "Churned" else "green"
        st.markdown(f"**Status:** :{status_color}[{c['Status']}]")
        st.markdown(f"**Sentiment:** {c['Sentiment']}")
        st.markdown(f"**Channel:** {c['Preferred_Channel']}")

    with col2:
        # Stats Grid
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Spend", f"{c['Total_Spend']} MAD")
        s2.metric("Visits", c['Visits'])
        s3.metric("Avg Basket", f"{c['Avg_Basket']} MAD")
        s4.metric("Last Visit", c['Last_Visit'])
        
        st.info(f"📝 **Latest Feedback:** \"{c['Feedback']}\"")

    st.divider()

    # 2. The AI Agent Analysis
    st.subheader("🤖 AI Agent Solution")
    
    if st.button("⚡ Generate Personal Solution"):
        with st.spinner(f"Analyzing Client {selected_id}'s psychology..."):
            res = requests.post(f"{API_URL}/agent/individual_solution", json={"customer_data": c})
            st.session_state['solution'] = res.json()

    if 'solution' in st.session_state:
        sol = st.session_state['solution']
        
        # Two Columns: Analysis vs Action
        ac1, ac2 = st.columns(2)
        
        with ac1:
            with st.container(border=True):
                st.markdown("#### 🧠 Root Cause Analysis")
                st.write(sol['root_cause'])
                st.markdown("#### 🎯 Strategy")
                st.write(sol['solution_strategy'])
        
        with ac2:
            with st.container(border=True):
                st.markdown(f"#### 📨 Draft {c['Preferred_Channel']}")
                st.text_area("Message", value=sol['drafted_message'], height=150)
                
                incentive = sol.get('recommended_incentive', 'None')
                st.success(f"**Recommended Incentive:** {incentive}")
                
                if st.button("🚀 Send Message Now", type="primary"):
                    st.toast(f"Message sent to Client {c['ClientID']} via {c['Preferred_Channel']}!", icon="✅")
                    time.sleep(2)
                    st.balloons()

else:
    st.info("👈 Upload 'customer_360_data.csv' and pick a Customer ID from the sidebar.")