import ccxt

# Define exchange configurations
exchanges = {
    'binance': {
        'apiKey': 'QgmjbPAlNgG0LPBxLdxg575QxEGUp6hli0FEPDYxAeUUUp2hKVpyyfKnMxHhO5cs',
        'secret': 'ok1wRuiL4200vBadVaFyi1f6A0R0MMoMdetNmdQ9jO2XTk3T8ogj8ATHvxgeiWZp',
        'enableRateLimit': True,
        # 'verbose':True,
        'options': {
            'sandbox': True  # Enable sandbox mode
        }
    },
    #     'kucoin': {
    #     'apiKey': '668eba2a1d7c5a0001bcbbee',
    #     'secret': '500943ca-fffb-4735-8325-58f0a7b09d19',
    #     'enableRateLimit': True
    # },
    # Add more exchanges as needed
}

# Create exchange objects
exchange_objects = {name: getattr(ccxt, name)(config) for name, config in exchanges.items()}
