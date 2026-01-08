import pandas as pd
import random
from datetime import datetime, timedelta

def generate_unified_dataset():
    data = []
    
    complaints = ["App crashing at checkout", "Vegetables not fresh", "Price higher than shelf", "Long queue"]
    praises = ["Love the bakery", "Staff helpful", "Good parking", "Great selection"]
    channels = ["Email", "SMS", "Push"]
    
    print("generating 500 records...")
    
    for i in range(1001, 1501):
        # 1. Decide Profile
        is_churned = random.random() < 0.3 # 30% Churn Rate
        status = "Churned" if is_churned else "Active"
        
        # 2. Logic based on Status
        if is_churned:
            days_ago = random.randint(60, 150)
            spend = random.uniform(2000, 8000) if random.random() > 0.5 else random.uniform(100, 500)
            feedback = random.choice(complaints)
            sentiment = "Negative"
        else:
            days_ago = random.randint(1, 30)
            spend = random.uniform(500, 3000)
            feedback = random.choice(praises) if random.random() > 0.6 else "None"
            sentiment = "Positive" if feedback != "None" else "Neutral"
            
        # 3. Common Fields
        visits = random.randint(1, 50)
        avg_basket = round(spend / max(visits, 1), 2)
        
        data.append({
            "ClientID": str(i),
            "Status": status,
            "Last_Visit": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "Total_Spend": round(spend, 2),
            "Visits": visits,
            "Avg_Basket": avg_basket,
            "Feedback": feedback,
            "Sentiment": sentiment,
            "Preferred_Channel": random.choice(channels)
        })

    # Save
    df = pd.DataFrame(data)
    df.to_csv("unified_data.csv", index=False)
    print("✅ Success! Created 'unified_data.csv'. Use this file for ALL modules.")

if __name__ == "__main__":
    generate_unified_dataset()