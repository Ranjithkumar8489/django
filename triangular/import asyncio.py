import asyncio
import json
from binance import AsyncClient
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.info
error = logging.error

# Global Variables
pairs = []
client = None
sym_val_j = defaultdict(lambda: {'bidPrice': 0, 'askPrice': 0})

Filtered_Symbols = [
    "BTCUSDT", "SNTBTC", "SNTUSDT",
    "ETHBTC", "ETHUSDT",
    "BNBBTC", "BNBUSDT",
    "ADABTC", "ADAUSDT",
    "XRPETH", "XRPUSDT"
]

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

risk_percentage = 1

async def get_pairs():
    try:
        e_info = await client.get_exchange_info()
        
        valid_pairs = [d['symbol'] for d in e_info['symbols'] if d['status'] == 'TRADING']
        
        for symbol in valid_pairs:
            if symbol in Filtered_Symbols:
                sym_val_j[symbol] = {'bidPrice': 0, 'askPrice': 0}

        symbols = list(sym_val_j.keys())

        for d1 in symbols:
            for d2 in symbols:
                for d3 in symbols:
                    if not (d1 == d2 or d2 == d3 or d3 == d1):
                        lv1, lv2, lv3, l1, l2, l3 = [], [], [], '', '', ''
                        
                        if f"{d1}{d2}" in sym_val_j:
                            lv1.append(f"{d1}{d2}")
                            l1 = 'num'
                        if f"{d2}{d1}" in sym_val_j:
                            lv1.append(f"{d2}{d1}")
                            l1 = 'den'
                        
                        if f"{d2}{d3}" in sym_val_j:
                            lv2.append(f"{d2}{d3}")
                            l2 = 'num'
                        if f"{d3}{d2}" in sym_val_j:
                            lv2.append(f"{d3}{d2}")
                            l2 = 'den'
                        
                        if f"{d3}{d1}" in sym_val_j:
                            lv3.append(f"{d3}{d1}")
                            l3 = 'num'
                        if f"{d1}{d3}" in sym_val_j:
                            lv3.append(f"{d1}{d3}")
                            l3 = 'den'
                        
                        if lv1 and lv2 and lv3:
                            pairs.append({
                                'l1': l1,
                                'l2': l2,
                                'l3': l3,
                                'd1': d1,
                                'd2': d2,
                                'd3': d3,
                                'lv1': lv1[0],
                                'lv2': lv2[0],
                                'lv3': lv3[0],
                                'value': -100,
                                'tpath': '',
                            })

        log(f"Finished identifying Arbitrage Paths. Total paths = {len(pairs)}")

    except Exception as e:
        error(f"Error fetching pairs: {e}")

async def process_data():
    try:
        for d in pairs:
            if (
                sym_val_j[d['lv1']]['bidPrice'] > 0 and
                sym_val_j[d['lv2']]['bidPrice'] > 0 and
                sym_val_j[d['lv3']]['bidPrice'] > 0
            ):
                lv_calc = 1.0
                lv_str = ""

                for idx, (level, symbol, d_key) in enumerate([(d['l1'], d['lv1'], d['d1']), (d['l2'], d['lv2'], d['d2']), (d['l3'], d['lv3'], d['d3'])]):
                    if level == 'num':
                        lv_calc *= sym_val_j[symbol]['bidPrice']
                        lv_str += f"{d_key}->{symbol}['bidPrice']['{sym_val_j[symbol]['bidPrice']}]"
                    else:
                        lv_calc *= 1 / sym_val_j[symbol]['askPrice']
                        lv_str += f"{d_key}->{symbol}['askPrice']['{sym_val_j[symbol]['askPrice']}]"
                    if idx < 2:
                        lv_str += "->"

                d['tpath'] = lv_str
                d['value'] = round((lv_calc - 1) * 100, 3)

        arbitrage_pairs = sorted([d for d in pairs if d['value'] > 0], key=lambda x: x['value'], reverse=True)

        if arbitrage_pairs:
            await executed_trades(arbitrage_pairs)

    except Exception as e:
        error(f"Error processing data: {e}")

