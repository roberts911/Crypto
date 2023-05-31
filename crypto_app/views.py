from django.core.cache import cache
from django.shortcuts import render
from pycoingecko import CoinGeckoAPI
import plotly.express as px
import httpx
import asyncio
import requests

BASE_API_URL = "https://api.coingecko.com/api/v3"

def fetch_from_cache_or_api(cache_key, url, cache_time=300):
    """
    Fetches data from cache if available, otherwise fetches from API and stores in cache.
    """
    data = cache.get(cache_key)

    if data is None:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            cache.set(cache_key, data, cache_time)

    return data

def crypto_list(request):
    """
    Renders the 'crypto_list' template with the fetched crypto data.
    """
    url = f"{BASE_API_URL}/coins/markets?vs_currency=pln&order=market_cap_desc&per_page=30&page=1&sparkline=false"
    crypto_data = fetch_from_cache_or_api('crypto_data', url)

    return render(request, 'crypto_app/crypto_list.html', {'crypto_list': crypto_data})

def get_crypto_list():
    """
    Returns a list of crypto data, fetching from cache if available, otherwise fetches from API and stores in cache.
    """
    url = f"{BASE_API_URL}/coins/markets?vs_currency=pln&order=market_cap_desc&per_page=20&page=1&sparkline=false"
    crypto_data = fetch_from_cache_or_api('crypto_data', url)

    return [(crypto['id'], crypto['symbol'].lower(), crypto['name']) for crypto in crypto_data if crypto] if crypto_data else []

def get_conversion_rate(from_currency_id):
    """
    Fetches conversion rate for a given cryptocurrency.
    """
    url = f"{BASE_API_URL}/simple/price?ids={from_currency_id}&vs_currencies=pln"
    response = requests.get(url)
    return response.json().get(from_currency_id, {}).get('pln') if response.status_code == 200 else None


    
def crypto_convert(request):
    """
    Handles the conversion of a given amount of a selected cryptocurrency to another currency.
    Renders the 'crypto_convert' template with conversion results or error messages.
    """
    crypto_list = get_crypto_list()
    
    if request.method == 'POST':
        amount = float(request.POST['amount'])
        from_currency_id = request.POST['from_currency']
        from_currency_symbol = next((item[1] for item in crypto_list if item[0] == from_currency_id), None)

        if not from_currency_symbol:
            return render(request, 'crypto_app/crypto_convert.html', {
                'error_message': 'Unable to find the selected cryptocurrency. Please try again.',
                'crypto_list': crypto_list
            })

        conversion_rate = get_conversion_rate(from_currency_id)
        if conversion_rate:
            return render(request, 'crypto_app/crypto_convert.html', {
                'converted_amount': amount * conversion_rate,
                'from_currency': from_currency_symbol,
                'amount': amount,
                'crypto_list': crypto_list
            })
        else:
            return render(request, 'crypto_app/crypto_convert.html', {
                'error_message': "An error occurred while connecting to the CoinGecko API. Please try again later.",
                'crypto_list': crypto_list
            })

    return render(request, 'crypto_app/crypto_convert.html', {'crypto_list': crypto_list})


async def async_get_coins_list():
    """
    Asynchronously fetches a list of coins from cache if available, otherwise fetches from API and stores in cache.
    """
    coins = cache.get('coins_list')
    if not coins:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{BASE_API_URL}/coins/markets?vs_currency=pln&order=market_cap_desc&per_page=30&page=1&sparkline=false')
        coins = [{'id': coin['id'], 'name': coin['name']} for coin in response.json()]
        cache.set('coins_list', coins, 3600)  # Cache data for 1 hour
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
            response = await client.get(f'{BASE_API_URL}/coins/{selected_coin}/market_chart?vs_currency=pln&days={days}&interval=daily')
        coin_data = response.json()
        cache.set(cache_key, coin_data, 1800)  # Cache data for 30 minutes
    return coin_data

def crypto_chart(request):
    """
    Fetches coin data and renders a chart of coin price over time.
    Coin data is fetched asynchronously from cache if available, otherwise fetched from API and stored in cache.
    Renders the 'crypto_chart' template with the chart and related data.
    """
    selected_coin = request.GET.get('coin', 'bitcoin')  # Default 'bitcoin'
    selected_days = request.GET.get('days', '30')  # Default '30'

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    coins = loop.run_until_complete(async_get_coins_list())
    coin_data = loop.run_until_complete(async_get_coin_data(selected_coin, selected_days))

    loop.close()

    prices = coin_data.get('prices', [])
    price_x = [price[0] for price in prices]
    price_y = [price[1] for price in prices]

    fig = px.line(x=price_x, y=price_y, labels={'x': 'Date', 'y': 'Price in PLN'}, title=f'{selected_coin.upper()} exchange rate over the past {selected_days} days')
    fig.update_xaxes(type='date')

    context = {
        'plot_div': fig.to_html(full_html=False),
        'coins': coins,
        'selected_coin': selected_coin,
        'selected_days': selected_days,
    }
    
    return render(request, 'crypto_app/crypto_chart.html', context)
