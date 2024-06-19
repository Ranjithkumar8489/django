from django import forms

class ArbitrageBotForm(forms.Form):
    symbol = forms.CharField(label='Symbol', max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    exchange_list = forms.CharField(label='Exchange List', widget=forms.TextInput(attrs={'class': 'form-control'}))
    balance = forms.FloatField(label='Balance', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    stop_loss_percentage = forms.FloatField(label='Stop Loss Percentage', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    target_profit_percentage = forms.FloatField(label='Target Profit Percentage', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    risk_per_trade_percentage = forms.FloatField(label='Risk Per Trade Percentage', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    price_difference_threshold = forms.FloatField(label='Price Difference Threshold', widget=forms.NumberInput(attrs={'class': 'form-control'}))
