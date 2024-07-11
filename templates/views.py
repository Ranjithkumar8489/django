from django.http import HttpResponse
from .arbitrage import arbitrage

def arbitrage_view(request):
    symbol = "TRX/USDT"
    amount = 60.00

    result = arbitrage(symbol, amount,exchanges=["binance","kucoin"])
    return HttpResponse(result)
