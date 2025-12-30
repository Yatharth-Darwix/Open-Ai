import os
import json
import time
import shutil
from monitor import OpenAIMonitor
from datetime import datetime

# Setup
LEDGER_FILE = "ledger.json"
BACKUP_FILE = "ledger.json.bak"

print("--- Starting Local Simulation Test ---")

# 1. Backup existing ledger if it exists to simulate a clean slate
if os.path.exists(LEDGER_FILE):
    print(f"Backing up existing {LEDGER_FILE}...")
    shutil.move(LEDGER_FILE, BACKUP_FILE)

# 2. Set Environment Variable for Initial Deposit
os.environ["INITIAL_TOTAL_DEPOSITED"] = "16.00"
print(f"Environment INITIAL_TOTAL_DEPOSITED set to: {os.environ['INITIAL_TOTAL_DEPOSITED']}")

try:
    # 3. Initialize Monitor (triggers _ensure_ledger)
    print("Initializing OpenAIMonitor...")
    monitor = OpenAIMonitor(ledger_file=LEDGER_FILE)
    
    # 4. Verify Start Date (Should be ~90 days ago)
    with open(LEDGER_FILE, "r") as f:
        data = json.load(f)
    
    start_date = data.get("start_date")
    now = int(time.time())
    days_diff = (now - start_date) / 86400
    
    print("Ledger initialized.")
    print(f"Start Date Timestamp: {start_date}")
    print(f"Current Timestamp:    {now}")
    print(f"Lookback Days:        {days_diff:.2f} days")
    
    if 89 < days_diff < 91:
        print("SUCCESS: Start date is correctly set to ~90 days ago.")
    else:
        print("FAILURE: Start date is NOT 90 days ago.")

    # 5. Fetch Costs to verify API connectivity and history population
    print("\nFetching aggregated costs from OpenAI (this simulates the first page load)...")
    costs = monitor.get_aggregated_costs()
    
    print("\n--- Monthly Expenses Retrieved ---")
    history = costs.get("history", [])
    if not history:
        print("WARNING: No history found. (This might be valid if the account is brand new, but unexpected for this account).")
    else:
        for entry in history:
            print(f"{entry['month']}: ${entry['amount']:.2f}")
            
    print("\n--- Balance Check ---")
    balance_info = monitor.get_balance()
    print(f"Calculated Balance: ${balance_info['balance']}")
    print(f"Total Deposited:    ${balance_info['total_deposited']}")
    print(f"Total Spend:        ${balance_info['total_spend']}")

finally:
    # 6. Cleanup: Restore backup
    if os.path.exists(BACKUP_FILE):
        print("\nRestoring original ledger...")
        if os.path.exists(LEDGER_FILE):
            os.remove(LEDGER_FILE)
        shutil.move(BACKUP_FILE, LEDGER_FILE)
    else:
        # If we created a ledger but didn't have a backup, maybe leave it or remove it?
        # Let's remove the test ledger if no backup existed (clean up after test)
        if os.path.exists(LEDGER_FILE):
             os.remove(LEDGER_FILE)

print("\nTest Complete.")
