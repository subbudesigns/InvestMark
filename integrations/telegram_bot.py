import utils.config as config
from utils.logger import get_logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from core.trader import Trader
from core.predictor import Predictor

logger = get_logger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.trader = Trader()
        self.predictor = Predictor()
        
        if self.token:
            self.app = ApplicationBuilder().token(self.token).build()
            self._setup_handlers()
        else:
            self.app = None
            logger.warning("TELEGRAM_BOT_TOKEN not found. Bot will not start.")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("portfolio", self.portfolio_command))
        self.app.add_handler(CommandHandler("buy", self.buy_command))
        self.app.add_handler(CommandHandler("sell", self.sell_command))
        self.app.add_handler(CommandHandler("predict", self.predict_command))
        self.app.add_handler(CommandHandler("setlimit", self.setlimit_command))
        self.app.add_handler(CommandHandler("addlist", self.addlist_command))
        self.app.add_handler(CommandHandler("showlist", self.showlist_command))
        self.app.add_handler(CommandHandler("calc", self.calc_command))
        self.app.add_handler(CommandHandler("removelist", self.removelist_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Welcome to InvestMark Bot!  Use \n /buy SYMBOL QTY for buying stocks \n /sell SYMBOL QTY for selling stocks \n /predict SYMBOL for predicting stock prices \n /setlimit SYMBOL SL TARGET for setting stop loss and target prices \n /addlist SYMBOL to add to wishlist \n /removelist SYMBOL to remove from wishlist \n /showlist to display wishlist \n /calc SYMBOL QTY to calculate total price and taxes.")

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        holdings = self.trader.get_holdings()
        if not holdings:
            await update.message.reply_text("Portfolio is empty.")
            return
        
        await update.message.reply_text("⏳ Fetching live prices for portfolio...")
        
        msg = "📈 **Portfolio Summary**\n\n"
        total_invested = 0.0
        total_current = 0.0
        
        for sym, d in holdings.items():
            qty = d['quantity']
            if qty == 0:
                continue
            
            avg_price = d['avg_price']
            invested = d.get('total_invested', qty * avg_price)
            
            ltp = self.trader.client.get_ltp(sym)
            if ltp:
                current_val = qty * ltp
                pnl = current_val - invested
                pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
                
                total_invested += invested
                total_current += current_val
                
                emoji = "🟩" if pnl >= 0 else "🟥"
                msg += f"**{sym}** ({qty} shares)\n"
                msg += f"Avg: ₹{round(avg_price, 2)} | LTP: ₹{round(ltp, 2)}\n"
                msg += f"Invested: ₹{round(invested, 2)} | Current: ₹{round(current_val, 2)}\n"
                msg += f"P&L: {emoji} ₹{round(pnl, 2)} ({round(pnl_pct, 2)}%)\n\n"
            else:
                msg += f"**{sym}** ({qty} shares) - Error fetching live price\n\n"
                total_invested += invested
                total_current += invested

        overall_pnl = total_current - total_invested
        overall_pnl_pct = (overall_pnl / total_invested) * 100 if total_invested > 0 else 0
        overall_emoji = "🟩" if overall_pnl >= 0 else "🟥"
        
        msg += "📊 **Overall Summary**\n"
        msg += f"Total Invested: ₹{round(total_invested, 2)}\n"
        msg += f"Current Value: ₹{round(total_current, 2)}\n"
        msg += f"Total P&L: {overall_emoji} ₹{round(overall_pnl, 2)} ({round(overall_pnl_pct, 2)}%)"
        
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def buy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /buy SYMBOL QTY")
            return
            
        symbol = context.args[0].upper()
        try:
            qty = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Quantity must be a valid number.")
            return

        price = self.trader.client.get_ltp(symbol)
        if not price:
            await update.message.reply_text(f"❌ Could not fetch live price for {symbol}. Invalid symbol or API error.")
            return

        base_total = price * qty
        stt = base_total * 0.001
        exch_txn = base_total * 0.0000345
        sebi = base_total * 0.000001
        stamp = base_total * 0.00015
        gst = (exch_txn + sebi) * 0.18
        total_tax = stt + exch_txn + sebi + stamp + gst
        grand_total = base_total + total_tax

        msg = (f"🛒 **Confirm BUY Order**\n"
               f"Symbol: {symbol}\n"
               f"Quantity: {qty}\n"
               f"Live Price: ₹{round(price, 2)}\n"
               f"Base Cost: ₹{round(base_total, 2)}\n"
               f"Est. Taxes & Charges: ₹{round(total_tax, 2)}\n"
               f"**Grand Total:** ₹{round(grand_total, 2)}\n\n"
               f"Do you want to proceed?")

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Buy", callback_data=f"buy_{symbol}_{qty}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "cancel_action":
            await query.edit_message_text(text="🚫 Action cancelled by user.")
            return

        if data.startswith("buy_"):
            parts = data.split("_")
            if len(parts) == 3:
                symbol = parts[1]
                qty = int(parts[2])
                success = self.trader.buy(symbol, qty)
                if success:
                    await query.edit_message_text(text=f"✅ BUY order successfully placed for {qty} {symbol}.")
                else:
                    await query.edit_message_text(text=f"❌ Failed to place BUY order for {symbol}.")

    async def sell_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /sell SYMBOL QTY")
            return
        symbol, qty = context.args[0], int(context.args[1])
        success = self.trader.sell(symbol, qty)
        if success:
            await update.message.reply_text(f"✅ SELL order placed for {qty} {symbol}")
        else:
            await update.message.reply_text(f"❌ Failed to place SELL order for {symbol}")

    async def predict_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /predict SYMBOL")
            return
        symbol = context.args[0]
        await update.message.reply_text(f"⏳ Generating prediction for {symbol}...")
        
        res = self.predictor.predict_next_day(symbol)
        if "error" in res:
            await update.message.reply_text(f"❌ Prediction error: {res['error']}")
            return
            
        msg = (f"🔮 **Prediction: {res['symbol']}**\n"
               f"Current: ₹{res['current_price']}\n"
               f"Predicted Next Day: ₹{res['predicted_price']}\n"
               f"Expected Return: {res['expected_return_pct']}%\n"
               f"Trend: {res['trend']}\n"
               f"Risk: {res['risk_score']}")
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def setlimit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /setlimit SYMBOL SL TARGET")
            return
        symbol, sl, target = context.args[0], float(context.args[1]), float(context.args[2])
        self.trader.set_limit(symbol, sl, target)
        await update.message.reply_text(f"✅ Limits set for {symbol}: SL={sl}, Target={target}")

    def _read_wishlist(self):
        import os, json
        if not os.path.exists(config.WISHLIST_FILE):
            return []
        with open(config.WISHLIST_FILE, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return []

    def _write_wishlist(self, wl):
        import json
        with open(config.WISHLIST_FILE, 'w') as f:
            json.dump(wl, f, indent=4)

    async def addlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /addlist SYMBOL")
            return
        symbol = context.args[0].upper()
        wl = self._read_wishlist()
        if symbol not in wl:
            wl.append(symbol)
            self._write_wishlist(wl)
            await update.message.reply_text(f"✅ {symbol} added to wishlist.")
        else:
            await update.message.reply_text(f"ℹ️ {symbol} is already in the wishlist.")

    async def removelist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /removelist SYMBOL")
            return
        symbol = context.args[0].upper()
        wl = self._read_wishlist()
        if symbol in wl:
            wl.remove(symbol)
            self._write_wishlist(wl)
            await update.message.reply_text(f"✅ {symbol} removed from wishlist.")
        else:
            await update.message.reply_text(f"ℹ️ {symbol} is not in the wishlist.")

    async def showlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        wl = self._read_wishlist()
        if not wl:
            await update.message.reply_text("Your wishlist is empty.")
            return
        
        await update.message.reply_text("⏳ Fetching latest prices for wishlist...")
        msg = "📋 **Wishlist:**\n"
        for sym in wl:
            price = self.trader.client.get_ltp(sym)
            if price:
                msg += f"- {sym}: ₹{round(price, 2)}\n"
            else:
                msg += f"- {sym}: Error Fetching Price\n"
                
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def calc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /calc SYMBOL QTY")
            return
            
        symbol = context.args[0].upper()
        try:
            qty = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Quantity must be a valid number.")
            return

        price = self.trader.client.get_ltp(symbol)
        if not price:
            await update.message.reply_text(f"❌ Could not fetch live price for {symbol}")
            return
            
        base_total = price * qty
        
        # Approximate Delivery Charges for Indian Equities
        stt = base_total * 0.001          # 0.1% STT
        exch_txn = base_total * 0.0000345 # NSE 0.00345%
        sebi = base_total * 0.000001      # SEBI 0.0001%
        stamp = base_total * 0.00015      # Stamp Duty 0.015%
        gst = (exch_txn + sebi) * 0.18    # 18% GST on Exchange & SEBI charges
        brokerage = 0.0                   # Free delivery assumption
        
        total_tax = stt + exch_txn + sebi + stamp + gst + brokerage
        grand_total = base_total + total_tax
        
        msg = (f"🧮 **Calculator: {symbol}**\n"
               f"Live Price: ₹{round(price, 2)}\n"
               f"Quantity: {qty}\n\n"
               f"Base Price: ₹{round(base_total, 2)}\n"
               f"Est. Taxes & Charges: ₹{round(total_tax, 2)}\n"
               f"**Grand Total:** ₹{round(grand_total, 2)}")
               
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def send_alert(self, message):
        if self.app and self.chat_id:
            try:
                await self.app.bot.send_message(chat_id=self.chat_id, text=message)
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")

    async def start_polling(self):
        if self.app:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            logger.info("Telegram Bot started.")
            
    async def stop(self):
        if self.app:
             await self.app.updater.stop()
             await self.app.stop()
             await self.app.shutdown()
