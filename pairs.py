import ccxt
import asyncio
from collections import defaultdict
from time import sleep

pairs = []
sym_val_j = defaultdict(lambda: {'bidPrice': 0, 'askPrice': 0})
FILTERED_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT',
    'SOL/USDT', 'DOT/USDT', 'LTC/USDT', 'LINK/USDT', 'MATIC/USDT',
    'BCH/BTC', 'DOGE/BTC', 'AVAX/ETH', 'TRX/USDT', 'SHIB/ETH',
    'UNI/USDT', 'ETC/BTC', 'VET/USDT', 'FIL/USDT', 'ICP/USDT',
    'ETH/BTC', 'BNB/ETH'
]
async def get_pairs(exchange):
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

async def fetch_data(exchange):
    global pairs, sym_val_j
    while True:
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
            await execute_trade(exchange, trade)

        await asyncio.sleep(10)  # Fetch data every 10 seconds

async def execute_trade(exchange, trade_info):
    try:
        # Fetch market precision
        market = exchange.market(trade_info['lv1'])
        precision = market['precision']
        print("pre",precision)

        # Define amount to trade (this can be adjusted based on your requirements)
        amount = 1  # This should be in accordance with your balance and strategy
        
        amount_precision = int(precision['amount'])
        rounded_amount = round(amount, amount_precision)
        print("Rounded",rounded_amount)
        
        # Execute a market order
       # order = await exchange.create_market_order(trade_info['lv1'], 'buy', rounded_amount)
        #print(f"Order executed for {trade_info['lv1']}: {order}")
    except Exception as e:
        print(f"Error executing trade for {trade_info['lv1']}: {e}")



async def main():
    exchange = ccxt.binance({
       # 'apiKey': 'wcLe0WgciPNWSmFest18LORVbJO2h87vEAd7hrzFFkgBIYxgvmzmxvaRCB0Ko8la',      # Replace with your API key
        #'secret': 'wHEqk4UhR65FzvwLwZHsq1tgPhBfeENVqDMB4uZYpgzfF8edD18b9LIb6NnUrPTx', 
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot'  # Set to spot market
        }
    })
    exchange.set_sandbox_mode(True)
    await get_pairs(exchange)
    await fetch_data(exchange)

if __name__ == "__main__":
    asyncio.run(main())
