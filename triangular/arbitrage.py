import asyncio
from binance import AsyncClient
from binance.enums import *
import math
client = None
sym_val_j = {}
pairs = []

Filtered_Symbols = [
    "BTCUSDT", "SNTBTC", "SNTUSDT",
    "BTCUSDT", "ETHBTC", "ETHUSDT",
    "BTCUSDT", "BNBBTC", "BNBUSDT",
    "ETHUSDT", "BNBETH", "BNBUSDT",
    "BTCUSDT", "ADABTC", "ADAUSDT",
    "ETHUSDT", "XRPETH", "XRPUSDT",
    "LTCUSDT", "LTCEUR", "EURUSDT",
    "BTCUSDT", "LTCBTC", "LTUSDT",
    "ETHBTC", "LTCETH", "LTCUSDT",
    "BNBUSDT", "ETCBTC", "ETCUSDT",
    "XRPUSDT", "XRPBTC", "ETHXRP",
    "LINKUSDT", "LINKBTC", "ETHLINK",
    "DOTUSDT", "DOTBTC", "ETHDOT",
    "MATICUSDT", "MATICBTC", "ETHMATIC",
    "SOLUSDT", "SOLBTC", "ETHSOL"
]

amount=10
start_symbol = "USDT" 
async def get_pairs():
    global client
    e_info = await client.get_exchange_info()

    symbols = list(set(
        [item for sublist in [(d['baseAsset'], d['quoteAsset']) for d in e_info['symbols'] if d['status'] == 'TRADING'] for item in sublist]
    ))

    valid_pairs = [d['symbol'] for d in e_info['symbols'] if d['status'] == 'TRADING']

    for symbol in valid_pairs:
        if symbol in Filtered_Symbols:
            sym_val_j[symbol] = {'bidPrice': 0, 'askPrice': 0}

    for d1 in symbols:
        for d2 in symbols:
            for d3 in symbols:
                if d1 != d2 and d2 != d3 and d3 != d1:
                    lv1, lv2, lv3, l1, l2, l3 = [], [], [], '', '', ''
                    if f'{d1}{d2}' in sym_val_j:
                        lv1.append(f'{d1}{d2}')
                        l1 = 'num'
                    if f'{d2}{d1}' in sym_val_j:
                        lv1.append(f'{d2}{d1}')
                        l1 = 'den'

                    if f'{d2}{d3}' in sym_val_j:
                        lv2.append(f'{d2}{d3}')
                        l2 = 'num'
                    if f'{d3}{d2}' in sym_val_j:
                        lv2.append(f'{d3}{d2}')
                        l2 = 'den'

                    if f'{d3}{d1}' in sym_val_j:
                        lv3.append(f'{d3}{d1}')
                        l3 = 'num'
                    if f'{d1}{d3}' in sym_val_j:
                        lv3.append(f'{d1}{d3}')
                        l3 = 'den'

                    if lv1 and lv2 and lv3:
                        pairs.append({
                            'l1': l1, 'l2': l2, 'l3': l3, 
                            'd1': d1, 'd2': d2, 'd3': d3,
                            'lv1': lv1[0], 'lv2': lv2[0], 'lv3': lv3[0],
                            'value': -100, 'tpath': ''
                        })

    print("Scanner ready")
    print(f"Total Symbols: {len(symbols)}, Finished identifying Arbitrage Paths. Total paths = {len(pairs)}")

