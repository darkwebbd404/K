import json
import os
import requests
import signal
import sys
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIG ===

BOT_TOKEN = '8457409015:AAEhftH_WZqjHJOicWbOExW9WFRtZVJchZY'
API_KEY = '9274df6e182ad1b9c8d3a946eb8d876adc96dd2e'
BASE_URL = 'http://http://t.me/mrkalphalikebot?start=verified-'
GROUP_CHAT_IDS = [-1002523214973, -1002523214973, -1002523214973,-1002523214973]
LIKE_API_URL = 'https://likexthug.vercel.app'
VERIFIED_FILE = 'verified_users.json'
SHORT_LINK_FILE = 'verified_links.json'
USAGE_FILE = 'daily_usage.json'
VIP_FILE = 'vip_users.json'
ADMIN_IDS = [6632157651]

# === Helper Functions ===

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def load_vip_users(): return load_json(VIP_FILE)
def save_vip_users(data): save_json(VIP_FILE, data)

def get_vip_user(user_id):
    for u in load_vip_users():
        if u["id"] == user_id:
            return u
    return None

def is_vip(user_id):
    u = get_vip_user(user_id)
    return u and datetime.strptime(u["expiry"], "%Y-%m-%d") >= datetime.now()

def add_vip(user_id, day_limit, expiry_date, admin_added=False):
    users = load_vip_users()
    for u in users:
        if u["id"] == user_id:
            u.update({"limit": int(day_limit), "expiry": expiry_date, "admin_added": admin_added})
            break
    else:
        users.append({"id": user_id, "limit": int(day_limit), "expiry": expiry_date, "admin_added": admin_added})
    save_vip_users(users)

def remove_vip(user_id):
    users = [u for u in load_vip_users() if u["id"] != user_id]
    save_vip_users(users)

def decrement_vip_limit(user_id):
    users = load_vip_users()
    for u in users:
        if u["id"] == user_id:
            u["limit"] = max(0, u["limit"] - 1)
            break
    save_vip_users(users)

def load_verified_users(): return load_json(VERIFIED_FILE)
def save_verified_user(user_id):
    users = load_verified_users()
    now = datetime.now().isoformat()
    for u in users:
        if u["id"] == user_id:
            u["timestamp"] = now
            break
    else:
        users.append({"id": user_id, "timestamp": now})
    save_json(VERIFIED_FILE, users)

def is_user_verified_recently(user_id):
    for u in load_verified_users():
        if u["id"] == user_id:
            return datetime.now() - datetime.fromisoformat(u["timestamp"]) < timedelta(hours=12)
    return False

def load_short_links(): return load_json(SHORT_LINK_FILE)
def save_short_link(user_id):
    data = load_short_links()
    now = datetime.now().isoformat()
    for entry in data:
        if entry["id"] == user_id:
            entry["timestamp"] = now
            break
    else:
        data.append({"id": user_id, "timestamp": now})
    save_json(SHORT_LINK_FILE, data)

def is_short_link_expired(user_id):
    for entry in load_short_links():
        if entry["id"] == user_id:
            return datetime.now() - datetime.fromisoformat(entry["timestamp"]) > timedelta(minutes=10)
    return True

def load_daily_usage(): return load_json(USAGE_FILE)
def save_daily_usage(user_id):
    usage = load_daily_usage()
    today = datetime.now().strftime("%Y-%m-%d")
    for u in usage:
        if u["id"] == user_id:
            u["date"] = today
            break
    else:
        usage.append({"id": user_id, "date": today})
    save_json(USAGE_FILE, usage)

def has_used_today(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    return any(u["id"] == user_id and u["date"] == today for u in load_daily_usage())

async def call_like_api(region, uid):
    try:
        url = f"{LIKE_API_URL}/{uid}/{region}/GREAT"
        return requests.get(url).json()
    except Exception as e:
        return {"error": str(e)}

# === /like Command ===

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user.first_name or "there"
    loading_msg = await update.message.reply_text("⏳ Checking verification...")

    if len(context.args) < 2:
        await loading_msg.edit_text("❌ Use:\n`/like ind 8431487083`", parse_mode='Markdown')
        return

    region, uid = context.args[0].lower(), context.args[1]
    vip_user = get_vip_user(user_id)
    is_user_vip = is_vip(user_id)

    if not is_user_vip and not is_user_verified_recently(user_id):
        if not is_short_link_expired(user_id):
            await loading_msg.edit_text("⚠️ Use your previous verification link. Wait 10 mins.", parse_mode='Markdown')
            return

        user_param = "-".join(context.args)
        try:
            dest_url = f"{BASE_URL}{user_param}"
            short = requests.get(f"https://zegalinks.com/api?api={APo_KEY}&url={dest_url}").json()
            if short.get("status") != "success":
                raise Exception(short.get("message", "Unknown"))
            short_link = short["shortenedUrl"]
            save_short_link(user_id)
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ Link failed:\n`{e}`", parse_mode='Markdown')
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verify & Send Likes", url=short_link)],
            [InlineKeyboardButton("❓ How to Verify?", url="https://t.me/freelike99/2.com")]
        ])
        await loading_msg.edit_text(
            f"*Like Request*\n\n👤 `{user}`\n🆔 `{uid}`\n🌍 `{regioni.upper()}`\n\n🔗 {short_link}\n⚠️ Expires in 10 mins",
            reply_markup=keyboard, parse_mode='Markdown'
        )
        return

    if not is_user_vip and has_used_today(user_id):
        await loading_msg.edit_text("🚫 You already used free like today.\nTry after 4 AM IST.")
        return

    if is_user_vip and vip_user["limit"] <= 0:
        await loading_msg.edit_text("🚫 VIP like limit over for today.")
        return

    res = await call_like_api(region, uid)
    if "error" in res:
        await loading_msg.edit_text(f"⚠️ API error:\n`{res[uerror']}`", parse_mode='Markdown')
        return

    if is_user_vip:
        decrement_vip_limit(user_id)
    else:
        save_daily_usage(user_id)

    if res.get("status") == 1:
        msg = (
            f"✅ LIKE SUCCESSFULLY SEND\n\n"
            f"✨ NAME: `{res.get('PlayerNickname', 'N/A')}`\n"
            f"✨ UID: `{uid}`\n"
            f"✨ Like Before Command: `{res.get('LikesbeforeCommand', 0)}`\n"
            f"✨ Like After Command: `{res.get('LikesafterCommand', 0)}`\n"
            f"✨ Like Given By Bot: `{res.get('LikesGivenByAPI', 0)}`\n"
            f"📅 Valid Till: `{res.get('expire_date')}`"
        )
    elif res.get("status") == 2:
        msg = (
            f"🚫 *Limit Reached!*\n\n👤 `{res.get('PlayerNickname', 'N/A')}`\n🆔 `{uid}`\n"
            f"❤️ Likes Now: `{res.get('LikesNow', 0)}`\n📆 Try After 4 AM IST\n📅 `{res.get('expire_date')}`"
        )
    else:
        msg = f"⚠️ Unexpected:\n`{res}`"

    await loading_msg.edit_text(msg, parse_mode='Markdown')

