import json
import os
import utils.config as config
from utils.logger import get_logger

logger = get_logger(__name__)

class LimitManager:
    def __init__(self):
        self.filename = config.LIMITS_FILE
        self.limits = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading limits: {e}")
                return {}
        return {}

    def _save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.limits, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving limits: {e}")

    def set_limit(self, symbol, stop_loss=None, target=None):
        symbol = symbol.upper()
        if symbol not in self.limits:
            self.limits[symbol] = {}
        if stop_loss is not None:
            self.limits[symbol]['sl'] = float(stop_loss)
        if target is not None:
            self.limits[symbol]['target'] = float(target)
        self._save()
        logger.info(f"Limit updated for {symbol}: {self.limits[symbol]}")
        return self.limits[symbol]
        
    def get_limits(self, symbol=None):
        if symbol:
            return self.limits.get(symbol.upper())
        return self.limits

    def check_trigger(self, symbol, current_price):
        """
        Returns 'sl' if stop loss is hit, 'target' if target is hit. None otherwise.
        """
        symbol = symbol.upper()
        limits = self.get_limits(symbol)
        if not limits:
            return None
        
        if 'sl' in limits and current_price <= limits['sl']:
            return 'sl'
        if 'target' in limits and current_price >= limits['target']:
            return 'target'
        
        return None
