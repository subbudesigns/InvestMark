# InvestMark CLI

A production-ready CLI-based stock trading system with modular architecture in Python.

## Features

- **CLI Trading**: Buy, Sell, Hold stock quantities directly from the terminal.
- **Portfolio Tracking**: Locally manage and summarize holdings via lightweight JSON files.
- **Groww API Integration**: Direct API connection to execute trades and fetch latest prices.
- **Limits & Automation**: Set target and stop-loss limits which trigger auto-sells via a daemon watcher.
- **Telegram Bot**: Monitor portfolio, receive limit alerts, and trade directly from Telegram asynchronously.
- **Predictive Analytics**: On-the-fly technical analysis using `yfinance` and `scikit-learn` for next-day price prediction.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Copy `.env.example` to `.env` and fill in your credentials.
   ```bash
   copy .env.example .env
   ```
   - *Groww Trading API*: Subscribe and generate your API tokens from the Groww developer dashboard.
   - *Telegram*: Create a new bot using [BotFather](https://t.me/botfather) and get the token. Find your Chat ID so the bot can send you limit hit alerts.

## Usage Examples

**1. Basic Trading**
```bash
python main.py buy --symbol TCS --qty 10
python main.py sell --symbol INFY --qty 5
python main.py hold --symbol RELIANCE
```

**2. Portfolio Management**
```bash
python main.py portfolio
```

**3. Predictions**
```bash
python main.py predict --symbol HDFCBANK
```

**4. Limits & Watcher**
```bash
# Set limit (Stop Loss: 3200, Target: 3500)
python main.py set-limit --symbol TCS --sl 3200 --target 3500

# Start Daemon to watch limits and run Telegram Bot
python main.py daemon
```

## Telegram Bot Commands
Once the `daemon` is running, send the following over Telegram:
- `/start`
- `/portfolio`
- `/predict SYMBOL`
- `/buy SYMBOL QTY`
- `/sell SYMBOL QTY`
- `/setlimit SYMBOL SL TARGET`
- `/addlist SYMBOL` (Add stock to wishlist)
- `/removelist SYMBOL` (Remove stock from wishlist)
- `/showlist` (Show wishlist with live prices)
- `/calc SYMBOL QTY` (Calculate total price and estimated taxes)
