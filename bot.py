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
print("Userbot started successfully")

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
    await client.send_message(Config.LOG_ID, content, disable_notification=True, disable_web_page_preview=True)


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
    
@client.on_message(filters.command("radio", "") & base_filter)
async def radio_mirchi(e):
    xx = await eor(e, get_string("com_1"))
    if not len(e.text.split()) > 1:
        return await eor(xx, "Are You Kidding Me?\nWhat to Play?")
    input = e.text.split()
    if input[1].startswith("-"):
        chat = int(input[1])
        song = e.text.split(maxsplit=2)[2]
    elif input[1].startswith("@"):
        cid = (await vcClient.get_entity(input[1])).id
        chat = int(f"-100{cid}")
        song = e.text.split(maxsplit=2)[2]
    else:
        song = e.text.split(maxsplit=1)[1]
        chat = e.chat_id
    if not is_url_ok(song):
        return await eor(xx, f"`{song}`\n\nNot a playable link.🥱")
    ultSongs = Player(chat, e)
    if not ultSongs.group_call.is_connected:
        if not (await ultSongs.vc_joiner()):
            return
    await ultSongs.group_call.start_audio(song)
    await xx.reply(
        f"• Started Radio 📻\n\n• Station : `{song}`",
        file="https://telegra.ph/file/24e303c8dc0d5e50b3a53.jpg",
    )
    await xx.delete()



client.start()
idle()
client.stop()
