from django.core.cache import cache
import requests
from django.shortcuts import render
from pycoingecko import CoinGeckoAPI
import plotly.graph_objs as go
import plotly.express as px
import httpx
import asyncio

def crypto_list(request):
    """
    Fetches crypto data from cache if available, otherwise fetches from API and stores in cache.
    Renders the 'crypto_list' template with the fetched crypto data.
    """
    crypto_data = cache.get('crypto_data')

    if crypto_data is None:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=pln&order=market_cap_desc&per_page=30&page=1&sparkline=false"
        response = requests.get(url)
        crypto_data = response.json()
        cache.set('crypto_data', crypto_data, 300)  # Cache data for 5 minutes

    context = {'crypto_list': crypto_data}
    return render(request, 'crypto_app/crypto_list.html', context)

def get_crypto_list():
    """
    Returns a list of crypto data, fetching from cache if available, otherwise fetches from API and stores in cache.
    Each crypto datum is a tuple of (id, symbol, name).
    """
    crypto_data = cache.get('crypto_data')

    if crypto_data is None:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=pln&order=market_cap_desc&per_page=20&page=1&sparkline=false"
        response = requests.get(url)
        if response.status_code == 200:
            crypto_data = response.json()
            cache.set('crypto_data', crypto_data, 300)  # Cache data for 5 minutes
        else:
            return []

    return [(crypto['id'], crypto['symbol'].lower(), crypto['name']) for crypto in crypto_data]


def crypto_convert(request):
    """
    Handles the conversion of a given amount of a selected cryptocurrency to another currency.
    Fetches the list of available cryptocurrencies and conversion rates from an API.
    On POST request, validates form data and performs conversion.
    Renders the 'crypto_convert' template with conversion results or error messages.
    """
    crypto_list = get_crypto_list()

    if not crypto_list:
        return render(request, 'crypto_app/crypto_convert.html', {'error_message': 'Nie można pobrać listy kryptowalut. Spróbuj ponownie później.'})

    if request.method == 'POST':
        amount = float(request.POST['amount'])
        from_currency_id = request.POST['from_currency']
        from_currency_symbol = None

        for item in crypto_list:
            if item[0] == from_currency_id:
                from_currency_symbol = item[1]
                break

        if from_currency_symbol is None:
            return render(request, 'crypto_app/crypto_convert.html', {'error_message': 'Nie można znaleźć wybranej kryptowaluty. Spróbuj ponownie.', 'crypto_list': crypto_list})

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={from_currency_id}&vs_currencies=pln"
        response = requests.get(url)

        if response.status_code == 200:
            try:
                conversion_rate = response.json()[from_currency_id]['pln']
                converted_amount = amount * conversion_rate

                context = {
                    'converted_amount': converted_amount,
                    'from_currency': from_currency_symbol,
                    'amount': amount,
                    'crypto_list': crypto_list,
                }
                return render(request, 'crypto_app/crypto_convert.html', context)
            except KeyError:
                error_message = f"Nie można przeliczyć waluty '{from_currency_symbol}'. Upewnij się, że podałeś prawidłowy symbol kryptowaluty."
        else:
            error_message = "Wystąpił błąd podczas łączenia się z API CoinGecko. Spróbuj ponownie później."

        return render(request, 'crypto_app/crypto_convert.html', {'error_message': error_message, 'crypto_list': crypto_list})

    return render(request, 'crypto_app/crypto_convert.html', {'crypto_list': crypto_list})

cg = CoinGeckoAPI()

async def async_get_coins_list():
    """
    Asynchronously fetches a list of coins from cache if available, otherwise fetches from API and stores in cache.
    """
    coins = cache.get('coins_list')
    if not coins:
        async with httpx.AsyncClient() as client:
            response = await client.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=pln&order=market_cap_desc&per_page=30&page=1&sparkline=false')
        coins_list = response.json()
        coins = []
        for coin in coins_list:
            coins.append({'id': coin['id'], 'name': coin['name']})
        cache.set('coins_list', coins, 3600)  # Przechowywanie wyników w cache na 1 godzinę
    return coins

async def async_get_coin_data(selected_coin, days):
    """
    Asynchronously fetches coin data for a selected coin and number of days from cache if available,
    otherwise fetches from API and stores in cache.
    """
    cache_key = f'coin_data_{selected_coin}_{days}'
    coin_data = cache.get(cache_key)
    if not coin_data:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'https://api.coingecko.com/api/v3/coins/{selected_coin}/market_chart?vs_currency=usd&days={days}&interval=daily')
        coin_data = response.json()
        cache.set(cache_key, coin_data, 1800)  # Przechowywanie wyników w cache na 30 minut
    return coin_data

def crypto_chart(request):
    """
    Fetches coin data and renders a chart of coin price over time.
    Coin data is fetched asynchronously from cache if available, otherwise fetched from API and stored in cache.
    Renders the 'crypto_chart' template with the chart and related data.
    """
    selected_coin = request.GET.get('coin', 'bitcoin')  # Domyślnie 'bitcoin'
    selected_days = request.GET.get('days', '30')  # Domyślnie '30'

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    coins = loop.run_until_complete(async_get_coins_list())
    coin_data = loop.run_until_complete(async_get_coin_data(selected_coin, selected_days))

    loop.close()

    prices = coin_data['prices']
    price_x = [price[0] for price in prices]
    price_y = [price[1] for price in prices]

    fig = px.line(x=price_x, y=price_y, labels={'x': 'Date', 'y': 'Price in PLN'}, title=f'{selected_coin.upper()} exchange rate over the past {selected_days} days')
    fig.update_xaxes(type='date')

    plot_div = fig.to_html(full_html=False)

    context = {
        'plot_div': plot_div,
        'coins': coins,
        'selected_coin': selected_coin,
        'selected_days': selected_days,
    }
    
    return render(request, 'crypto_app/crypto_chart.html', context)