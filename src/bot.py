from dotenv import load_dotenv
import os
import telebot
from telebot import types
import sqlite3

load_dotenv()

tg_token = os.getenv('API_TOKEN_TG_BOT')

bot = telebot.TeleBot(tg_token)


def get_curr():
    with sqlite3.connect('coindatabase.db') as conn:
        cursor = conn.execute('SELECT asset, price FROM current_prices')
        return cursor.fetchall()


def format_currency(data):
    if not data:
        return "❌ Нет данных"

    text = "💰 Текущие курсы:\n\n"

    symbols = {
        "BTC": "₿",
        "ETH": "Ξ",
        "USD to BYN": "$",
        "EUR to BYN": "€"
    }

    for name, price in data:
        symbol = symbols.get(name, "")
        text += f"{symbol} {name} — {price:,} \n"

    return text

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("💰 Курсы валют")
    btn2 = types.KeyboardButton("🔄 Обновить")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Привет, ПУПСИКОВИЧ👋 Выбери действие:",
        reply_markup=markup
    )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "💰 Курсы валют":
        data = get_curr()
        text = format_currency(data)
        bot.send_message(message.chat.id, text)

    elif message.text == "🔄 Обновить":
        data = get_curr()
        text = format_currency(data)
        bot.send_message(message.chat.id, "🔄 Обновлено:\n\n" + text)
        
bot.polling()


