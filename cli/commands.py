from core.trader import Trader
from core.predictor import Predictor
from tabulate import tabulate
from utils.logger import get_logger

logger = get_logger(__name__)

def handle_buy(args):
    trader = Trader()
    success = trader.buy(args.symbol, args.qty)
    if success:
        print(f"✅ Successfully bought {args.qty} of {args.symbol}")
    else:
        print(f"❌ Failed to buy {args.symbol}")

def handle_sell(args):
    trader = Trader()
    success = trader.sell(args.symbol, args.qty)
    if success:
        print(f"✅ Successfully sold {args.qty} of {args.symbol}")
    else:
        print(f"❌ Failed to sell {args.symbol}")

def handle_hold(args):
    print(f"🛡️ Holding {args.symbol}. No action taken.")

def handle_portfolio(args):
    trader = Trader()
    holdings = trader.get_holdings()
    if not holdings:
        print("Portfolio is empty.")
        return
    
    table = []
    total_invested = 0.0
    total_current = 0.0
    
    print("Fetching live prices...")
    for sym, data in holdings.items():
        qty = data['quantity']
        if qty == 0:
            continue
        avg_price = data['avg_price']
        invested = data.get('total_invested', qty * avg_price)
        
        ltp = trader.get_ltp(sym)
        if ltp:
            current_val = qty * ltp
            pnl = current_val - invested
            pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
            total_invested += invested
            total_current += current_val
            
            pnl_str = f"₹{round(pnl, 2)} ({round(pnl_pct, 2)}%)"
            table.append([sym, qty, round(avg_price, 2), round(ltp, 2), round(invested, 2), round(current_val, 2), pnl_str])
        else:
            table.append([sym, qty, round(avg_price, 2), "Error", round(invested, 2), "Error", "Error"])
            total_invested += invested
            total_current += invested
            
    print(tabulate(table, headers=["Symbol", "Qty", "Avg Price", "LTP", "Invested", "Current Value", "P&L"], tablefmt="grid"))
    
    overall_pnl = total_current - total_invested
    overall_pnl_pct = (overall_pnl / total_invested) * 100 if total_invested > 0 else 0
    print(f"\n📊 Total Invested: ₹{round(total_invested, 2)} | Current Value: ₹{round(total_current, 2)} | Overall P&L: ₹{round(overall_pnl, 2)} ({round(overall_pnl_pct, 2)}%)")

def handle_predict(args):
    predictor = Predictor()
    print(f"⏳ Predicting for {args.symbol}...")
    res = predictor.predict_next_day(args.symbol)
    if "error" in res:
        print(f"❌ Error: {res['error']}")
        return

    table = [
        ["Symbol", res['symbol']],
        ["Current Price", f"₹{res['current_price']}"],
        ["Predicted Price", f"₹{res['predicted_price']}"],
        ["Expected Return", f"{res['expected_return_pct']}%"],
        ["Trend", res['trend']],
        ["Risk Score", res['risk_score']]
    ]
    print(tabulate(table, headers=["Metric", "Value"], tablefmt="grid"))

def handle_set_limit(args):
    trader = Trader()
    trader.set_limit(args.symbol, args.sl, args.target)
    print(f"✅ Limits updated for {args.symbol}: SL={args.sl}, Target={args.target}")

def handle_daemon(args):
    import asyncio
    from core.daemon import WatcherDaemon
    print("🚀 Starting Daemon (Bot + Watcher)... Press Ctrl+C to stop.")
    daemon = WatcherDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        print("Daemon stopped manually.")
