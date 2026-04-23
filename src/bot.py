import telebot
from telebot import types
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from load_from_api import run_update
from db import get_connection

load_dotenv()

bot = telebot.TeleBot(os.getenv("API_TOKEN_TG_BOT"))

user_currency = {}


def get_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT asset, price FROM current_prices")
    data = cur.fetchall()

    cur.close()
    conn.close()
    return data


# автообновление
scheduler = BackgroundScheduler()
scheduler.add_job(run_update, "interval", hours=6)
scheduler.start()


def format_list(data, mode):
    text = ""

    if mode == "crypto":
        text = "🪙 Топ коинов:\n\n"
        for name, price in data:
            text += f"🔹 {name} — {price:,.2f} $\n"

    if mode == "forex":
        text = "💱 Валюты:\n\n"
        for name, price in data:
            text += f"🔹 {name} — {price:,.4f}\n"

    return text


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("🪙 Коины", "💱 Валюты")
    markup.add("💱 Конвертер", "🔄 Обновить")

    bot.send_message(message.chat.id, "Выбери:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "🪙 Коины")
def coins(message):
    data = [x for x in get_data() if x[0] in ["BTC", "ETH", "SOL", "XRP", "ADA"]]
    bot.send_message(message.chat.id, format_list(data, "crypto"))


@bot.message_handler(func=lambda m: m.text == "💱 Валюты")
def forex(message):
    data = [x for x in get_data() if "to BYN" in x[0]]
    bot.send_message(message.chat.id, format_list(data, "forex"))


@bot.message_handler(func=lambda m: m.text == "🔄 Обновить")
def update(message):
    run_update()
    bot.send_message(message.chat.id, "✅ Обновлено")


# конвертер
@bot.message_handler(func=lambda m: m.text == "💱 Конвертер")
def converter(message):
    markup = types.InlineKeyboardMarkup()

    for c in ["USD", "EUR", "RUB", "PLN", "BYN"]:
        markup.add(types.InlineKeyboardButton(c, callback_data=f"cur_{c}"))

    bot.send_message(message.chat.id, "Выбери валюту:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cur_"))
def select_currency(call):
    curr = call.data.split("_")[1]
    user_currency[call.message.chat.id] = curr

    bot.send_message(call.message.chat.id, f"{curr} выбрано. Введи сумму:")
    bot.register_next_step_handler(call.message, convert)


def convert(message):
    try:
        amount = float(message.text)
        curr = user_currency.get(message.chat.id)

        data = dict(get_data())

        if curr == "BYN":
            bot.send_message(message.chat.id, f"{amount} BYN")
            return

        rate = data.get(f"{curr} to BYN")

        if rate:
            bot.send_message(message.chat.id, f"{amount} {curr} = {amount * rate:,.2f} BYN")
        else:
            bot.send_message(message.chat.id, "Нет курса")

    except:
        bot.send_message(message.chat.id, "Введите число")


bot.polling()