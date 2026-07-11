import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "ТВОЙ_ТОКЕН"
ADMIN_CHAT_ID = -100XXXXXXXXX  # чат админов

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ===== ДАННЫЕ =====
ticket_id_counter = 1
user_states = {}
active_dialogs = {}  # admin_id: user_id
user_ticket = {}     # user_id: ticket_id
banned_users = set()

# ===== КНОПКИ =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 Жалоба")],
        [KeyboardButton(text="⚖️ Обжалование")],
        [KeyboardButton(text="🐞 Баг")]
    ],
    resize_keyboard=True
)

# ===== /start =====
@dp.message(F.text == "/start")
async def start(msg: types.Message):
    if msg.from_user.id in banned_users:
        return
    await msg.answer("Привет! Это поддержка Aforiacraft\nВыбери действие:", reply_markup=main_kb)

# ===== ВЫБОР =====
@dp.message(F.text.in_(["📩 Жалоба", "⚖️ Обжалование", "🐞 Баг"]))
async def choose(msg: types.Message):
    if msg.from_user.id in banned_users:
        return

    if msg.from_user.id in user_ticket:
        await msg.answer("❗ У тебя уже есть активный тикет.")
        return

    user_states[msg.from_user.id] = msg.text
    await msg.answer("Опиши проблему подробно:")

# ===== СОЗДАНИЕ ТИКЕТА =====
@dp.message()
async def handle_message(msg: types.Message):
    global ticket_id_counter

    if msg.from_user.id in banned_users:
        return

    # если админ отвечает
    if msg.from_user.id in active_dialogs:
        user_id = active_dialogs[msg.from_user.id]

        await bot.send_message(
            user_id,
            f"💬 Ответ поддержки:\n\n{msg.text}"
        )
        return

    # если пользователь создаёт тикет
    if msg.from_user.id in user_states:
        ticket_id = ticket_id_counter
        ticket_id_counter += 1

        user_ticket[msg.from_user.id] = ticket_id

        category = user_states[msg.from_user.id]

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{msg.from_user.id}"),
                InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"close_{msg.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{msg.from_user.id}")
            ]
        ])

        await bot.send_message(
            ADMIN_CHAT_ID,
            f"📩 Тикет #{ticket_id}\n\n"
            f"👤 @{msg.from_user.username}\n"
            f"🆔 {msg.from_user.id}\n"
            f"Тип: {category}\n\n"
            f"{msg.text}",
            reply_markup=kb
        )

        await msg.answer(f"✅ Тикет #{ticket_id} отправлен в поддержку!")

        del user_states[msg.from_user.id]

    # если пользователь в диалоге
    elif msg.from_user.id in user_ticket:
        ticket_id = user_ticket[msg.from_user.id]

        await bot.send_message(
            ADMIN_CHAT_ID,
            f"💬 Ответ от пользователя (Тикет #{ticket_id}):\n\n{msg.text}"
        )

# ===== КНОПКИ АДМИНА =====
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    data = call.data
    admin_id = call.from_user.id

    if data.startswith("reply_"):
        user_id = int(data.split("_")[1])
        active_dialogs[admin_id] = user_id

        await call.message.answer("✍️ Напиши ответ пользователю:")
    
    elif data.startswith("close_"):
        user_id = int(data.split("_")[1])

        if user_id in user_ticket:
            del user_ticket[user_id]

        await bot.send_message(user_id, "🔒 Ваш тикет закрыт.")
        await call.message.answer("Тикет закрыт.")

    elif data.startswith("ban_"):
        user_id = int(data.split("_")[1])
        banned_users.add(user_id)

        await call.message.answer(f"🚫 Пользователь {user_id} забанен.")

    await call.answer()

# ===== СТАРТ =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
