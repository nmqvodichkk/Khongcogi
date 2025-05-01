from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import json
import os

TOKEN = "8199040677:AAE6cRip2khpaxjx7KmT6c5zgTJcU7Ff2Fg"
ADMIN_ID = 6355423837
STATE_FILE = "chat_state.txt"

# Load / save state
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"active": None, "queue": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Gửi yêu cầu đến admin
def send_request_to_admin(user_id, name, username, update: Update):
    info = f"<b>{name}</b>" + (f" (@{username})" if username else "") + f" - ID: <code>{user_id}</code>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✔️ Chấp nhận", callback_data=f"accept:{user_id}"),
         InlineKeyboardButton("❌ Từ chối", callback_data=f"reject:{user_id}")]
    ])
    update.message.bot.send_message(ADMIN_ID, f"🛎️ <b>Yêu cầu trò chuyện</b> từ {info}", reply_markup=keyboard)

# Lệnh /start
def start(update: Update, context: CallbackContext):
    state = load_state()
    user_id = update.message.from_user.id
    name = update.message.from_user.first_name or "Người dùng"
    username = update.message.from_user.username

    if state["active"] == user_id:
        update.message.reply_text("💬 <b>Bạn đang trò chuyện với admin.</b>", parse_mode='HTML')
    elif state["active"] is None:
        send_request_to_admin(user_id, name, username, update)
        update.message.reply_text("⏳ <i>Yêu cầu của bạn đã được gửi tới hệ thống. Vui lòng chờ xác nhận.</i>", parse_mode='HTML')
    elif all(u["id"] != user_id for u in state["queue"]):
        state["queue"].append({"id": user_id, "name": name, "username": username})
        update.message.reply_text("🔄 <i>Tất cả nhân viên CSKH đang bận. Bạn đã được thêm vào hàng chờ.</i>", parse_mode='HTML')
    else:
        update.message.reply_text("⏱️ <i>Bạn đang trong hàng chờ. Vui lòng chờ.</i>", parse_mode='HTML')

    save_state(state)

# Lệnh /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "<b>📌 Hướng dẫn sử dụng:</b>\n"
        "/start - Gửi yêu cầu trò chuyện\n"
        "/endchat - Kết thúc trò chuyện\n"
        "/dscho - (Chỉ admin) Xem danh sách chờ\n"
        "🌐 Website: <b>ChongLuaDao.Site</b>", parse_mode='HTML'
    )

# Lệnh /endchat
def endchat(update: Update, context: CallbackContext):
    state = load_state()
    from_id = update.message.from_user.id

    if state["active"] == from_id or from_id == ADMIN_ID:
        target = state["active"]
        if target:
            update.message.bot.send_message(target, "❗ <b>Cuộc trò chuyện đã kết thúc.</b>", parse_mode='HTML')
        update.message.bot.send_message(ADMIN_ID, f"🔚 <i>Đã kết thúc trò chuyện với ID:</i> <code>{target}</code>")
        state["active"] = None
        if state["queue"]:
            next_user = state["queue"].pop(0)
            state["active"] = next_user["id"]
            update.message.bot.send_message(next_user["id"], "✅ <b>Bạn đã được kết nối với admin.</b>", parse_mode='HTML')
            update.message.bot.send_message(ADMIN_ID,
                f"🟢 <b>Đang trò chuyện với</b> <b>{next_user['name']}</b> (ID: <code>{next_user['id']}</code>)", parse_mode='HTML')
        save_state(state)
    else:
        update.message.reply_text("⚠️ <i>Bạn không có phiên trò chuyện nào đang hoạt động.</i>", parse_mode='HTML')

# Lệnh /dscho (chỉ admin)
def dscho(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    state = load_state()
    if not state["queue"]:
        update.message.reply_text("📭 <i>Không có người dùng nào đang chờ.</i>", parse_mode='HTML')
    else:
        msg = "<b>📋 Danh sách chờ:</b>\n"
        for i, user in enumerate(state["queue"]):
            msg += f"{i+1}. <b>{user['name']}</b>" + (f" (@{user['username']})" if user['username'] else "") + f" - ID: <code>{user['id']}</code>\n"
        update.message.reply_text(msg, parse_mode='HTML')

# Nhắn tin 2 chiều
def chat(update: Update, context: CallbackContext):
    state = load_state()
    from_id = update.message.from_user.id
    text = update.message.text

    if state["active"] is not None:
        if from_id == state["active"]:
            update.message.bot.send_message(ADMIN_ID, f"<b>👤 Người dùng:</b> {text}", parse_mode='HTML')
        elif from_id == ADMIN_ID:
            update.message.bot.send_message(state["active"], f"<b>👨‍💼 Admin:</b> {text}", parse_mode='HTML')

# Xử lý callback từ admin
def callback_handler(update: Update, context: CallbackContext):
    state = load_state()
    from_id = update.callback_query.from_user.id
    data = update.callback_query.data

    if from_id != ADMIN_ID:
        return

    if data.startswith("accept:"):
        user_id = int(data.split(":")[1])
        state["active"] = user_id
        update.callback_query.message.bot.send_message(user_id, "✅ <b>Hệ thống đã chấp nhận trò chuyện.</b>\n<i>Bạn có thể nhắn tin ngay bây giờ.</i>", parse_mode='HTML')
        update.callback_query.message.bot.send_message(ADMIN_ID, f"✅ <b>Đã chấp nhận trò chuyện với ID:</b> <code>{user_id}</code>", parse_mode='HTML')
    elif data.startswith("reject:"):
        user_id = int(data.split(":")[1])
        update.callback_query.message.bot.send_message(user_id, "❌ <b>Hệ thống đã từ chối trò chuyện.</b>\n<i>Vui lòng thử lại sau.</i>", parse_mode='HTML')
        update.callback_query.message.bot.send_message(ADMIN_ID, f"❌ <b>Đã từ chối yêu cầu từ ID:</b> <code>{user_id}</code>", parse_mode='HTML')

    save_state(state)

# Khởi động bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("endchat", endchat))
    dp.add_handler(CommandHandler("dscho", dscho))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, chat))
    dp.add_handler(CallbackQueryHandler(callback_handler))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
