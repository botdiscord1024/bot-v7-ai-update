import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import google.generativeai as genai
from utils import load, save, err, ok

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class ROTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rotd_scheduler.start()

    def cog_unload(self):
        self.rotd_scheduler.cancel()

    def get_config(self, gid):
        return load('config.json').get(str(gid), {}).get('rotd_settings', {})

    async def run_rotd(self, guild):
        m_cfg = self.get_config(guild.id)
        if not m_cfg.get('enabled', True): return
        
        channel = guild.get_channel(int(m_cfg.get('channel_id', 0))) if m_cfg.get('channel_id') else None
        if not channel: return

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            res = await asyncio.to_thread(model.generate_content, "Generate a tricky, fun Riddle of the Day (ROTD) for a gaming server. Do NOT include the answer anywhere. Just output the riddle cleanly.")
            ai_content = res.text.strip()
        except:
            ai_content = "I have keys but open no locks. I have space but no room. You can enter but can't go outside. What am I? (A Keyboard!)"

        embed = discord.Embed(title="?? Riddle Of The Day", description=m_cfg.get('announcement_message', f"Can you solve today's riddle?\n\n> {ai_content}").replace("{content}", ai_content), color=discord.Color.orange())
        
        pings = "".join([f"<@&{rid}>" for rid in m_cfg.get('mentioned_roles', [])])
        msg = await channel.send(content=pings if pings else None, embed=embed)

        try:
            thread = await msg.create_thread(name=m_cfg.get('thread_name', "?? Leave your guesses here!"), auto_archive_duration=int(m_cfg.get('archive_duration', 1440)))
            if int(m_cfg.get('slowmode', 0)) > 0: await thread.edit(slowmode_delay=int(m_cfg.get('slowmode', 0)))
        except: pass

    @tasks.loop(hours=24)
    async def rotd_scheduler(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds: await self.run_rotd(g)

    @app_commands.command(name="trigger_rotd", description="Test ROTD instantly")
    @commands.has_permissions(administrator=True)
    async def trigger_rotd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.run_rotd(interaction.guild)
        await interaction.followup.send("? ROTD Posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ROTD(bot))