async def update_prices():
    global client
    while True:
        for symbol in sym_val_j.keys():
            order_book = await client.get_order_book(symbol=symbol)
            if order_book:
                sym_val_j[symbol]['bidPrice'] = float(order_book['bids'][0][0]) if order_book['bids'] else 0.0
                sym_val_j[symbol]['askPrice'] = float(order_book['asks'][0][0]) if order_book['asks'] else 0.0

        for pair in pairs:
            lv1_bid = sym_val_j[pair['lv1']]['bidPrice']
            lv2_bid = sym_val_j[pair['lv2']]['bidPrice']
            lv3_bid = sym_val_j[pair['lv3']]['bidPrice']
            lv1_ask = sym_val_j[pair['lv1']]['askPrice']
            lv2_ask = sym_val_j[pair['lv2']]['askPrice']
            lv3_ask = sym_val_j[pair['lv3']]['askPrice']

            lv_calc, lv_str = 0, ''
            if pair['l1'] == 'num':
                lv_calc = lv1_bid
                lv_str = f"{pair['d2']}...{pair['lv1']}-SELL-{lv1_bid}--"
            else:
                lv_calc = 1 / lv1_ask
                lv_str = f"{pair['d2']}...{pair['lv1']}-BUY-{lv1_ask}--"

            if pair['l2'] == 'num':
                lv_calc *= lv2_bid
                lv_str += f"{pair['d3']}...{pair['lv2']}-SELL-{lv2_bid}--"
            else:
                lv_calc *= 1 / lv2_ask
                lv_str += f"{pair['d3']}...{pair['lv2']}-BUY-{lv2_ask}--"

            if pair['l3'] == 'num':
                lv_calc *= lv3_bid
                lv_str += f"{pair['d1']}...{pair['lv3']}-SELL-{lv3_bid}"
            else:
                lv_calc *= 1 / lv3_ask
                lv_str += f"{pair['d1']}...{pair['lv3']}-BUY-{lv3_ask}"

            pair['tpath'] = lv_str
            pair['value'] = round((lv_calc - 1) * 100, 3)

        arbitrage_pairs = sorted([pair for pair in pairs if pair['value'] > 0], key=lambda x: x['value'], reverse=True)
        if arbitrage_pairs:
                await executed_trades(arbitrage_pairs)

        await asyncio.sleep(5)

def stepSizer(sy):
    with open("stepSize.txt") as f:
        for num, line in enumerate(f, 1):
            if sy in line:
                lineDect = line
                lineDetected = lineDect.replace("\n", "")
                stepSize_raw = lineDetected.partition(": ")[2]

                stepSize_raw_position = stepSize_raw.find("1")
                stepSize_pre_raw = stepSize_raw.partition(".")[2]
                stepSize_pre_raw_raw = stepSize_pre_raw.partition("1")[0]
                if stepSize_raw_position == 0:
                    noDec = True
                    return 0 
                else:
                    noDec = False
                    return stepSize_pre_raw_raw.count("0") + 1

# Truncate decimals without rounding them
def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

