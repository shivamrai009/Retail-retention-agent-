import os
import io
import json
import random
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Unified Loyalty Engine")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- IN-MEMORY STATE (Resets when server restarts) ---
GLOBAL_DF = None
ACTIVE_CAMPAIGNS = []

# ==========================================
# PART 1: DATA INGESTION & COMMON UTILS
# ==========================================
@app.post("/upload_data")
async def upload_data(file: UploadFile = File(...)):
    global GLOBAL_DF
    content = await file.read()
    # Load CSV and normalize column names if needed
    GLOBAL_DF = pd.read_csv(io.BytesIO(content))
    return {"status": "Data Indexed", "count": len(GLOBAL_DF)}

@app.get("/get_ids_by_status/{status_type}")
def get_ids_by_status(status_type: str):
    """Filter IDs for the Customer 360 Dropdown"""
    if GLOBAL_DF is None: return []
    
    if status_type == "Churned":
        # Case insensitive check
        filtered = GLOBAL_DF[GLOBAL_DF['Status'].str.title() == "Churned"]
    else:
        filtered = GLOBAL_DF[GLOBAL_DF['Status'].str.title() == "Active"]
        
    return filtered['ClientID'].astype(str).tolist()

@app.get("/get_customer_details/{client_id}")
def get_details(client_id: str):
    if GLOBAL_DF is None: raise HTTPException(404, "No data loaded")
    
    customer = GLOBAL_DF[GLOBAL_DF['ClientID'].astype(str) == client_id]
    if customer.empty: raise HTTPException(404, "Customer not found")
    
    return customer.iloc[0].to_dict()

# ==========================================
# PART 2: INDIVIDUAL DETECTIVE (CUSTOMER 360)
# ==========================================
class IndividualRequest(BaseModel):
    customer_data: dict

@app.post("/agent/individual_solution")
def solve_individual(req: IndividualRequest):
    c = req.customer_data
    
    system_prompt = (
        "You are a Senior Customer Success Manager. "
        "Analyze this specific customer's profile and feedback. "
        "Determine the best 'Next Best Action' to retain them. "
        "Output JSON ONLY: {root_cause, solution_strategy, drafted_message, recommended_incentive}"
    )
    
    user_prompt = f"""
    Customer: {c['ClientID']}
    Status: {c['Status']} (Last Visit: {c['Last_Visit']})
    Total Spend: {c['Total_Spend']}
    Feedback: "{c.get('Feedback', 'None')}"
    
    Task: Draft a short, personal {c.get('Preferred_Channel', 'Email')} message to address their feedback.
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(500, str(e))

# ==========================================
# PART 3: CAMPAIGN ORCHESTRATOR
# ==========================================

# --- A. SEGMENTATION ---
@app.get("/analyze_segments")
def analyze_segments():
    """Scans for 'Churned High Rollers' and 'Active Price Sensitive' users."""
    if GLOBAL_DF is None: return []
    
    # Logic: Status + Spend Thresholds
    churned_whales = GLOBAL_DF[
        (GLOBAL_DF['Status'] == 'Churned') & 
        (GLOBAL_DF['Total_Spend'] > 2000)
    ]
    
    active_cheap = GLOBAL_DF[
        (GLOBAL_DF['Status'] == 'Active') & 
        (GLOBAL_DF['Total_Spend'] < 1000)
    ]
    
    return [
        {
            "id": "seg_high_churn",
            "name": "🚨 Churned High-Rollers",
            "behavior_change": "High value (>2000) but stopped visiting.",
            "size": len(churned_whales),
            "avg_basket": round(churned_whales['Avg_Basket'].mean(), 2) if not churned_whales.empty else 0,
            "recommended_channel": "Email"
        },
        {
            "id": "seg_price_sens",
            "name": "🌱 Price-Sensitive Regulars",
            "behavior_change": "Frequent visits but low basket size (<1000 total).",
            "size": len(active_cheap),
            "avg_basket": round(active_cheap['Avg_Basket'].mean(), 2) if not active_cheap.empty else 0,
            "recommended_channel": "SMS"
        }
    ]

# --- B. STRATEGY & ROI ---
class ProposalRequest(BaseModel):
    name: str
    behavior_change: str
    size: int
    avg_basket: float
    recommended_channel: str

@app.post("/generate_campaign_proposal")
def generate_proposal(seg: ProposalRequest):
    # 1. AI Content Strategy
    system_prompt = "You are a Loyalty Strategist. Output JSON: {message, incentive, duration_days}"
    user_prompt = f"Create a {seg.recommended_channel} campaign for segment: {seg.name} (Avg Basket: {seg.avg_basket})."
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        strategy = json.loads(completion.choices[0].message.content)
        
        # 2. Financial Math (CFO Logic)
        PARTICIPATION_RATE = 0.18 # 18% conversion
        UPLIFT_FACTOR = 1.4       # Spends 40% more than usual
        COST_PER_MSG = 0.4        # 0.40 MAD per message
        
        marketing_cost = seg.size * COST_PER_MSG
        # Incentive cost (estimated 15% discount redemption)
        incentive_cost = (seg.size * PARTICIPATION_RATE) * (seg.avg_basket * 0.15)
        total_cost = marketing_cost + incentive_cost
        
        est_revenue = (seg.size * PARTICIPATION_RATE) * (seg.avg_basket * UPLIFT_FACTOR)
        est_roi = round((est_revenue - total_cost) / total_cost, 2) if total_cost > 0 else 0
        
        return {
            "strategy": strategy,
            "financials": {
                "est_participation_rate": "18%",
                "total_campaign_cost": round(total_cost, 2),
                "estimated_roi": est_roi
            }
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# --- C. LAUNCH & MONITOR ---
class LaunchRequest(BaseModel):
    segment_name: str
    campaign_type: str
    message: str
    incentive: str
    duration: int
    est_roi: float
    total_cost: float

@app.post("/launch_campaign")
def launch(c: LaunchRequest):
    new_id = len(ACTIVE_CAMPAIGNS) + 1
    ACTIVE_CAMPAIGNS.append({
        "id": new_id,
        "config": c.dict(),
        "live_data": {
            "participants": 0,
            "transactions": 0,
            "points_distributed": 0,
            "revenue": 0.0,
            "actual_cost": c.total_cost,
            "actual_roi": 0.0
        }
    })
    return {"status": "Launched", "id": new_id}

@app.get("/monitor_campaigns")
def monitor():
    # Simulate live traffic
    for c in ACTIVE_CAMPAIGNS:
        # Random growth
        new_actions = random.randint(0, 5)
        if new_actions > 0:
            c['live_data']['participants'] += new_actions
            c['live_data']['transactions'] += new_actions
            c['live_data']['points_distributed'] += new_actions * 50
            
            # Revenue & ROI Update
            basket = 120 + random.uniform(-20, 50) # Simulated basket variance
            c['live_data']['revenue'] += new_actions * basket
            
            rev = c['live_data']['revenue']
            cost = c['live_data']['actual_cost']
            c['live_data']['actual_roi'] = round((rev - cost) / cost, 2) if cost > 0 else 0
            
    return ACTIVE_CAMPAIGNS