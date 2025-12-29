import argparse
from monitor import OpenAIMonitor

def main():
    parser = argparse.ArgumentParser(description="Manually add funds to the OpenAI Monitor Ledger.")
    parser.add_argument("--amount", type=float, required=True, help="Amount to add (e.g., 50.00)")
    args = parser.parse_args()

    monitor = OpenAIMonitor()
    monitor.add_deposit(args.amount)
    print(f"Successfully added ${args.amount:.2f} to the ledger.")
    status = monitor.get_balance()
    print(f"New Estimated Balance: ${status['balance']:.2f}")

if __name__ == "__main__":
    main()
