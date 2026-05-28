import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import asyncio
import os
import base64  # Добавено за декодиране на генерираните изображения
import google.generativeai as genai
from utils import load, save, err, ok

GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class AIAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, gid):
        return load('config.json').get(str(gid), {})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        gid = str(message.guild.id)
        cfg = self.get_guild_config(gid)

        if not cfg.get('ai_enabled', True):
            return

        # 🛑 --- АВТОМАТИЧНА ЗАЩИТА ОТ ИГРИ И КОМАНДИ ---
        bot_mention = f"<@{self.bot.user.id}>"
        bot_mention_nick = f"<@!{self.bot.user.id}>"
        pure_text = message.content.replace(bot_mention, "").replace(bot_mention_nick, "").strip()

        if pure_text.startswith(('!', '?', '/', '$', '.', '-', '>')):
            return

        if len(pure_text) == 1:
            return
        # ----------------------------------------------

        # Проверка дали съобщението е Reply (Отговор) към бота
        is_reply_to_bot = False
        referenced_msg = None
        
        if message.reference:
            if isinstance(message.reference.resolved, discord.Message):
                referenced_msg = message.reference.resolved
            else:
                try:
                    referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                except:
                    referenced_msg = None
            
            if referenced_msg and referenced_msg.author.id == self.bot.user.id:
                is_reply_to_bot = True

        is_mentioning_bot = self.bot.user in message.mentions

        if (is_reply_to_bot or is_mentioning_bot) and cfg.get('ai_reply_on_mention', True):
            async with message.channel.typing():
                try:
                    contents = [message.content if message.content else "Look at this image."]
                    
                    # 1. Проверка за картинки в текущото съобщение
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.content_type and attachment.content_type.startswith("image/"):
                                img_bytes = await attachment.read()
                                contents.append({
                                    "mime_type": attachment.content_type,
                                    "data": img_bytes
                                })
                    
                    # 2. НОВО: Ако е Reply към картинка на бота, изтегли я, за да може Gemini да я ВИДИ и коментира!
                    if referenced_msg and referenced_msg.attachments:
                        for attachment in referenced_msg.attachments:
                            if attachment.content_type and attachment.content_type.startswith("image/"):
                                img_bytes = await attachment.read()
                                contents.append({
                                    "mime_type": attachment.content_type,
                                    "data": img_bytes
                                })

                    model = genai.GenerativeModel(
                        model_name="gemini-2.0-flash", 
                        system_instruction=(
                            "You are a witty, hype, and slightly chaotic Discord assistant for an English Smash Karts gaming community. "
                            "Match the high-energy vibe of the server. Drop casual gaming slang, reference karts, power-ups, "
                            "weapons (like missiles, mines, lobbers), and blowing up opponents. "
                            "You can also analyze images/screenshots shared by users (like end-game scoreboards or clips). "
                            "Keep your responses concise, fun, and ALWAYS reply in English."
                        )
                    )
                    response = await asyncio.to_thread(
                        model.generate_content, 
                        contents
                    )
                    
                    await message.reply(response.text)
                    
                except Exception as e:
                    await message.reply(f"🎰 *Engine stalled! Error:* `{e}`")

    @app_commands.command(name="imagine", description="Generate a unique image using Gemini (Imagen 3)!")
    @app_commands.describe(prompt="Describe in detail what you want the AI to draw")
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        try:
            # Директна HTTP заявка към API-то на Google за Imagen 3 (Заобикаляне на грешката от снимка image_ad589d.png)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_API_KEY}"
            payload = {
                "prompt": prompt,
                "numberOfImages": 1,
                "aspectRatio": "1:1",
                "outputMimeType": "image/jpeg"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Google API Error ({resp.status})")
                    
                    result = await resp.json()
                    if "generatedImages" not in result:
                        raise Exception("Image generation blocked by safety filters or prompt issue.")
                    
                    # Изваждане на картинката от base64 формат
                    base64_image = result["generatedImages"][0]["image"]["imageBytes"]
                    image_bytes = base64.b64decode(base64_image)
            
            img_file = discord.File(io.BytesIO(image_bytes), filename="gemini_artwork.png")
            
            await interaction.followup.send(
                content=f"🎨 **Look what I created for you!**\n`Prompt:` *{prompt}*", 
                file=img_file
            )
                        
        except Exception as e:
            await interaction.followup.send(embed=err(f"Error drawing image: `{e}`"), ephemeral=True)

    @app_commands.command(name="ai_emoji", description="Use an external custom emoji from the web dashboard")
    @app_commands.describe(name="The custom name of the emoji assigned on the dashboard")
    async def ai_emoji(self, interaction: discord.Interaction, name: str):
        gid = str(interaction.guild.id)
        cfg = self.get_guild_config(gid)
        custom_emojis = cfg.get('custom_external_emojis', {})

        if name not in custom_emojis:
            return await interaction.response.send_message(embed=err(f"Emoji named `:{name}:` was not found on the web dashboard!"), ephemeral=True)

        await interaction.response.defer()
        url = custom_emojis[name]

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    img_file = discord.File(io.BytesIO(img_data), filename=f"{name}.png")
                    await interaction.followup.send(file=img_file)
                else:
                    await interaction.followup.send(embed=err("Failed to download the custom emoji asset from the provided link."), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIAssistant(bot))
