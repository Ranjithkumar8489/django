from django.urls import path
from . import views

urlpatterns = [
    path('arbitrage/', views.arbitrage_view, name='arbitrage'),
    # Add other URL patterns as needed
]
