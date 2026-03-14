import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
import json
import os

# Portfolio data file path
PORTFOLIO_FILE = "portfolio_data.json"

# --- PORTFOLIO PERSISTENCE FUNCTIONS ---
def load_portfolio_from_file():
    """Load portfolio data from JSON file"""
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            st.warning(f"Could not load portfolio data: {e}")
            return []
    return []

def save_portfolio_to_file(portfolio_data):
    """Save portfolio data to JSON file"""
    try:
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(portfolio_data, f, indent=4)
        return True
    except IOError as e:
        st.error(f"Could not save portfolio data: {e}")
        return False

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

# --- PORTFOLIO HELPER FUNCTIONS ---
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_current_price(ticker: str):
    """Get current price for a ticker using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except:
        return None

def add_to_portfolio(ticker: str, quantity: float, buy_price: float):
    """Add a stock to the portfolio"""
    st.session_state.portfolio.append({
        'ticker': ticker.upper(),
        'quantity': quantity,
        'buy_price': buy_price,
        'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    # Save to file
    save_portfolio_to_file(st.session_state.portfolio)

def remove_from_portfolio(index: int):
    """Remove a stock from the portfolio"""
    if 0 <= index < len(st.session_state.portfolio):
        st.session_state.portfolio.pop(index)
        # Save to file
        save_portfolio_to_file(st.session_state.portfolio)

def initialize_portfolio():
    """Initialize portfolio from file if not already loaded"""
    if 'portfolio_loaded' not in st.session_state:
        st.session_state.portfolio = load_portfolio_from_file()
        st.session_state.portfolio_loaded = True

def clear_portfolio():
    """Clear all portfolio data"""
    st.session_state.portfolio = []
    save_portfolio_to_file([])

def export_portfolio_json():
    """Export portfolio as JSON string for download"""
    return json.dumps(st.session_state.portfolio, indent=4)

def calculate_portfolio_value():
    """Calculate total portfolio value and P&L"""
    total_invested = 0
    total_current = 0
    
    for holding in st.session_state.portfolio:
        ticker = holding['ticker']
        quantity = holding['quantity']
        buy_price = holding['buy_price']
        
        current_price = get_current_price(ticker)
        if current_price:
            total_invested += quantity * buy_price
            total_current += quantity * current_price
    
    total_pnl = total_current - total_invested
    pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    return {
        'total_invested': total_invested,
        'total_current': total_current,
        'total_pnl': total_pnl,
        'pnl_percent': pnl_percent
    }

# --- FUNCTION: Display Portfolio Page ---
def display_portfolio_page():
    """Display the portfolio management page"""
    # Initialize portfolio from file
    initialize_portfolio()
    
    st.title("💼 My Portfolio")
    
    # Portfolio Management Buttons
    col1, col2, col3, col4 = st.columns([5, 1.5, 1, 1])
    with col1:
        # Show last saved info
        if os.path.exists(PORTFOLIO_FILE):
            last_modified = os.path.getmtime(PORTFOLIO_FILE)
            last_saved = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')
            st.caption(f"💾 Last saved: {last_saved}")
        else:
            st.caption("💾 No saved portfolio data")
    with col2:
        if st.session_state.portfolio:
            st.caption(f"📊 {len(st.session_state.portfolio)} stocks")
    with col3:
        if st.session_state.portfolio:
            portfolio_json = export_portfolio_json()
            st.download_button(
                label="📥 Export",
                data=portfolio_json,
                file_name=f"portfolio_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Download portfolio as JSON backup",
                use_container_width=True
            )
    with col4:
        if st.session_state.portfolio:
            if st.button("🗑️ Clear All", help="Clear entire portfolio", use_container_width=True, type="secondary"):
                if st.session_state.get('confirm_clear', False):
                    clear_portfolio()
                    st.success("Portfolio cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm clearing all data")
    
    # Reset confirmation if user didn't click again
    if st.session_state.get('confirm_clear', False) and len(st.session_state.portfolio) > 0:
        # This will reset after any other action
        pass
    
    st.markdown("---")
    
    # Calculate portfolio metrics
    if st.session_state.portfolio:
        portfolio_stats = calculate_portfolio_value()
        
        # Top Summary Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Invested</div>
                <div class="metric-value">${portfolio_stats['total_invested']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Current Value</div>
                <div class="metric-value">${portfolio_stats['total_current']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pnl_class = "prediction-up" if portfolio_stats['total_pnl'] >= 0 else "prediction-down"
            pnl_arrow = "▲" if portfolio_stats['total_pnl'] >= 0 else "▼"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value {pnl_class}">{pnl_arrow} ${portfolio_stats['total_pnl']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            pnl_class = "prediction-up" if portfolio_stats['pnl_percent'] >= 0 else "prediction-down"
            pnl_arrow = "▲" if portfolio_stats['pnl_percent'] >= 0 else "▼"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Return</div>
                <div class="metric-value {pnl_class}">{pnl_arrow} {portfolio_stats['pnl_percent']:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Add Stock Form
    with st.expander("➕ Add Stock to Portfolio", expanded=not st.session_state.portfolio):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            new_ticker = st.text_input("Ticker Symbol", placeholder="e.g., AAPL, TSLA", key="new_ticker")
        with col2:
            new_quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.01, key="new_quantity")
        with col3:
            new_buy_price = st.number_input("Buy Price", min_value=0.01, value=100.0, step=0.01, key="new_buy_price")
        with col4:
            st.write("")
            st.write("")
            if st.button("Add Stock", type="primary", use_container_width=True):
                if new_ticker:
                    add_to_portfolio(new_ticker, new_quantity, new_buy_price)
                    st.success(f"Added {new_quantity} shares of {new_ticker.upper()} to portfolio!")
                    st.rerun()
                else:
                    st.error("Please enter a ticker symbol")
    
    # Display Portfolio Holdings
    if st.session_state.portfolio:
        st.subheader("📊 Holdings")
        
        # Create portfolio dataframe with current prices
        portfolio_data = []
        for i, holding in enumerate(st.session_state.portfolio):
            ticker = holding['ticker']
            quantity = holding['quantity']
            buy_price = holding['buy_price']
            current_price = get_current_price(ticker)
            
            if current_price:
                invested = quantity * buy_price
                current_value = quantity * current_price
                pnl = current_value - invested
                pnl_percent = (pnl / invested * 100) if invested > 0 else 0
                currency = get_currency_symbol(ticker)
                
                portfolio_data.append({
                    'Ticker': ticker,
                    'Quantity': quantity,
                    'Buy Price': f"{currency}{buy_price:,.2f}",
                    'Current Price': f"{currency}{current_price:,.2f}",
                    'Invested': f"{currency}{invested:,.2f}",
                    'Current Value': f"{currency}{current_value:,.2f}",
                    'P&L': f"{currency}{pnl:,.2f}",
                    'P&L %': f"{pnl_percent:+.2f}%",
                    'Index': i
                })
        
        if portfolio_data:
            df = pd.DataFrame(portfolio_data)
            
            # Display header row
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])
            with col1:
                st.markdown("**Ticker**")
            with col2:
                st.markdown("**Quantity**")
            with col3:
                st.markdown("**Buy Price**")
            with col4:
                st.markdown("**Current Price**")
            with col5:
                st.markdown("**Invested**")
            with col6:
                st.markdown("**Current Value**")
            with col7:
                st.markdown("**P&L**")
            with col8:
                st.markdown("**P&L %**")
            with col9:
                st.markdown("**Action**")
            
            st.markdown("---")
            
            # Display data rows
            for idx, row in df.iterrows():
                col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])
                
                with col1:
                    st.write(f"**{row['Ticker']}**")
                with col2:
                    st.write(row['Quantity'])
                with col3:
                    st.write(row['Buy Price'])
                with col4:
                    st.write(row['Current Price'])
                with col5:
                    st.write(row['Invested'])
                with col6:
                    st.write(row['Current Value'])
                with col7:
                    pnl_value = row['P&L']
                    if '-' in pnl_value:
                        st.markdown(f"<span style='color: #ef4444;'>{pnl_value}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: #22c55e;'>{pnl_value}</span>", unsafe_allow_html=True)
                with col8:
                    pnl_pct = row['P&L %']
                    if '-' in pnl_pct:
                        st.markdown(f"<span style='color: #ef4444;'>{pnl_pct}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: #22c55e;'>{pnl_pct}</span>", unsafe_allow_html=True)
                with col9:
                    if st.button("🗑️", key=f"delete_{row['Index']}", help="Remove from portfolio"):
                        remove_from_portfolio(row['Index'])
                        st.rerun()
                
                st.markdown("---")
            
            # Portfolio Composition Chart
            st.subheader("📈 Portfolio Composition")
            
            # Prepare data for pie chart
            composition_data = []
            for holding in st.session_state.portfolio:
                ticker = holding['ticker']
                quantity = holding['quantity']
                current_price = get_current_price(ticker)
                if current_price:
                    current_value = quantity * current_price
                    composition_data.append({
                        'Ticker': ticker,
                        'Value': current_value
                    })
            
            if composition_data:
                comp_df = pd.DataFrame(composition_data)
                fig = go.Figure(data=[go.Pie(
                    labels=comp_df['Ticker'],
                    values=comp_df['Value'],
                    hole=0.3,
                    marker=dict(colors=['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'])
                )])
                fig.update_layout(
                    title="Portfolio Distribution by Value",
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👆 Your portfolio is empty. Add your first stock using the form above!")