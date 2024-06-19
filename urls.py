from django.urls import path
from . import views

urlpatterns = [
    path('arbitrage/', views.arbitrage_bot_view, name='arbitrage_bot'),
    path('stop-bot/', views.stop_bot_view, name='stop_bot'),
]
