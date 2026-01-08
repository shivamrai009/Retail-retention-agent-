import os
import io
import json
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Customer 360 Agent")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# In-Memory Database
GLOBAL_DF = None

# --- 1. DATA INGESTION ---
@app.post("/upload_data")
async def upload_data(file: UploadFile = File(...)):
    global GLOBAL_DF
    content = await file.read()
    GLOBAL_DF = pd.read_csv(io.BytesIO(content))
    return {"status": "Data Indexed", "count": len(GLOBAL_DF)}

@app.get("/get_ids_by_status/{status_type}")
def get_ids_by_status(status_type: str):
    """
    Returns IDs filtered by status: 'Churned' or 'Active'
    """
    if GLOBAL_DF is None: return []
    
    # Filter logic
    if status_type == "Churned":
        filtered = GLOBAL_DF[GLOBAL_DF['Status'] == "Churned"]
    else:
        filtered = GLOBAL_DF[GLOBAL_DF['Status'] == "Active"]
        
    return filtered['ClientID'].astype(str).tolist()

@app.get("/get_customer_details/{client_id}")
def get_details(client_id: str):
    if GLOBAL_DF is None: raise HTTPException(404, "No data loaded")
    
    customer = GLOBAL_DF[GLOBAL_DF['ClientID'].astype(str) == client_id]
    if customer.empty: raise HTTPException(404, "Customer not found")
    
    return customer.iloc[0].to_dict()

# --- 2. INDIVIDUAL AGENT ANALYSIS ---
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
    Total Value: {c['Total_Spend']} MAD
    Feedback History: "{c['Feedback']}"
    Sentiment: {c['Sentiment']}
    
    Task:
    1. Identify why they are happy or unhappy (Root Cause).
    2. Draft a {c['Preferred_Channel']} message. If unhappy, apologize and solve. If happy, thank and upsell.
    3. Suggest an incentive (Points, Voucher, or None).
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