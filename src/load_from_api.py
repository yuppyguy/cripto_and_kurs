import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from db import get_connection

load_dotenv()

logging.basicConfig(level=logging.INFO)

fst_forex_key = os.getenv("API_KEY_FAST_FOREX")


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS current_prices (
            asset TEXT PRIMARY KEY,
            price FLOAT,
            updated_at TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def get_crypto():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,solana,ripple,cardano",
        "vs_currencies": "usd"
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()

        return {
            "BTC": data["bitcoin"]["usd"],
            "ETH": data["ethereum"]["usd"],
            "SOL": data["solana"]["usd"],
            "XRP": data["ripple"]["usd"],
            "ADA": data["cardano"]["usd"]
        }
    except:
        return {}


def get_forex():
    url = "https://api.fastforex.io/fetch-multi"
    params = {
        "from": "USD",
        "to": "BYN,EUR,RUB,PLN",
        "api_key": fst_forex_key
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()["results"]

        usd_byn = data["BYN"]

        return {
            "USD to BYN": usd_byn,
            "EUR to BYN": usd_byn / data["EUR"],
            "RUB to BYN": usd_byn / data["RUB"],
            "PLN to BYN": usd_byn / data["PLN"]
        }
    except:
        return {}


def run_update():
    init_db()

    data = {}
    data.update(get_crypto())
    data.update(get_forex())

    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now()

    for asset, price in data.items():
        cur.execute("""
            INSERT INTO current_prices (asset, price, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (asset)
            DO UPDATE SET price = EXCLUDED.price,
                          updated_at = EXCLUDED.updated_at
        """, (asset, price, now))

    conn.commit()
    cur.close()
    conn.close()

    logging.info("Updated")