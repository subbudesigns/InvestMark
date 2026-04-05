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
    for sym, data in holdings.items():
        table.append([sym, data['quantity'], round(data['avg_price'], 2), round(data['total_invested'], 2)])
    
    print(tabulate(table, headers=["Symbol", "Quantity", "Avg Price", "Total Invested"], tablefmt="grid"))

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
