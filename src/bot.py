from dotenv import load_dotenv
import os
import telebot
from telebot import types
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from load_from_api import run_daily_update

load_dotenv()

tg_token = os.getenv('API_TOKEN_TG_BOT')

bot = telebot.TeleBot(tg_token)
user_selected_currency = {}


def job_update():
    run_daily_update() 
    print("Данные обновлены автоматически!")

scheduler = BackgroundScheduler()
scheduler.add_job(job_update, 'interval', hours=20) 
scheduler.start()

def get_curr():
    with sqlite3.connect('coindatabase.db') as conn:
        cursor = conn.execute('SELECT asset, price FROM current_prices')
        return cursor.fetchall()

def get_analytics():
    with sqlite3.connect('coindatabase.db') as conn:
        
        query = """
        SELECT ticker, AVG(close) as avg_price, MAX(high) as max_price 
        FROM historical_data 
        GROUP BY ticker
        """
        cursor = conn.execute(query)
        return cursor.fetchall()

def format_analytics(data):
    if not data:
        return "❌ Нет исторических данных для анализа."
    
    text = "📊 Аналитика за неделю:\n\n"
    for ticker, avg_p, max_p in data:
        text += f"🔹 {ticker}:\n"
        text += f"   Средняя: {avg_p:,.2f}\n"
        text += f"   Пик: {max_p:,.2f}\n\n"
    return text


def format_currency(data):
    text = "💰 Текущие курсы:\n\n"
    for name, price in data:
        
        text += f"🔹 {name} — {price:,.2f} \n"
    return text

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("💰 Курсы валют")
    btn2 = types.KeyboardButton("🔄 Обновить")
    btn3 = types.KeyboardButton("📊 Аналитика")
    btn4 = types.KeyboardButton("💱 Конвертер")
    
    markup.add(btn1, btn2, btn3, btn4)


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
        bot.send_message(message.chat.id, "⏳ Секунду, обновляю данные из API...")
        try:
            run_daily_update()
            data = get_curr()
            text = format_currency(data)
            bot.send_message(message.chat.id, "🔄 Обновлено:\n\n" + text)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка обновления: {e}")
        
    elif message.text == "📊 Аналитика":
        data = get_analytics()
        text = format_analytics(data)
        bot.send_message(message.chat.id, text)
    
@bot.message_handler(func=lambda message: message.text == "💱 Конвертер")
def convert_start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("USD", callback_data="curr_USD"),
        types.InlineKeyboardButton("EUR", callback_data="curr_EUR"),
        types.InlineKeyboardButton("RUB", callback_data="curr_RUB"),
        types.InlineKeyboardButton("PLN", callback_data="curr_PLN"),
        types.InlineKeyboardButton("BYN", callback_data="curr_BYN")
    )
    bot.send_message(message.chat.id, "Выберите валюту для конвертации:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("curr_"))
def callback_currency(call):
    currency = call.data.split("_")[1]
    user_selected_currency[call.message.chat.id] = currency
    
    bot.edit_message_text(
        chat_id=call.message.chat.id, 
        message_id=call.message.message.id, 
        text=f"✅ Выбрано: {currency}. Теперь введите сумму (например, 100):"
    )
    
    bot.register_next_step_handler(call.message, process_amount)

def process_amount(message):
    try:
        amount = float(message.text)
        chat_id = message.chat.id
        currency = user_selected_currency.get(chat_id)
        
        if not currency:
            bot.send_message(chat_id, "Ошибка, начните сначала нажав кнопку '💱 Конвертер'.")
            return

        if currency == "BYN":
            bot.send_message(chat_id, f"📈 {amount:,.2f} BYN = {amount:,.2f} BYN")
            return

        # Получаем данные из базы
        data = dict(get_curr()) # Превращаем список кортежей в словарь {'USD to BYN': 3.2}
        key = f"{currency} to BYN"
        
        if key in data:
            result = amount * data[key]
            bot.send_message(chat_id, f"📈 {amount:,.2f} {currency} = {result:,.2f} BYN")
        else:
            bot.send_message(chat_id, f"❌ Курс для {currency} сейчас недоступен в базе.")
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число.")
        
bot.polling()


