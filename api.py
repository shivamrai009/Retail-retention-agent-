import os
import random
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

app = FastAPI(title="Supermarket Retention Engine")

# Initialize Groq Client
# Ensure GROQ_API_KEY is in your .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- In-Memory Database (For History) ---
CAMPAIGN_HISTORY = []

# --- Data Models ---
class CustomerProfile(BaseModel):
    customer_id: str
    last_purchase_days: int
    total_spend: float
    frequency: int
    feedback_sentiment: str  # "Positive", "Neutral", "Negative"
    recent_feedback: str

class CampaignStrategy(BaseModel):
    root_cause: str
    action_type: str
    email_subject: str
    email_body: str
    recommended_discount: str

# --- Mock Data Generator ---
@app.get("/data/customers", response_model=List[CustomerProfile])
def get_customers():
    """Generates mock supermarket data."""
    customers = []
    complaints = [
        "Prices for organic milk are too high.",
        "The checkout line was way too long.",
        "I found expired yogurt on the shelf.",
        "The app keeps crashing when I try to use coupons.",
        "Moved to a new neighborhood, too far to drive."
    ]
    praises = ["Love the fresh bakery!", "Great staff.", "Clean store."]
    
    for i in range(10):  # Generate 10 profiles
        is_churned = random.choice([True, False])
        sentiment = "Negative" if is_churned else "Positive"
        feedback = random.choice(complaints) if is_churned else random.choice(praises)
        
        customers.append({
            "customer_id": f"CUST-{1000+i}",
            "last_purchase_days": random.randint(30, 120) if is_churned else random.randint(1, 20),
            "total_spend": round(random.uniform(100.0, 2000.0), 2),
            "frequency": random.randint(1, 50),
            "feedback_sentiment": sentiment,
            "recent_feedback": feedback
        })
    return customers

# --- The Agentic Core ---
@app.post("/agent/analyze", response_model=CampaignStrategy)
def analyze_customer(customer: CustomerProfile):
    """
    The Agentic Workflow:
    1. Ingests Customer Data.
    2. Reasons about 'Why' they left.
    3. Formulates a personalized win-back strategy.
    4. Saves the action to history.
    """
    
    # 1. Construct the Prompt
    system_prompt = (
        "You are 'Timi', an expert Retail Retention AI Agent. "
        "Your goal is to analyze a churned supermarket customer and create a win-back campaign. "
        "Return ONLY a JSON object with these exact keys: root_cause, action_type, email_subject, email_body, recommended_discount. "
        "Do not include any text outside the JSON object."
    )
    
    user_prompt = f"""
    Analyze this customer:
    - ID: {customer.customer_id}
    - Days since last shop: {customer.last_purchase_days}
    - Total Value: ${customer.total_spend}
    - Feedback: "{customer.recent_feedback}"
    
    Task:
    1. Diagnose the root cause (Price, Service, Quality, or Convenience).
    2. Write a personalized email to win them back.
    3. Suggest a discount based on their Total Value (High value = higher discount).
    """

    try:
        # 2. Call Groq with the NEW Model ID
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",  # <--- FIXED MODEL ID HERE
            response_format={"type": "json_object"}
        )
        
        # 3. Parse Response
        content = completion.choices[0].message.content
        response_data = json.loads(content)
        
        # 4. Save to History (Persistence)
        history_entry = {
            "customer_id": customer.customer_id,
            "root_cause": response_data.get('root_cause'),
            "action": response_data.get('action_type'),
            "discount": response_data.get('recommended_discount'),
            "status": "Generated"
        }
        CAMPAIGN_HISTORY.append(history_entry)
        
        return response_data

    except Exception as e:
        # Log the error to the console and return it to the UI
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- History Endpoint ---
@app.get("/history")
def get_history():
    return CAMPAIGN_HISTORY