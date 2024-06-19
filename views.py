from django.shortcuts import render
from django.http import HttpResponse
from .exchange_config import exchange_keys
from .arbitrage import connect_exchanges, start_arbitrage_bot,stop_arbitrage_bot
from .forms import ArbitrageBotForm

def arbitrage_bot_view(request):
    if request.method == 'POST':
        form = ArbitrageBotForm(request.POST)
        if form.is_valid():
            symbol = form.cleaned_data['symbol']
            exchange_list = form.cleaned_data['exchange_list'].split(",")  # Split comma-separated values into a list
            balance = form.cleaned_data['balance']
            stop_loss_percentage = form.cleaned_data['stop_loss_percentage']
            target_profit_percentage = form.cleaned_data['target_profit_percentage']
            risk_per_trade_percentage = form.cleaned_data['risk_per_trade_percentage']
            price_difference_threshold = form.cleaned_data['price_difference_threshold']

            exchanges = connect_exchanges(exchange_list, exchange_keys)

            start_arbitrage_bot(
                symbol,
                balance,
                stop_loss_percentage,
                target_profit_percentage,
                risk_per_trade_percentage,
                price_difference_threshold
            )

            return HttpResponse("Arbitrage bot started.")
    else:
        form = ArbitrageBotForm()

    return render(request, 'arbitrage_bot.html', {'form': form})
def stop_bot_view(request):
    if request.method == 'POST':
        stop_arbitrage_bot()  # Implement the logic to stop the bot
        return HttpResponse("Arbitrage bot stopped.")
    else:
        return HttpResponse(status=405)  # Method Not Allowed

