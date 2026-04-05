from integrations.zerodha import ZerodhaClient
from core.portfolio import Portfolio
from core.limits import LimitManager
from utils.logger import get_logger

logger = get_logger(__name__)

class Trader:
    def __init__(self):
        self.client = ZerodhaClient()
        self.portfolio = Portfolio()
        self.limits = LimitManager()

    def buy(self, symbol, quantity, price=None):
        logger.info(f"Initiating BUY for {quantity} {symbol}")
        current_price = price if price else self.client.get_ltp(symbol)
        
        if not current_price:
            logger.error(f"Could not fetch price for {symbol}")
            return False

        order_id = self.client.place_order(symbol, "BUY", quantity, "MARKET")
        if order_id:
            logger.info(f"BUY order successful. Executing local portfolio add for {symbol} at ~{current_price}")
            return self.portfolio.add_trade(symbol, quantity, current_price, 'buy')
        return False

    def sell(self, symbol, quantity, price=None):
        logger.info(f"Initiating SELL for {quantity} {symbol}")
        current_price = price if price else self.client.get_ltp(symbol)
        
        if not current_price:
            logger.error(f"Could not fetch price for {symbol}")
            return False

        order_id = self.client.place_order(symbol, "SELL", quantity, "MARKET")
        if order_id:
            logger.info(f"SELL order successful. Updating local portfolio for {symbol} at ~{current_price}")
            return self.portfolio.add_trade(symbol, quantity, current_price, 'sell')
        return False
        
    def get_holdings(self):
        return self.portfolio.get_summary()
        
    def get_ltp(self, symbol):
        return self.client.get_ltp(symbol)

    def set_limit(self, symbol, sl, target):
        return self.limits.set_limit(symbol, sl, target)
