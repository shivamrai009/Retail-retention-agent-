import pandas as pd
import random
from datetime import datetime, timedelta

def generate_customer_360():
    data = []
    
    # Complaints & Praises
    complaints = [
        "Found a bug in the rice bag", "Milk expired 2 days after buying", 
        "Cashier was rude at checkout", "Delivery was 2 hours late",
        "App keeps crashing", "Prices are higher than Marjane"
    ]
    praises = [
        "Love the new bakery section", "Staff is very helpful",
        "Fresh vegetables are great", "Good parking space"
    ]
    
    # Generate 500 Customers
    for i in range(1001, 1501):
        # Determine Profile
        if random.random() < 0.2: # 20% Churned/Angry
            status = "Churned"
            days_ago = random.randint(60, 120)
            feedback = random.choice(complaints)
            sentiment = "Negative"
        else: # 80% Active/Happy
            status = "Active"
            days_ago = random.randint(1, 30)
            feedback = random.choice(praises) if random.random() > 0.5 else "No Feedback"
            sentiment = "Positive" if feedback != "No Feedback" else "Neutral"
            
        spend = round(random.uniform(500, 10000), 2)
        freq = random.randint(1, 50)
        
        data.append({
            "ClientID": str(i),
            "Status": status,
            "Last_Visit": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "Total_Spend": spend,
            "Visits": freq,
            "Avg_Basket": round(spend/freq, 2),
            "Top_Category": random.choice(["Fresh", "Electronics", "Bakery", "Home"]),
            "Feedback": feedback,
            "Sentiment": sentiment,
            "Preferred_Channel": random.choice(["WhatsApp", "Email", "SMS"])
        })

    df = pd.DataFrame(data)
    df.to_csv("customer_360_data.csv", index=False)
    print("✅ Created 'customer_360_data.csv' with individual feedback.")

if __name__ == "__main__":
    generate_customer_360()