import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import asyncio
import google.generativeai as genai  
from utils import load, save, err, ok

GEMINI_API_KEY = "AIzaSyCd-N-s-MTjS1S7vhrVqWwHnJg0Qx-mxdI"
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

        is_reply_to_bot = False
        if message.reference and message.reference.cached_message:
            if message.reference.cached_message.author.id == self.bot.user.id:
                is_reply_to_bot = True

        is_mentioning_bot = self.bot.user in message.mentions

        if (is_reply_to_bot or is_mentioning_bot) and cfg.get('ai_reply_on_mention', True):
            async with message.channel.typing():
                try:
                    contents = [message.content if message.content else "Look at this image."]
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.content_type and attachment.content_type.startswith("image/"):
                                img_bytes = await attachment.read()
                                image_part = {
                                    "mime_type": attachment.content_type,
                                    "data": img_bytes
                                }
                                contents.append(image_part)
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
                    await message.reply(f"? *Engine stalled! Error:* `{e}`")

    @app_commands.command(name="imagine", description="Generate a unique image using Gemini (Imagen 3)!")
    @app_commands.describe(prompt="Describe in detail what you want the AI to draw")
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        try:
            # ?????????? Imagen 3 ?????? ?? ?????????? ?? ???????????
            imagen = genai.ImageGenerationModel("imagen-3.0-generate-002")
            
            # ????????? ?????? ??????????
            result = await asyncio.to_thread(
                imagen.generate_images,
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1"
            )
            
            # ??????? ????????? ?? ???????? ???????
            generated_image = result.images[0]
            image_bytes = generated_image.image_bytes
            img_file = discord.File(io.BytesIO(image_bytes), filename="gemini_artwork.png")
            
            await interaction.followup.send(
                content=f"?? **Look what I created for you!**\n`Prompt:` *{prompt}*", 
                file=img_file
            )
                        
        except Exception as e:
            await interaction.followup.send(embed=err(f"Error drawing image: `{e}`"), ephemeral=True)

    # -- ??? ???????????? ?????? ??????? ?? ???????? ----------
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