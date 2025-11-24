# 📈 StockSentry AI - Stock Price Prediction System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=Streamlit&logoColor=white)](https://streamlit.io)
[![GitHub](https://img.shields.io/badge/GitHub-StockSentry--AI-181717?logo=github)](https://github.com/Navneetg2003/StockSentry-AI)

An AI-powered stock price prediction system that combines machine learning, FinBERT sentiment analysis, and real-time news integration to predict next-day stock prices with high accuracy.

> ⚠️ **Disclaimer**: This tool is for educational and research purposes only. Not financial advice. Always do your own research before making investment decisions.

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start---step-by-step)
- [Usage](#-usage)
- [Supported Markets](#-supported-markets--currencies)
- [How It Works](#-how-it-works)
- [Configuration](#️-configuration)
- [Project Structure](#️-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🎥 Demo

### Sample Prediction Output
```
Company: Apple Inc. (AAPL)
Current Price: $185.50
Predicted Price (Next Day): $187.25
Expected Change: +0.94% ↗️
Sentiment Score: 0.68 (Positive)
Confidence: High
```

### What You'll See
- 📊 Real-time stock price charts
- 📰 Latest news headlines with sentiment scores
- 🤖 ML model predictions with confidence levels
- 📈 Historical price trends and technical indicators
- 💹 Multi-timeframe analysis

## 🌟 Key Features

### 🤖 AI & Machine Learning
- **Dual ML Models**: Random Forest and XGBoost with time-series cross-validation
- **FinBERT Sentiment Analysis**: Analyzes financial news using state-of-the-art NLP
- **Feature Engineering**: 20+ technical indicators including MA, volatility, and momentum

### 📊 Market Coverage
- **Multi-Market Support**: US, Indian (NSE/BSE), UK, European, Japanese exchanges
- **Smart Ticker Resolution**: Enter "Apple" or "AAPL" - both work!
- **Dynamic Currency Display**: Auto-detects exchange and shows correct currency (₹, $, £, €, ¥)

### 🎨 User Experience
- **Interactive Dashboard**: Beautiful Streamlit UI with real-time charts
- **Live News Integration**: Fetches latest headlines via n8n workflow
- **Comprehensive Visualizations**: Plotly charts, price trends, sentiment graphs
- **One-Click Predictions**: Simple interface for complex analysis

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

### Step 1: Clone the Repository
```bash
# Clone from GitHub
git clone https://github.com/Navneetg2003/StockSentry-AI.git
cd StockSentry-AI

# OR download ZIP and extract
cd "f:\StockSentry-AI"
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
cd "f:\StockSentry-AI"

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

### Common Issues

#### FinBERT Model Download
**Problem**: First run takes long time or fails  
**Solution**: 
- First run downloads ~400MB FinBERT model
- Ensure stable internet connection
- Model is cached locally after first download
- Check `~/.cache/huggingface/` for downloaded models

#### Execution Policy Error (Windows)
**Problem**: `.\venv\Scripts\Activate.ps1 cannot be loaded`  
**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Webhook Timeouts
**Problem**: n8n webhook times out or fails  
**Solution**: 
- System continues with existing Google Sheet data
- Check n8n workflow status
- Verify webhook URL in settings
- Use test_webhook.py to debug

#### Missing Stock Data
**Problem**: "No data available for this ticker"  
**Solution**: 
- Verify ticker symbol is correct
- Add exchange suffix (.NS for NSE, .BO for BSE, etc.)
- Some stocks have limited historical data
- Try different date ranges (3-6 months recommended)

#### Currency Not Showing Correctly
**Problem**: Wrong currency symbol displayed  
**Solution**: 
- Ensure ticker has correct exchange suffix
- Examples: RELIANCE.NS (₹), AAPL ($), BP.L (£)
- Check supported markets table

#### Import Errors
**Problem**: `ModuleNotFoundError`  
**Solution**:
```powershell
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Or install specific package
pip install streamlit yfinance transformers
```

#### Port Already in Use
**Problem**: `Port 8501 is already in use`  
**Solution**:
```powershell
# Use different port
streamlit run app.py --server.port 8502

# Or kill existing process
netstat -ano | findstr :8501
taskkill /PID <process_id> /F
```

## 📝 Important Notes

- **Educational Purpose**: Predictions are for educational and research purposes only - **NOT financial advice**
- **Fresh Training**: Model trains from scratch on each run (no model persistence)
- **Sentiment Impact**: News sentiment has 15% base weight in final predictions
- **Data Window**: Uses last 6 months of historical data by default
- **Real-time Analysis**: Sentiment scores computed fresh on each run (no caching)
- **Market Hours**: Predictions work 24/7, but market data updates only during trading hours
- **Accuracy**: Past performance doesn't guarantee future results

## 🚀 Future Enhancements

- [ ] Model persistence and incremental training
- [ ] Multiple timeframe predictions (1 day, 1 week, 1 month)
- [ ] Portfolio analysis and optimization
- [ ] Real-time price updates via WebSocket
- [ ] Backtesting framework
- [ ] Technical analysis indicators dashboard
- [ ] Email/SMS alerts for price targets
- [ ] API endpoint for programmatic access

## ❓ Frequently Asked Questions (FAQ)

### Q: Is this suitable for real trading decisions?
**A**: No. This is an educational project. Never make investment decisions based solely on AI predictions. Always consult financial advisors and do thorough research.

### Q: How accurate are the predictions?
**A**: Accuracy varies by stock and market conditions. The model is trained on historical data and sentiment, but markets are unpredictable. Use predictions as one of many data points.

### Q: Can I use this for cryptocurrencies?
**A**: Yes! Use crypto tickers like `BTC-USD`, `ETH-USD`, etc. However, crypto markets are highly volatile.

### Q: How often should I retrain the model?
**A**: The model retrains automatically on each prediction using the latest 6 months of data.

### Q: What if my company name isn't recognized?
**A**: Use the exact ticker symbol with exchange suffix (e.g., `RELIANCE.NS` for Reliance on NSE).

### Q: Can I run this on a server 24/7?
**A**: Yes! Deploy on cloud platforms like AWS, Google Cloud, or Heroku. Update the Streamlit config for production use.

### Q: Does it work without the n8n webhook?
**A**: Yes. If the webhook fails, it falls back to Google Sheets data or continues without sentiment analysis.

### Q: How much RAM do I need?
**A**: Minimum 4GB RAM recommended. 8GB+ preferred for smooth operation with FinBERT model.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
   ```bash
   git clone https://github.com/Navneetg2003/StockSentry-AI.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Add new features
   - Fix bugs
   - Improve documentation
   - Optimize performance

4. **Commit your changes**
   ```bash
   git commit -m "Add: amazing feature description"
   ```

5. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**
   - Provide clear description of changes
   - Include screenshots/examples if applicable
   - Reference any related issues

### Contribution Guidelines
- Follow PEP 8 style guide for Python code
- Add comments for complex logic
- Update README.md if needed
- Test thoroughly before submitting

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **FinBERT Model**: [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert) for financial sentiment analysis
- **Yahoo Finance**: Free stock market data API via [yfinance](https://github.com/ranaroussi/yfinance)
- **Streamlit**: Amazing framework for building ML web apps
- **HuggingFace**: Transformer models and NLP infrastructure
- **n8n**: Workflow automation for news integration
- **Open Source Community**: All the amazing libraries that make this possible

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Navneetg2003/StockSentry-AI/issues)
- **Developer**: [Navneetg2003](https://github.com/Navneetg2003)

## ⭐ Show Your Support

If you find this project helpful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 🤝 Contributing to the code

---

**Made with ❤️ by stock market enthusiasts for AI learners**

*Last Updated: November 2025*
