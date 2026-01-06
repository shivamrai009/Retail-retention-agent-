import streamlit as st
import pandas as pd
import requests

# Configuration
API_URL = "http://127.0.0.1:8000"  # Localhost for Codespaces

st.set_page_config(layout="wide", page_title="Antavo Agentic Demo")

# Custom CSS for "Great UI"
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🛒 Supermarket Retention Cloud")
st.markdown("### Agentic Customer Win-Back Pipeline")
st.divider()

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        response = requests.get(f"{API_URL}/data/customers")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame()
    except:
        st.error("Backend not connected. Run 'uvicorn api:app --reload' first.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Top Level Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    churn_risk = df[df['feedback_sentiment'] == 'Negative']
    
    col1.metric("Total Customers", len(df))
    col2.metric("At Risk (Churn)", len(churn_risk), delta="-"+str(len(churn_risk)), delta_color="inverse")
    col3.metric("Revenue at Risk", f"${churn_risk['total_spend'].sum():,.2f}")
    col4.metric("Avg Days Inactive", f"{int(churn_risk['last_purchase_days'].mean())} days")

    st.divider()

    # --- Main Interface ---
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.subheader("⚠️ At-Risk List")
        # Filter for churned customers only
        churn_list = df[df['feedback_sentiment'] == 'Negative']
        
        if not churn_list.empty:
            selected_id = st.selectbox("Select Customer to Analyze:", churn_list['customer_id'])
            
            # Get selected row
            customer_data = churn_list[churn_list['customer_id'] == selected_id].iloc[0]
            
            st.info(f"**Last Seen:** {customer_data['last_purchase_days']} days ago")
            st.warning(f"**Feedback:** {customer_data['recent_feedback']}")
            st.write(f"**Lifetime Value:** ${customer_data['total_spend']}")

            # Button to trigger AI Agent
            analyze_btn = st.button(f"✨ Ask Agent to Fix {selected_id}")
        else:
            st.success("No churned customers found! Good job!")
            analyze_btn = False

    with right_col:
        st.subheader("🧠 Agentic Campaign Optimizer")
        
        if analyze_btn:
            with st.spinner(f"Agent is analyzing {selected_id}'s behavior and sentiment..."):
                try:
                    # 1. Prepare Payload
                    payload = customer_data.to_dict()
                    
                    # 2. Call API
                    response = requests.post(f"{API_URL}/agent/analyze", json=payload)
                    
                    # 3. Check for valid response BEFORE reading keys
                    if response.status_code == 200:
                        strategy = response.json()
                        
                        st.success("Analysis Complete!")
                        
                        c1, c2 = st.columns(2)
                        c1.info(f"**Diagnosis:** {strategy.get('root_cause', 'Unknown')}")
                        c2.success(f"**Action:** {strategy.get('action_type', 'General Outreach')}")
                        
                        st.markdown("#### 📩 Drafted Win-Back Email")
                        st.text_input("Subject", value=strategy.get('email_subject', ''))
                        st.text_area("Body", value=strategy.get('email_body', ''), height=200)
                        
                        if st.button("🚀 Deploy Campaign Now", type="primary"):
                            st.toast(f"Email sent to {selected_id}!", icon="✅")
                            st.balloons()
                            
                    else:
                        # Show the actual error from backend
                        try:
                            error_detail = response.json().get('detail', 'Unknown Backend Error')
                        except:
                            error_detail = response.text
                        st.error(f"Brain Freeze! The Agent failed: {error_detail}")
                        
                except Exception as e:
                    st.error(f"Connection Error: {e}")
        else:
            st.markdown(
                """
                <div style="text-align: center; color: gray; padding: 50px;">
                    Select a customer on the left and click <b>'Ask Agent'</b> to generate a recovery strategy.
                </div>
                """, unsafe_allow_html=True
            )

    # --- Campaign History Section ---
    st.divider()
    st.subheader("📜 Campaign Audit Log")
    
    if st.button("Refresh History"):
        try:
            res = requests.get(f"{API_URL}/history")
            if res.status_code == 200:
                history_data = res.json()
                if history_data:
                    history_df = pd.DataFrame(history_data)
                    st.dataframe(history_df, use_container_width=True)
                else:
                    st.info("No campaigns generated yet.")
            else:
                st.error("Failed to fetch history.")
        except Exception as e:
            st.error(f"Connection Error: {e}")