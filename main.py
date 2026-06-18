import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from google import genai
from google.genai import types as genai_types

# --- НАЛАШТУВАННЯ КЛЮЧІВ ---
GEMINI_KEY = "AQ.Ab8RN6Lzaw4UXFfeRA9ONhql7xgsb3WVbjoUwgaNCeA41KhcUw"
# Сюди встав новий токен, який дав BotFather замість старого:
BOT_TOKEN = "8651328518:AAEy54p_p0LKKllI-zqbp6XJVfIrQc39q8s"

client = genai.Client(api_key=GEMINI_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_history = {}

def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="🧹 Очистити пам'ять"), types.KeyboardButton(text="ℹ️ Що ти вмієш?")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "🤖 **Привіт! Я твій ОФІЦІЙНИЙ ЦІЛОДОБОВИЙ ШІ-ПОМІЧНИК!**\n\n"
        "Тепер я працюю стабільно 24/7! Розмовляю українською, вмію писати коди, тексти, вирішувати задачі та пам'ятаю хід нашої розмови.\n\n"
        "Керування пам'яттю — на кнопках знизу!"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text in ["🧹 Очистити пам'ять", "/clear"])
async def clear_memory_handler(message: types.Message):
    uid = message.chat.id
    user_history[uid] = []
    await message.reply("🧹 Пам'ять очищена! Я все забув і готовий до нової теми.", reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text in ["ℹ️ Що ти вмієш?", "/help"])
async def send_help_handler(message: types.Message):
    help_text = (
        "ℹ️ **Що я вмію:**\n\n"
        "🧠 **Утримувати контекст:** Спілкуйся як з людиною, задавай уточнюючі питання.\n"
        "📝 **Генерувати тексти:** Пишу есе, твори, вірші, сценарії.\n"
        "💻 **Кодити:** Створюю і виправляю скрипти на будь-якій мові програмування."
    )
    await message.reply(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message()
async def handle_text_ai(message: types.Message):
    uid = message.chat.id
    user_text = message.text
    
    if uid not in user_history:
        user_history[uid] = []
        
    try:
        await bot.send_chat_action(chat_id=uid, action="typing")
        user_history[uid].append({"role": "user", "parts": [{"text": user_text}]})
        
        if len(user_history[uid]) > 14:
            user_history[uid] = user_history[uid][-14:]
            
        system_instruction = "You are a brilliant and helpful AI assistant. Always reply in Ukrainian language naturally and intelligently."
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_history[uid],
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7
                )
            )
        )
        
        bot_response = response.text
        user_history[uid].append({"role": "model", "parts": [{"text": bot_response}]})
        await message.answer(bot_response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        await message.answer("⚠️ Виникла затримка ШІ. Спробуй ще раз.", reply_markup=get_main_keyboard())

# Веб-сервер для проходження перевірки хостингу
async def handle_web(request):
    return web.Response(text="Бот активний!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