async def executed_trades(arbitrage_pairs):
    try:
        for arbitrage in arbitrage_pairs:
            asset1, asset2, asset3 = arbitrage['d1'], arbitrage['d2'], arbitrage['d3']

            starting_balance1 = await fetch_balance(asset1)
            starting_balance2 = await fetch_balance(asset2)
            starting_balance3 = await fetch_balance(asset3)

            if starting_balance1 <= 0 or starting_balance2 <= 0 or starting_balance3 <= 0:
                print(f"Insufficient balance for {asset1}, {asset2}, or {asset3}. Skipping this arbitrage opportunity.")
                continue

            filled_qty1 = await execute_trade(arbitrage, asset1, 'SELL' if arbitrage['l1'] == 'num' else 'BUY', starting_balance1)
            if not filled_qty1:
                continue

            filled_qty2 = await execute_trade(arbitrage, asset2, 'SELL' if arbitrage['l2'] == 'num' else 'BUY', filled_qty1)
            if not filled_qty2:
                continue

            filled_qty3 = await execute_trade(arbitrage, asset3, 'SELL' if arbitrage['l3'] == 'num' else 'BUY', filled_qty2)
            if not filled_qty3:
                continue

            print(f"Successfully completed arbitrage trade for {arbitrage['lv1']} -> {arbitrage['lv2']} -> {arbitrage['lv3']}")

    except Exception as e:
        error(f"Error executing arbitrage trade for {arbitrage}: {e}")

async def execute_trade(arbitrage, symbol, side, trade_quantity):
    try:
        min_qty, max_qty, step_size, min_notional, max_notional = await get_limit_qty(symbol)

        # Calculate the trade quantity based on risk percentage
        trade_quantity = round((risk_percentage / 100) * trade_quantity, 8)

        # Ensure trade quantity adheres to market limits
        if trade_quantity < min_qty:
            trade_quantity = min_qty
        elif trade_quantity > max_qty:
            trade_quantity = max_qty

        notional_value = trade_quantity * (sym_val_j[symbol]['bidPrice'] if side == 'SELL' else sym_val_j[symbol]['askPrice'])
        if notional_value < min_notional:
            trade_quantity = min_notional / (sym_val_j[symbol]['bidPrice'] if side == 'SELL' else sym_val_j[symbol]['askPrice'])

        order = await create_order(symbol, side, trade_quantity)
        if not order:
            error(f"Failed to execute order for {symbol}.")
            return None

        filled_qty = await wait_until_trade_close(order['orderId'], symbol)
        return filled_qty if filled_qty > 0 else None

    except Exception as e:
        error(f"Error executing trade for {symbol}: {e}")
        return None

async def wait_until_trade_close(order_id, symbol):
    while True:
        try:
            order_info = await client.get_order(symbol=symbol, orderId=order_id)
            if order_info['status'] == 'FILLED':
                return float(order_info['executedQty'])
            await asyncio.sleep(2)
        except Exception as e:
            error(f"Error fetching order {order_id} on {symbol}: {e}")
            await asyncio.sleep(2)

async def get_limit_qty(symbol):
    try:
        exchange_info = await client.get_symbol_info(symbol)
        filters = exchange_info['filters']

        for f in filters:
            if f['filterType'] == 'LOT_SIZE':
                min_qty = float(f['minQty'])
                max_qty = float(f['maxQty'])
                step_size = float(f['stepSize'])
            elif f['filterType'] == 'NOTIONAL':
                min_notional = float(f['minNotional'])
                max_notional = float(f.get('maxNotional', float('inf')))

        return min_qty, max_qty, step_size, min_notional, max_notional

    except Exception as e:
        error(f"Error getting limit quantities for {symbol}: {e}")
        return None, None, None, None, None

async def fetch_balance(asset):
    try:
        balance_info = await client.get_asset_balance(asset=asset)
        return float(balance_info['free'])
    except Exception as e:
        error(f"Error fetching balance for {asset}: {e}")
        return 0.0

async def create_order(symbol, side, quantity):
    try:
        order = await client.create_order(
            symbol=symbol,
            side=side,
            type='LIMIT',
            quantity=quantity,
            price=str(sym_val_j[symbol]['bidPrice'] if side == 'SELL' else sym_val_j[symbol]['askPrice']),
            timeInForce='GTC'
        )
        return order
    except Exception as e:
        error(f"Error creating order for {symbol}: {e}")
        return None

async def fetch_ticker_data():
    while True:
        try:
            for symbol in sym_val_j.keys():
                ticker = await client.get_ticker(symbol=symbol)
                if ticker['symbol'] in sym_val_j:
                    sym_val_j[ticker['symbol']]['bidPrice'] = float(ticker['bidPrice'])
                    sym_val_j[ticker['symbol']]['askPrice'] = float(ticker['askPrice'])

            await process_data()
            await asyncio.sleep(5)

        except Exception as e:
            error(f"Error fetching ticker data: {e}")
            await asyncio.sleep(5)

async def main():
    global client
    try:
        client = await AsyncClient.create(API_KEY, API_SECRET, testnet=True)
        
        await get_pairs()
        await fetch_ticker_data()

    except KeyboardInterrupt:
        print("Keyboard interrupt received. Closing connection...")
    finally:
        if client:
            await client.close_connection()
        print("Client connection closed. Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
