from random import shuffle

from config import BANNED_USERS, db
from strings import get_command

from pyrogram import filters
from pyrogram.types import Message

from RiruruMusic import YouTube, app
from RiruruMusic.core.call import AltCall
from RiruruMusic.utils import AdminRightsCheck, seconds_to_min
from RiruruMusic.utils.database import is_music_playing, music_off, music_on, set_loop


# Commands
STOP_COMMAND = get_command("STOP_COMMAND")
PAUSE_COMMAND = get_command("PAUSE_COMMAND")
RESUME_COMMAND = get_command("RESUME_COMMAND")
SEEK_COMMAND = get_command("SEEK_COMMAND")
LOOP_COMMAND = get_command("LOOP_COMMAND")
SHUFFLE_COMMAND = get_command("SHUFFLE_COMMAND")


@app.on_message(filters.command(STOP_COMMAND) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def stop_music(cli, message: Message, _, chat_id):
    await AltCall.stop_stream(chat_id)
    await set_loop(chat_id, 0)
    await message.reply_text(_["admin_9"].format(message.from_user.mention))


@app.on_message(filters.command(PAUSE_COMMAND) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def pause_admin(cli, message: Message, _, chat_id):
    if not await is_music_playing(chat_id):
        return await message.reply_text(_["admin_1"])
    await music_off(chat_id)
    await AltCall.pause_stream(chat_id)
    await message.reply_text(_["admin_2"].format(message.from_user.mention))


@app.on_message(filters.command(RESUME_COMMAND) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def resume_com(cli, message: Message, _, chat_id):
    if await is_music_playing(chat_id):
        return await message.reply_text(_["admin_3"])
    await music_on(chat_id)
    await AltCall.resume_stream(chat_id)
    await message.reply_text(_["admin_4"].format(message.from_user.mention))


@app.on_message(filters.command(SEEK_COMMAND) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def seek_comm(cli, message: Message, _, chat_id):
    txt = message.text.split(" ", 1)
    try:
        query = txt[1].strip()
    except:
        return await message.reply_text(_["admin_28"])
    if not query.isnumeric():
        return await message.reply_text(_["admin_29"])
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await message.reply_text(_["admin_30"])
    file_path = playing[0]["file"]
    if "index_" in file_path or "live_" in file_path:
        return await message.reply_text(_["admin_30"])
    duration_played = int(playing[0]["played"])
    duration_to_skip = int(query)
    duration = playing[0]["dur"]
    if txt[0][-2] == "c":
        if (duration_played - duration_to_skip) <= 10:
            return await message.reply_text(
                _["admin_31"].format(seconds_to_min(duration_played), duration)
            )
        to_seek = duration_played - duration_to_skip + 1
    else:
        if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
            return await message.reply_text(
                _["admin_31"].format(seconds_to_min(duration_played), duration)
            )
        to_seek = duration_played + duration_to_skip + 1
    mystic = await message.reply_text(_["admin_32"])
    if "vid_" in file_path:
        n, file_path = await YouTube.video(playing[0]["vidid"], True)
        if n == 0:
            return await message.reply_text(_["admin_30"])
    try:
        await AltCall.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration,
            playing[0]["streamtype"],
        )
    except:
        return await mystic.edit_text(_["admin_34"])
    if txt[0][-2] == "c":
        db[chat_id][0]["played"] -= duration_to_skip
    else:
        db[chat_id][0]["played"] += duration_to_skip
    await mystic.edit_text(_["admin_33"].format(seconds_to_min(to_seek)))


@app.on_message(filters.command(LOOP_COMMAND) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def admins(client, message: Message, _, chat_id):
    try:
        state = message.text.split(" ", 1)[1].strip()
    except:
        return await message.reply_text(_["admin_24"])

    if state.isnumeric():
        state = int(state)
        if 1 <= state <= 10:
            await set_loop(chat_id, state)
            return await message.reply_text(_["admin_25"].format(message.from_user.first_name, state))
        else:
            return await message.reply_text(_["admin_26"])

    elif state.lower() == "enable":
        await set_loop(chat_id, 3)
        return await message.reply_text(_["admin_25"].format(message.from_user.first_name, 3))

    elif state.lower() == "disable":
        await set_loop(chat_id, 0)
        return await message.reply_text(_["admin_27"])

    else:
        return await message.reply_text(_["admin_24"])


@app.on_message(filters.command(SHUFFLE_COMMAND) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def admins(Client, message: Message, _, chat_id):
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["admin_21"])
    try:
        popped = check.pop(0)
    except:
        return await message.reply_text(_["admin_22"])
    check = db.get(chat_id)
    if not check:
        check.insert(0, popped)
        return await message.reply_text(_["admin_22"])
    shuffle(check)
    check.insert(0, popped)
    await message.reply_text(_["admin_23"].format(message.from_user.first_name))
