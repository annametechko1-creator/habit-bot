import asyncio
import datetime
import random
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

users_habits = {}

# ===== МЕМЫ / АЧИВКИ =====
ACHIEVEMENTS = {
    1: {
        "text": "🌱 Первый шаг сделан!",
        "photo": "AgACAgIAAxkBAAPhaeJd7KveuIPHdpVqfL5OHbynKv4AAs8Qaxs-pxhLq45gzxVfVxsBAAMCAAN4AAM7BA"
    },
    3: {
        "text": "😎 Уже 3 дня!",
        "photo": "AgACAgIAAxkBAAPkaeJePHYNWnPN2J8QLlro-WOYxbAAAuMQaxs-pxhLJKos_qgiidQBAAMCAAN4AAM7BA"
    },
    7: {
        "text": "🔥 7 дней — ты держишься!",
        "photo": "AgACAgIAAxkBAAPqaeJeaoBcqCxdokD_i9iPSYc8rV8AAu8Qaxs-pxhL8kr2dpmSqi0BAAMCAAN5AAM7BA"
    },
    14: {
        "text": "💛 14 дней — это уже характер",
        "photo": "AgACAgIAAxkBAAPuaeJegV0HmzPsmUG7Hg2Nm91rMp0AAvQQaxs-pxhL4IPxizt7q-QBAAMCAAN5AAM7BA"
    },
    21: {
        "text": "🧠 21 день — привычка закрепилась",
        "photo": "AgACAgIAAxkBAAPwaeJejf79IjqkV-Cdozdic9nzykUAAvcQaxs-pxhLv0Qr2tnQHv8BAAMCAAN5AAM7BA"
    },
    30: {
        "text": "🏆 30 дней!!! Ты машина дисциплины",
        "photo": "AgACAgIAAxkBAAPyaeJel6VR9qtkIRXtTjwVCiTCF6EAAvoQaxs-pxhL5AhdzkIzSwwBAAMCAAN4AAM7BA"
    },
    "bonus": {
        "text": "💥 Бонусная ачивка!",
        "photo": "AgACAgIAAxkBAAPmaeJeUrUAAWWsf_u_Pzz90OIsd1NgAALqEGsbPqcYSygGYPzfEyHIAQADAgADeQADOwQ"
    }
}

# ===== ЦИТАТЫ =====
quotes = [
    "Начни сейчас.",
    "Ты уже молодец 💛",
    "Дисциплина сильнее мотивации.",
    "Маленькие шаги — результат.",
    "Не идеально, а регулярно.",
]

def get_quote():
    return random.choice(quotes)

def coach(streak):
    if streak == 0:
        return "Начать — уже победа 💛"
    elif streak < 3:
        return "Ты в начале пути 🌱"
    elif streak < 7:
        return "Ты формируешь привычку 🔥"
    else:
        return "Это уже часть тебя 😎"

# ===== КНОПКИ =====
menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить привычку")],
        [KeyboardButton(text="📊 Мои привычки")],
        [KeyboardButton(text="ℹ️ Инструкция")]
    ],
    resize_keyboard=True
)

# ===== FSM =====
class AddHabit(StatesGroup):
    name = State()
    hour = State()
    minute = State()

# ===== START =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🌿 Я твой коуч привычек\n\nВыбери действие 👇",
        reply_markup=menu_kb
    )

# ===== ДОБАВЛЕНИЕ =====
@dp.message(F.text == "➕ Добавить привычку")
async def add(message: types.Message, state: FSMContext):
    await message.answer("Название привычки:")
    await state.set_state(AddHabit.name)

@dp.message(AddHabit.name)
async def name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Час (0-23):")
    await state.set_state(AddHabit.hour)

@dp.message(AddHabit.hour)
async def hour(message: types.Message, state: FSMContext):
    await state.update_data(hour=int(message.text))
    await message.answer("Минута (0-59):")
    await state.set_state(AddHabit.minute)

@dp.message(AddHabit.minute)
async def minute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id

    users_habits.setdefault(user_id, {})
    users_habits[user_id][data["name"]] = {
        "time": (data["hour"], int(message.text)),
        "streak": 0,
        "last_done": None
    }

    await message.answer("✅ Добавлено")
    await state.clear()

# ===== СПИСОК =====
@dp.message(F.text == "📊 Мои привычки")
async def habits(message: types.Message):
    user_id = message.from_user.id
    habits = users_habits.get(user_id, {})

    if not habits:
        return await message.answer("Нет привычек 🌱")

    for h, d in habits.items():
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"done:{h}")]
            ]
        )

        await message.answer(
            f"🔹 {h}\n🔥 Серия: {d['streak']}",
            reply_markup=kb
        )

# ===== STREAK + АЧИВКИ =====
@dp.callback_query(lambda c: c.data.startswith("done:"))
async def done_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    habit_name = callback.data.split(":")[1]
    today = datetime.date.today()

    habit = users_habits[user_id][habit_name]

    if habit["last_done"] == today:
        return await callback.answer("Уже выполнено 😎", show_alert=True)

    if habit["last_done"] == today - datetime.timedelta(days=1):
        habit["streak"] += 1
    else:
        habit["streak"] = 1

    habit["last_done"] = today
    streak = habit["streak"]

    # 🎉 АЧИВКИ
    if streak in ACHIEVEMENTS:
        ach = ACHIEVEMENTS[streak]
        await callback.message.answer_photo(
            photo=ach["photo"],
            caption=ach["text"]
        )
    else:
        # бонус шанс
        if random.random() < 0.1:
            ach = ACHIEVEMENTS["bonus"]
            await callback.message.answer_photo(
                photo=ach["photo"],
                caption=ach["text"]
            )

    await callback.message.answer(
        f"🔥 {habit_name}\n\n{coach(streak)}\n📈 Серия: {streak}"
    )

    await callback.answer("Засчитано ✅")

# ===== ИНСТРУКЦИЯ =====
@dp.message(F.text == "ℹ️ Инструкция")
async def help_func(message: types.Message):
    await message.answer(
        "📘 Как пользоваться ботом:\n\n"
        "➕ Добавь привычку\n"
        "⏰ Укажи время\n"
        "🔔 Получай напоминания\n"
        "🔥 Отмечай выполнение\n"
        "📈 Следи за streak\n"
        "💛 Главное — регулярность"
    )

# ===== НАПОМИНАНИЯ =====
async def reminders():
    while True:
        now = datetime.datetime.now()

        for user_id, habits in users_habits.items():
            for h, d in habits.items():
                hour, minute = d["time"]

                if now.hour == hour and now.minute == minute:
                    kb = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"done:{h}")]
                        ]
                    )

                    await bot.send_message(
                        user_id,
                        f"🔔 {h}\n\n{get_quote()}",
                        reply_markup=kb
                    )

        await asyncio.sleep(60)

# ===== RUN =====
async def main():
    asyncio.create_task(reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
