import discord
from discord.ext import commands
import json
import os

class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_config(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        config = self.load_config()
        
        # Взимане на настройките за конкретния сървър
        guild_config = config.get(guild_id, {})
        welcomer_config = guild_config.get('welcomer', {})
        
        # Проверка дали модулът изобщо е пуснат от таблото
        if not welcomer_config.get('enabled', False):
            return

        # Дефиниране на динамичните променливи
        member_count = len(member.guild.members)
        placeholders = {
            "{user.mention}": member.mention,
            "{user.name}": member.name,
            "{server.name}": member.guild.name,
            "{member_count}": str(member_count)
        }

        def replace_placeholders(text):
            if not text:
                return ""
            for placeholder, value in placeholders.items():
                text = text.replace(placeholder, value)
            return text

        # ─── 1. АВТОМАТИЧНО ДАВАНЕ НА РОЛИ (AUTO-ROLE) ───
        if welcomer_config.get('autorole_enabled', False):
            roles_str = welcomer_config.get('autorole_roles', '')
            if roles_str:
                # Разделяне на ролите, ако са изброени със запетая
                role_ids = [r.strip() for r in roles_str.split(',') if r.strip().isdigit()]
                for r_id in role_ids:
                    role = member.guild.get_role(int(r_id))
                    if role:
                        try:
                            await member.add_roles(role)
                        except discord.Forbidden:
                            print(f"[Welcomer Error] Нямам права да добавя роля {role.name} на {member.name}")
                        except Exception as e:
                            print(f"[Welcomer Error] Грешка при добавяне на роля: {e}")

        # ─── 2. СЪОБЩЕНИЕ НА ЛИЧНО СЪОБЩЕНИЕ (DM ON JOIN) ───
        if welcomer_config.get('dm_enabled', False):
            dm_msg = welcomer_config.get('dm_message', '')
            if dm_msg:
                try:
                    await member.send(replace_placeholders(dm_msg))
                except discord.Forbidden:
                    print(f"[Welcomer] Не мога да пратя DM на {member.name} (Личните съобщения са спрени).")
                except Exception as e:
                    print(f"[Welcomer Error] Проблем при пращане на DM: {e}")

        # ─── 3. ПУБЛИЧНО СЪОБЩЕНИЕ В КАНАЛ (TEXT / EMBED) ───
        channel_id_str = welcomer_config.get('channel', '')
        if channel_id_str and channel_id_str.isdigit():
            channel = member.guild.get_channel(int(channel_id_str))
            if channel:
                plain_message = welcomer_config.get('message', '')
                
                # Ако е включен красивият Embed стил
                if welcomer_config.get('embed_enabled', False):
                    embed_title = welcomer_config.get('embed_title', 'Welcome!')
                    embed_color_hex = welcomer_config.get('embed_color', '#5865f2').lstrip('#')
                    
                    try:
                        embed_color = int(embed_color_hex, 16)
                    except ValueError:
                        embed_color = 0x5865f2 # Цвят по подразбиране (Discord Blurple)
                        
                    embed = discord.Embed(
                        title=replace_placeholders(embed_title),
                        description=replace_placeholders(plain_message),
                        color=embed_color
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        print(f"[Welcomer Error] Липсват права за писане/Embeds в канал {channel.name}")
                else:
                    # Чисто текстово съобщение
                    if plain_message:
                        try:
                            await channel.send(replace_placeholders(plain_message))
                        except discord.Forbidden:
                            print(f"[Welcomer Error] Липсват права за писане в канал {channel.name}")

async def setup(bot):
    await bot.add_cog(Welcomer(bot))
