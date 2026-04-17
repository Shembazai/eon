import pandas as pd
from pathlib import Path
import json
from .config import AI_BUDGET_CSV, TRAINING_DATA_FILE

def main():
    if not AI_BUDGET_CSV.exists():
        raise FileNotFoundError(f"Missing data file: {AI_BUDGET_CSV}")

    df = pd.read_csv(AI_BUDGET_CSV)

    # Clean + Normalize
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df.dropna(subset=["date", "amount"], inplace=True)

    if df.empty:
        raise ValueError("No valid data found in CSV after cleaning")

    # Add month field
    df["month"] = df["date"].dt.to_period("M")

    # Categorize transactions
    df["category"] = df["transaction_type"].str.lower().fillna("uncategorized")

    # Group by month
    monthly = df.groupby(["month", "category"])["amount"].sum().unstack(fill_value=0)
    monthly["net"] = df.groupby("month")["amount"].sum()

    # Compute rolling stats
    rolling_income = monthly.clip(lower=0).mean().to_dict()
    rolling_expense = monthly.clip(upper=0).mean().to_dict()
    rolling_net = monthly["net"].mean()

    # Build training Q&A
    samples = []

    samples.append({
        "prompt": "How much do I earn monthly?",
        "response": f"You earn about ${round(rolling_income.get('income', 0), 2)} per month on average."
    })

    samples.append({
        "prompt": "How much do I spend monthly?",
        "response": f"You spend about ${abs(round(rolling_expense.get('expense', 0), 2))} per month on average."
    })

    samples.append({
        "prompt": "How much money do I have left over each month?",
        "response": f"You typically end the month with about ${round(rolling_net, 2)}."
    })

    # Forecast end-of-month balance if current data available
    current_balance = df["amount"].sum()
    avg_daily_net = monthly["net"].mean() / 30
    days_remaining = 30 - df["date"].dt.day.max()
    forecast_balance = current_balance + (avg_daily_net * days_remaining)

    samples.append({
        "prompt": "How much money will I have at the end of the month?",
        "response": f"Based on recent patterns, you'll likely have around ${round(forecast_balance, 2)} by month end."
    })

    # Write to JSONL
    TRAINING_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRAINING_DATA_FILE, "w") as f:
        for pair in samples:
            f.write(json.dumps(pair) + "\n")

    print(f"✅ Generated {len(samples)} Q&A pairs → {TRAINING_DATA_FILE}")

if __name__ == "__main__":
    main()
