import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extractaudio': True,
    'noprogress': True,
    'concurrent_fragment_downloads': 5,  # จำนวนการดาวน์โหลดไฟล์พร้อมกัน
    'download_archive': 'downloaded.txt',  # เก็บประวัติการดาวน์โหลด
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -threads 4',
    'options': '-vn -b:a 192k  -bufsize 9000k'  # ปรับขนาด buffer ขึ้น
}

queue = []

@bot.command(name='play', aliases=['p','P'],help='เล่นเพลงจาก YouTube')
async def play(ctx, url):
    voice_channel = ctx.author.voice.channel

    if not voice_channel:
        await ctx.send("คุณต้องอยู่ใน voice channel เพื่อใช้คำสั่งนี้")
        return

    voice_client = ctx.voice_client
    if not voice_client:
        await voice_channel.connect()
        voice_client = ctx.voice_client

    ytdl = YoutubeDL(ytdl_options)
    info = ytdl.extract_info(url, download=False)
    url2 = info['url']
    title = info.get('title', 'Unknown Title')

    queue.append({'title': title, 'url': url2})
    await ctx.send(f"เพิ่มเพลง `{title}` ลงในคิว")

    if not voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    voice_client = ctx.voice_client
    if not queue:
        await ctx.send("คิวว่างแล้ว")
        await asyncio.sleep(120)  # 60 วินาที
        if not queue and voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send("บอทออกจากช่องแล้ว เนื่องจากไม่มีเพลงในคิว")
        return

    song = queue.pop(0)
    url = song['url']
    title = song['title']

    def after_song_end(error):
        if error:
            print(f"Error playing song: {error}")
        bot.loop.create_task(play_next(ctx))

    # เริ่มโหลดเพลงถัดไปก่อนที่เพลงปัจจุบันจะจบ
    voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=after_song_end)
    await ctx.send(f"กำลังเล่น `{title}`")

@bot.command(name='stop', help='หยุดเล่นเพลง')
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("หยุดเพลงแล้ว")

@bot.command(name='skip',aliases=['s','S'], help='ข้ามเพลง')
async def skip(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("ข้ามไปยังเพลงถัดไป")

@bot.command(name='leave', help='ให้ออกจาก voice channel')
async def leave(ctx):
    voice_client = ctx.voice_client
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("บอทออกจากช่องแล้ว")

bot.run("")
