import re
from config import Config, Database
from pyrogram import Client, idle, filters
from pytgcalls import GroupCallFactory
from youtube_dl import YoutubeDL


client = Client(
    Config.SESSION_STRING,
    Config.API_ID,
    Config.API_HASH,
)
ytdl = YoutubeDL({
    "quiet": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
})
print("UserBot Started Enjoy")

factory = GroupCallFactory(client)
base_filter = filters.outgoing & ~filters.forwarded & ~filters.edited
yt_regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"


def with_group_call(func):
    async def wrapper(client, message):
        group_call = Database.VIDEO_CALL.get(message.chat.id)
        await message.delete()
        if group_call:
            return await func(client, message, group_call)
    return wrapper


def init_group_call(func):
    async def wrapper(client, message):
        group_call = Database.VIDEO_CALL.get(message.chat.id)
        if not group_call:
            group_call = factory.get_group_call()
            Database.VIDEO_CALL[message.chat.id] = group_call
        await message.delete()
        return await func(client, message, group_call)
    return wrapper


async def send_log(content):
    await client.send_message(Config.CHAT_ID, content, disable_notification=True, disable_web_page_preview=True)


@client.on_message(filters.command("ps", "") & base_filter)
@with_group_call
async def pause_stream(_, _2, group_call):
    group_call.set_pause(True)


@client.on_message(filters.command("rs", "") & base_filter)
@with_group_call
async def pause_stream(_, _2, group_call):
    group_call.set_pause(False)


@client.on_message(filters.command("stop", "") & base_filter)
@with_group_call
async def stop_stream(_, m, group_call):
    if group_call.is_running:
        await group_call.stop_media()
    await group_call.leave()
    Database.VIDEO_CALL.pop(m.chat.id)


@client.on_message(filters.command("stream", "") & base_filter)
@init_group_call
async def start_stream(_, m, group_call):
    if ' ' not in m.text:
        return
    query = m.text.split(' ', 1)[1]
    print(query)
    link = query
    match = re.match(yt_regex, query)
    if match:
        await send_log("Got YouTube link: " + query)
        try:
            meta = ytdl.extract_info(query, download=False)
            formats = meta.get('formats', [meta])
            for f in formats:
                link = f['url']
        except Exception as e:
            await send_log(f"**YouTube Download Error!** \n\nError: `{e}`")
            print(e)
            return
    await send_log(f"Got video link: {link}")
    try:
        if not group_call.is_connected:
            await group_call.join(m.chat.id)
        await group_call.start_video(link, with_audio=True, repeat=False, enable_experimental_lip_sync=True)
        await send_log(f"starting {link}")
    except Exception as e:
        await send_log(f"**An Error Occoured!** \n\nError: `{e}`")
        print(e)
        return
    
# play songs
@app.on_message(filters.command('play') & self_or_contact_filter)
async def play_track(client, message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        return
    input_filename = os.path.join(
        client.workdir, DEFAULT_DOWNLOAD_DIR,
        'input.raw',
    )
    audio = message.reply_to_message.audio
    audio_original = await message.reply_to_message.download()
    a = await message.reply('Downloading...')
    ffmpeg.input(audio_original).output(
        input_filename,
        format='s16le',
        acodec='pcm_s16le',
        ac=2, ar='48k',
    ).overwrite_output().run()
    os.remove(audio_original)
    if VOICE_CHATS and message.chat.id in VOICE_CHATS:
        text = f'▶️ Playing **{audio.title}** at **{message.chat.title}** by JEVC Player...'
    else:
        try:
            group_call = GroupCall(client, input_filename)
            await group_call.start(message.chat.id)
        except RuntimeError:
            await message.reply('Group Call doesnt exist')
            return
        VOICE_CHATS[message.chat.id] = group_call
    await a.edit(f'▶️ Playing **{audio.title}** at **{message.chat.title}** by JEVC Player...')


client.start()
idle()
client.stop()