# === /start Command ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.first_name or "there"
    args = context.args

    if args and args[0].startswith("verified"):
        save_verified_user(user_id)
        await update.message.reply_text(
            f"✅ Your verification is complete, {name}!\nLikes will now be sent from the group.",
            parse_mode='Markdown'
        )
        for group_id in GROUP_CHAT_IDS:
            await context.bot.send_message(
                chat_id=group_id,
                text=f"✅ Verified: {name} (ID: {user_id})"
            )

        if "-" in args[0]:
            _, region, uid = args[0].split("-")
            res = await call_like_api(region, uid)
            if "error" in res:
                for group_id in GROUP_CHAT_IDS:
                    await context.bot.send_message(chat_id=group_id, text=f"⚠️ API error:\n`{res['error']}`", parse_mode='Markdown')
                return
            if res.get("status") == 1:
                msg = (
                   f"✅ LIKE SUCCESSFULLY SEND\n\n"
                   f"✨ NAME: `{res.get('PlayerNickname', 'N/A')}`\n"
                   f"✨ UID: `{uid}`\n"
                   f"✨ Like Before Command: `{res.get('LikesbeforeCommand', 0)}`\n"
                   f"✨ Like After Command: `{res.get('LikesafterCommand', 0)}`\n"
                   f"✨ Like Given By Bot: `{res.get('LikesGivenByAPI', 0)}`\n"
                   f"📅 Valid Till: `{res.get('expire_date')}`"
                )
                for group_id in GROUP_CHAT_IDS:
                    await context.bot.send_message(chat_id=group_id, text=msg, parse_mode='Markdown')

# === Other Admin Commands ===

async def addvip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Not allowed.")
        return
    if len(context.args) != 3:
        await update.message.reply_text("❌ Use: `/addvip user_id limit YYYY-MM-DD`", parse_mode='Markdown')
        return
    try:
        user_id = int(context.args[0])
        limit = int(context.args[1])
        expiry = context.args[2]
        datetime.strptime(expiry, "%Y-%m-%d")
        add_vip(user_id, limit, expiry, admin_added=True)
        await update.message.reply_text(f"✅ VIP Added: {user_id}\nLimit: {limit}/day\nExpires: {expiry}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def removevip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Use: /removevip user_id")
        return
    remove_vip(int(context.args[0]))
    await update.message.reply_text("❌ VIP removed.")

async def viplist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    users = load_vip_users()
    if not users:
        await update.message.reply_text("📭 No VIP users.")
        return
    text = "👑 VIP List:\n\n"
    for u in users:
        text += f"🆔 {u['id']} | 🔁 {ulimit']}/day | ⏳ {u['expiry']}\n"
    await update.message.reply_text(text)

async def remain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    vip = get_vip_user(user_id)
    if vip and is_vip(user_id):
        expiry = datetime.strptime(vip["expiry"], "%Y-%m-%d")
        days_left = (expiry - datetime.now()).days
        await update.message.reply_text(f"🔁 Left: {vip['limit']}\n📅 Expires: {vip['expiry']} ({days_left} days)")
    else:
        await update.message.reply_text("❌ You're not a VIP.")

# === Shutdown Cleanup ===

def clear_verified_data():
    for f in [VERIFIED_FILE, SHORT_LINK_FILE, USAGE_FILE]:
        with open(f, 'w') as file:
            json.dump([], file)

def handle_shutdown(signum, frame):
    print("🔴 Stopping...")
    clear_verified_data()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# === Start Bot ===

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("like", like_command))
    app.add_handler(CommandHandler("addvip", addvip_command))
    app.add_handler(CommandHandler("removevip", removevip_command))
    app.add_handler(CommandHandler("viplist", viplist_command))
    app.add_handler(CommandHandler("remain", remain_command))
    print("🤖 Narayan Likes Bot is running...")
    app.run_polling()