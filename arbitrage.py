import ccxt
import time

exchanges = {}
stop_bot = False  # Global flag to control bot execution

def connect_exchanges(exchange_list, exchange_keys):
    for exchange_name, keys in exchange_keys.items():
        if exchange_name in exchange_list:
            exchange_class = getattr(ccxt, exchange_name.lower())
            exchanges[exchange_name] = exchange_class({
                'apiKey': keys['api_key'],
                'secret': keys['secret']
            })
    return exchanges

def start_arbitrage_bot(symbol, balance, stop_loss_percentage, target_profit_percentage, risk_per_trade_percentage, price_difference_threshold):
    global stop_bot
    stop_bot = False  # Reset stop_bot flag when starting the bot
    while not stop_bot:
        for name, exchange in exchanges.items():
            try:
                balance_info = exchange.fetch_balance()
                if balance_info['total']['USD'] >= balance:
                    order_book = exchange.fetch_order_book(symbol)
                    if order_book['bids'] and order_book['asks']:
                        buy_price = order_book['bids'][0][0]
                        sell_price = order_book['asks'][0][0]
                        price_difference = abs(buy_price - sell_price)
                        print(buy_price)
                        print(sell_price)
                        print(price_difference)
                        if price_difference >= price_difference_threshold:
                            stop_loss_price = buy_price - (buy_price * stop_loss_percentage / 100)
                            target_profit_price = buy_price + (buy_price * target_profit_percentage / 100)
                            risk_amount = balance * (risk_per_trade_percentage / 100)
                            position_size = risk_amount / (buy_price - stop_loss_price)
                            print(f"Arbitrage opportunity found on {name}! Buying at {buy_price} and selling at {sell_price}.")
                            print(f"Stop loss at {stop_loss_price}, target profit at {target_profit_price}, position size: {position_size}")
                            # Place buy order
                            buy_order = exchange.create_limit_buy_order(symbol, position_size, buy_price)
                            # Place sell order with stop-loss and take-profit
                            sell_order = exchange.create_limit_sell_order(symbol, position_size, sell_price, {
                                'stopLoss': stop_loss_price,
                                'takeProfit': target_profit_price
                            })
                            print(f"Buy order placed: {buy_order}, Sell order placed: {sell_order}")
                        else:
                            print(f"Price difference below threshold on {name}. Skipping trade.")
                else:
                    print(f"Not enough balance on {name} for arbitrage.")
            except ccxt.BaseError as e:
                print(f"An error occurred on {name}: {e}")
                # Add more specific exception handling if needed
        time.sleep(5)  # Wait before checking again

def stop_arbitrage_bot():
    global stop_bot
    stop_bot = True
    print("Arbitrage bot stopped.")

