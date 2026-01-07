import os
import random
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load Env
load_dotenv()

app = FastAPI(title="Antavo-Style Omni-Industry Engine")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Persistence (In-Memory) ---
CAMPAIGNS_DB = []  # Stores launched campaigns for the "Monitoring" dashboard

# --- Data Models ---
class CustomerSegment(BaseModel):
    segment_name: str
    behavior_change: str  # e.g., "Stopped buying fuel", "Decreased loan usage"
    size: int
    avg_value: float
    industry: str

class AIRecommendation(BaseModel):
    segment_name: str
    campaign_type: str  # SMS, Push, Bonus Points
    message: str
    duration_days: int
    incentive: str
    estimated_participation: float  # 0.0 to 1.0
    estimated_roi: float
    total_cost: float
    industry_context: str

# --- 1. Industry Data Generator ---
@app.get("/data/segments")
def get_segments(industry: str = "Supermarket"):
    """Generates behavioral segments based on the selected industry."""
    segments = []
    
    if industry == "Supermarket":
        names = ["Churned Organic Shoppers", "Price-Sensitive Families", "Dormant Premium Users"]
        behaviors = ["Stopped buying fresh produce", "Only buys on discount", "No visit in 60 days"]
    elif industry == "Oil & Gas":
        names = ["Fleet Card Slippage", "Weekend Fuelers", "Car Wash Lapsers"]
        behaviors = ["Fuel volume down 20%", "Stopped visiting on Saturdays", "No car wash in 3 months"]
    elif industry == "Banking":
        names = ["Credit Card Dormancy", "High-Net-Worth At Risk", "Loan Refinance Seekers"]
        behaviors = ["Zero transactions in 30 days", "Large withdrawal recently", "High checks on competitor rates"]
    else:
        names = ["General At-Risk"]
        behaviors = ["Low Activity"]

    for i in range(3):
        segments.append({
            "segment_name": names[i],
            "behavior_change": behaviors[i],
            "size": random.randint(50, 5000),
            "avg_value": random.randint(100, 2000),
            "industry": industry
        })
    return segments

# --- 2. The AI Campaign Architect ---
@app.post("/agent/plan_campaign", response_model=AIRecommendation)
def plan_campaign(segment: CustomerSegment):
    """
    Antavo Logic: Analyzes the segment -> Proposes Campaign -> Calculates ROI.
    """
    
    system_prompt = (
        "You are an Expert Loyalty AI Manager. "
        "Your goal is to design a retention campaign for a specific customer segment. "
        "Output ONLY JSON with keys: campaign_type, message, duration_days, incentive, estimated_participation (0.1-0.9), estimated_roi (ratio)."
    )
    
    user_prompt = f"""
    Industry: {segment.industry}
    Segment: {segment.segment_name}
    Behavior Issue: {segment.behavior_change}
    Avg Customer Value: ${segment.avg_value}
    
    Task:
    1. Select channel (SMS/Push/Email).
    2. Write a short, punchy message.
    3. Define an incentive (Discount, Points, Free Service).
    4. Estimate ROI based on customer value.
    """

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content)
        
        # Calculate Mock Financials
        cost_per_user = 2.50 if data['campaign_type'] == "SMS" else 0.10
        total_cost = round(cost_per_user * segment.size, 2)
        
        return {
            "segment_name": segment.segment_name,
            "campaign_type": data['campaign_type'],
            "message": data['message'],
            "duration_days": data['duration_days'],
            "incentive": data['incentive'],
            "estimated_participation": data['estimated_participation'],
            "estimated_roi": data['estimated_roi'],
            "total_cost": total_cost,
            "industry_context": segment.industry
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. Campaign Launch & Monitor ---
@app.post("/campaign/launch")
def launch_campaign(campaign: AIRecommendation):
    """Saves the campaign to the 'Live Monitor' database."""
    # Simulate "Live" data for the dashboard
    live_stats = {
        "status": "Active",
        "participants": 0,  # Starts at 0
        "revenue": 0,
        "target_participants": int(campaign.estimated_participation * 1000), # Mock size
        "budget": campaign.total_cost
    }
    # Merge campaign details with live stats
    full_record = {**campaign.dict(), **live_stats}
    CAMPAIGNS_DB.append(full_record)
    return {"status": "Launched", "id": len(CAMPAIGNS_DB)}

@app.get("/campaign/dashboard")
def get_dashboard():
    """Returns data for the Real-Time Monitoring Dashboard."""
    # Simulate real-time updates (randomly increase numbers every time we refresh)
    for c in CAMPAIGNS_DB:
        if c['participants'] < c['target_participants']:
            growth = random.randint(5, 50)
            c['participants'] += growth
            c['revenue'] += growth * random.uniform(10, 50)
    return CAMPAIGNS_DB