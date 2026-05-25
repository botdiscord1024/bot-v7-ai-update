import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import google.generativeai as genai
from utils import load, save, err, ok

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qotd_scheduler.start()

    def cog_unload(self):
        self.qotd_scheduler.cancel()

    def get_config(self, gid):
        return load('config.json').get(str(gid), {}).get('qotd_settings', {})

    async def run_qotd(self, guild):
        m_cfg = self.get_config(guild.id)
        if not m_cfg.get('enabled', True): return
        
        channel = guild.get_channel(int(m_cfg.get('channel_id', 0))) if m_cfg.get('channel_id') else None
        if not channel: return

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            res = await asyncio.to_thread(model.generate_content, "Generate a fun, engaging, and open-ended Question of the Day (QOTD) for a Smash Karts gaming community to start a chat. No AI filler, just the question.")
            ai_content = res.text.strip()
        except:
            ai_content = "What is your absolute favorite weapon combination in Smash Karts?"

        embed = discord.Embed(title="? Question Of The Day", description=m_cfg.get('announcement_message', f"New question for today!\n\n> {ai_content}").replace("{content}", ai_content), color=discord.Color.red())
        
        pings = "".join([f"<@&{rid}>" for rid in m_cfg.get('mentioned_roles', [])])
        msg = await channel.send(content=pings if pings else None, embed=embed)

        try:
            thread = await msg.create_thread(name=m_cfg.get('thread_name', "?? Answer the QOTD here!"), auto_archive_duration=int(m_cfg.get('archive_duration', 1440)))
            if int(m_cfg.get('slowmode', 0)) > 0: await thread.edit(slowmode_delay=int(m_cfg.get('slowmode', 0)))
        except: pass

    @tasks.loop(hours=24)
    async def qotd_scheduler(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds: await self.run_qotd(g)

    @app_commands.command(name="trigger_qotd", description="Test QOTD instantly")
    @commands.has_permissions(administrator=True)
    async def trigger_qotd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.run_qotd(interaction.guild)
        await interaction.followup.send("? QOTD Posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(QOTD(bot))