async def executed_trades(arbitrage_pairs):
    for arbitrage in arbitrage_pairs:
        try:
            tradePath = arbitrage['tpath']
            pathComponents = tradePath.split("--")

            first_side = "BUY" if "BUY" in pathComponents[0] else "SELL"
            second_side = "BUY" if "BUY" in pathComponents[1] else "SELL"
            third_side = "BUY" if "BUY" in pathComponents[2] else "SELL"

            
            first_mono_symbol = pathComponents[0].split("...")[0]
            second_mono_symbol = pathComponents[1].split("...")[0]
            third_mono_symbol = pathComponents[2].split("...")[0]

            first_symbol = pathComponents[0].split("...")[1].split("-")[0]
            second_symbol = pathComponents[1].split("...")[1].split("-")[0]
            third_symbol = pathComponents[2].split("...")[1].split("-")[0]

            first_raw_qty = pathComponents[0].split("-")[2]
            second_raw_qty = pathComponents[1].split("-")[2]
            third_raw_qty = pathComponents[2].split("-")[2]

            print("first_raw",first_raw_qty)
            print("second_raw",second_raw_qty)
            print("third_raw",third_raw_qty)

            # Definition of qty
            first_pre_qty = ""
            second_pre_qty = ""
            third_pre_qty = ""
            third_pass_qty = ""
            third_pass_pass_qty = ""

            for raw_qty in [first_raw_qty, second_raw_qty, third_raw_qty]:
                if "-" in str(raw_qty):
                    raw_qty = raw_qty.replace("-", "")
                    raw_qty = float(raw_qty)
                if "e" in str(raw_qty):
                    raw_qty = raw_qty.replace("e", "")
                    raw_qty = float(raw_qty)

            first_raw_qty = float(first_raw_qty)
            second_raw_qty = float(second_raw_qty)
            third_raw_qty = float(third_raw_qty)

            # Print processed quantities
            print(f"Processed quantities: {first_raw_qty}, {second_raw_qty}, {third_raw_qty}")

            # Combinations of orders and determination of quantities

            if first_side == "SELL" and second_side == "BUY" and third_side == "SELL":
                first_pre_qty = amount  
                first_qty = truncate(first_pre_qty, stepSizer(first_symbol))

                second_pre_qty = ((1 / float(second_raw_qty)) * (float(first_raw_qty) * amount)) 
                second_qty = truncate(second_pre_qty, stepSizer(second_symbol))

                third_pre_qty = ((1 / float(second_raw_qty)) * truncate((float(first_raw_qty) * amount), stepSizer(first_symbol)))  
                third_qty = truncate(second_qty, stepSizer(third_symbol))
                third_pass_qty = float(third_raw_qty) * third_pre_qty 

                # 

                st_to_nd_final = float(first_raw_qty) * first_qty 
                nd_from_st_final = float(second_raw_qty) * second_qty 

                nd_to_rd_final = second_qty 
                rd_from_nd_final = third_qty 

                st_to_rd_final = first_qty 
                rd_from_st_final = float(third_raw_qty) * third_qty


            ####################################################################################

            if first_side == "SELL" and second_side == "BUY" and third_side == "BUY":
                first_pre_qty = amount  
                first_qty = truncate(first_pre_qty, stepSizer(first_symbol))

                second_pre_qty = ((1 / float(second_raw_qty)) * (float(first_raw_qty) * amount)) 
                second_qty = truncate(second_pre_qty, stepSizer(second_symbol))

                third_pre_qty = (1 / float(third_raw_qty)) * float(second_pre_qty) 
                third_qty = truncate(third_pre_qty, stepSizer(third_symbol))
                third_pass_qty = third_pre_qty

                # 

                st_to_nd_final = float(first_raw_qty) * first_qty 
                nd_from_st_final = second_qty 

                nd_to_rd_final = float(second_raw_qty) * second_qty 
                rd_from_nd_final = float(third_raw_qty) * third_qty 

                st_to_rd_final = first_qty 
                rd_from_st_final = third_qty

            ####################################################################################

            if first_side == "BUY" and second_side == "BUY" and third_side == "SELL": 
                first_pre_qty = ((1 / float(first_raw_qty)) * amount) 
                first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

                second_pre_qty = ((1 / float(second_raw_qty)) * (1 / float(first_raw_qty) * amount)) 
                second_qty = truncate(float(second_pre_qty), stepSizer(second_symbol))

                third_pre_qty = second_pre_qty 
                third_qty = truncate(float(second_qty), stepSizer(third_symbol))
                third_pass_qty = float(third_raw_qty) * third_pre_qty

                # 

                st_to_nd_final = first_qty 
                nd_from_st_final = float(second_raw_qty) * second_qty 

                nd_to_rd_final = second_qty 
                rd_from_nd_final = third_qty 

                st_to_rd_final = float(first_raw_qty) * first_qty
                rd_from_st_final = float(third_raw_qty) * third_qty

            ####################################################################################

            if first_side == "BUY" and second_side == "SELL" and third_side == "BUY": 
                first_pre_qty = ((1 / float(first_raw_qty)) * amount) 
                first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

                second_pre_qty = first_pre_qty    
                second_qty = truncate(float(first_qty), stepSizer(second_symbol))

                third_pre_qty = ((1 / float(third_raw_qty)) * (float(second_raw_qty) * truncate(first_qty, stepSizer(first_symbol)))) 
                third_qty = truncate(float(third_pre_qty), stepSizer(third_symbol))
                third_pass_qty = third_pre_qty

                # 

                st_to_nd_final = first_qty 
                nd_from_st_final = second_qty 

                nd_to_rd_final = float(second_raw_qty) * second_qty  
                rd_from_nd_final = float(third_raw_qty) * third_qty  

                st_to_rd_final = float(first_raw_qty) * first_qty 
                rd_from_st_final = third_qty

            ####################################################################################

            if first_side == "SELL" and second_side == "SELL" and third_side == "BUY":
                first_pre_qty = amount 
                first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

                second_pre_qty = (float(first_raw_qty) * amount) 
                second_qty = truncate(float(second_pre_qty), stepSizer(second_symbol))
        
                third_pre_qty = ((1 / float(third_raw_qty)) * (float(second_raw_qty) * second_pre_qty)) 
                third_qty = truncate(float(third_pre_qty), stepSizer(third_symbol))
                third_pass_qty = third_pre_qty

                # 

                st_to_nd_final = float(first_raw_qty) * first_qty 
                nd_from_st_final = second_qty 

                nd_to_rd_final = float(second_raw_qty) * second_qty  
                rd_from_nd_final = float(third_raw_qty) * third_qty  

                st_to_rd_final = first_qty 
                rd_from_st_final = third_qty

            ####################################################################################

            if first_side == "BUY" and second_side == "SELL" and third_side == "SELL":
                first_pre_qty = ((1 / float(first_raw_qty)) * amount) 
                first_qty = truncate(float(first_pre_qty), stepSizer(first_symbol))

                second_pre_qty = first_pre_qty 
                second_qty = truncate(float(first_qty), stepSizer(second_symbol))

                third_pre_qty = float(second_raw_qty) * float(second_pre_qty)
                third_qty = truncate(float(third_pre_qty), stepSizer(third_symbol))
                third_pass_qty = float(third_raw_qty) * third_pre_qty

                # 

                st_to_nd_final = first_qty 
                nd_from_st_final = second_qty 

                nd_to_rd_final = float(second_raw_qty) * second_qty  
                rd_from_nd_final = third_qty  

                st_to_rd_final = float(first_raw_qty) * first_qty 
                rd_from_st_final = float(third_raw_qty) * third_qty


                if third_mono_symbol == start_symbol: 
                    if (st_to_nd_final <= nd_from_st_final and 
                        nd_to_rd_final <= rd_from_nd_final and 
                        st_to_rd_final <= rd_from_st_final):

                        print("qty 1",first_qty)
                        print("qty 2",second_qty)
                        print("qty 3",third_qty)


        
                    try:
                        order1= await client.create_order(symbol=first_symbol, side=first_side, type=ORDER_TYPE_MARKET, quantity=first_qty)
                        order2= await client.create_order(symbol=second_symbol, side=second_side, type=ORDER_TYPE_MARKET, quantity=second_qty)
                        order3= await client.create_order(symbol=third_symbol, side=third_side, type=ORDER_TYPE_MARKET, quantity=third_qty)

                        print("order1",order1)
                        print("order2",order2)
                        print("order3",order3)
                        print("\n" + str(first_symbol) + ": " + str(first_qty) + " - " + 
                              str(second_symbol) + ": " + str(second_qty) + " - " + 
                              str(third_symbol) + ": " + str(third_qty))
                        
                        print("ORDERS DONE" + "\n")

                    except Exception as e:
                        flash(e.message, "error")
                        print(f"\nError executing orders for {first_symbol}, {second_symbol}, {third_symbol}: {e.message}\n")

        
        except Exception as e:
            print(f"General Error executing trade for {arbitrage['tpath']}: {e}")



async def main():
    global client
    API_KEY = '4SA6iXTp6m5HlpjczckAlVk5uLfcVyGwQe8MNUCr5O7m1l8rjvgGOzza27efpDeB'
    API_SECRET = '5CQ5ycPLBQ7Ryk5hyTfQBoGCNYSlKNZI6zVyGMRf13QzAMj4VnlTuJE7mPkgKvx0'


    client = await AsyncClient.create(API_KEY, API_SECRET, testnet=True)

    await get_pairs()
    await update_prices()

    await client.close_connection()

if __name__ == '__main__':
    asyncio.run(main())
