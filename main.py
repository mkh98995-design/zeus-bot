
try:
    import telebot
except ModuleNotFoundError:
    import os
    os.system("pip install pyTelegramBotAPI")
    import telebot

import re
import os

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("❌ BOT_TOKEN environment variable not set!")
    exit(1)

bot = telebot.TeleBot(bot_token)

# Global variables
warnings = {}  # user_id: warning_count
registered_users = {}  # user_id: name
war_participants = []  # list of names who are ready for war

# 👋 خوش‌آمدگویی
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:
        bot.send_message(
            message.chat.id,
            f"👋 عزیز {user.first_name} به گروه ZEUS خوش آمدی ⚔️"
        )

# ⚠️ اخطار
@bot.message_handler(commands=['اخطار'])
def warn_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ لطفاً این دستور را روی پیام کاربر ریپلای کنید.")
        return
    
    user_id = message.reply_to_message.from_user.id
    username = message.reply_to_message.from_user.first_name
    
    if user_id not in warnings:
        warnings[user_id] = 0
    warnings[user_id] += 1
    
    bot.send_message(message.chat.id, f"❗ {username} اخطار دریافت کرد. (اخطار {warnings[user_id]})")

# 🤫 سکوت
@bot.message_handler(commands=['سکوت'])
def mute_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "🔇 لطفاً این دستور را روی پیام کاربر ریپلای کنید.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=telebot.types.ChatPermissions(can_send_messages=False)
        )
        bot.send_message(message.chat.id, "🔇 کاربر با موفقیت ساکت شد.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ خطا در ساکت کردن کاربر.")

# ⛔ اخراج
@bot.message_handler(commands=['اخراج'])
def kick_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "⛔ برای اخراج، باید روی پیام کاربر ریپلای کنید.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, "🚫 کاربر از گروه اخراج شد.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ خطا در اخراج کاربر.")

# 🚀 ریست اخطار
@bot.message_handler(commands=['ریست_اخطار'])
def reset_warn(message):
    if not message.reply_to_message:
        bot.reply_to(message, "ℹ️ لطفاً این دستور را روی پیام کاربر ریپلای کنید.")
        return

    user_id = message.reply_to_message.from_user.id
    username = message.reply_to_message.from_user.first_name

    # پاک کردن اخطارها
    warnings.pop(user_id, None)

    bot.send_message(message.chat.id, f"✅ اخطارهای {username} با موفقیت ریست شد.")

# مرحله 1: ثبت‌نام اولیه با دستور /ثبت
@bot.message_handler(commands=['ثبت'])
def register(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    if user_id not in registered_users:
        registered_users[user_id] = name
        bot.reply_to(message, f"✅ {name} با موفقیت ثبت‌نام شد.")
    else:
        bot.reply_to(message, f"ℹ️ {name} قبلاً ثبت‌نام کرده.")

# مرحله 2: شروع وار جدید با /شروع_وار
@bot.message_handler(commands=['شروع_وار'])
def start_war(message):
    global war_participants
    war_participants = []
    bot.send_message(message.chat.id, "⚔️ وار جدید آغاز شد!\nاعضای ثبت‌نام‌شده لطفاً با دستور /من_هستم اعلام آمادگی کنند.")

# مرحله 3: اعلام آمادگی فقط توسط فرد خودش
@bot.message_handler(commands=['من_هستم'])
def confirm_participation(message):
    user_id = message.from_user.id
    name = registered_users.get(user_id)

    if not name:
        bot.reply_to(message, "❗ اول باید با دستور /ثبت ثبت‌نام کنی.")
        return

    if name in war_participants:
        bot.reply_to(message, f"ℹ️ {name} قبلاً اعلام آمادگی کرده.")
    else:
        war_participants.append(name)
        bot.reply_to(message, f"✅ {name} برای وار اعلام آمادگی کرد.")

# مرحله 4: دیدن لیست آماده‌ها با /آماده_ها
@bot.message_handler(commands=['آماده_ها'])
def show_ready(message):
    if war_participants:
        text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(war_participants)])
        bot.send_message(message.chat.id, f"📋 لیست افراد آماده:\n{text}")
    else:
        bot.send_message(message.chat.id, "⚠️ هنوز کسی اعلام آمادگی نکرده.")

# Anti-link handler - must be last to avoid conflicts
@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_anti_link(message):
    # نادیده‌گرفتن پیام‌های خود ربات
    if message.from_user.id == bot.get_me().id:
        return

    # بررسی اینکه کاربر مدیر نیست
    try:
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ['administrator', 'creator']:
            return
    except:
        pass

    # بررسی وجود لینک در پیام
    if message.text and re.search(r"(https?://t\.me/)", message.text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "⛔ ارسال لینک‌های تلگرام در گروه مجاز نیست.")
        except:
            bot.reply_to(message, "⛔ ارسال لینک‌های تلگرام در گروه مجاز نیست.")

if __name__ == "__main__":
    print("🤖 Bot started...")
    bot.infinity_polling()
