import threading
import time
import ccxt
import asyncio
from collections import defaultdict
from time import sleep

running = False
thread = None

trading_output=[]

pairs = []
sym_val_j = defaultdict(lambda: {'bidPrice': 0, 'askPrice': 0})
FILTERED_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT',
    'BCH/BTC', 'DOGE/BTC', 'AVAX/ETH', 'TRX/USDT', 'SHIB/ETH',
    'UNI/USDT', 'ETC/BTC', 'VET/USDT', 'FIL/USDT', 'ICP/USDT',
    'ETH/BTC', 'BNB/ETH'
]

bybit_api='BamIlL6uOV7K4ytPbV'
bybit_sec='wF5oory8kAwB66X6ea2zqv5eWlfRz8QXTPRH'

api='wcLe0WgciPNWSmFest18LORVbJO2h87vEAd7hrzFFkgBIYxgvmzmxvaRCB0Ko8la'
secret='wHEqk4UhR65FzvwLwZHsq1tgPhBfeENVqDMB4uZYpgzfF8edD18b9LIb6NnUrPTx'
exchange = ccxt.bybit({
    'apiKey': bybit_api,
    'secret': bybit_sec,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot' , # Set to spot market
        'adjustForTimeDifference': True


    }
})

#exchange.set_sandbox_mode(True)
exchange.enableDemoTrading(True)

async def get_pairs():
    global pairs, sym_val_j
    markets = exchange.load_markets()

    for symbol in markets:
        # Check if the market type is 'spot'
        if markets[symbol]['type'] == 'spot'  and symbol in FILTERED_SYMBOLS:
            sym_val_j[symbol]  # Initialize entry

    base_symbols = set()
    quote_symbols = set()

    #print(sym_val_j)
    for symbol in sym_val_j.keys():
        base_symbols.add(symbol.split('/')[0])
        quote_symbols.add(symbol.split('/')[1])

    valid_pairs = list(sym_val_j.keys())

    for d1 in base_symbols:
        for d2 in quote_symbols:
            for d3 in base_symbols:
                if d1 != d2 and d1 != d3 and d2 != d3:
                    lv1, lv2, lv3 = [], [], []
                    l1, l2, l3 = "", "", ""
                    if f"{d1}/{d2}" in valid_pairs:
                        lv1.append(f"{d1}/{d2}")
                        l1 = "num"
                    if f"{d2}/{d1}" in valid_pairs:
                        lv1.append(f"{d2}/{d1}")
                        l1 = "den"
                    if f"{d2}/{d3}" in valid_pairs:
                        lv2.append(f"{d2}/{d3}")
                        l2 = "num"
                    if f"{d3}/{d2}" in valid_pairs:
                        lv2.append(f"{d3}/{d2}")
                        l2 = "den"
                    if f"{d3}/{d1}" in valid_pairs:
                        lv3.append(f"{d3}/{d1}")
                        l3 = "num"
                    if f"{d1}/{d3}" in valid_pairs:
                        lv3.append(f"{d1}/{d3}")
                        l3 = "den"

                    if lv1 and lv2 and lv3:
                        pairs.append({
                            'l1': l1, 'l2': l2, 'l3': l3,
                            'd1': d1, 'd2': d2, 'd3': d3,
                            'lv1': lv1[0], 'lv2': lv2[0], 'lv3': lv3[0],
                            'value': -100, 'tpath': ""
                        })

    print(f"Finished identifying all the paths. Total symbols = {len(sym_val_j)}. Total paths = {len(pairs)}")



