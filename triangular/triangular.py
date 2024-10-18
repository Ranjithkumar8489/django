import asyncio
import json
from binance import AsyncClient
from binance.streams import BinanceSocketManager
import logging
from collections import defaultdict

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
    "BTCUSDT", "ETHBTC", "ETHUSDT",
    "BTCUSDT", "BNBBTC", "BNBUSDT",
    "ETHUSDT", "BNBETH", "BNBUSDT",
    "BTCUSDT", "ADABTC", "ADAUSDT",
    "ETHUSDT", "XRPETH", "XRPUSDT"
]

API_KEY = '4SA6iXTp6m5HlpjczckAlVk5uLfcVyGwQe8MNUCr5O7m1l8rjvgGOzza27efpDeB'
API_SECRET = '5CQ5ycPLBQ7Ryk5hyTfQBoGCNYSlKNZI6zVyGMRf13QzAMj4VnlTuJE7mPkgKvx0'

risk_percentage = 1

async def get_pairs():
    try:
        # Fetch exchange info
        e_info = await client.get_exchange_info()
        
        symbols = list(set(
            [item for sublist in [(d['baseAsset'], d['quoteAsset']) for d in e_info['symbols'] if d['status'] == 'TRADING'] for item in sublist]
        ))
        
        valid_pairs = [d['symbol'] for d in e_info['symbols'] if d['status'] == 'TRADING']
        
        for symbol in valid_pairs:
            if symbol in Filtered_Symbols:
                sym_val_j[symbol] = {'bidPrice': 0, 'askPrice': 0}

        s1, s2, s3 = symbols, symbols, symbols

        #print(symbols)

        # Identify Arbitrage Paths
        for d1 in s1:
            for d2 in s2:
                for d3 in s3:
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
                            #print(pairs)

        log(f"Finished identifying Arbitrage Paths. Total paths = {len(pairs)}")

    except Exception as e:
        error(f"Error fetching pairs: {e}")

async def process_data():
    try:
        # Perform calculations and prepare for alerts
        for d in pairs:
            if (
                sym_val_j[d['lv1']]['bidPrice'] > 0 and
                sym_val_j[d['lv2']]['bidPrice'] > 0 and
                sym_val_j[d['lv3']]['bidPrice'] > 0
            ):
                if d['l1'] == 'num':
                    lv_calc = sym_val_j[d['lv1']]['bidPrice']
                    lv_str = f"{d['d1']}->{d['lv1']}['bidPrice']['{sym_val_j[d['lv1']]['bidPrice']}']"
                else:
                    lv_calc = 1 / sym_val_j[d['lv1']]['askPrice']
                    lv_str = f"{d['d1']}->{d['lv1']}['askPrice']['{sym_val_j[d['lv1']]['askPrice']}']"
                
                # Level 2 calculation
                if d['l2'] == 'num':
                    lv_calc *= sym_val_j[d['lv2']]['bidPrice']
                    lv_str += f"->{d['d2']}->{d['lv2']}['bidPrice']['{sym_val_j[d['lv2']]['bidPrice']}']"
                else:
                    lv_calc *= 1 / sym_val_j[d['lv2']]['askPrice']
                    lv_str += f"->{d['d2']}->{d['lv2']}['askPrice']['{sym_val_j[d['lv2']]['askPrice']}']"
                
                # Level 3 calculation
                if d['l3'] == 'num':
                    lv_calc *= sym_val_j[d['lv3']]['bidPrice']
                    lv_str += f"->{d['d3']}->{d['lv3']}['bidPrice']['{sym_val_j[d['lv3']]['bidPrice']}']->{d['d1']}"
                else:
                    lv_calc *= 1 / sym_val_j[d['lv3']]['askPrice']
                    lv_str += f"->{d['d3']}->{d['lv3']}['askPrice']['{sym_val_j[d['lv3']]['askPrice']}']->{d['d1']}"

                d['tpath'] = lv_str
                d['value'] = round((lv_calc - 1) * 100, 3)

        # Send results sorted using built-in sorted function
        arbitrage_pairs = sorted([d for d in pairs if d['value'] > 0], key=lambda x: x['value'], reverse=True)

        if arbitrage_pairs:
            #print(arbitrage_pairs)
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

            print(f"{asset1}: {starting_balance1}")
            print(f"{asset2}: {starting_balance2}")
            print(f"{asset3}: {starting_balance3}")




            if starting_balance1 <= 0 or starting_balance2 <= 0 or starting_balance3 <= 0:
                print(f"Insufficient balance for {asset1}, {asset2}, or {asset3}. Skipping this arbitrage opportunity.")
                continue

            if arbitrage['l1'] == 'num':
                price1 = sym_val_j[arbitrage['lv1']]['bidPrice']
                side1 = 'SELL'
            else:
                price1 = sym_val_j[arbitrage['lv1']]['askPrice']
                side1 = 'BUY'

            if arbitrage['l2'] == 'num':
                price2 = sym_val_j[arbitrage['lv2']]['bidPrice']
                side2 = 'SELL'
            else:
                price2 = sym_val_j[arbitrage['lv2']]['askPrice']
                side2 = 'BUY'

            if arbitrage['l3'] == 'num':
                price3 = sym_val_j[arbitrage['lv3']]['bidPrice']
                side3 = 'SELL'
            else:
                price3 = sym_val_j[arbitrage['lv3']]['askPrice']
                side3 = 'BUY'

            trade_quantity1 = (risk_percentage / 100) * starting_balance1
            min_qty1, max_qty1, step_size1, min_notional1, max_notional1 = await get_limit_qty(arbitrage['lv1'])


            # Step 1: Execute the first trade
            side1 = 'SELL' if arbitrage['l1'] == 'num' else 'BUY'
            price1 = sym_val_j[arbitrage['lv1']]['bidPrice'] if side1 == 'SELL' else sym_val_j[arbitrage['lv1']]['askPrice']
            trade_quantity1 = (risk_percentage / 100) * starting_balance1

            filled_qty1 = await execute_trade(arbitrage['lv1'], side1, trade_quantity1, price1)
            if not filled_qty1:
                print(f"Skipping arbitrage due to failure in the first trade for {arbitrage['lv1']}.")
                continue

            # Step 2: Execute the second trade
            side2 = 'SELL' if arbitrage['l2'] == 'num' else 'BUY'
            price2 = sym_val_j[arbitrage['lv2']]['bidPrice'] if side2 == 'SELL' else sym_val_j[arbitrage['lv2']]['askPrice']
            filled_qty2 = await execute_trade(arbitrage['lv2'], side2, filled_qty1, price2)
            if not filled_qty2:
                print(f"Skipping arbitrage due to failure in the second trade for {arbitrage['lv2']}.")
                continue

            # Step 3: Execute the third trade
            side3 = 'SELL' if arbitrage['l3'] == 'num' else 'BUY'
            price3 = sym_val_j[arbitrage['lv3']]['bidPrice'] if side3 == 'SELL' else sym_val_j[arbitrage['lv3']]['askPrice']
            filled_qty3 = await execute_trade(arbitrage['lv3'], side3, filled_qty2, price3)
            if not filled_qty3:
                print(f"Skipping arbitrage due to failure in the third trade for {arbitrage['lv3']}.")
                continue

            print(f"Successfully completed arbitrage trade for {arbitrage['lv1']} -> {arbitrage['lv2']} -> {arbitrage['lv3']}")

            
            ending_balance1 = await fetch_balance(asset1)
            ending_balance2 = await fetch_balance(asset2)
            ending_balance3 = await fetch_balance(asset3)

            print(f"{asset1}: {ending_balance1}")
            print(f"{asset2}: {ending_balance2}")
            print(f"{asset3}: {ending_balance3}")


    
    except Exception as e:
        print(f"Error executing arbitrage trade for {arbitrage}: {e}")
