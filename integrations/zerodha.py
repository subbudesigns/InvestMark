from kiteconnect import KiteConnect
import utils.config as config
from utils.logger import get_logger

logger = get_logger(__name__)

class ZerodhaClient:
    def __init__(self):
        self.api_key = config.ZERODHA_API_KEY
        self.api_secret = config.ZERODHA_API_SECRET
        self.access_token = config.ZERODHA_ACCESS_TOKEN
        
        self.kite = None
        if self.api_key and self.access_token:
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                logger.info("Zerodha API initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Zerodha API: {e}")
        else:
            logger.warning("Zerodha credentials missing in environment variables. Running in mock/offline mode.")

    def place_order(self, tradingsymbol, transaction_type, quantity, order_type="MARKET", price=None):
        if not self.kite:
            logger.error("Kite client not initialized. Returning mock order ID.")
            return "MOCK_ORDER_12345"
            
        try:
            exchange = self.kite.EXCHANGE_NSE
            t_type = self.kite.TRANSACTION_TYPE_BUY if transaction_type.upper() == 'BUY' else self.kite.TRANSACTION_TYPE_SELL
            o_type = self.kite.ORDER_TYPE_LIMIT if order_type.upper() == 'LIMIT' else self.kite.ORDER_TYPE_MARKET
            
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=t_type,
                quantity=quantity,
                product=self.kite.PRODUCT_CNC, # Cash and Carry setup
                order_type=o_type,
                price=price
            )
            logger.info(f"Order placed: {order_id} for {quantity} {tradingsymbol} {transaction_type}")
            return order_id
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    def get_ltp(self, tradingsymbol):
        if not self.kite:
            # Fallback to yfinance if client not initialized
            try:
                import yfinance as yf
                yf_symbol = f"{tradingsymbol}.NS" if not tradingsymbol.endswith('.NS') and not tradingsymbol.endswith('.BO') else tradingsymbol
                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    return float(hist['Close'].iloc[-1])
            except Exception as e:
                logger.error(f"Error fetching LTP fallback from yfinance for {tradingsymbol}: {e}")
            return 100.0 
        try:
            instrument = f"NSE:{tradingsymbol}"
            quote = self.kite.quote(instrument)
            return quote[instrument]['last_price']
        except Exception as e:
            logger.error(f"Error fetching LTP for {tradingsymbol}: {e}")
            return None
            
    def get_holdings(self):
        if not self.kite:
            return []
        try:
            return self.kite.holdings()
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            return []
