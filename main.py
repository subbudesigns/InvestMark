import argparse
from cli import commands

def main():
    parser = argparse.ArgumentParser(description="InvestMark CLI - Stock Trading System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Buy command
    parser_buy = subparsers.add_parser("buy", help="Buy a stock")
    parser_buy.add_argument("--symbol", required=True, help="Stock symbol")
    parser_buy.add_argument("--qty", required=True, type=int, help="Quantity to buy")

    # Sell command
    parser_sell = subparsers.add_parser("sell", help="Sell a stock")
    parser_sell.add_argument("--symbol", required=True, help="Stock symbol")
    parser_sell.add_argument("--qty", required=True, type=int, help="Quantity to sell")

    # Hold command
    parser_hold = subparsers.add_parser("hold", help="Hold a stock")
    parser_hold.add_argument("--symbol", required=True, help="Stock symbol")

    # Portfolio command
    subparsers.add_parser("portfolio", help="View portfolio summary")

    # Predict command
    parser_predict = subparsers.add_parser("predict", help="Predict next day price")
    parser_predict.add_argument("--symbol", required=True, help="Stock symbol")

    # Set-limit command
    parser_limit = subparsers.add_parser("set-limit", help="Set stop-loss and target")
    parser_limit.add_argument("--symbol", required=True, help="Stock symbol")
    parser_limit.add_argument("--sl", type=float, help="Stop loss price")
    parser_limit.add_argument("--target", type=float, help="Target price")

    # Daemon command
    subparsers.add_parser("daemon", help="Run background watcher and Telegram bot")

    args = parser.parse_args()

    if args.command == "buy":
        commands.handle_buy(args)
    elif args.command == "sell":
        commands.handle_sell(args)
    elif args.command == "hold":
        commands.handle_hold(args)
    elif args.command == "portfolio":
        commands.handle_portfolio(args)
    elif args.command == "predict":
        commands.handle_predict(args)
    elif args.command == "set-limit":
        commands.handle_set_limit(args)
    elif args.command == "daemon":
        commands.handle_daemon(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
