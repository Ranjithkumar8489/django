# botapp/views.py

from django.shortcuts import render
from .arbitrage import start_bot, stop_bot, is_running

def bot(request):
    status = "Bot is not running" if not is_running() else "Bot is running"

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'start':
            if not is_running():
                start_bot()
                status = "Bot started"
            else:
                status = "Bot is already running"
        elif action == 'stop':
            if is_running():
                stop_bot()
                status = "Bot stopped"
            else:
                status = "Bot is not running"
    
    return render(request, 'bot.html', {'status': status})
