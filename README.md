# IMP - Investment Management Panel

A comprehensive stock analysis and portfolio management tool designed for traders in the Borsa Istanbul (BIST) and other markets. IMP provides technical analysis, portfolio tracking, and performance monitoring capabilities through both an intuitive **Web Dashboard** and **Command-Line Interface**.

## Features

### 📊 Technical Analysis
- **Comprehensive Indicators**:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Simple & Exponential Moving Averages (SMA/EMA)
  - Stochastic Oscillator
  - Average True Range (ATR)
  - On-Balance Volume (OBV)

- **Automated Signals**:
  - Overbought/Oversold detection
  - Trend analysis (short-term and long-term)
  - Bullish/Bearish crossovers
  - Overall signal with confidence scoring

### 💼 Portfolio Management
- Buy/Sell transaction tracking
- Real-time position monitoring
- Profit/Loss calculation (realized and unrealized)
- Commission tracking
- Performance metrics
- Excel export functionality

### 📈 Stock Comparison
- Compare multiple stocks side-by-side
- Analyze relative performance
- Technical indicator comparison

### 👀 Watchlist
- Track stocks of interest
- Set target prices and stop losses
- Quick access to monitored stocks

### 🗄️ Data Persistence
- SQLite database for transaction history
- Analysis history tracking
- Watchlist management
- Cache system for faster data retrieval

### 🌐 Web Dashboard
- **Interactive Streamlit Interface**: Modern, user-friendly web interface
- **Real-time Charts**: Interactive price charts with technical indicators (Plotly)
- **Portfolio Overview**: Visual representation of your portfolio performance
- **Multi-page Dashboard**: Dedicated pages for analysis, portfolio, watchlist, alerts
- **Responsive Design**: Works on desktop and mobile devices

### ⚠️ Alert System
- **Price Alerts**: Get notified when stocks hit target prices or stop losses
- **Technical Alerts**: RSI overbought/oversold alerts, MACD crossovers
- **Email Notifications**: Automatic email alerts for triggered conditions
- **Watchlist Monitoring**: Automated monitoring of your watchlist
- **Customizable Alerts**: Set your own thresholds and conditions

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/EmreErbek/IMP.git
cd IMP
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install the package**:
```bash
pip install -e .
```

## Usage

### 🌐 Web Dashboard (Recommended)

The easiest way to use IMP is through the web dashboard:

```bash
# Quick start
./start_dashboard.sh

# Or manually
streamlit run src/web/app.py
```

Then open your browser to **http://localhost:8501**

The web dashboard includes:
- 🏠 **Home**: Portfolio overview and quick actions
- 📈 **Stock Analysis**: Interactive charts with technical indicators
- 💼 **Portfolio**: Manage transactions and view performance
- 👀 **Watchlist**: Track your favorite stocks
- ⚠️ **Alerts**: Set up price and technical alerts
- 📊 **Compare**: Side-by-side stock comparison

### 💻 Command-Line Interface

For advanced users and automation, use the CLI:

#### Stock Analysis

Analyze a single stock with technical indicators:

```bash
imp analyze THYAO
imp analyze THYAO --period 6mo
imp analyze THYAO --save  # Save analysis to database
```

### Compare Stocks

Compare multiple stocks:

```bash
imp compare THYAO AKBNK SAHOL EREGL
imp compare THYAO AKBNK --period 1y
```

### Portfolio Management

#### Buy Stocks
```bash
imp portfolio buy THYAO 100 45.50
imp portfolio buy THYAO 100 45.50 --commission 4.55
imp portfolio buy THYAO 100 45.50 --date 2024-01-15 --notes "Long position"
```

#### Sell Stocks
```bash
imp portfolio sell THYAO 50 47.00
imp portfolio sell THYAO 50 47.00 --commission 2.35
```

#### View Portfolio Summary
```bash
imp portfolio summary
```

This displays:
- Total positions and their current values
- Invested amount vs. current value
- Realized and unrealized profit/loss
- Individual position details with P&L percentages

### Watchlist Management

#### Add to Watchlist
```bash
imp watchlist add THYAO
imp watchlist add THYAO --name "Türk Hava Yolları" --target 50.00 --stop 40.00
```

#### View Watchlist
```bash
imp watchlist show
```

#### Remove from Watchlist
```bash
imp watchlist remove THYAO
```

### ⚠️ Alert System

#### Setting Up Email Alerts

1. **Configure email settings** in `config/config.yaml`:
```yaml
alerts:
  enabled: true
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    sender_email: "your-email@gmail.com"
    sender_password: "your-app-password"  # Use Gmail App Password
```

2. **For Gmail users**:
   - Go to Google Account settings
   - Enable 2-factor authentication
   - Generate an "App Password" for IMP
   - Use this app password in the config

#### Using Alerts (Python API)

```python
from src.alerts.alert_manager import AlertManager
from src.alerts.email_service import EmailService

# Initialize
email_service = EmailService(
    sender_email="your-email@gmail.com",
    sender_password="your-app-password",
    enabled=True
)
alert_manager = AlertManager(email_service=email_service)

# Check price alert
alert_manager.check_price_alert(
    ticker="THYAO",
    target_price=50.00,
    stop_loss=40.00,
    notification_email="recipient@gmail.com"
)

# Check technical alert (RSI)
alert_manager.check_technical_alert(
    ticker="THYAO",
    indicator="RSI",
    condition="above",
    threshold=70,
    notification_email="recipient@gmail.com"
)

# Monitor watchlist (runs in background)
watchlist = db.get_watchlist()
alert_manager.start_monitoring(
    watchlist=watchlist,
    notification_email="recipient@gmail.com"
)
```

