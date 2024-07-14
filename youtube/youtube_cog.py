from os import name
import discord
from discord import app_commands
from discord.embeds import Embed
from discord.ext import commands
from youtube.utils import YTDLSource
from youtube.youtube import Youtube
from youtube.youtube_control_view import YoutubeControlView

class YoutubeCog(commands.Cog):

    youtubes: dict[Youtube] = {}

    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Successfully loaded: YoutubeCog')
        await self.bot.tree.sync()

    @app_commands.command(name='youtube', description='Youtubeの動画を再生するよ')
    async def youtube(self, context: discord.Interaction):

        await context.response.defer(thinking=True)

        if context.user.voice is None:
            await context.response.send_message('ボイスチャンネルに参加してね', ephemeral=True)
            return

        if context.guild.voice_client is None:
            await context.user.voice.channel.connect()

        if not context.guild.id in self.youtubes:
            self.youtubes[context.guild.id] = Youtube(client=context.guild.voice_client)

        # ViewとEmbedを生成
        youtube: Youtube = self.youtubes[context.guild_id]
        embed = youtube.make_embed()
        view = YoutubeControlView(youtube=youtube)
        # すでにセッションに紐づいたメッセージがある場合は先に消しておく
        if youtube.message:
            await context.followup.delete_message(youtube.message.id)
        # メッセージを送信
        message = await context.followup.send(embed=embed, view=view)
        youtube.message = message

    @app_commands.command(name='bye', description='ボイスチャンネルから抜けるよ')
    async def disconnect(self, context: discord.Interaction):
        # セッションをリセット
        self.youtubes[context.guild.id] = None
        # ボイスチャンネルに接続してるか
        if context.guild.voice_client is None:
            await context.response.send_message('ボイスチャンネルに参加してないよ', ephemeral=True)
        else:
            await context.response.send_message('またね', ephemeral=True)
            await context.guild.voice_client.disconnect()

def setup(bot):
    return bot.add_cog(YoutubeCog(bot))
