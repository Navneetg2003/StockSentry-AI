# 📈 StockSentry AI - Stock Price Prediction System

An AI-powered stock price prediction system that combines machine learning, FinBERT sentiment analysis, and real-time news integration to predict next-day stock prices.

## 🌟 Features

- **Smart Ticker Resolution**: Enter company names (e.g., "Apple", "Adani Power") or tickers (e.g., "AAPL", "RELIANCE.NS")
- **Sentiment Analysis**: Uses FinBERT AI model to analyze financial news headlines
- **Multi-Market Support**: US, Indian (NSE/BSE), UK, European, Japanese, and other global exchanges
- **Dynamic Currency Display**: Automatically shows correct currency symbol based on stock exchange
- **Real-time News Integration**: Fetches latest news via n8n workflow integration
- **Interactive Dashboard**: Beautiful Streamlit UI with charts and visualizations
- **Machine Learning**: Random Forest and XGBoost models with time-series cross-validation

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **ML/AI**: scikit-learn, XGBoost, HuggingFace Transformers (FinBERT)
- **Data**: yfinance, pandas, numpy
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Integration**: n8n webhook, Google Sheets API

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection (for fetching stock data and news)

## 🚀 Quick Start - Step by Step

### Step 1: Download/Clone the Project
```bash
# If using Git
git clone <your-repo-url>
cd <project-folder>

# OR download ZIP and extract to a folder like:
cd "f:\New folder"
```

### Step 2: Create Virtual Environment
```powershell
# Windows PowerShell (RECOMMENDED)
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Alternative for Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install All Dependencies
```powershell
# Make sure you see (venv) at the start of your terminal prompt
pip install -r requirements.txt

# This will install (~500MB total):
# ✓ streamlit - Web interface
# ✓ yfinance - Stock market data
# ✓ scikit-learn, xgboost - ML models
# ✓ transformers, torch - FinBERT AI (~400MB)
# ✓ gspread - Google Sheets integration
# ✓ plotly, matplotlib - Charts
```

**Wait for installation to complete** (may take 3-5 minutes)

### Step 4: Verify Installation
```powershell
# Check if packages installed correctly
pip list | Select-String "streamlit|yfinance|transformers"

# You should see version numbers for all three packages
```

### Step 5: Run the Application
```powershell
# Start the Streamlit web app
streamlit run app.py

# The terminal will show:
# Local URL: http://localhost:8501
# Network URL: http://192.168.x.x:8501
```

**Your browser will automatically open** to http://localhost:8501

### Step 6: Use the Stock Predictor

1. **Enter a company** in the text box:
   - Company name: "Apple", "Tesla", "Reliance", "Adani Power"
   - Or ticker: "AAPL", "TSLA", "RELIANCE.NS", "ADANIPOWER.NS"

2. **Click "Predict Stock Price"**

3. **Wait 30-60 seconds** for:
   - Stock data download
   - News fetching (n8n webhook)
   - Sentiment analysis (FinBERT)
   - ML model training

4. **View Results**:
   - Current price with currency (₹ for India, $ for US)
   - Tomorrow's predicted price
   - Expected change %
   - Interactive charts
   - Sentiment analysis

---

## 🔄 Running Again (After First Setup)

Every time you want to use the app:

```powershell
# 1. Open PowerShell and navigate to project folder
cd "f:\New folder"

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Run the app
streamlit run app.py

# 4. Open browser to http://localhost:8501
```

## ⏹️ Stopping the Application

```powershell
# In the terminal running Streamlit:
# Press Ctrl + C

