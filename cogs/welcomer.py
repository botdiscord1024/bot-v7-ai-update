import os
import json
import threading
import builtins
import asyncio
import discord
from discord.ext import commands
from dashboard import app

# 1. НАСТРОЙКА НА DISCORD БОТА
# Задаваме пълни Intents (увери се, че са включени и в Discord Developer Portal)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Инициализиране на кеш структурата, която dashboard.py изисква
bot.cached_data = {
    'moderation': {},
    'levels': {},
    'counting': {},
    'smashkarts': {},
    'story': {},
    'welcomer': {}
}

# Функция за синхронизиране на данните от файловете към уеб таблото
def refresh_bot_cache():
    print("🔄 Обновяване на кеша на бота от JSON файловете...")
    try:
        # Нулиране на текущия кеш
        for key in bot.cached_data:
            bot.cached_data[key] = {}

        # Зареждане на основните конфигурации (модерация и welcomer)
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for gid, cfg in data.items():
                    bot.cached_data['moderation'][gid] = cfg
                    if 'welcomer' in cfg:
                        bot.cached_data['welcomer'][gid] = cfg['welcomer']

        # Зареждане на останалите модули
        for key in ['levels', 'counting', 'smashkarts', 'story']:
            filename = f"{key}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    bot.cached_data[key] = json.load(f)
                    
        print("✅ Кешът на бота е обновен успешно!")
    except Exception as e:
        print(f"❌ Грешка при обновяване на кеша: {e}")

# Закачаме функцията към builtins, за да може dashboard.py да я вика директно
builtins.refresh_bot_cache = refresh_bot_cache

# 2. АВТОМАТИЧНО ЗАРЕЖДАНЕ НА COGS (МОДУЛИ)
@bot.event
async def setup_hook():
    # Автоматично намиране и зареждане на всички cogs в папка 'cogs'
    if os.path.exists('cogs'):
        for filename in os.listdir('cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                cog_name = f'cogs.{filename[:-3]}'
                try:
                    await bot.load_extension(cog_name)
                    print(f"✅ Успешно зареден модул: {cog_name}")
                except Exception as e:
                    print(f"❌ Грешка при зареждане на {cog_name}: {e}")
    else:
        print("⚠️ Папка 'cogs' не беше намерена. Пропускане на автоматичното зареждане.")
    
    # Първоначално пълнене на кеша при стартиране
    refresh_bot_cache()

@bot.event
async def on_ready():
    print(f"👑 Ботът е онлайн! Влязъл като: {bot.user.name} (ID: {bot.user.id})")

# 3. СТАРТИРАНЕ НА FLASK УЕБ ТАБЛОТО
def run_dashboard():
    # Взема порта, предоставен от Render (по подразбиране 5000)
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Стартиране на уеб таблото на порт {port}...")
    # debug=False предотвратява двоен старт на нишките в среда за продукция
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# 4. ОСНОВЕН СТАРТЕР НА ПРИЛОЖЕНИЕТО
if __name__ == '__main__':
    print("⚙️ Подготовка на системата...")
    
    # Свързваме инстанцията на бота с Flask уеб приложението
    app.config['BOT'] = bot

    # Стартираме уеб таблото в отделна фонова нишка (Thread)
    flask_thread = threading.Thread(target=run_dashboard, daemon=True)
    flask_thread.start()

    # Вземаме Discord токена от променливите на средата (Environment Variables) в Render
    token = os.environ.get("DISCORD_TOKEN")
    
    if not token:
        print("⚠️ ВНИМАНИЕ: DISCORD_TOKEN не е намерен в променливите на средата!")
        # Локален спасителен вариант (ако тестваш на компютъра си)
        token = input("Въведи твоя Discord Token ръчно за локален тест: ").strip()

    if token:
        print("🚀 Стартиране на Discord бота...")
        try:
            bot.run(token)
        except discord.errors.LoginFailure:
            print("❌ Грешка: Невалиден Discord токен! Проверете настройките си.")
    else:
        print("❌ КРИТИЧНА ГРЕШКА: Липсва Discord токен. Приложението спира.")
