import json
from pathlib import Path

"""
This script updates a user's financial profile by calculating and estimating key financial metrics. 
It processes income and expense data from a JSON file and computes monthly income, expenses, 
and savings. The script performs the following tasks:

1. **Load Financial Profile**:
   - Reads the user's financial profile from `profile.json`.

2. **Income Handling**:
   - Extracts income data, including multiple streams with amounts and frequencies.
   - Converts income to monthly equivalents based on frequency.

3. **Expense Estimation**:
   - Aggregates all expenses listed in the profile to calculate total monthly expenses.

4. **Savings Calculation**:
   - Computes estimated monthly savings as the difference between monthly income and expenses.

5. **Update Profile**:
   - Updates the financial profile with the following calculated fields:
     - `estimated_monthly_income`: The user's monthly income.
     - `estimated_monthly_expenses`: The user's total monthly expenses.
     - `estimated_monthly_savings`: The user's monthly savings.

6. **Save Updated Profile**:
   - Writes the updated financial profile back to `profile.json`.

7. **Output**:
   - Displays a confirmation message indicating that the profile has been successfully updated.

This script is useful for individuals who want to maintain an up-to-date financial profile 
and gain insights into their monthly income, expenses, and savings.
"""

def compute_monthly_amount(amount: float, frequency: str) -> float:
    """Convert income/expense amount to monthly equivalent."""
    frequency = frequency.lower()
    if frequency == "weekly":
        return amount * 52 / 12
    elif frequency == "bi-weekly" or frequency == "biweekly":
        return amount * 26 / 12
    else:  # monthly
        return amount

def main():
    PROFILE_PATH = Path(__file__).parent / "profile.json"
    
    # Load existing profile
    try:
        with open(PROFILE_PATH, "r") as f:
            profile = json.load(f)
    except FileNotFoundError:
        print(f"❌ Profile file not found: {PROFILE_PATH}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in profile file: {e}")
        return

    # Handle multiple income streams
    income_streams = profile.get("income_streams", [])
    monthly_income = 0.0
    for stream in income_streams:
        if isinstance(stream, dict):
            amount = float(stream.get("amount", 0))
            frequency = stream.get("frequency", "monthly")
            monthly_income += compute_monthly_amount(amount, frequency)

    # Handle legacy single income format
    if not income_streams:
        income_data = profile.get("income", {})
        if isinstance(income_data, dict):
            amount = float(income_data.get("amount", 0))
            frequency = income_data.get("frequency", "monthly")
            monthly_income = compute_monthly_amount(amount, frequency)

    # Estimate expenses
    bills = profile.get("bills", {})
    expenses = profile.get("expenses", {})
    rent = float(profile.get("rent", 0))
    
    monthly_expenses = rent
    monthly_expenses += sum(float(amount) for amount in bills.values() if amount)
    monthly_expenses += sum(float(amount) for amount in expenses.values() if amount)

    # Save result back into profile
    profile["estimated_monthly_income"] = round(monthly_income, 2)
    profile["estimated_monthly_expenses"] = round(monthly_expenses, 2)
    profile["estimated_monthly_savings"] = round(monthly_income - monthly_expenses, 2)

    try:
        with open(PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=4)
        print("✅ Profile updated with monthly income, expenses, and savings.")
    except Exception as e:
        print(f"❌ Failed to save profile: {e}")

if __name__ == "__main__":
    main()
