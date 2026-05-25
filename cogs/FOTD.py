import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import google.generativeai as genai
from utils import load, save, err, ok

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class FOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fotd_scheduler.start()

    def cog_unload(self):
        self.fotd_scheduler.cancel()

    def get_config(self, gid):
        return load('config.json').get(str(gid), {}).get('fotd_settings', {})

    async def run_fotd(self, guild):
        m_cfg = self.get_config(guild.id)
        if not m_cfg.get('enabled', True): return
        
        channel = guild.get_channel(int(m_cfg.get('channel_id', 0))) if m_cfg.get('channel_id') else None
        if not channel: return

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            res = await asyncio.to_thread(model.generate_content, "Generate a mind-blowing, fun Fact of the Day (FOTD) about gaming, history, or crazy tech. Keep it under 3 sentences, no AI chat, just the fact.")
            ai_content = res.text.strip()
        except:
            ai_content = "Did you know that the first video game tournament took place in 1972 at Stanford University?"

        embed = discord.Embed(title="?? Fact Of The Day", description=m_cfg.get('announcement_message', f"Expand your mind today!\n\n> {ai_content}").replace("{content}", ai_content), color=discord.Color.blue())
        
        pings = "".join([f"<@&{rid}>" for rid in m_cfg.get('mentioned_roles', [])])
        msg = await channel.send(content=pings if pings else None, embed=embed)

        try:
            thread = await msg.create_thread(name=m_cfg.get('thread_name', "?? Discussion thread!"), auto_archive_duration=int(m_cfg.get('archive_duration', 1440)))
            if int(m_cfg.get('slowmode', 0)) > 0: await thread.edit(slowmode_delay=int(m_cfg.get('slowmode', 0)))
        except: pass

    @tasks.loop(hours=24)
    async def fotd_scheduler(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds: await self.run_fotd(g)

    @app_commands.command(name="trigger_fotd", description="Test FOTD instantly")
    @commands.has_permissions(administrator=True)
    async def trigger_fotd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.run_fotd(interaction.guild)
        await interaction.followup.send("? FOTD Posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(FOTD(bot))