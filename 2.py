import telebot
import requests
import datetime
import pytz
import threading

# Configuration
BOT_TOKEN = "7747847120:AAGYuaPr_9lzNa1dUw10SraTVp0OzF8k7Kg"
API_KEY = "m4@1234"
API_URL = "https://likes.api.freefireofficial.com/api/{region}/{uid}?key=" + API_KEY

SUPPORTED_REGIONS = {
    "ind", "sg", "eu", "me", "id", "bd", "ru", "vn",
    "tw", "th", "pk", "br", "sac", "us", "cis", "na"
}

OWNER_IDS = {7029114703, 7297041846}  # 👑
VIP_IDS = {1234567890, 9876543210}     # ⭐

# Usage limit
DAILY_LIMITS = {
    "owner": 3000,
    "vip": 50,
    "user": 1
}

timezone = pytz.timezone('Asia/Kolkata')
usage_data = {}  # {user_id: {"count": int, "last_reset": datetime}}

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# Background task to reset usage at 4:00 AM IST
def reset_usage_loop():
    while True:
        now = datetime.datetime.now(timezone)
        if now.hour == 4 and now.minute == 0:
            usage_data.clear()
        threading.Event().wait(60)

threading.Thread(target=reset_usage_loop, daemon=True).start()

def get_role(user_id):
    if user_id in OWNER_IDS:
        return "owner"
    elif user_id in VIP_IDS:
        return "vip"
    else:
        return "user"

def is_allowed(user_id):
    role = get_role(user_id)
    limit = DAILY_LIMITS[role]
    now = datetime.datetime.now(timezone)
    if user_id not in usage_data:
        usage_data[user_id] = {"count": 0, "last_reset": now}
    return usage_data[user_id]["count"] < limit

def increment_usage(user_id):
    usage_data[user_id]["count"] += 1

@bot.message_handler(commands=['like'])
def like_handler(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "❌ Format: /like region uid\nExample: /like bd 388235783")
            return

        region, uid = args[1].lower(), args[2]
        if region not in SUPPORTED_REGIONS:
            bot.reply_to(message, f"❌ Unsupported region. Try one of: {', '.join(SUPPORTED_REGIONS)}")
            return

        user_id = message.from_user.id
        if not is_allowed(user_id):
            bot.reply_to(message, "❌ Daily limit reached. Try again after 4:00 AM IST.")
            return

        url = API_URL.format(region=region, uid=uid)
        res = requests.get(url)
        data = res.json()

        if data.get("status") == 1:
            r = data["response"]
            increment_usage(user_id)
            bot.reply_to(message, (
                "✅ <b>Likes Sent</b>\n"
                f"• Name: {r['PlayerNickname']}\n"
                f"• UID: {r['UID']}\n"
                f"• Before: {r['LikesbeforeCommand']}\n"
                f"• Sent: {r['LikesGivenByAPI']}\n"
                f"• After: {r['LikesafterCommand']}\n\n"
                "🔗 <b>Join our Telegram</b>:\nhttps://t.me/freefireproxyserver"
            ))
        else:
            bot.reply_to(message, f"❌ {data.get('message', 'API Error')}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['remain'])
def remain_handler(message):
    user_id = message.from_user.id
    role = get_role(user_id)
    used = usage_data.get(user_id, {}).get("count", 0)
    limit = DAILY_LIMITS[role]

    now = datetime.datetime.now(timezone)
    next_reset = now.replace(hour=4, minute=0, second=0, microsecond=0)
    if now > next_reset:
        next_reset += datetime.timedelta(days=1)
    remaining_time = next_reset - now
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    bot.reply_to(message, (
        "📊 <b>Your Daily Usage</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🔹 Role: {'👑 Owner' if role == 'owner' else '⭐ VIP' if role == 'vip' else '🧑 User'}\n"
        f"🔹 /like: {used}/{limit} used\n"
        "━━━━━━━━━━━━━━━━\n"
        f"⏳ Resets daily at 4:00 AM IST ({hours}h {minutes}m left)"
    ))

@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.reply_to(message, (
        "🤖 <b>Free Fire Like Bot</b>\n\n"
        "Commands:\n"
        "/like region uid - Send likes to Free Fire profile\n"
        "/remain - Check how many times you can still use today\n"
        "/help - Show this help message\n\n"
        "Example: /like bd 388235783"
    ))

bot.polling()
