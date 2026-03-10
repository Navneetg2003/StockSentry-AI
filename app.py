import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns

# --- IMPORT YOUR BACKEND ---
try:
    from backend import StockSentryML 
except ImportError:
    st.error("Could not import 'StockSentryML'. Make sure backend.py is in the same folder.")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="StockSentry AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    .prediction-up { color: #28a745; }
    .prediction-down { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTION: Get Currency Symbol ---
def get_currency_symbol(ticker: str) -> str:
    """Determine currency symbol based on ticker exchange suffix"""
    ticker = ticker.upper()
    
    # Indian exchanges
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        return '₹'  # Indian Rupee
    
    # UK exchanges
    elif ticker.endswith('.L'):
        return '£'  # British Pound
    
    # European exchanges
    elif ticker.endswith('.PA') or ticker.endswith('.DE') or ticker.endswith('.MI'):
        return '€'  # Euro
    
    # Japanese exchanges
    elif ticker.endswith('.T'):
        return '¥'  # Japanese Yen
    
    # Hong Kong
    elif ticker.endswith('.HK'):
        return 'HK$'  # Hong Kong Dollar
    
    # Canadian
    elif ticker.endswith('.TO'):
        return 'CA$'  # Canadian Dollar
    
    # Australian
    elif ticker.endswith('.AX'):
        return 'A$'  # Australian Dollar
    
    # Default to USD for US stocks and others
    else:
        return '$'  # US Dollar

# --- FinBERT: Load once per server session, reused across all runs ---
@st.cache_resource(show_spinner="Loading FinBERT model (first time only)...")
def load_finbert_pipeline():
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    model_name = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1)

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.title("🤖 StockSentry AI")
    st.markdown("---")
    
    # Inputs - now accepts company name or ticker
    company_input = st.text_input("Company Name or Ticker", value="AAPL", help="Enter company name (e.g., 'Apple', 'Adani Power') or ticker symbol (e.g., 'AAPL', 'ADANIPOWER.NS')")
    
    # Auto-calculate dates: 6 months ago to today
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # Approximately 6 months
    
    st.markdown("---")
    
    # Secrets Management (Better than hardcoding for a UI)
    # Try to load from .env or Streamlit secrets first
    load_dotenv()
    default_sheet = os.getenv("GOOGLE_SHEET_NAME", "stocksentry")
    # Updated to the user's production webhook URL
    default_webhook = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/138bb9dd-f80c-4c3a-a941-f90b62870a37")
    
    with st.expander("⚙️ Advanced Settings"):
        sheet_name = st.text_input("Google Sheet Name", value=default_sheet)
        webhook_url = st.text_input("n8n Webhook URL", value=default_webhook, help="This is the n8n webhook URL that triggers the news fetching workflow.")
        service_account_path = st.text_input("Service Account Path", value="stsn-478509-8fe20c776dfb.json")

    run_btn = st.button("🚀 Run Analysis", type="primary")

