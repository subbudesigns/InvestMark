import pyotp
from growwapi import GrowwAPI
import utils.config as config
from utils.logger import get_logger

logger = get_logger(__name__)

class GrowwClient:
    def __init__(self):
        self.api_key = config.GROWW_API_KEY  # Used as TOTP Token
        self.api_secret = config.GROWW_API_SECRET # Used as TOTP Secret
        
        self.groww = None
        if self.api_key:
            try:
                if self.api_key.startswith("ey"):
                    # If it looks like a JWT, assume it's the access token already
                    logger.info("Groww API Key detected as JWT. Using it directly as access token.")
                    self.groww = GrowwAPI(self.api_key)
                    logger.info("GrowwAPI object created from JWT.")
                elif self.api_secret:
                    # Official Groww API TOTP Flow
                    totp_gen = pyotp.TOTP(self.api_secret)
                    totp = totp_gen.now()
                    
                    logger.info(f"Fetching Groww Access Token via TOTP flow (TOTP: {totp})...")
                    access_token = GrowwAPI.get_access_token(api_key=self.api_key, totp=totp)
                    
                    self.groww = GrowwAPI(access_token)
                    logger.info("GrowwAPI object created from TOTP flow.")
                else:
                    logger.warning("No TOTP Secret found for standard Flow. Falling back.")
                
                if self.groww:
                    logger.info("Groww API initialized successfully with live session.")
            except Exception as e:
                import traceback
                logger.error(f"Failed to initialize Groww API: {e}")
                logger.debug(traceback.format_exc())
                logger.warning("Running in mock/offline mode due to initialization failure.")
        else:
            logger.warning("Groww credentials (Key/Secret for TOTP) missing. Running in mock/offline mode.")

    def place_order(self, tradingsymbol, transaction_type, quantity, order_type="MARKET", price=None):
        if not self.groww:
            logger.info(f"Mocking Groww order placement for {quantity} {tradingsymbol} {transaction_type}")
            return f"GROWW_MOCK_{tradingsymbol}_{transaction_type}_123"

        try:
            # Mapping internal types to Groww SDK constants
            # For simplicity, assuming NSE and CNC for now as per docs
            side = GrowwAPI.TRANSACTION_TYPE_BUY if transaction_type.upper() == "BUY" else GrowwAPI.TRANSACTION_TYPE_SELL
            o_type = GrowwAPI.ORDER_TYPE_MARKET if order_type.upper() == "MARKET" else GrowwAPI.ORDER_TYPE_LIMIT
            
            response = self.groww.place_order(
                trading_symbol=tradingsymbol.upper(),
                quantity=int(quantity),
                validity=GrowwAPI.VALIDITY_DAY,
                exchange=GrowwAPI.EXCHANGE_NSE,
                segment=GrowwAPI.SEGMENT_CASH,
                product=GrowwAPI.PRODUCT_CNC,
                order_type=o_type,
                transaction_type=side,
                price=price
            )
            logger.info(f"Groww Order Response: {response}")
            # The SDK usually returns a dict with 'order_id' or similar
            return response.get('order_id') or response.get('orderId') or str(response)
        except Exception as e:
            logger.error(f"Error placing order via Groww API: {e}")
            return None

    def get_ltp(self, tradingsymbol):
        if self.groww:
            try:
                # get_ltp supports multiple, but we wrap for single
                symbol = tradingsymbol.upper()
                if not symbol.startswith("NSE_"):
                    lookup_symbol = f"NSE_{symbol}"
                else:
                    lookup_symbol = symbol
                    
                response = self.groww.get_ltp(
                    segment=GrowwAPI.SEGMENT_CASH,
                    exchange_trading_symbols=lookup_symbol
                )
                logger.debug(f"Groww LTP Response for {lookup_symbol}: {response}")
                # Response format: { "NSE_RELIANCE": 2500.5 }
                if lookup_symbol in response:
                    return float(response[lookup_symbol])
                
                # If NSE prefix didn't work, try raw
                if symbol in response:
                    return float(response[symbol])
                    
            except Exception as e:
                logger.error(f"Error fetching LTP from Groww API for {tradingsymbol}: {e}")
                
        # Fallback Mock value if API is unavailable
        logger.info(f"Mocking LTP for {tradingsymbol} as 100.0 via Groww")
        return 100.0 
            
    def get_holdings(self):
        if not self.groww:
            return []
        try:
            # Based on docs, get_portfolio might be the method
            return self.groww.get_portfolio()
        except Exception as e:
            logger.error(f"Error fetching holdings from Groww: {e}")
            return []

