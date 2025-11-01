"""Streamlit web dashboard for IMP."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yaml
from pathlib import Path

# Import IMP modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.data_fetcher import DataFetcher
from src.analysis.stock_analyzer import StockAnalyzer
from src.analysis.technical_indicators import TechnicalIndicators
from src.portfolio.portfolio_manager import PortfolioManager
from src.portfolio.transaction import TransactionType
from src.database.db_manager import DatabaseManager
from src.alerts.alert_manager import AlertManager
from src.alerts.email_service import EmailService


# Page config
st.set_page_config(
    page_title="IMP - Investment Management Panel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive {
        color: #00cc00;
    }
    .negative {
        color: #ff0000;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_config():
    """Load configuration."""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


@st.cache_resource
def init_components():
    """Initialize IMP components."""
    config = load_config()

    data_config = config.get("data", {})
    data_fetcher = DataFetcher(
        market_suffix=data_config.get("market_suffix", ".IS"),
        cache_enabled=data_config.get("cache_enabled", True)
    )

    analyzer = StockAnalyzer(data_fetcher)

    portfolio_config = config.get("portfolio", {})
    portfolio = PortfolioManager(
        data_fetcher=data_fetcher,
        commission_rate=portfolio_config.get("commission_rate", 0.001)
    )

    db_config = config.get("database", {})
    db = DatabaseManager(
        db_path=db_config.get("path", "data/imp.db"),
        echo=db_config.get("echo", False)
    )

    email_service = EmailService(enabled=False)  # Disable by default
    alert_manager = AlertManager(data_fetcher=data_fetcher, email_service=email_service)

    return data_fetcher, analyzer, portfolio, db, alert_manager


# Initialize components
data_fetcher, analyzer, portfolio, db, alert_manager = init_components()


def main():
    """Main dashboard application."""

    # Sidebar
    st.sidebar.markdown('<p class="main-header">📊 IMP</p>', unsafe_allow_html=True)
    st.sidebar.markdown("**Investment Management Panel**")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "📈 Stock Analysis", "💼 Portfolio", "👀 Watchlist", "⚠️ Alerts", "📊 Compare Stocks"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "IMP is a comprehensive stock analysis and portfolio management tool "
        "for Borsa Istanbul (BIST) traders."
    )

    # Route to pages
    if page == "🏠 Home":
        show_home_page()
    elif page == "📈 Stock Analysis":
        show_analysis_page()
    elif page == "💼 Portfolio":
        show_portfolio_page()
    elif page == "👀 Watchlist":
        show_watchlist_page()
    elif page == "⚠️ Alerts":
        show_alerts_page()
    elif page == "📊 Compare Stocks":
        show_comparison_page()


def show_home_page():
    """Display home page with overview."""
    st.markdown('<p class="main-header">Dashboard Overview</p>', unsafe_allow_html=True)
    st.markdown("Welcome to your Investment Management Panel")

    col1, col2, col3 = st.columns(3)

    # Load portfolio data
    try:
        # Load transactions from DB
        db_transactions = db.get_transactions(limit=1000)
        for t in db_transactions:
            try:
                portfolio.add_transaction(
                    ticker=t["ticker"],
                    transaction_type=TransactionType[t["type"]],
                    quantity=t["quantity"],
                    price=t["price"],
                    date=t["date"],
                    commission=t["commission"]
                )
            except:
                pass

        summary = portfolio.get_portfolio_summary()

        with col1:
            st.metric(
                "Portfolio Value",
                f"₺{summary['current_value']:,.2f}",
                f"{summary['return_percentage']:.2f}%"
            )

        with col2:
            pl_color = "positive" if summary['total_profit_loss'] >= 0 else "negative"
            st.metric(
                "Total P&L",
                f"₺{summary['total_profit_loss']:,.2f}",
                f"{summary['return_percentage']:.2f}%"
            )

        with col3:
            st.metric(
                "Total Positions",
                summary['total_positions']
            )
    except Exception as e:
        st.info("No portfolio data available yet. Start by adding transactions!")

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📈 Analyze Stock", use_container_width=True):
            st.session_state.page = "📈 Stock Analysis"
            st.rerun()

    with col2:
        if st.button("💼 View Portfolio", use_container_width=True):
            st.session_state.page = "💼 Portfolio"
            st.rerun()

    with col3:
        if st.button("👀 Watchlist", use_container_width=True):
            st.session_state.page = "👀 Watchlist"
            st.rerun()

    with col4:
        if st.button("⚠️ Set Alert", use_container_width=True):
            st.session_state.page = "⚠️ Alerts"
            st.rerun()

    st.markdown("---")

    # Recent activity
    st.subheader("Recent Transactions")

    try:
        recent_transactions = db.get_transactions(limit=10)
        if recent_transactions:
            df = pd.DataFrame(recent_transactions)
            df = df[['date', 'ticker', 'type', 'quantity', 'price', 'commission']]
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
            df['total'] = df['quantity'] * df['price']
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent transactions")
    except Exception as e:
        st.info("No transaction history available")

    # Market overview
    st.markdown("---")
    st.subheader("Market Overview")

    watchlist_items = db.get_watchlist()
    if watchlist_items:
        tickers = [item['ticker'] for item in watchlist_items[:5]]  # First 5

        try:
            comparison = analyzer.compare_stocks(tickers, period="1d")
            if not comparison.empty:
                st.dataframe(comparison, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Could not load market data: {str(e)}")
    else:
        st.info("Add stocks to your watchlist to see market overview")


def show_analysis_page():
    """Display stock analysis page."""
    st.markdown('<p class="main-header">Stock Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        ticker = st.text_input("Enter Stock Symbol (e.g., THYAO)", value="THYAO").upper()

    with col2:
        period = st.selectbox(
            "Time Period",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=5
        )

    if st.button("Analyze", type="primary"):
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # Perform analysis
                analysis = analyzer.analyze_stock(ticker, period=period)

                # Display results
                display_analysis_results(ticker, period, analysis)

                # Save to database
                if st.checkbox("Save analysis to database"):
                    db.save_analysis(ticker, analysis)
                    st.success("Analysis saved!")

            except Exception as e:
                st.error(f"Error analyzing {ticker}: {str(e)}")


def display_analysis_results(ticker, period, analysis):
    """Display analysis results with charts."""
    latest = analysis['latest_data']
    signals = analysis['technical_signals']
    trend = analysis['trend_analysis']
    summary = analysis['summary']

    # Price metrics
    st.subheader("Price Information")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        price_change = latest.get('price_change', 0)
        price_change_pct = latest.get('price_change_pct', 0)
        st.metric(
            "Current Price",
            f"₺{latest['close']:.2f}",
            f"{price_change:.2f} ({price_change_pct:.2f}%)"
        )

    with col2:
        st.metric("High", f"₺{latest['high']:.2f}")

    with col3:
        st.metric("Low", f"₺{latest['low']:.2f}")

    with col4:
        st.metric("Volume", f"{latest['volume']:,.0f}")

    # Technical indicators
    st.subheader("Technical Indicators")
    col1, col2, col3 = st.columns(3)

    with col1:
        if 'rsi' in latest:
            rsi_color = "🔴" if signals.get('rsi') == 'OVERBOUGHT' else "🟢" if signals.get('rsi') == 'OVERSOLD' else "🟡"
            st.metric(f"{rsi_color} RSI", f"{latest['rsi']:.2f}", signals.get('rsi', 'NEUTRAL'))

    with col2:
        if 'macd' in latest:
            macd_color = "🟢" if 'BULLISH' in signals.get('macd', '') else "🔴" if 'BEARISH' in signals.get('macd', '') else "🟡"
            st.metric(f"{macd_color} MACD", f"{latest['macd']:.4f}", signals.get('macd', 'NEUTRAL'))

    with col3:
        overall_color = "🟢" if summary['overall_signal'] == 'BULLISH' else "🔴" if summary['overall_signal'] == 'BEARISH' else "🟡"
        st.metric(f"{overall_color} Overall Signal", summary['overall_signal'], f"Confidence: {summary['confidence']*100:.0f}%")

    # Trend analysis
    st.subheader("Trend Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Short-term Trend:**", trend.get('short_term', 'N/A'))
        st.write("**Price vs SMA20:**", trend.get('price_vs_sma20', 'N/A'))
        st.write("**Price vs SMA50:**", trend.get('price_vs_sma50', 'N/A'))

    with col2:
        st.write("**Long-term Trend:**", trend.get('long_term', 'N/A'))
        st.write("**Price vs SMA200:**", trend.get('price_vs_sma200', 'N/A'))

    # Chart
    st.subheader("Price Chart with Indicators")
    create_price_chart(ticker, period)


def create_price_chart(ticker, period):
    """Create interactive price chart with technical indicators."""
    try:
        df = data_fetcher.get_stock_data(ticker, period=period)
        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all_indicators(df)

        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(f'{ticker} Price', 'RSI', 'MACD')
        )

        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_with_indicators.index,
                open=df_with_indicators['Open'],
                high=df_with_indicators['High'],
                low=df_with_indicators['Low'],
                close=df_with_indicators['Close'],
                name='Price'
            ),
            row=1, col=1
        )

        # Add moving averages
        if 'SMA_20' in df_with_indicators.columns:
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['SMA_20'],
                          name='SMA 20', line=dict(color='orange', width=1)),
                row=1, col=1
            )

        if 'SMA_50' in df_with_indicators.columns:
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['SMA_50'],
                          name='SMA 50', line=dict(color='blue', width=1)),
                row=1, col=1
            )

        # Bollinger Bands
        if 'BB_Upper' in df_with_indicators.columns:
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['BB_Upper'],
                          name='BB Upper', line=dict(color='gray', width=1, dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['BB_Lower'],
                          name='BB Lower', line=dict(color='gray', width=1, dash='dash'),
                          fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)'),
                row=1, col=1
            )

        # RSI
        if 'RSI' in df_with_indicators.columns:
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['RSI'],
                          name='RSI', line=dict(color='purple', width=1)),
                row=2, col=1
            )
            # Overbought/Oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        # MACD
        if 'MACD' in df_with_indicators.columns:
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['MACD'],
                          name='MACD', line=dict(color='blue', width=1)),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(x=df_with_indicators.index, y=df_with_indicators['MACD_Signal'],
                          name='Signal', line=dict(color='red', width=1)),
                row=3, col=1
            )
            fig.add_trace(
                go.Bar(x=df_with_indicators.index, y=df_with_indicators['MACD_Hist'],
                      name='Histogram'),
                row=3, col=1
            )

        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )

        fig.update_yaxes(title_text="Price (TRY)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")


def show_portfolio_page():
    """Display portfolio management page."""
    st.markdown('<p class="main-header">Portfolio Management</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Summary", "➕ Add Transaction", "📜 History"])

    with tab1:
        show_portfolio_summary()

    with tab2:
        add_transaction_form()

    with tab3:
        show_transaction_history()


def show_portfolio_summary():
    """Display portfolio summary."""
    try:
        # Load transactions
        db_transactions = db.get_transactions(limit=1000)
        for t in db_transactions:
            try:
                portfolio.add_transaction(
                    ticker=t["ticker"],
                    transaction_type=TransactionType[t["type"]],
                    quantity=t["quantity"],
                    price=t["price"],
                    date=t["date"],
                    commission=t["commission"]
                )
            except:
                pass

        summary = portfolio.get_portfolio_summary()

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Invested", f"₺{summary['total_invested']:,.2f}")

        with col2:
            st.metric("Current Value", f"₺{summary['current_value']:,.2f}")

        with col3:
            pl = summary['total_profit_loss']
            st.metric("Total P&L", f"₺{pl:,.2f}", f"{summary['return_percentage']:.2f}%")

        with col4:
            st.metric("Positions", summary['total_positions'])

        st.markdown("---")

        # Positions table
        if summary['positions']:
            st.subheader("Current Positions")

            positions_data = []
            for ticker, pos in summary['positions'].items():
                positions_data.append({
                    'Ticker': ticker,
                    'Quantity': f"{pos['quantity']:.2f}",
                    'Avg Cost': f"₺{pos['average_cost']:.2f}",
                    'Current Price': f"₺{pos.get('current_price', 0):.2f}",
                    'Total Value': f"₺{pos.get('current_value', 0):,.2f}",
                    'P&L': f"₺{pos.get('profit_loss', 0):,.2f}",
                    'P&L %': f"{pos.get('profit_loss_pct', 0):.2f}%"
                })

            df = pd.DataFrame(positions_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No positions in portfolio")

    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")


def add_transaction_form():
    """Form to add new transaction."""
    st.subheader("Add New Transaction")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input("Ticker Symbol").upper()
        transaction_type = st.selectbox("Transaction Type", ["BUY", "SELL"])
        quantity = st.number_input("Quantity", min_value=0.01, step=0.01)

    with col2:
        price = st.number_input("Price per Share", min_value=0.01, step=0.01)
        commission = st.number_input("Commission (optional)", min_value=0.0, step=0.01)
        notes = st.text_area("Notes (optional)")

    if st.button("Add Transaction", type="primary"):
        if ticker and quantity > 0 and price > 0:
            try:
                # Add to database
                db.add_transaction(
                    ticker=ticker,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    commission=commission if commission > 0 else None
                )

                st.success(f"✅ {transaction_type} transaction added for {ticker}")
                st.rerun()

            except Exception as e:
                st.error(f"Error adding transaction: {str(e)}")
        else:
            st.warning("Please fill in all required fields")


def show_transaction_history():
    """Display transaction history."""
    st.subheader("Transaction History")

    col1, col2 = st.columns(2)

    with col1:
        ticker_filter = st.text_input("Filter by Ticker (optional)").upper()

    with col2:
        limit = st.number_input("Number of transactions to show", min_value=10, max_value=1000, value=50, step=10)

    try:
        transactions = db.get_transactions(
            ticker=ticker_filter if ticker_filter else None,
            limit=limit
        )

        if transactions:
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
            df['total'] = (df['quantity'] * df['price']).round(2)
            df = df[['date', 'ticker', 'type', 'quantity', 'price', 'commission', 'total']]

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions found")

    except Exception as e:
        st.error(f"Error loading history: {str(e)}")


def show_watchlist_page():
    """Display watchlist page."""
    st.markdown('<p class="main-header">Watchlist</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 View Watchlist", "➕ Add Stock"])

    with tab1:
        show_watchlist()

    with tab2:
        add_to_watchlist_form()


def show_watchlist():
    """Display watchlist."""
    try:
        watchlist = db.get_watchlist()

        if watchlist:
            # Get current prices
            watchlist_data = []
            for item in watchlist:
                try:
                    df = data_fetcher.get_stock_data(item['ticker'], period='1d')
                    current_price = float(df['Close'].iloc[-1])
                    price_change = float(df['Close'].iloc[-1] - df['Close'].iloc[-2]) if len(df) > 1 else 0
                    price_change_pct = (price_change / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0

                    watchlist_data.append({
                        'Ticker': item['ticker'],
                        'Current Price': f"₺{current_price:.2f}",
                        'Change': f"{price_change:.2f} ({price_change_pct:.2f}%)",
                        'Target': f"₺{item['target_price']:.2f}" if item['target_price'] else '-',
                        'Stop Loss': f"₺{item['stop_loss']:.2f}" if item['stop_loss'] else '-',
                        'Added': item['added_date'].strftime('%Y-%m-%d')
                    })
                except Exception as e:
                    st.warning(f"Could not fetch price for {item['ticker']}")

            if watchlist_data:
                df = pd.DataFrame(watchlist_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Your watchlist is empty. Add some stocks!")

    except Exception as e:
        st.error(f"Error loading watchlist: {str(e)}")


def add_to_watchlist_form():
    """Form to add stock to watchlist."""
    st.subheader("Add to Watchlist")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input("Ticker Symbol").upper()
        name = st.text_input("Company Name (optional)")

    with col2:
        target_price = st.number_input("Target Price (optional)", min_value=0.0, step=0.01)
        stop_loss = st.number_input("Stop Loss (optional)", min_value=0.0, step=0.01)

    notes = st.text_area("Notes (optional)")

    if st.button("Add to Watchlist", type="primary"):
        if ticker:
            try:
                db.add_to_watchlist(
                    ticker=ticker,
                    name=name if name else None,
                    target_price=target_price if target_price > 0 else None,
                    stop_loss=stop_loss if stop_loss > 0 else None,
                    notes=notes if notes else None
                )

                st.success(f"✅ {ticker} added to watchlist")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a ticker symbol")


def show_alerts_page():
    """Display alerts page."""
    st.markdown('<p class="main-header">Price & Technical Alerts</p>', unsafe_allow_html=True)

    st.info("💡 Set up alerts to get notified when stocks reach target prices or trigger technical signals")

    tab1, tab2 = st.tabs(["📍 Price Alerts", "📊 Technical Alerts"])

    with tab1:
        show_price_alerts()

    with tab2:
        show_technical_alerts()


def show_price_alerts():
    """Display price alerts interface."""
    st.subheader("Check Price Alerts")

    col1, col2, col3 = st.columns(3)

    with col1:
        ticker = st.text_input("Ticker Symbol", key="price_alert_ticker").upper()

    with col2:
        target_price = st.number_input("Target Price", min_value=0.0, step=0.01, key="target_price")

    with col3:
        stop_loss = st.number_input("Stop Loss", min_value=0.0, step=0.01, key="stop_loss")

    if st.button("Check Alert", type="primary"):
        if ticker and (target_price > 0 or stop_loss > 0):
            with st.spinner("Checking alert..."):
                try:
                    result = alert_manager.check_price_alert(
                        ticker=ticker,
                        target_price=target_price if target_price > 0 else None,
                        stop_loss=stop_loss if stop_loss > 0 else None
                    )

                    if result.get('triggered'):
                        st.success(f"🎯 Alert triggered! {result['alert_type']}")
                        st.write(f"Current Price: ₺{result['current_price']:.2f}")
                    else:
                        st.info(f"No alert triggered. Current Price: ₺{result['current_price']:.2f}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def show_technical_alerts():
    """Display technical alerts interface."""
    st.subheader("Check Technical Alerts")

    col1, col2, col3 = st.columns(3)

    with col1:
        ticker = st.text_input("Ticker Symbol", key="tech_alert_ticker").upper()

    with col2:
        indicator = st.selectbox("Indicator", ["RSI", "MACD"])

    with col3:
        threshold = st.number_input("Threshold", value=70.0 if indicator == "RSI" else 0.0, step=0.01)

    condition = st.selectbox("Condition", ["above", "below"])

    if st.button("Check Alert", type="primary", key="check_tech_alert"):
        if ticker:
            with st.spinner("Checking alert..."):
                try:
                    result = alert_manager.check_technical_alert(
                        ticker=ticker,
                        indicator=indicator,
                        condition=condition,
                        threshold=threshold
                    )

                    if result.get('triggered'):
                        st.success(f"📊 Alert triggered! {result.get('signal')}")
                        st.write(f"{indicator}: {result['current_value']:.2f}")
                    else:
                        st.info(f"No alert triggered. {indicator}: {result.get('current_value', 'N/A')}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def show_comparison_page():
    """Display stock comparison page."""
    st.markdown('<p class="main-header">Compare Stocks</p>', unsafe_allow_html=True)

    st.write("Compare multiple stocks side by side")

    col1, col2 = st.columns([3, 1])

    with col1:
        tickers_input = st.text_input(
            "Enter ticker symbols (comma-separated)",
            placeholder="e.g., THYAO, AKBNK, SAHOL"
        ).upper()

    with col2:
        period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=5, key="compare_period")

    if st.button("Compare", type="primary"):
        if tickers_input:
            tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]

            if len(tickers) > 1:
                with st.spinner("Comparing stocks..."):
                    try:
                        comparison = analyzer.compare_stocks(tickers, period=period)

                        if not comparison.empty:
                            st.dataframe(comparison, use_container_width=True, hide_index=True)

                            # Performance chart
                            st.subheader("Performance Comparison")
                            create_comparison_chart(tickers, period)
                        else:
                            st.warning("No data available for comparison")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter at least 2 ticker symbols")
        else:
            st.warning("Please enter ticker symbols")


def create_comparison_chart(tickers, period):
    """Create comparison chart for multiple stocks."""
    try:
        fig = go.Figure()

        for ticker in tickers:
            try:
                df = data_fetcher.get_stock_data(ticker, period=period)

                # Normalize to percentage change
                normalized = ((df['Close'] / df['Close'].iloc[0]) - 1) * 100

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=normalized,
                    name=ticker,
                    mode='lines'
                ))
            except:
                st.warning(f"Could not load data for {ticker}")

        fig.update_layout(
            title="Normalized Performance (%)",
            xaxis_title="Date",
            yaxis_title="Return (%)",
            height=500,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")


if __name__ == "__main__":
    main()