async def fetch_data():
    global pairs, sym_val_j
    while running:
        for symbol in sym_val_j.keys():
            ticker = exchange.fetch_ticker(symbol)
            bid_price = ticker['bid']
            ask_price = ticker['ask']
            sym_val_j[symbol]['bidPrice'] = bid_price if bid_price else sym_val_j[symbol]['bidPrice']
            sym_val_j[symbol]['askPrice'] = ask_price if ask_price else sym_val_j[symbol]['askPrice']

            #print(sym_val_j)

        # Perform calculations
        for d in [p for p in pairs if p['lv1'] in sym_val_j or p['lv2'] in sym_val_j or p['lv3'] in sym_val_j]:
            if (sym_val_j[d['lv1']]['bidPrice'] and
                sym_val_j[d['lv2']]['bidPrice'] and
                sym_val_j[d['lv3']]['bidPrice']):

                #print(sym_val_j)
                
                lv_calc, lv_str = 1.0, ""
                
                if d['l1'] == "num":
                    lv_calc *= sym_val_j[d['lv1']]['bidPrice']
                    lv_str += f"{d['d1']}->{d['lv1']}['bidP']['{sym_val_j[d['lv1']]['bidPrice']}']->{d['d2']}<br/>"
                else:
                    lv_calc *= 1 / sym_val_j[d['lv1']]['askPrice']
                    lv_str += f"{d['d1']}->{d['lv1']}['askP']['{sym_val_j[d['lv1']]['askPrice']}']->{d['d2']}<br/>"

                if d['l2'] == "num":
                    lv_calc *= sym_val_j[d['lv2']]['bidPrice']
                    lv_str += f"{d['d2']}->{d['lv2']}['bidP']['{sym_val_j[d['lv2']]['bidPrice']}']->{d['d3']}<br/>"
                else:
                    lv_calc *= 1 / sym_val_j[d['lv2']]['askPrice']
                    lv_str += f"{d['d2']}->{d['lv2']}['askP']['{sym_val_j[d['lv2']]['askPrice']}']->{d['d3']}<br/>"

                if d['l3'] == "num":
                    lv_calc *= sym_val_j[d['lv3']]['bidPrice']
                    lv_str += f"{d['d3']}->{d['lv3']}['bidP']['{sym_val_j[d['lv3']]['bidPrice']}']->{d['d1']}"
                else:
                    lv_calc *= 1 / sym_val_j[d['lv3']]['askPrice']
                    lv_str += f"{d['d3']}->{d['lv3']}['askP']['{sym_val_j[d['lv3']]['askPrice']}']->{d['d1']}"

                d['tpath'] = lv_str
                d['value'] = round((lv_calc - 1) * 100, 3)

        # Print results
        arbitrage_pairs = sorted([d for d in pairs if d['value'] > 0], key=lambda x: x['value'], reverse=True)
        #print("ARBITRAGE:", arbitrage_pairs)
        for trade in arbitrage_pairs:
            print(trade['tpath'], trade['value'])
            await execute_trade(trade)

        await asyncio.sleep(10)  # Fetch data every 10 seconds

async def execute_trade(trade_info):
    try:
        # Define base trading amount
        trading_amount = 0.01  # Modify as needed for trading amount

        # First trade: (either buy or sell based on `l1`)
        if trade_info['l1'] == "num":
            print(f"Executing: Buy {trade_info['d1']}/{trade_info['d2']}")
            order1 = exchange.create_order(trade_info['lv1'], 'market', 'buy', trading_amount)
        else:
            print(f"Executing: Sell {trade_info['d1']}/{trade_info['d2']}")
            order1 = exchange.create_order(trade_info['lv1'], 'market', 'sell', trading_amount)

        # Wait for the first order to be filled
        order1 = await wait_for_order_filled(order1['id'], trade_info['lv1'])
        trading_amount = order1['filled']  # Use filled amount as new trading amount

        # Second trade: (either buy or sell based on `l2`)
        if trade_info['l2'] == "num":
            print(f"Executing: Buy {trade_info['d2']}/{trade_info['d3']}")
            order2 = exchange.create_order(trade_info['lv2'], 'market', 'buy', trading_amount)
        else:
            print(f"Executing: Sell {trade_info['d2']}/{trade_info['d3']}")
            order2 = exchange.create_order(trade_info['lv2'], 'market', 'sell', trading_amount)

        # Wait for the second order to be filled
        order2 = await wait_for_order_filled( order2['id'], trade_info['lv2'])
        trading_amount = order2['filled']

        # Third trade: (either buy or sell based on `l3`)
        if trade_info['l3'] == "num":
            print(f"Executing: Buy {trade_info['d3']}/{trade_info['d1']}")
            order3 = exchange.create_order(trade_info['lv3'], 'market', 'buy', trading_amount)
        else:
            print(f"Executing: Sell {trade_info['d3']}/{trade_info['d1']}")
            order3 = exchange.create_order(trade_info['lv3'], 'market', 'sell', trading_amount)

        # Wait for the third order to be filled
        order3 = await wait_for_order_filled( order3['id'], trade_info['lv3'])

        # Check the status of all orders
        print("Trade executed successfully:")
        print(f"Order 1: {order1}")
        print(f"Order 2: {order2}")
        print(f"Order 3: {order3}")

    except Exception as e:
        print(f"Error executing trade: {e}")

async def wait_for_order_filled(order_id, symbol):
    print("wait")
    """
    Helper function to wait for an order to be filled.
    It will periodically check the order status until it is 'closed' or 'filled'.
    """
    while True:
        order = exchange.fetchOpenOrder(order_id, symbol)
        if order['status'] == 'closed' or order['status'] == 'filled':
            return order
        await asyncio.sleep(1)


async def main():
    global running
    await get_pairs()
    while running:
        await fetch_data()



def _run():
    global running
    initial_balance = exchange.fetch_balance()
    print("Starting Balance:", initial_balance)
    while running:
        asyncio.run(main())
        time.sleep(5)
    final_balance = exchange.fetch_balance()
    print("Ending Balance:", final_balance)
    print("Bot has exited the run loop.")

def start_bot():
    global running, thread
    if not running:
        running = True
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        print("Bot started")

def stop_bot():
    global running
    if running:
        running = False
        print("Signaled bot to stop...")
        thread.join(timeout=0)
        print("Bot stopped")

def is_running():
    return running
