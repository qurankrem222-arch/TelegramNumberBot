import telebot
import random
import string
import io
import sqlite3
import requests
from PIL import Image, ImageDraw
from telebot import types

# --- الإعدادات ---
TOKEN = 'YOUR_BOT_TOKEN'  # استبدل بـ توكن البوت الخاص بك
ADMIN_ID = 61824874
OWNER_ID = ADMIN_ID  # استخدام نفس معرف المالك
SUPPORT_USER = "@SocialSMSSUPPORT"
CHANNELS = ['@directionssms', '@Activations223', '@telesms223']
DELIVERY_CHANNEL_ID = -1004394543430
API_KEY = 'z4Hj3efMdalD1C0ywx'  # مفتاح API الخاص بك
YOUR_ID = 'Your_ID'  # استبدل بـ Your_ID الخاص بك

bot = telebot.TeleBot(TOKEN)
user_captchas = {}

# --- معلومات الدفع ---
payment_info = {
    "USDT/BEB20": "0x3dcF20c18f03F0016BeB5dE3A2979cF65e5DE596",
    "USDT/TRX20": "TRmkCedsJP9MongBrvy4gwdfBX5v8g65sgq6h0s79ucfyl6ld",
    "USDT/ERC20": "0x5623f438C721D284e9257d2815a82a267b7F4d51",
    "USDT/POL": "0x5D14363342328D49C9094b61822608aB285Db59",
    "LTC/LITECOIN": "ltc1qk7gs0gt4zt0e0ztsv8g65sgq6h0s79ucfyl6ld",
    "BNB/BEB20": "0x3dcF20c18f03F0016BeB5dE3A2979cF65e5DE596",
    "USDC/SOL": "Dw27gnVFsjQRTG3HpsVwawBPfzx1RPpRDsJtdKGNop2p",
    "FAUCET PAY": "primexstore22"
}

# --- قاعدة البيانات ---
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, is_banned INTEGER DEFAULT 0, referrer INTEGER, balance REAL DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, status TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS numbers (number TEXT PRIMARY KEY, status TEXT)')  # جدول الأرقام
conn.commit()

# --- دالة لإنشاء كابتشا ---
def generate_captcha():
    code = ''.join(random.choices(string.digits, k=4))
    img = Image.new('RGB', (150, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 20), code, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf, code

# --- دالة للتحقق من الاشتراك ---
def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            if bot.get_chat_member(channel, user_id).status in ['left', 'kicked']: 
                return False
        except: 
            return False
    return True

# --- دالة للتحقق إذا كان المستخدم محظور ---
def is_user_banned(user_id):
    res = cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    return res and res[0] == 1

# --- دالة لاستدعاء API للحصول على رقم ---
def get_number(country_code):
    url = f"https://TG-Lion.net?action=getNumber&apiKey={API_KEY}&YourID={YOUR_ID}&country_code={country_code}"
    response = requests.get(url)
    return response.json()

# --- دالة لاستدعاء API للحصول على كود ---
def get_code(number):
    url = f"https://TG-Lion.net?action=getCode&number={number}&apiKey={API_KEY}&YourID={YOUR_ID}"
    response = requests.get(url)
    return response.json()

# --- دالة لاستدعاء API للحصول على الرصيد ---
def get_balance(user_id):
    url = f"https://TG-Lion.net?action=get_balance&apiKey={API_KEY}&YourID={YOUR_ID}"
    response = requests.get(url)
    return response.json()

# --- دالة لاستدعاء API للحصول على الدول المتاحة ---
def available_countries():
    url = f"https://TG-Lion.net?action=available_countries&apiKey={API_KEY}&YourID={YOUR_ID}"
    response = requests.get(url)
    return response.json()

# --- دالة لاستدعاء API للحصول على معلومات الدولة ---
def country_info(country_code):
    url = f"https://TG-Lion.net?action=country_info&apiKey={API_KEY}&YourID={YOUR_ID}&country_code={country_code}"
    response = requests.get(url)
    return response.json()

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    args = message.text.split()
    
    # التحقق إذا كان مستخدم جديد
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        referrer = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        cursor.execute('INSERT INTO users (user_id, referrer) VALUES (?, ?)', (user_id, referrer))
        conn.commit()
        
        # إشعار الأدمن
        bot.send_message(ADMIN_ID, f"🆕 مستخدم جديد دخل البوت: {user_id}")
        
        # إضافة مكافأة للداعي
        if referrer:
            cursor.execute('UPDATE users SET balance = balance + 0.003 WHERE user_id = ?', (referrer,))
            conn.commit()
            bot.send_message(referrer, "🎉 مبروك! حصلت على 0.003 بسبب دعوة مستخدم جديد.")

    # زر الدعوة
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 رابط دعوتك", url=invite_link))
    
    bot.send_message(user_id, f"مرحباً بك! لطلب رقم: /new_order\nرصيدك الحالي: {cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,)).fetchone()[0]}", reply_markup=markup)

@bot.message_handler(commands=['new_order'])
def new_order(message):
    if is_user_banned(message.from_user.id): 
        return bot.send_message(message.chat.id, "❌ محظور.")
    if not check_subscription(message.from_user.id): 
        return bot.send_message(message.chat.id, "⚠️ اشترك في القنوات أولاً.")
    
    country_code = 'uz'  # يمكنك تغيير ذلك حسب الحاجة
    result = get_number(country_code)
    if result.get("status") == "success":
        number = result.get("number")
        cursor.execute('INSERT OR IGNORE INTO numbers (number, status) VALUES (?, ?)', (number, 'available'))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ تم الحصول على الرقم: {number}")
    else:
        bot.send_message(message.chat.id, "❌ فشل في الحصول على الرقم.")

@bot.message_handler(commands=['payment_info'])
def payment_info_command(message):
    msg = "🪙 معلومات الدفع:\n"
    for currency, address in payment_info.items():
        msg += f"{currency}: {address}\n"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['get_balance'])
def balance_command(message):
    result = get_balance(message.from_user.id)
    if result.get("status") == "success":
        balance = result.get("balance")
        bot.send_message(message.chat.id, f"💰 رصيدك: {balance}")
    else:
        bot.send_message(message.chat.id, "❌ فشل في الحصول على الرصيد.")

@bot.message_handler(commands=['available_countries'])
def available_countries_command(message):
    result = available_countries()
    if result.get("status") == "success":
        countries = result.get("countries")
        msg = "الدول المتاحة:\n" + "\n".join(countries)
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "❌ فشل في الحصول على قائمة الدول.")

@bot.message_handler(commands=['country_info'])
def country_info_command(message):
    try:
        country_code = message.text.split()[1]  # يتوقع أن يرسل المستخدم الأمر كالتالي: /country_info country_code
        result = country_info(country_code)
        if result.get("status") == "success":
            info = result.get("info")
            bot.send_message(message.chat.id, f"معلومات الدولة {country_code}:\n{info}")
        else:
            bot.send_message(message.chat.id, "❌ فشل في الحصول على معلومات الدولة.")
    except IndexError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال كود الدولة بعد الأمر.")

# --- بدء البوت ---
bot.polling()
