# OpenAI Credit Monitor & Alerting System

A robust, self-hosted financial observability tool for OpenAI. It tracks your prepaid credit usage using the **Costs API** and alerts you via email when your balance drops below a threshold.

Includes a **React Dashboard** for visualization and a **Shadow Ledger** backend (FastAPI) to maintain accurate balance tracking despite API limitations.

![Dashboard Preview](https://via.placeholder.com/800x400?text=OpenAI+Monitor+Dashboard)

## Features

*   **Real-time Cost Tracking:** Queries the official OpenAI Costs API (`/v1/organization/costs`).
*   **Shadow Ledger:** Accurately calculates remaining balance by tracking deposits vs. spend.
*   **Drift Correction:** "Sync Balance" feature allows you to instantly calibrate the system with the official OpenAI dashboard.
*   **Automated Alerts:** Checks balance **every 15 minutes**. Sends an email if `Balance < $10` (configurable).
*   **Dockerized:** Ready for deployment on Google Cloud Run, AWS, or any VPS.

## Prerequisites

1.  **OpenAI Admin API Key:** Must be a **User Key** (starts with `sk-...`) or a Project Key with `Usage` read permissions.
2.  **SMTP Credentials:** An email account to send alerts (e.g., Gmail with App Password).

## Quick Start (Local)

### 1. Setup Backend
1.  Navigate to `backend`:
    ```bash
    cd openai-monitor/backend
    ```
2.  Create a virtual environment & install dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  Configure Environment:
    *   Rename `.env.example` (or create new) to `.env`.
    *   Edit `.env` with your keys:
        ```ini
        OPENAI_ADMIN_KEY=sk-...
        SMTP_EMAIL=your@gmail.com
        SMTP_PASSWORD=your_app_password
        ALERT_RECIPIENT_EMAIL=alert_me_here@example.com
        ```

### 2. Setup Frontend
1.  Navigate to `frontend`:
    ```bash
    cd ../frontend
    ```
2.  Install & Build:
    ```bash
    npm install
    npm run build
    ```

### 3. Run the App
1.  Go back to `backend`:
    ```bash
    cd ../backend
    ```
2.  Start the server:
    ```bash
    ../backend/venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
3.  Open **http://localhost:8000** in your browser.

## Using the Dashboard

1.  **Initial Setup:** When you first run it, the balance will be wrong (likely negative).
2.  **Sync Balance:** Look at your official [OpenAI Billing Dashboard](https://platform.openai.com/settings/organization/billing/overview).
3.  **Enter Amount:** In the "Sync Balance" card on your local dashboard, enter the **exact** Credit Balance you see on OpenAI (e.g., `42.93`).
4.  **Click Sync:** The system will reverse-calculate your total deposits and lock in the correct balance.

## Deployment: Google Cloud Platform (Cloud Run)

This app is optimized for GCP Cloud Run (Serverless).

1.  **Install Google Cloud SDK** and authenticate:
    ```bash
    gcloud auth login
    gcloud config set project [YOUR_PROJECT_ID]
    ```

2.  **Build & Deploy:**
    From the root `openai-monitor/` folder:
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/openai-monitor

    gcloud run deploy openai-monitor \
      --image gcr.io/[YOUR_PROJECT_ID]/openai-monitor \
      --platform managed \
      --allow-unauthenticated \
      --set-env-vars OPENAI_ADMIN_KEY="sk-...",SMTP_EMAIL="...",SMTP_PASSWORD="...",ALERT_RECIPIENT_EMAIL="..."
    ```

3.  **Persistence Note:** Cloud Run is stateless. If the container restarts, the `ledger.json` (and your balance) will reset.
    *   **Solution A:** Use the "Sync Balance" button after a restart.
    *   **Solution B (Advanced):** Mount a Cloud Storage bucket as a volume to persist `ledger.json`.

## Project Structure

*   `backend/monitor.py`: Core logic. Fetches costs, manages ledger, sends emails.
*   `backend/main.py`: FastAPI server & Scheduler (runs every 15 mins).
*   `frontend/`: React application.