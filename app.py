import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from datetime import datetime, timedelta

# --- IMPORT YOUR BACKEND ---
try:
    from backend import StockSentryML 
except ImportError:
    st.error("Could not import 'StockSentryML'. Make sure backend.py is in the same folder.")
    st.stop()

# --- IMPORT PORTFOLIO MODULE ---
try:
    from portfolio import display_portfolio_page, get_currency_symbol, initialize_portfolio
except ImportError:
    st.error("Could not import portfolio module. Make sure portfolio.py is in the same folder.")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="StockSentry AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZE SESSION STATE FOR NIGHT MODE ---
if "night_mode" not in st.session_state:
    st.session_state.night_mode = False

# Initialize session state for chart type
if "chart_type" not in st.session_state:
    st.session_state.chart_type = "line"  # 'line' or 'candlestick'

# Initialize session state for storing analysis results
if "cached_results" not in st.session_state:
    st.session_state.cached_results = None

# Initialize session state for portfolio (will be loaded from file)
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "Analysis"

# Load portfolio from file on app start
initialize_portfolio()

# --- DYNAMIC CSS BASED ON NIGHT MODE ---
def get_theme_css(is_night_mode: bool) -> str:
    """Generate CSS for light or dark mode"""
    if is_night_mode:
        # Dark mode colors
        bg_color = "#0e1117"
        secondary_bg = "#262730"
        card_bg = "#1e1e1e"
        card_text = "#ffffff"
        card_label = "#b0b0b0"
        text_color = "#fafafa"
        secondary_text = "#a0a0a0"
        border_color = "#333333"
        card_shadow = "rgba(255,255,255,0.1)"
        input_bg = "#262730"
        input_text = "#fafafa"
        return f"""
        <style>
            /* Main app background */
            .stApp {{
                background-color: {bg_color};
                color: {text_color};
            }}
            
            /* Sidebar styling */
            [data-testid="stSidebar"] {{
                background-color: {secondary_bg};
            }}
            
            [data-testid="stSidebar"] .stMarkdown {{
                color: {text_color};
            }}
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {{
                color: {text_color} !important;
            }}
            
            /* Regular text */
            p, span, div, label {{
                color: {text_color};
            }}
            
            /* Input fields */
            .stTextInput input {{
                background-color: {input_bg} !important;
                color: {input_text} !important;
                border-color: {border_color} !important;
            }}
            
            /* Buttons */
            .stButton button {{
                background-color: {secondary_bg};
                color: {text_color};
                border: 1px solid {border_color};
            }}
            
            .stButton button:hover {{
                background-color: {card_bg};
                border-color: {card_label};
            }}
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {{
                background-color: {secondary_bg};
            }}
            
            .stTabs [data-baseweb="tab"] {{
                color: {secondary_text};
            }}
            
            .stTabs [aria-selected="true"] {{
                color: {text_color} !important;
            }}
            
            /* DataFrames */
            .stDataFrame {{
                background-color: {secondary_bg};
                color: {text_color};
            }}
            
            /* Expander */
            .streamlit-expanderHeader {{
                background-color: {secondary_bg} !important;
                color: {text_color} !important;
            }}
            
            .streamlit-expanderContent {{
                background-color: {secondary_bg};
                border-color: {border_color};
            }}
            
            /* Info/Success/Warning boxes */
            .stAlert {{
                background-color: {secondary_bg};
                color: {text_color};
                border-color: {border_color};
            }}
            
            /* Metric cards */
            .metric-card {{
                background-color: {card_bg};
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 2px 2px 10px {card_shadow};
                border: 1px solid {border_color};
            }}
            
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: {card_text};
            }}
            
            .metric-label {{
                font-size: 14px;
                color: {card_label};
            }}
            
            .prediction-up {{ color: #4ade80; }}
            .prediction-down {{ color: #f87171; }}
            
            /* Horizontal rule */
            hr {{
                border-color: {border_color};
            }}
            
            /* Spinner */
            .stSpinner > div {{
                border-top-color: {text_color} !important;
            }}
        </style>
        """
    else:
        # Light mode colors
        bg_color = "#ffffff"
        secondary_bg = "#f0f2f6"
        card_bg = "#f8f9fa"
        card_text = "#262626"
        card_label = "#666666"
        text_color = "#262626"
        secondary_text = "#555555"
        border_color = "#e0e0e0"
        card_shadow = "rgba(0,0,0,0.08)"
        return f"""
        <style>
            /* Main app background */
            .stApp {{
                background-color: {bg_color};
                color: {text_color};
            }}
            
            /* Sidebar styling */
            [data-testid="stSidebar"] {{
                background-color: {secondary_bg};
            }}
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {{
                color: {text_color} !important;
            }}
            
            /* Regular text */
            p, span, div, label {{
                color: {text_color};
            }}
            
            /* Input fields */
            .stTextInput input {{
                background-color: {bg_color} !important;
                color: {text_color} !important;
                border-color: {border_color} !important;
            }}
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {{
                background-color: {secondary_bg};
            }}
            
            .stTabs [data-baseweb="tab"] {{
                color: {secondary_text};
            }}
            
            .stTabs [aria-selected="true"] {{
                color: {text_color} !important;
            }}
            
            /* Metric cards */
            .metric-card {{
                background-color: {card_bg};
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 2px 2px 10px {card_shadow};
                border: 1px solid {border_color};
            }}
            
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: {card_text};
            }}
            
            .metric-label {{
                font-size: 14px;
                color: {card_label};
            }}
            
            .prediction-up {{ color: #22c55e; }}
            .prediction-down {{ color: #ef4444; }}
            
            /* Horizontal rule */
            hr {{
                border-color: {border_color};
            }}
        </style>
        """

