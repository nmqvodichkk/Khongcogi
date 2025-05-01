import telebot
import json
import os

TOKEN = "8199040677:AAE6cRip2khpaxjx7KmT6c5zgTJcU7Ff2Fg"
ADMIN_ID = 6355423837
STATE_FILE = "chat_state.txt"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

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
def send_request_to_admin(user_id, name, username):
    info = f"<b>{name}</b>" + (f" (@{username})" if username else "") + f" - ID: <code>{user_id}</code>"
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("✔️ Chấp nhận", callback_data=f"accept:{user_id}"),
        telebot.types.InlineKeyboardButton("❌ Từ chối", callback_data=f"reject:{user_id}")
    )
    bot.send_message(ADMIN_ID, f"🛎️ <b>Yêu cầu trò chuyện</b> từ {info}", reply_markup=keyboard)

# Lệnh /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    state = load_state()
    user_id = message.from_user.id
    name = message.from_user.first_name or "Người dùng"
    username = message.from_user.username

    if state["active"] == user_id:
        bot.send_message(user_id, "💬 <b>Bạn đang trò chuyện với admin.</b>")
    elif state["active"] is None:
        send_request_to_admin(user_id, name, username)
        bot.send_message(user_id, "⏳ <i>Yêu cầu của bạn đã được gửi tới hệ thống. Vui lòng chờ xác nhận.</i>")
    elif all(u["id"] != user_id for u in state["queue"]):
        state["queue"].append({"id": user_id, "name": name, "username": username})
        bot.send_message(user_id, "🔄 <i>Tất cả nhân viên CSKH đang bận. Bạn đã được thêm vào hàng chờ.</i>")
    else:
        bot.send_message(user_id, "⏱️ <i>Bạn đang trong hàng chờ. Vui lòng chờ.</i>")

    save_state(state)

# Lệnh /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id,
        "<b>📌 Hướng dẫn sử dụng:</b>\n"
        "/start - Gửi yêu cầu trò chuyện\n"
        "/endchat - Kết thúc trò chuyện\n"
        "/dscho - (Chỉ admin) Xem danh sách chờ\n"
        "🌐 Website: <b>ChongLuaDao.Site</b>")

# Lệnh /endchat
@bot.message_handler(commands=['endchat'])
def handle_endchat(message):
    state = load_state()
    from_id = message.from_user.id

    if state["active"] == from_id or from_id == ADMIN_ID:
        target = state["active"]
        if target:
            bot.send_message(target, "❗ <b>Cuộc trò chuyện đã kết thúc.</b>")
        bot.send_message(ADMIN_ID, f"🔚 <i>Đã kết thúc trò chuyện với ID:</i> <code>{target}</code>")
        state["active"] = None
        if state["queue"]:
            next_user = state["queue"].pop(0)
            state["active"] = next_user["id"]
            bot.send_message(next_user["id"], "✅ <b>Bạn đã được kết nối với admin.</b>")
            bot.send_message(ADMIN_ID,
                f"🟢 <b>Đang trò chuyện với</b> <b>{next_user['name']}</b> (ID: <code>{next_user['id']}</code>)")
        save_state(state)
    else:
        bot.send_message(from_id, "⚠️ <i>Bạn không có phiên trò chuyện nào đang hoạt động.</i>")

# Lệnh /dscho (chỉ admin)
@bot.message_handler(commands=['dscho'])
def handle_dscho(message):
    if message.from_user.id != ADMIN_ID:
        return
    state = load_state()
    if not state["queue"]:
        bot.send_message(ADMIN_ID, "📭 <i>Không có người dùng nào đang chờ.</i>")
    else:
        msg = "<b>📋 Danh sách chờ:</b>\n"
        for i, user in enumerate(state["queue"]):
            msg += f"{i+1}. <b>{user['name']}</b>" + (f" (@{user['username']})" if user['username'] else "") + f" - ID: <code>{user['id']}</code>\n"
        bot.send_message(ADMIN_ID, msg)

# Nhắn tin 2 chiều
@bot.message_handler(func=lambda m: True)
def handle_chat(message):
    state = load_state()
    from_id = message.from_user.id
    text = message.text

    if state["active"] is not None:
        if from_id == state["active"]:
            bot.send_message(ADMIN_ID, f"<b>👤 Người dùng:</b> {text}")
        elif from_id == ADMIN_ID:
            bot.send_message(state["active"], f"<b>👨‍💼 Admin:</b> {text}")

# Xử lý callback từ admin
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    state = load_state()
    from_id = call.from_user.id
    data = call.data

    if from_id != ADMIN_ID:
        return

    if data.startswith("accept:"):
        user_id = int(data.split(":")[1])
        state["active"] = user_id
        bot.send_message(user_id, "✅ <b>Hệ thống đã chấp nhận trò chuyện.</b>\n<i>Bạn có thể nhắn tin ngay bây giờ.</i>")
        bot.send_message(ADMIN_ID, f"✅ <b>Đã chấp nhận trò chuyện với ID:</b> <code>{user_id}</code>")
    elif data.startswith("reject:"):
        user_id = int(data.split(":")[1])
        bot.send_message(user_id, "❌ <b>Hệ thống đã từ chối trò chuyện.</b>\n<i>Vui lòng thử lại sau.</i>")
        bot.send_message(ADMIN_ID, f"❌ <b>Đã từ chối yêu cầu từ ID:</b> <code>{user_id}</code>")

    save_state(state)

# Khởi động bot
print("Bot is running...")
bot.remove_webhook()
bot.infinity_polling()