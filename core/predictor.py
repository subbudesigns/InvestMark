import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from utils.logger import get_logger

logger = get_logger(__name__)

class Predictor:
    def __init__(self):
        self.model = LinearRegression()

    def fetch_data(self, symbol, period="6mo"):
        try:
            # yfinance symbol usually requires '.NS' for NSE stocks like RELIANCE
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                yf_symbol = f"{symbol}.NS"
            else:
                yf_symbol = symbol
                
            logger.info(f"Fetching {period} data for {yf_symbol}")
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                logger.warning(f"No data found for {yf_symbol}")
                return None
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def predict_next_day(self, symbol):
        df = self.fetch_data(symbol)
        if df is None or len(df) < 10:
            return {"error": "Not enough data"}

        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_30'] = df['Close'].rolling(window=30).mean()
        df['Prev_Close'] = df['Close'].shift(1)
        
        df['Next_Close'] = df['Close'].shift(-1)
        
        df_clean = df.dropna()
        
        if len(df_clean) < 10:
             return {"error": "Not enough data after cleaning"}
             
        features = ['Close', 'Prev_Close', 'SMA_10', 'SMA_30']
        X = df_clean[features]
        y = df_clean['Next_Close']

        self.model.fit(X, y)
        
        last_row = df.iloc[-1]
        
        # Simple fallback for NaNs on the very last row if rolling averages aren't available
        _c = last_row['Close']
        _pc = last_row['Prev_Close'] if not pd.isna(last_row['Prev_Close']) else _c
        _s10 = last_row['SMA_10'] if not pd.isna(last_row['SMA_10']) else _c
        _s30 = last_row['SMA_30'] if not pd.isna(last_row['SMA_30']) else _c
        
        X_pred = pd.DataFrame([{
            'Close': _c, 
            'Prev_Close': _pc, 
            'SMA_10': _s10, 
            'SMA_30': _s30
        }])
        
        prediction = self.model.predict(X_pred)[0]
        current_price = _c
        diff = prediction - current_price
        
        # >0.5% return = BULLISH
        trend = "BULLISH" if diff > (current_price * 0.005) else "BEARISH" if diff < -(current_price * 0.005) else "NEUTRAL"

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "predicted_price": round(prediction, 2),
            "expected_return_pct": round((diff / current_price) * 100, 2),
            "trend": trend,
            "risk_score": "Medium" 
        }