# --- MAIN APP LOGIC ---
if run_btn:
    if not company_input or not sheet_name:
        st.error("Please fill in all required fields (Company/Ticker, Sheet Name).")
    else:
        # Pass raw input; backend's resolve_ticker() is the single source of truth
        normalized_input = company_input.strip()
        
        try:
            # 1. Initialize the Backend (FinBERT loaded once via st.cache_resource)
            finbert_pipeline = load_finbert_pipeline()
            with st.spinner(f"Initializing StockSentry AI..."):
                stock_sentry = StockSentryML(
                    google_sheet_name=sheet_name,
                    service_account_file=service_account_path,
                    webhook_url=webhook_url,
                    preloaded_pipeline=finbert_pipeline
                )

            # 2. Run Full Workflow (resolves ticker, fetches news, trains, predicts)
            with st.spinner(f"Analyzing {normalized_input} (last 6 months data): resolving ticker, fetching news, training models..."):
                # Auto-calculated dates: 6 months to today
                s_date_str = start_date.strftime('%Y-%m-%d')
                e_date_str = end_date.strftime('%Y-%m-%d')
                
                predicted_price = stock_sentry.run_full_workflow(
                    company_or_ticker=normalized_input,
                    start_date=s_date_str,
                    end_date=e_date_str
                )

            if predicted_price is not None:
                # Get resolved ticker for display
                resolved_ticker = stock_sentry.resolve_ticker(normalized_input)
                
                # Get currency symbol based on ticker
                currency = get_currency_symbol(resolved_ticker)
                
                # Get current price for comparison
                if stock_sentry.data is not None and not stock_sentry.data.empty:
                    latest_price = float(stock_sentry.data.iloc[-1]['Close'])
                else:
                    st.error("No price data available")
                    st.stop()
                    
                change = predicted_price - latest_price
                pct_change = (change / latest_price) * 100
                color_class = "prediction-up" if change >= 0 else "prediction-down"
                arrow = "▲" if change >= 0 else "▼"

                # --- DISPLAY RESULTS ---
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                st.success(f"Analysis Complete for {company_input} ({resolved_ticker})!")
                st.info(f"📅 Prediction for: {tomorrow} (Tomorrow)")
                
                # Top Metrics Row
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Current Price ({end_date.strftime('%Y-%m-%d')})</div>
                        <div class="metric-value">{currency}{latest_price:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Predicted Price (Tomorrow)</div>
                        <div class="metric-value {color_class}">{currency}{predicted_price:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Expected Change</div>
                        <div class="metric-value {color_class}">{arrow} {pct_change:.2f}% ({currency}{change:,.2f})</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # --- TABS FOR VISUALIZATIONS ---
                tab1, tab2, tab3, tab4 = st.tabs(["📈 Interactive Dashboard", "📉 Performance", "📰 Raw Data", "📰 News & Sentiment"])

                with tab1:
                    st.subheader(f"{resolved_ticker}: Price vs. Sentiment Analysis")
                    # Interactive price and sentiment chart
                    if stock_sentry.data is not None and len(stock_sentry.data) > 0:
                        plot_data = stock_sentry.data.copy()
                        
                        # Create figure
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # Price Line - handle both 'Date' and 'date' columns
                        date_col = 'date' if 'date' in plot_data.columns else 'Date'
                        close_col = 'Close' if 'Close' in plot_data.columns else 'close'
                        
                        fig.add_trace(
                            go.Scatter(x=plot_data[date_col], y=plot_data[close_col], name="Price", line=dict(color='blue')),
                            secondary_y=False
                        )
                        
                        # Sentiment (if available)
                        if 'Sentiment' in plot_data.columns:
                            colors = ['green' if s > 0 else 'red' for s in plot_data['Sentiment']]
                            fig.add_trace(
                                go.Bar(x=plot_data[date_col], y=plot_data['Sentiment'], name="Sentiment", marker_color=colors, opacity=0.4),
                                secondary_y=True
                            )
                        
                        fig.update_layout(height=500, hovermode="x unified", title_text="Price Timeline")
                        st.plotly_chart(fig, width="stretch")
                    else:
                        st.warning("No sentiment data available to plot.")

                with tab2:
                    st.subheader("Model Performance")
                    if stock_sentry.model is not None and stock_sentry.data is not None:
                        st.info("Model trained successfully. Showing historical price data.")
                        # Show price chart as performance indicator
                        date_col = 'date' if 'date' in stock_sentry.data.columns else 'Date'
                        close_col = 'Close' if 'Close' in stock_sentry.data.columns else 'close'
                        
                        fig_perf = go.Figure()
                        fig_perf.add_trace(go.Scatter(
                            x=stock_sentry.data[date_col], 
                            y=stock_sentry.data[close_col], 
                            name='Historical Price', 
                            mode='lines'
                        ))
                        fig_perf.update_layout(title="Historical Price Performance", height=500)
                        st.plotly_chart(fig_perf, width="stretch")
                    else:
                        st.info("Model performance metrics unavailable.")

                with tab3:
                    st.subheader("Historical Data")
                    if stock_sentry.data is not None:
                        st.dataframe(stock_sentry.data.tail(100))  # Show last 100 rows
                    else:
                        st.warning("No data available")

                with tab4:
                    st.subheader("News Headlines & Sentiment")
                    news_df = stock_sentry.get_headlines_with_sentiment()
                    if news_df is not None and not news_df.empty:
                        st.caption(f"{len(news_df)} headlines fetched from Google Sheet")
                        # Colour-code the sentiment_score column
                        def _colour_score(val):
                            if val > 0.1:
                                return 'color: #28a745; font-weight: bold'
                            elif val < -0.1:
                                return 'color: #dc3545; font-weight: bold'
                            return 'color: #888'
                        styled = news_df.style.applymap(_colour_score, subset=['sentiment_score'])
                        st.dataframe(styled, use_container_width=True)
                    else:
                        st.info("No headlines available. Check that the Google Sheet is populated and the n8n webhook ran successfully.")

            else:
                st.error("""Prediction failed. Please check the logs and ensure:
- Service account file exists OR GOOGLE_SHEET_ID is set
- n8n webhook is accessible
- Ticker/company name is valid""")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
else:
    st.info("👈 Enter your settings in the sidebar and click 'Run Analysis' to start.")