# Then deactivate virtual environment:
deactivate
```

## 🎯 Access the App
Once running:
- **Local**: http://localhost:8501
- **Network**: http://<your-ip>:8501 (for other devices on same network)

## 💻 Usage

### Web Interface
1. Enter a company name or ticker symbol (e.g., "Apple" or "AAPL")
2. Click "Run Analysis"
3. View:
   - Current price
   - Predicted price for tomorrow
   - Expected change percentage
   - Interactive charts
   - Historical data

### Command Line
```bash
python backend.py
# Follow the prompts to enter company/ticker
```

## 🌍 Supported Markets & Currencies

| Exchange | Suffix | Currency | Example |
|----------|--------|----------|---------|
| US (NASDAQ/NYSE) | - | $ (USD) | AAPL, MSFT, GOOGL |
| India (NSE) | .NS | ₹ (INR) | RELIANCE.NS, TCS.NS |
| India (BSE) | .BO | ₹ (INR) | TATAMOTORS.BO |
| UK (LSE) | .L | £ (GBP) | BP.L, HSBA.L |
| Europe | .PA/.DE/.MI | € (EUR) | SAP.DE, AIR.PA |
| Japan | .T | ¥ (JPY) | SONY.T, 7203.T |
| Hong Kong | .HK | HK$ | 0700.HK |
| Canada | .TO | CA$ | SHOP.TO |
| Australia | .AX | A$ | BHP.AX |

## 📊 How It Works

1. **Ticker Resolution**: Converts company names to ticker symbols using built-in alias map and Yahoo Finance search
2. **News Fetching**: Triggers n8n webhook to fetch latest news headlines
3. **Historical Data**: Downloads 6 months of stock price data from Yahoo Finance
4. **Feature Engineering**: Creates technical indicators (moving averages, volatility, returns)
5. **Sentiment Analysis**: Runs FinBERT on news headlines to compute sentiment scores
6. **Model Training**: Trains Random Forest/XGBoost on historical data with time-series validation
7. **Prediction**: Combines ML prediction with sentiment-weighted adjustment
8. **Results**: Displays predicted next-day price with currency and change percentage

## ⚙️ Configuration

### Environment Variables (Optional)
Create a `.env` file:
```env
# Google Sheets (if using service account)
GOOGLE_SHEET_NAME=stocksentry
GOOGLE_SHEET_ID=1sUCmw_J13onwgsHqMxPUkBaY3-TvSBRlfow7ZiuyX1A
SERVICE_ACCOUNT_FILE=credentials.json

# n8n Webhook
N8N_WEBHOOK_URL=https://navneetgupta.app.n8n.cloud/webhook/138bb9dd-f80c-4c3a-a941-f90b62870a37

# Logging
LOG_LEVEL=INFO
```

**Google Sheets Setup**:
- Sheet URL: https://docs.google.com/spreadsheets/d/1sUCmw_J13onwgsHqMxPUkBaY3-TvSBRlfow7ZiuyX1A/edit
- Required Columns: `headline`, `snippet` (lowercase)
- Must be set to public view access for CSV export OR use service account authentication

### Advanced Settings (in Streamlit UI)
- Google Sheet Name
- n8n Webhook URL
- Service Account Path

## 🗂️ Project Structure

```
.
├── app.py                  # Streamlit web interface
├── backend.py              # Core ML and sentiment logic
├── requirements.txt        # Python dependencies
├── test_webhook.py         # Webhook testing utility
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── .venv/                 # Virtual environment (created)
```

## 📦 Dependencies

Key packages:
- `streamlit` - Web interface
- `pandas`, `numpy` - Data manipulation
- `yfinance` - Stock data
- `scikit-learn`, `xgboost` - Machine learning
- `transformers`, `torch` - FinBERT sentiment analysis
- `plotly`, `matplotlib`, `seaborn` - Visualization
- `gspread`, `oauth2client` - Google Sheets integration
- `requests` - HTTP requests

See `requirements.txt` for complete list.

## 🎯 Example Companies

Try these company names:
- **US**: Apple, Microsoft, Tesla, Amazon, Google
- **India**: Reliance Industries, Tata Motors, Adani Power, HDFC Bank
- **Or use tickers directly**: AAPL, TSLA, RELIANCE.NS, TATAMOTORS.NS

## 🔧 Troubleshooting

### FinBERT Model Download
First run downloads ~400MB FinBERT model. Ensure stable internet connection.

### Webhook Timeouts
If n8n webhook times out, the system continues with existing sheet data.

### Missing Data
Some stocks may have limited historical data. Try using 3-6 month date ranges.

### Currency Not Showing
Ensure ticker has correct exchange suffix (e.g., .NS for NSE, .L for London).

## 📝 Notes

- **Predictions are for educational purposes only** - Not financial advice
- Model trains fresh on each run (no persistence)
- Sentiment has 15% base impact on predictions
- Uses last 6 months of data by default
- News sentiment is computed fresh (no caching)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- FinBERT model by ProsusAI
- Yahoo Finance for stock data
- Streamlit for the amazing framework
- HuggingFace for transformer models

---

**Made with ❤️ for stock market enthusiasts and AI learners**
