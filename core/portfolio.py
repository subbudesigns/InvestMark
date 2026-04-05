import json
import os
import utils.config as config
from utils.logger import get_logger

logger = get_logger(__name__)

class Portfolio:
    def __init__(self):
        self.filename = config.PORTFOLIO_FILE
        self.holdings = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
                return {}
        return {}

    def _save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.holdings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")

    def add_trade(self, symbol, quantity, price, trade_type):
        """
        trade_type: 'buy' or 'sell'
        """
        symbol = symbol.upper()
        if symbol not in self.holdings:
            if trade_type == 'sell':
                logger.error(f"Cannot sell {symbol}: Not in portfolio.")
                return False
            self.holdings[symbol] = {
                'quantity': 0,
                'avg_price': 0.0,
                'total_invested': 0.0
            }

        holding = self.holdings[symbol]

        if trade_type == 'buy':
            total_cost = price * quantity
            holding['total_invested'] += total_cost
            holding['quantity'] += quantity
            holding['avg_price'] = holding['total_invested'] / holding['quantity']
        elif trade_type == 'sell':
            if holding['quantity'] < quantity:
                logger.error(f"Cannot sell {quantity} of {symbol}: Insufficient quantity ({holding['quantity']} available).")
                return False
            
            # Simple average cost reduction, real accounting might use FIFO
            cost_of_sold = holding['avg_price'] * quantity
            holding['total_invested'] -= cost_of_sold
            holding['quantity'] -= quantity
            
            if holding['quantity'] == 0:
                holding['avg_price'] = 0.0
                holding['total_invested'] = 0.0

            # If completely sold out, maybe want to remove or keep for history. 
            # We will keep it with 0 qty so it shows in history or we can remove.
            if holding['quantity'] == 0:
                del self.holdings[symbol]
                
        self._save()
        return True

    def get_summary(self):
        return self.holdings
