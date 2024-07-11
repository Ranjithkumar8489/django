import time

from .exchange_config import exchange_objects

def arbitrage(symbol, amount, exchanges):
    try:
        for exchange_name in exchanges:
            exchange = exchange_objects.get(exchange_name)
            if not exchange:
                print(f"Exchange '{exchange_name}' not found. Skipping.")
                continue

            if exchange_name.lower() == "kucoin":
                kucoin_password = "200023"  # Replace with actual password
                exchange.password = kucoin_password

            # Fetch prices
            ticker = exchange.fetch_ticker(symbol)
            if not ticker:
                print(f"Failed to fetch ticker for {symbol} on {exchange_name}. Skipping.")
                continue

            bid_price = ticker['bid']
            ask_price = ticker['ask']

            # Calculate profit
            buy_total = bid_price * amount
            sell_total = ask_price * amount
            profit = sell_total - buy_total

            

            # Execute buy order
            buy_order = exchange.create_limit_buy_order(symbol, amount, bid_price)
            if not buy_order:
                print(f"Buy order on {exchange_name} failed. Skipping.")
                continue

           
            if buy_order:
                print(buy_order)
                print(f"Buy order placed on {exchange_name} successfully.")

            # Execute sell order
                sell_order = exchange.create_limit_sell_order(symbol, amount, ask_price)
                if not sell_order:
                    print(f"Sell order on {exchange_name} failed. Skipping.")
                    continue

                print(f"Sell order placed on {exchange_name} successfully.")
                print(sell_order)

                if buy_order and sell_order:
                    print("Arbitrage successful!")

    except Exception as e:
        print(f"Error during arbitrage: {e}")
        return 0
