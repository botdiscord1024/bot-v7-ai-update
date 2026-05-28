import os
import json
import threading
import builtins
import asyncio
import discord
from discord.ext import commands
from dashboard import app

# 1. DISCORD BOT SETUP
# Enabling all intents (Make sure they are also toggled ON in the Discord Developer Portal)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Initializing the cache structure required by dashboard.py
bot.cached_data = {
    'moderation': {},
    'levels': {},
    'counting': {},
    'smashkarts': {},
    'story': {},
    'welcomer': {}
}

# Function to synchronize file data with the web dashboard cache
def refresh_bot_cache():
    print("🔄 Refreshing bot cache from JSON files...")
    try:
        # Reset current cache
        for key in bot.cached_data:
            bot.cached_data[key] = {}

        # Loading core configurations (moderation and welcomer)
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for gid, cfg in data.items():
                    bot.cached_data['moderation'][gid] = cfg
                    if 'welcomer' in cfg:
                        bot.cached_data['welcomer'][gid] = cfg['welcomer']

        # Loading remaining modules
        for key in ['levels', 'counting', 'smashkarts', 'story']:
            filename = f"{key}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    bot.cached_data[key] = json.load(f)
                    
        print("✅ Bot cache refreshed successfully!")
    except Exception as e:
        print(f"❌ Error refreshing cache: {e}")

# Attaching the function to builtins so dashboard.py can invoke it globally
builtins.refresh_bot_cache = refresh_bot_cache

# 2. AUTOMATIC COGS (MODULES) LOADER
@bot.event
async def setup_hook():
    # Automatically scan and load all cogs inside the 'cogs' directory
    if os.path.exists('cogs'):
        for filename in os.listdir('cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                cog_name = f'cogs.{filename[:-3]}'
                try:
                    await bot.load_extension(cog_name)
                    print(f"✅ Successfully loaded module: {cog_name}")
                except Exception as e:
                    print(f"❌ Error loading {cog_name}: {e}")
    else:
        print("⚠️ 'cogs' folder not found. Skipping automatic extension loading.")
    
    # Perform initial cache population on startup
    refresh_bot_cache()

@bot.event
async def on_ready():
    print(f"👑 Bot is online! Logged in as: {bot.user.name} (ID: {bot.user.id})")

# 3. FLASK WEB DASHBOARD RUNNER
def run_dashboard():
    # Fetch the port allocated by Render (defaults to 5000)
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting web dashboard on port {port}...")
    # debug=False prevents duplicate thread initialization in production environments
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# 4. MAIN APPLICATION ENTRY POINT
if __name__ == '__main__':
    print("⚙️ Preparing system...")
    
    # Bind the bot instance to the Flask app configuration context
    app.config['BOT'] = bot

    # Launch the web dashboard inside a separate background thread
    flask_thread = threading.Thread(target=run_dashboard, daemon=True)
    flask_thread.start()

    # Pull the Discord token from Render's Environment Variables
    token = os.environ.get("DISCORD_TOKEN")
    
    if not token:
        print("⚠️ WARNING: DISCORD_TOKEN environment variable not found!")
        # Local safety fallback (if running tests on your local machine)
        token = input("Enter your Discord Token manually for local testing: ").strip()

    if token:
        print("🚀 Starting Discord bot...")
        try:
            bot.run(token)
        except discord.errors.LoginFailure:
            print("❌ Error: Invalid Discord token provided! Check your credentials.")
    else:
        print("❌ CRITICAL ERROR: Missing Discord token. Application halting.")
