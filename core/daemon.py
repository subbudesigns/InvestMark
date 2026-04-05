import asyncio
from core.trader import Trader
from integrations.telegram_bot import TelegramBot
from utils.logger import get_logger

logger = get_logger(__name__)

class WatcherDaemon:
    def __init__(self, check_interval=60):
        self.interval = check_interval
        self.trader = Trader()
        self.bot = TelegramBot()
        self._running = False

    async def _alert(self, msg):
        logger.info(f"ALERT: {msg}")
        await self.bot.send_alert(f"🔔 {msg}")

    async def watch_limits(self):
        logger.info("Starting limits watcher...")
        while self._running:
            try:
                holdings = self.trader.get_holdings()
                for symbol, holding in holdings.items():
                    if holding['quantity'] > 0:
                        current_price = self.trader.get_ltp(symbol)
                        if not current_price:
                            continue
                            
                        trigger = self.trader.limits.check_trigger(symbol, current_price)
                        if trigger == 'sl':
                            await self._alert(f"Stop-loss hit for {symbol} at {current_price}!")
                            success = self.trader.sell(symbol, holding['quantity'], current_price)
                            if success:
                                await self._alert(f"Auto-sold {holding['quantity']} {symbol}")
                                # Self-update: clear SL to avoid infinite loops, keep target
                                self.trader.limits.set_limit(symbol, stop_loss=0) 
                        elif trigger == 'target':
                            await self._alert(f"Target hit for {symbol} at {current_price}!")
                            success = self.trader.sell(symbol, holding['quantity'], current_price)
                            if success:
                                await self._alert(f"Auto-sold {holding['quantity']} {symbol} for profit!")
                                self.trader.limits.set_limit(symbol, target=0) 
                                
            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")
                
            await asyncio.sleep(self.interval)

    async def run(self):
        self._running = True
        logger.info("Starting daemon...")
        
        # Start Telegram Bot polling
        bot_task = asyncio.create_task(self.bot.start_polling())
        
        # Start Watcher Loop
        watcher_task = asyncio.create_task(self.watch_limits())

        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self._running = False
            await self.bot.stop()
