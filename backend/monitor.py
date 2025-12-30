import os
import json
import time
import smtplib
import requests
from email.message import EmailMessage
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenAIMonitor")

class OpenAIMonitor:
    def __init__(self, ledger_file="ledger.json"):
        self.ledger_file = ledger_file
        self.api_key = os.getenv("OPENAI_ADMIN_KEY")
        self.smtp_user = os.getenv("SMTP_EMAIL")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.threshold = float(os.getenv("ALERT_THRESHOLD", 10.0))
        self.recipient_email = os.getenv("ALERT_RECIPIENT_EMAIL", self.smtp_user)
        
        if self.api_key:
            logger.info(f"API Key loaded: {self.api_key[:8]}... (Length: {len(self.api_key)})")
        else:
            logger.error("API Key NOT loaded from environment!")
            
        logger.info(f"Alert Threshold set to: ${self.threshold}")
        logger.info(f"SMTP Config: {self.smtp_server}:{self.smtp_port} (User: {self.smtp_user})")

        self._ensure_ledger()

    def _ensure_ledger(self):
        if not os.path.exists(self.ledger_file):
            initial_deposit = float(os.getenv("INITIAL_TOTAL_DEPOSITED", 0.0))
            # Default to 90 days ago to ensure history is populated on fresh deploy
            ninety_days_ago = int(time.time()) - (90 * 86400)
            initial_state = {
                "total_deposited": initial_deposit,
                "start_date": ninety_days_ago, 
                "historical_spend": 0.0,
                "monthly_history": {},
                "last_alert_sent": 0
            }
            self._save_ledger(initial_state)
            if initial_deposit > 0:
                logger.info(f"Initialized ledger from Environment Variable with Total Deposit: ${initial_deposit}")

    def _load_ledger(self):
        try:
            with open(self.ledger_file, "r") as f:
                data = json.load(f)
                if "historical_spend" not in data:
                    data["historical_spend"] = 0.0
                if "monthly_history" not in data:
                    data["monthly_history"] = {}
                return data
        except Exception as e:
            logger.error(f"Error loading ledger: {e}")
            # Default to 90 days ago to rebuild history on fresh start
            ninety_days_ago = int(time.time()) - (90 * 86400)
            return {
                "total_deposited": float(os.getenv("INITIAL_TOTAL_DEPOSITED", 0.0)), 
                "start_date": ninety_days_ago, 
                "historical_spend": 0.0, 
                "monthly_history": {},
                "last_alert_sent": 0
            }

    def _save_ledger(self, data):
        with open(self.ledger_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_deposit(self, amount: float):
        ledger = self._load_ledger()
        ledger["total_deposited"] += amount
        if ledger["total_deposited"] == amount and ledger["historical_spend"] == 0: 
             ledger["start_date"] = int(time.time())
        
        ledger["last_alert_sent"] = 0
        self._save_ledger(ledger)
        logger.info(f"Added ${amount}. New Total Deposit: ${ledger['total_deposited']}")
        return ledger

    def sync_balance(self, actual_balance: float):
        costs = self.get_aggregated_costs()
        current_total_spend = costs["total"]
        new_total_deposited = actual_balance + current_total_spend
        
        ledger = self._load_ledger()
        ledger["total_deposited"] = new_total_deposited
        self._save_ledger(ledger)
        logger.info(f"Synced Balance to ${actual_balance}. Recalculated Total Deposit: ${new_total_deposited}")
        return self.get_balance()

    def get_aggregated_costs(self):
        if not self.api_key:
            logger.warning("OPENAI_ADMIN_KEY not set. Cannot fetch costs.")
            return {"total": 0.0, "daily": 0.0, "monthly": 0.0, "history": []}

        ledger = self._load_ledger()
        # Retrieve state
        current_query_start = ledger.get("start_date", int(time.time()) - 86400)
        historical_spend = ledger.get("historical_spend", 0.0)
        monthly_history = ledger.get("monthly_history", {})
        
        url = "https://api.openai.com/v1/organization/costs"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        new_spend_ephemeral = 0.0
        new_spend_finalized = 0.0
        daily_spend = 0.0
        monthly_spend = 0.0
        
        now_utc = datetime.utcnow()
        today_str = now_utc.strftime('%Y-%m-%d')
        current_month_str = now_utc.strftime('%Y-%m')
        
        # We only 'finalize' costs that are older than the current month
        checkpoint_ts = int(datetime(now_utc.year, now_utc.month, 1).timestamp())

        has_more = True
        loop_count = 0
        max_loops = 100 
        
        last_processed_time = current_query_start

        while has_more and loop_count < max_loops:
            params = {
                "start_time": int(current_query_start), 
                "bucket_width": "1d", 
                "limit": 100
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 429:
                    time.sleep(2)
                    continue
                
                response.raise_for_status()
                data = response.json()
                buckets = data.get("data", [])
                
                if not buckets:
                    has_more = False
                    break
                    
                last_bucket_end = current_query_start

                for bucket in buckets:
                    start_t = bucket.get("start_time")
                    end_t = bucket.get("end_time")
                    
                    if end_t and end_t > last_bucket_end:
                        last_bucket_end = end_t
                    
                    bucket_date_str = None
                    bucket_month_display = None
                    
                    if start_t:
                        dt = datetime.utcfromtimestamp(start_t)
                        bucket_date_str = dt.strftime('%Y-%m-%d')
                        bucket_month_display = dt.strftime('%b %Y')

                    bucket_spend = 0.0
                    for result in bucket.get("results", []):
                        val = result.get("amount", {}).get("value", 0.0)
                        bucket_spend += float(val)
                    
                    # Update Monthly History Map (Accumulate)
                    if bucket_month_display:
                        # If finalized (older than current month), save to ledger map permanently later
                        # If ephemeral (current month), we just add it to a temporary display copy?
                        # Actually, since we only save ledger if we finalize, we can update the map here safely.
                        # The map in memory starts with what was in ledger.
                        monthly_history[bucket_month_display] = monthly_history.get(bucket_month_display, 0.0) + bucket_spend

                    # Core Logic: If bucket is older than current month, finalize it
                    if end_t and end_t <= checkpoint_ts:
                        new_spend_finalized += bucket_spend
                        if end_t > last_processed_time:
                            last_processed_time = end_t
                    else:
                        new_spend_ephemeral += bucket_spend

                    if bucket_date_str:
                        if bucket_date_str == today_str:
                            daily_spend += bucket_spend
                        if bucket_date_str.startswith(current_month_str):
                            monthly_spend += bucket_spend
                
                if len(buckets) < 100:
                    has_more = False
                else:
                    if last_bucket_end <= current_query_start:
                         current_query_start += 86400
                    else:
                        current_query_start = last_bucket_end
                
                loop_count += 1
                time.sleep(0.05)

            except Exception as e:
                logger.error(f"Failed to fetch costs: {e}")
                has_more = False

        # Persist finalized history
        if new_spend_finalized > 0 or last_processed_time > ledger.get("start_date", 0):
            ledger["historical_spend"] = historical_spend + new_spend_finalized
            ledger["start_date"] = int(last_processed_time)
            # IMPORTANT: We save the monthly_history back to ledger. 
            # Note: This contains EVERYTHING (old banked + new finalized + new ephemeral).
            # We should technically only save the finalized parts to avoid "drift" if we crash?
            # Actually, saving ephemeral parts is harmless because next time we load, we might double count?
            # YES. If we save ephemeral 'Dec 2025'=$10 now.
            # Next time, we load 'Dec 2025'=$10.
            # Then we re-fetch 'Dec 2025' (because start_date is Nov 30). We get $10.
            # We add it: $10 + $10 = $20. DOUBLE COUNT.
            
            # FIX: We must NOT save ephemeral months to the ledger!
            # We need to filter `monthly_history` before saving.
            
            # Create a clean map for saving (only finalized months)
            # We know finalized months are anything BEFORE current_month_str? 
            # Or roughly based on checkpoint.
            
            map_to_save = {}
            current_display = now_utc.strftime('%b %Y')
            
            for k, v in monthly_history.items():
                if k != current_display:
                    map_to_save[k] = v
            
            ledger["monthly_history"] = map_to_save
            self._save_ledger(ledger)
            logger.info(f"Banked ${new_spend_finalized:.2f} into history. New start_date: {ledger['start_date']}")

        total_accumulated = ledger["historical_spend"] + new_spend_ephemeral
        
        history_list = [{"month": k, "amount": v} for k, v in monthly_history.items()]
        # Sort by month
        try:
            history_list.sort(key=lambda x: datetime.strptime(x["month"], "%b %Y"), reverse=True)
        except:
            pass

        return {
            "total": total_accumulated,
            "daily": daily_spend,
            "monthly": monthly_spend,
            "history": history_list
        }

    def get_balance(self):
        ledger = self._load_ledger()
        costs = self.get_aggregated_costs()
        spend = costs["total"]
        balance = ledger["total_deposited"] - spend
        return {
            "balance": round(balance, 2),
            "total_deposited": ledger["total_deposited"],
            "total_spend": round(spend, 2),
            "daily_usage": round(costs["daily"], 2),
            "monthly_usage": round(costs["monthly"], 2),
            "history": costs["history"],
            "currency": "USD"
        }

    def check_and_alert(self):
        status = self.get_balance()
        balance = status["balance"]
        ledger = self._load_ledger()
        logger.info(f"Current Balance Check: ${balance}. Threshold: ${self.threshold}")
        if balance < self.threshold:
            last_sent = ledger.get("last_alert_sent", 0)
            # Alert every 2 hours (7200 seconds)
            if (time.time() - last_sent) > 7200:
                # Quiet hours check (9 PM to 6 AM)
                current_hour = datetime.now().hour
                if 6 <= current_hour < 21:
                    self.send_email_alert(balance)
                    ledger["last_alert_sent"] = time.time()
                    self._save_ledger(ledger)
                else:
                    logger.info("Skipping alert due to quiet hours (9PM - 6AM)")
        return status

    def send_email_alert(self, balance):
        if not self.smtp_user or not self.smtp_pass:
            logger.warning("SMTP credentials not set. Skipping email alert.")
            return

        msg = EmailMessage()
        msg["Subject"] = f"ACTION REQUIRED: OpenAI Credit Balance Critical (${balance:.2f})"
        msg["From"] = self.smtp_user
        msg["To"] = self.recipient_email

        # Professional HTML Template
        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
              <div style="background-color: #d32f2f; color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">CRITICAL ALERT: Low Balance</h2>
              </div>
              <div style="padding: 30px;">
                <p>Dear Team,</p>
                <p>This is an automated notification from the <strong>OpenAI Financial Monitor</strong>.</p>
                <p>The available prepaid credit balance for the organization has dropped below the configured safety threshold.</p>
                
                <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                  <tr style="background-color: #f9f9f9;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Current Balance:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">${balance:.2f}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Alert Threshold:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${self.threshold:.2f}</td>
                  </tr>
                  <tr style="background-color: #f9f9f9;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Timestamp:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                  </tr>
                </table>

                <p style="font-weight: bold;">Immediate Action Required:</p>
                <p>Please recharge the OpenAI account immediately to ensure uninterrupted service for production applications.</p>
                
                <div style="text-align: center; margin-top: 30px;">
                  <a href="https://platform.openai.com/settings/organization/billing/overview" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Go to OpenAI Billing Dashboard</a>
                </div>
              </div>
              <div style="background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                <p>&copy; {datetime.now().year} Darwix AI Automation. All rights reserved.</p>
                <p>This is an automated system message. Please do not reply directly to this email.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        msg.add_alternative(html_content, subtype='html')

        try:
            logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
            
            if self.smtp_port == 465:
                # Use SMTP_SSL for port 465
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
            else:
                # Use standard SMTP + STARTTLS for 587 or others
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
            
            logger.info(f"Alert email sent to recipients: {self.recipient_email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
