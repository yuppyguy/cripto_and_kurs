import requests
import pandas as pd
import os
import time
from datetime import datetime
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv
import sqlite3
import logging
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

coin_key = os.getenv("API_KEY_COIN")
fst_forex_key = os.getenv("API_KEY_FAST_FOREX")

def init_db():
    conn = sqlite3.connect("coindatabase.db")
    cursor = conn.cursor()
    # Таблица для текущих цен 
    cursor.execute('''CREATE TABLE IF NOT EXISTS current_prices 
                    (asset TEXT PRIMARY KEY, price REAL, timestamp TEXT)''')
    # Таблица для истории (
    cursor.execute('''CREATE TABLE IF NOT EXISTS historical_data 
                    (date TEXT, open REAL, high REAL, low REAL, close REAL, ticker TEXT)''')
    conn.commit()
    conn.close()
class Coin:
    def __init__(self):
        self.cg = CoinGeckoAPI()

    def get_data_coin(self):
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {  
                'ids': 'bitcoin,ethereum,solana,tether,ripple',
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
            logging.error(f'Smthng wrong: {e}')
        return None
    
    def get_history(self, coin_id, days=7):
        try:
            ohlc = self.cg.get_coin_ohlc_by_id(id=coin_id, vs_currency='usd', days=days)
            df = pd.DataFrame(ohlc, columns=['date', 'open', 'high', 'low', 'close'])
            df['date'] = pd.to_datetime(df['date'], unit='ms').dt.strftime('%Y-%m-%d %H:%M')
            df['ticker'] = coin_id.upper()
            return df
        except Exception as e:
            logging.error(f"Ошибка истории {coin_id}: {e}")
            return pd.DataFrame()
    

class Currency:
    def get_data_currency(self):
        url = 'https://api.fastforex.io/fetch-multi'
        params = {
            'from': 'USD', 
            'to': 'BYN,EUR,RUB,PLN', 
            'api_key': fst_forex_key 
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data['results']
                # Сохраняем все, что получили из API
                res_dict = {}
                for curr, rate in results.items():
                    # Приводим к твоему формату 'CURR to BYN'
                    res_dict[f'{curr} to BYN'] = rate
                return res_dict
        except Exception as e:
            logging.error(f'Smthng wrong: {e}')
        return None



def run_daily_update():
    init_db()
    conn = sqlite3.connect("coindatabase.db")
    
    crypto = Coin()
    currency = Currency()
    
    # 1. Обновляем текущие цены
    current_data = {}
    
    coin_prices = crypto.get_data_coin()
    if coin_prices:
        current_data.update(coin_prices)
    
    currency_prices = currency.get_data_currency()
    if currency_prices:
        current_data.update(currency_prices)
    
    with sqlite3.connect('coindatabase.db') as conn:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for asset, price in current_data.items():
            conn.execute("INSERT OR REPLACE INTO current_prices VALUES (?, ?, ?)", 
                        (asset, price, now_str))
        
    # 2. Обновляем историю (для кнопок аналитики)
        for coin in ['bitcoin', 'ethereum']:
            df_hist = crypto.get_history(coin)
            if not df_hist.empty:
                df_hist.to_sql("historical_data", conn, if_exists="replace", index=False)
                logging.info(f'История для {coin} сохранена')
                time.sleep(2)


    logging.info("Обновление завершено успешно!")


if __name__ == "__main__":
    run_daily_update()