async def execute_trade(symbol, side, trade_quantity, price):
    try:
        min_qty, max_qty, step_size, min_notional, max_notional = await get_limit_qty(symbol)

        # Ensure trade quantity adheres to market limits
        trade_quantity = round(trade_quantity, 8)
        
        if trade_quantity < min_qty:
            trade_quantity = min_qty
        elif trade_quantity > max_qty:
            trade_quantity = max_qty

        notional_value = trade_quantity * price
        if notional_value < min_notional:
            trade_quantity = min_notional / price
        
        trade_quantity = round(trade_quantity, 8)

        order = await create_order(symbol, side, trade_quantity, price)
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
                filled_qty = float(order_info['executedQty'])
                return filled_qty
            await asyncio.sleep(2)
        except Exception as e:
            error(f"Error fetching order {order_id} on {symbol}: {e}")
            await asyncio.sleep(2)

async def get_limit_qty(symbol):
    try:
        # Fetch exchange information for the specific symbol
        exchange_info = await client.get_symbol_info(symbol)
        filters = exchange_info['filters']

        min_qty = max_qty = step_size = None
        min_notional = max_notional = None

        for f in filters:
            if f['filterType'] == 'LOT_SIZE':
                min_qty = float(f['minQty'])
                max_qty = float(f['maxQty'])
                step_size = float(f['stepSize'])
            elif f['filterType'] == 'NOTIONAL':
                min_notional = float(f['minNotional'])
                if 'maxNotional' in f:
                    max_notional = float(f['maxNotional'])

        return min_qty, max_qty, step_size, min_notional, max_notional

    except Exception as e:
        error(f"Error getting limit quantities for {symbol}: {e}")
        return None, None, None, None, None



async def fetch_balance(asset):
    try:
        balance_info = await client.get_asset_balance(asset=asset)
        available_balance = float(balance_info['free'])
        return available_balance
    except Exception as e:
        print(f"Error fetching balance for {asset}: {e}")
        return 0.0

async def create_order(symbol, side, quantity, price):
    try:
        min_qty, max_qty, step_size, min_notional, max_notional = await get_limit_qty(symbol)
        
        if quantity < min_qty:
            quantity = min_qty
        
        quantity = round(quantity - (quantity % step_size), 8)
        
        notional_value = quantity * price
        if notional_value < min_notional:
            quantity = min_notional / price
        
        quantity = round(quantity - (quantity % step_size), 8)
        
        order = await client.create_order(
            symbol=symbol,
            side=side,
            type='LIMIT',
            quantity=quantity,
            price=str(price),
            timeInForce='GTC'
        )
        return order
    
    except Exception as e:
        print(f"Error creating order for {symbol}: {e}")
        return None


async def fetch_ticker_data():
    while True:
        try:
            for symbol in sym_val_j.keys():
                ticker = await client.get_ticker(symbol=symbol)
                if ticker['symbol'] in sym_val_j:
                    sym_val_j[ticker['symbol']]['bidPrice'] = float(ticker['bidPrice'])
                    sym_val_j[ticker['symbol']]['askPrice'] = float(ticker['askPrice'])

            #print(sym_val_j)
            await process_data()
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Error fetching ticker data: {e}")
            await asyncio.sleep(5)



async def main():
    global client
    try:
        # Initialize the client
        client = await AsyncClient.create(API_KEY, API_SECRET, testnet=True)
        
        await get_pairs()
        
        # Start fetching ticker data
        await fetch_ticker_data()

    except KeyboardInterrupt:
        print("Keyboard interrupt received. Closing connection...")
    finally:
        if client:
            await client.close_connection()
        print("Client connection closed. Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