# Apply theme CSS
st.markdown(get_theme_css(st.session_state.night_mode), unsafe_allow_html=True)

# --- FinBERT: Load once per server session, reused across all runs ---
@st.cache_resource(show_spinner="Loading FinBERT model (first time only)...")
def load_finbert_pipeline():
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    model_name = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1)

# --- FUNCTION: Display Analysis Results ---
def display_results(stock_sentry, resolved_ticker, predicted_price, latest_price, company_input, end_date, start_date):
    """Display all analysis results"""
    change = predicted_price - latest_price
    pct_change = (change / latest_price) * 100
    color_class = "prediction-up" if change >= 0 else "prediction-down"
    arrow = "▲" if change >= 0 else "▼"
    currency = get_currency_symbol(resolved_ticker)
    
    # Display results header
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
        # Chart type toggle
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(f"{resolved_ticker}: Price vs. Sentiment Analysis")
        with col2:
            if st.button("📊 " + ("Candlestick" if st.session_state.chart_type == "line" else "Line Chart"), 
                        key="chart_toggle", 
                        help="Toggle between Line Chart and Candlestick Chart",
                        use_container_width=True):
                st.session_state.chart_type = "candlestick" if st.session_state.chart_type == "line" else "line"
                st.rerun()
        
        # Interactive price and sentiment chart
        if stock_sentry.data is not None and len(stock_sentry.data) > 0:
            plot_data = stock_sentry.data.copy()
            
            # Handle both 'Date' and 'date' columns
            date_col = 'date' if 'date' in plot_data.columns else 'Date'
            close_col = 'Close' if 'Close' in plot_data.columns else 'close'
            
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            if st.session_state.chart_type == "candlestick":
                # Candlestick Chart
                open_col = 'Open' if 'Open' in plot_data.columns else 'open'
                high_col = 'High' if 'High' in plot_data.columns else 'high'
                low_col = 'Low' if 'Low' in plot_data.columns else 'low'
                
                fig.add_trace(
                    go.Candlestick(
                        x=plot_data[date_col],
                        open=plot_data[open_col],
                        high=plot_data[high_col],
                        low=plot_data[low_col],
                        close=plot_data[close_col],
                        name="Price",
                        increasing_line_color='#22c55e',
                        decreasing_line_color='#ef4444'
                    ),
                    secondary_y=False
                )
            else:
                # Line Chart
                fig.add_trace(
                    go.Scatter(
                        x=plot_data[date_col], 
                        y=plot_data[close_col], 
                        name="Price", 
                        line=dict(color='#3b82f6', width=2)
                    ),
                    secondary_y=False
                )
            
            # Sentiment (if available)
            if 'Sentiment' in plot_data.columns:
                colors = ['#22c55e' if s > 0 else '#ef4444' for s in plot_data['Sentiment']]
                fig.add_trace(
                    go.Bar(
                        x=plot_data[date_col], 
                        y=plot_data['Sentiment'], 
                        name="Sentiment", 
                        marker_color=colors, 
                        opacity=0.4
                    ),
                    secondary_y=True
                )
            
            # Update layout
            fig.update_layout(
                height=500, 
                hovermode="x unified", 
                title_text=f"Price Timeline ({'Candlestick' if st.session_state.chart_type == 'candlestick' else 'Line Chart'})",
                xaxis_title="Date",
                yaxis_title="Price",
                yaxis2_title="Sentiment Score",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Remove rangeslider for cleaner look
            fig.update_xaxes(rangeslider_visible=False)
            
            st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(fig_perf, use_container_width=True)
        else:
            st.info("Model performance metrics unavailable.")

    with tab3:
        st.subheader("Historical Data")
        if stock_sentry.data is not None:
            st.dataframe(stock_sentry.data.tail(100), use_container_width=True)  # Show last 100 rows
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

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.title("🤖 StockSentry AI")
    st.markdown("---")
    
    # Page Navigation
    st.markdown("### 📍 Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Analysis", use_container_width=True, type="primary" if st.session_state.current_page == "Analysis" else "secondary"):
            st.session_state.current_page = "Analysis"
            st.rerun()
    with col2:
        if st.button("💼 Portfolio", use_container_width=True, type="primary" if st.session_state.current_page == "Portfolio" else "secondary"):
            st.session_state.current_page = "Portfolio"
            st.rerun()
    
    st.markdown("---")
    
    # Night Mode Toggle
    st.markdown("### 🎨 Theme")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Night Mode")
    with col2:
        if st.button("🌙" if not st.session_state.night_mode else "☀️", key="theme_toggle", help="Toggle Night Mode", use_container_width=True):
            st.session_state.night_mode = not st.session_state.night_mode
            st.rerun()
    
    st.markdown("---")
    
    # Show analysis inputs only on Analysis page
    if st.session_state.current_page == "Analysis":
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
    else:
        run_btn = False
        company_input = None
        sheet_name = None

# --- MAIN APP LOGIC ---
if st.session_state.current_page == "Portfolio":
    # Display Portfolio Page
    display_portfolio_page()

elif st.session_state.current_page == "Analysis":
    # Analysis Page Logic
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
                    
                    # Get current price for comparison
                    if stock_sentry.data is not None and not stock_sentry.data.empty:
                        latest_price = float(stock_sentry.data.iloc[-1]['Close'])
                    else:
                        st.error("No price data available")
                        st.stop()
                    
                    # Cache the results in session state for theme toggling
                    st.session_state.cached_results = {
                        'stock_sentry': stock_sentry,
                        'resolved_ticker': resolved_ticker,
                        'predicted_price': predicted_price,
                        'latest_price': latest_price,
                        'company_input': company_input,
                        'end_date': end_date,
                        'start_date': start_date
                    }
                    
                    # Display results
                    display_results(stock_sentry, resolved_ticker, predicted_price, latest_price, company_input, end_date, start_date)
                else:
                    st.error("""Prediction failed. Please check the logs and ensure:
    - Service account file exists OR GOOGLE_SHEET_ID is set
    - n8n webhook is accessible
    - Ticker/company name is valid""")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Display cached results if they exist (for theme toggling)
    elif st.session_state.cached_results is not None:
        results = st.session_state.cached_results
        display_results(
            results['stock_sentry'],
            results['resolved_ticker'],
            results['predicted_price'],
            results['latest_price'],
            results['company_input'],
            results['end_date'],
            results['start_date']
        )
    else:
        st.info("👈 Enter your settings in the sidebar and click 'Run Analysis' to start.")