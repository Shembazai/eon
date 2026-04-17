"""
This script consolidates financial data from multiple sources into a unified JSON file. 
It is designed to process transaction summaries and user profiles, categorize transactions, 
and generate a comprehensive financial report. The script performs the following tasks:

1. **Input Data Sources**:
   - Reads transaction data from `mastercard_summary.json`.
   - Reads user profile data (e.g., recurring bills) from `profile.json`.

2. **Categorization**:
   - Uses predefined keywords to categorize transactions into categories such as "food", "transport", "health", etc.
   - If a transaction does not match any category, it is assigned to the "other" category.

3. **Data Aggregation**:
   - Aggregates transaction amounts by category.
   - Ensures all categories are represented, even if no transactions exist for a category.

4. **Profile Integration**:
   - Adds missing categories and their expected amounts from the user profile (e.g., recurring bills) if they are not present in the transactions.

5. **Output**:
   - Generates a consolidated JSON file (`finance_data.json`) containing:
     - The original profile data.
     - Aggregated totals by category.
     - The raw list of transactions.

6. **Error Handling**:
   - Handles missing input files gracefully by displaying warnings.
   - Ensures all transactions are categorized, even if incomplete.

This script is useful for generating a unified financial overview, combining both transaction data and user-defined recurring expenses.
"""

import json
from pathlib import Path

# Use relative paths or environment variables for better portability
BASE_DIR = Path(__file__).parent
SUMMARY_PATH = BASE_DIR / "mastercard_summary.json"
PROFILE_PATH = BASE_DIR / "profile.json"
OUTPUT_PATH = BASE_DIR / "finance_data.json"

# Master category list (used for padding)
ALL_CATEGORIES = [
    "food", "transport", "health", "entertainment", "shopping", "utilities",
    "travel", "rent", "child support", "other"
]

CATEGORY_KEYWORDS = {
    "food": ["restaurant", "costco", "épicerie", "supermarché", "pizza", "pizzeria", "café", "grocery", "supermarket", "super c", "iga", "metro", "dollarama"],
    "transport": ["essence", "carburant", "stationnement", "uber", "bus", "train", "gas"],
    "health": ["pharmacie", "pharmacy", "dentiste", "clinic", "hôpital", "physio"],
    "entertainment": ["netflix", "spotify", "cinéma", "movie", "theatre", "film"],
    "shopping": ["amazon", "amzn", "boutique", "magasin", "store", "walmart"],
    "utilities": ["hydro", "électricité", "water", "internet", "fizz", "téléphone", "bell"],
    "travel": ["hôtel", "hotel", "vol", "flight", "airbnb"],
    "rent": ["loyer", "vallem", "rent", "paiement de loyer"],
    "child support": ["pensions alimentaires", "child support", "pension"],
    "other": []
}

def categorize(description):
    desc = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in desc for k in keywords):
            return category
    return "other"

def load_json(path):
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    else:
        print(f"⚠️ File not found: {path}")
        return {}

def main():
    print("🔄 Consolidating financial data...")

    transactions = load_json(SUMMARY_PATH)
    profile = load_json(PROFILE_PATH)

    if not transactions or not profile:
        print("❌ Cannot consolidate — missing required data.")
        return

    # Ensure all transactions have a category
    for tx in transactions:
        if "category" not in tx or not tx["category"]:
            tx["category"] = categorize(tx.get("description", ""))

    # Aggregate totals by category from transactions
    totals_by_category = {cat: 0.0 for cat in ALL_CATEGORIES}
    for tx in transactions:
        cat = tx.get("category", "other")
        amt = tx.get("amount", 0.0)
        totals_by_category[cat] += abs(amt)

    # 🔧 Add missing profile-defined bills if zero in transactions
    bills = profile.get("bills", {})
    for cat, expected_amt in bills.items():
        if cat in ALL_CATEGORIES:
            if totals_by_category.get(cat, 0.0) == 0.0:
                print(f"➕ Adding from profile: {cat} = {expected_amt}")
                totals_by_category[cat] = float(expected_amt)

    # Final unified structure
    merged = {
        "profile": profile,
        "category_totals": totals_by_category,
        "raw_transactions": transactions
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(merged, f, indent=4)

    print(f"✅ Merged file saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
