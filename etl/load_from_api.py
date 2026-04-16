import requests
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

coin_key = os.getenv("API_KEY_COIN")
fst_forex_key = os.getenv("API_KEY_FAST_FOREX")


class Coin:
    def get_data(self):
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {  
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'USD'
        }
        headers = { 'x-cg-demo-api-key': coin_key }

        try:
            response = requests.get(url, params = params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    'BTC' : data['bitcoin']['usd'],
                    'ETH' : data['ethereum']['usd']
                }
        except Exception as e:
            print(f'Smthng wrong: {e}')
        return None

class Currency:
    def get_data(self):
        url = 'https://api.fastforex.io/fetch-multi'
        params = {
            'from': 'USD',         
            'to': 'BYN,EUR',       
            'api_key': fst_forex_key 
        }

        try:
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                usd_to_byn = data['results']['BYN']
                eur_rate = data['results']['EUR']
                return {
                    'USD to BYN' : usd_to_byn,
                    'EUR to BYN' : round(usd_to_byn / eur_rate,2)
                }
        except Exception as e:
            print(f'Smthng wrong: {e}')
        return None

# from pycoingecko import CoinGeckoAPI
# cg = CoinGeckoAPI()
# ohlc = cg.get_coin_ohlc_by_id(id = 'ethereum', vs_currency = 'usd', days = '30')

# df = pd.DataFrame(ohlc)
# df.columns = ['date', 'open','high','low','close']

# df['date'] = pd.to_datetime(df['date'], unit='ms' )
# df.set_index('date',inplace= True)


# parameters = {
#         'id': ['bitcoin', 'ethereum'],
#         'vs_currency': 'usd',
#         'order': 'market_cap_desc',
#         'per_page': 100,
#         'page': 1,
#         'sparkline': False,
#         'locale': 'en'
#         }
# coin_market_data = cg.get_coins_markets(**parameters)

# eth_and_bts = cg.get_coins_categories(**parameters)
# df1 = pd.DataFrame(coin_market_data)
# df1 = df1.drop(['id', 'symbol', 'image', 'high_24h', 'low_24h', 'price_change_24h', 'price_change_percentage_24h',
# 'market_cap_change_24h','market_cap_change_percentage_24h', 'fully_diluted_valuation', 'ath_date', 'ath_change_percentage',
# 'atl_change_percentage', 'atl_date', 'roi'],  axis = 1)
# df1.to_csv('crypto_coins_market.csv')