#### Alert Types

- **Price Target**: Notified when stock reaches target price
- **Stop Loss**: Notified when stock hits stop loss
- **RSI Overbought**: Alert when RSI > 70
- **RSI Oversold**: Alert when RSI < 30
- **MACD Crossover**: Alert on bullish/bearish crossovers

## Configuration

Edit `config/config.yaml` to customize:

- **Data Settings**: Default period, interval, market suffix
- **Database**: Database path and settings
- **Technical Indicators**: Default parameters for RSI, MACD, Bollinger Bands, etc.
- **Logging**: Log level, file path, rotation settings
- **Portfolio**: Default currency, commission rates

Example configuration:
```yaml
data:
  default_period: "1y"
  market_suffix: ".IS"  # Borsa Istanbul

portfolio:
  commission_rate: 0.001  # 0.1%

indicators:
  rsi:
    period: 14
  macd:
    fast_period: 12
    slow_period: 26
    signal_period: 9
```

## Project Structure

```
IMP/
├── src/
│   ├── core/              # Core functionality
│   │   ├── data_fetcher.py    # Stock data retrieval
│   │   ├── logger.py          # Logging system
│   │   └── exceptions.py      # Custom exceptions
│   ├── analysis/          # Technical analysis
│   │   ├── technical_indicators.py
│   │   └── stock_analyzer.py
│   ├── portfolio/         # Portfolio management
│   │   ├── portfolio_manager.py
│   │   └── transaction.py
│   ├── database/          # Data persistence
│   │   ├── db_manager.py
│   │   └── models.py
│   └── cli/               # Command-line interface
│       └── main.py
├── tests/                 # Unit tests
├── config/                # Configuration files
├── data/                  # Database and logs
├── requirements.txt
├── setup.py
└── README.md
```

## Architecture

### Modular Design
- **Separation of Concerns**: Each module handles a specific responsibility
- **Dependency Injection**: Components can be easily tested and swapped
- **Configuration-Driven**: Behavior can be customized without code changes

### Data Flow
1. **Data Fetcher**: Retrieves stock data from Yahoo Finance
2. **Technical Indicators**: Calculates various technical indicators
3. **Stock Analyzer**: Combines data and indicators for analysis
4. **Portfolio Manager**: Tracks transactions and positions
5. **Database Manager**: Persists data for historical tracking
6. **CLI**: User interface for all operations

### Scalability Features
- **Caching System**: Reduces API calls and improves performance
- **Batch Processing**: Analyze multiple stocks efficiently
- **Database Indexing**: Fast queries on large datasets
- **Modular Architecture**: Easy to add new features and indicators

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_data_fetcher.py
```

## Examples

### Example 1: Quick Analysis
```bash
# Analyze a stock and save results
imp analyze THYAO --save

# View analysis with different time periods
imp analyze THYAO --period 3mo
imp analyze THYAO --period 1y
```

### Example 2: Build a Portfolio
```bash
# Buy multiple stocks
imp portfolio buy THYAO 100 45.50
imp portfolio buy AKBNK 200 30.25
imp portfolio buy SAHOL 150 25.80

# Check portfolio
imp portfolio summary

# Sell some position
imp portfolio sell THYAO 50 47.00
```

### Example 3: Monitor Stocks
```bash
# Add stocks to watchlist
imp watchlist add THYAO --target 50.00
imp watchlist add AKBNK --target 35.00
imp watchlist add SAHOL --target 28.00

# View watchlist
imp watchlist show

# Analyze all watchlist stocks
imp compare THYAO AKBNK SAHOL
```

## Technical Indicators Explained

- **RSI**: Measures momentum, values >70 indicate overbought, <30 oversold
- **MACD**: Trend-following indicator, crossovers signal potential buy/sell
- **Bollinger Bands**: Volatility indicator, price touching bands suggests reversal
- **Moving Averages**: Smoothed price trends, crossovers indicate trend changes
- **Stochastic**: Momentum indicator comparing closing price to price range
- **ATR**: Measures volatility, useful for stop-loss placement
- **OBV**: Volume-based indicator, confirms price trends

## Data Sources

- **Stock Data**: Yahoo Finance API (yfinance)
- **Market**: Primarily Borsa Istanbul (.IS), but supports other markets
- **Update Frequency**: Real-time data with optional caching

## Contributing

Contributions are welcome! Areas for improvement:
- Additional technical indicators
- Fundamental analysis features
- Web dashboard interface
- Mobile app integration
- Alert system (email/SMS)
- Backtesting capabilities

## Troubleshooting

### Common Issues

**"No data available for ticker"**
- Verify the ticker symbol is correct
- Check if the stock is traded on Borsa Istanbul (should end with .IS)
- Try a different time period

**"Insufficient data for analysis"**
- Use a longer time period (e.g., 1y instead of 1d)
- Some indicators require minimum data points

**"Cannot sell X shares"**
- Ensure you have enough shares in your portfolio
- Check your transaction history with `imp portfolio summary`

## License

This project is licensed under the MIT License.

## Contact

For questions, issues, or suggestions:
- GitHub Issues: https://github.com/EmreErbek/IMP/issues
- Project: https://github.com/EmreErbek/IMP

## Disclaimer

This tool is for educational and informational purposes only. It does not constitute financial advice. Always do your own research and consult with financial professionals before making investment decisions. Past performance does not guarantee future results.
