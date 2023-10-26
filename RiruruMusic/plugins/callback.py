import asyncio

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup

from strings import get_string
from config import (
    AUTO_DOWNLOADS_CLEAR, BANNED_USERS, STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL, TELEGRAM_VIDEO_URL, adminlist, db
)

from RiruruMusic import YouTube, app
from RiruruMusic.misc import SUDOERS
from RiruruMusic.core.call import AltCall
from RiruruMusic.utils.thumbnails import gen_thumb
from RiruruMusic.utils.formatters import seconds_to_min
from RiruruMusic.utils.inline import (
    stream_markup, stream_markup_timer, telegram_markup, telegram_markup_timer
)
from RiruruMusic.utils.database import (
    get_active_chats, get_lang, is_active_chat, is_music_playing,
    is_nonadmin_chat, music_off, music_on, set_loop
)
from RiruruMusic.utils.stream.autoclear import auto_clean
from RiruruMusic.utils.decorators.language import languageCB

checker = {}


@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_6"], show_alert=True)

    is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
    if not is_non_admin:
        if CallbackQuery.from_user.id not in SUDOERS:
            admins = adminlist.get(CallbackQuery.message.chat.id)
            if not admins:
                return await CallbackQuery.answer(_["admin_18"], show_alert=True)
            elif CallbackQuery.from_user.id not in admins:
                return await CallbackQuery.answer(_["admin_19"], show_alert=True)

    mention = CallbackQuery.from_user.mention

    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await music_off(chat_id)
        await AltCall.pause_stream(chat_id)
        await CallbackQuery.message.reply_text(_["admin_2"].format(mention))

    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await music_on(chat_id)
        await AltCall.resume_stream(chat_id)
        await CallbackQuery.message.reply_text(_["admin_4"].format(mention))

    elif command == "Stop" or command == "End":
        await CallbackQuery.answer()
        await AltCall.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        try:
            await CallbackQuery.message.delete()
        except:
            pass
        await CallbackQuery.message.reply_text(_["admin_9"].format(mention))

    elif command == "Skip":
        check = db.get(chat_id)
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                if AUTO_DOWNLOADS_CLEAR == str(True):
                    await auto_clean(popped)
            if not check:
                try:
                    await CallbackQuery.edit_message_text(_["admin_35"].format(mention))
                except:
                    pass
                try:
                    await CallbackQuery.message.reply_text(_["admin_10"].format(mention))
                    return await AltCall.stop_stream(chat_id)
                except:
                    return
        except:
            try:
                await CallbackQuery.edit_message_text(_["admin_35"].format(mention))
            except:
                pass
            try:
                await CallbackQuery.message.reply_text(_["admin_10"].format(mention))
                return await AltCall.stop_stream(chat_id)
            except:
                return

        await CallbackQuery.answer()
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        duration_min = check[0]["dur"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0

        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await CallbackQuery.message.reply_text(_["admin_11"].format(title))
            try:
                await AltCall.skip_stream(chat_id, link, video=status)
            except Exception:
                return await CallbackQuery.message.reply_text(_["call_6"])
            try:
                await CallbackQuery.edit_message_text(_["admin_35"].format(mention))
            except:
                pass
            button = telegram_markup(_, chat_id)
            img = await gen_thumb(videoid)
            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(title, f"https://t.me/{app.username}?start=info_{videoid}", duration_min, user[:31]),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        elif "vid_" in queued:
            mystic = await CallbackQuery.message.reply_text(_["call_7"], disable_web_page_preview=True)
            try:
                file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=status)
            except:
                return await mystic.edit_text(_["call_6"])
            try:
                await AltCall.skip_stream(chat_id, file_path, video=status)
            except Exception:
                return await mystic.edit_text(_["call_6"])
            try:
                await CallbackQuery.edit_message_text(_["admin_35"].format(mention))
            except:
                pass
            button = stream_markup(_, videoid, chat_id)
            img = await gen_thumb(videoid)
            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(title[:27], f"https://t.me/{app.username}?start=info_{videoid}", duration_min, user[:31]),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await mystic.delete()
        elif "index_" in queued:
            try:
                await AltCall.skip_stream(chat_id, videoid, video=status)
            except Exception:
                return await CallbackQuery.message.reply_text(_["call_6"])
            try:
                await CallbackQuery.edit_message_text(_["admin_35"].format(mention))
            except:
                pass
            button = telegram_markup(_, chat_id)
            run = await CallbackQuery.message.reply_photo(
                photo=STREAM_IMG_URL,
                caption=_["stream_2"].format(user[:31]),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            try:
                await AltCall.skip_stream(chat_id, queued, video=status)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            try:
                await CallbackQuery.edit_message_text(_["admin_35"].format(mention))
            except:
                pass
            if videoid == "telegram":
                button = telegram_markup(_, chat_id)
                run = await CallbackQuery.message.reply_photo(
                    photo=TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    caption=_["stream_3"].format(title, check[0]["dur"], user[:31]),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                button = stream_markup(_, videoid, chat_id)
                img = await gen_thumb(videoid)
                run = await CallbackQuery.message.reply_photo(
                    photo=img,
                    caption=_["stream_1"].format(title[:27], f"https://t.me/{app.username}?start=info_{videoid}", duration_min, user[:31]),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

    else:
        playing = db.get(chat_id)
        if not playing:
            return await CallbackQuery.answer(_["queue_2"], show_alert=True)

        duration_seconds = int(playing[0]["seconds"])
        if duration_seconds == 0:
            return await CallbackQuery.answer(_["admin_30"], show_alert=True)

        file_path = playing[0]["file"]
        if "index_" in file_path or "live_" in file_path:
            return await CallbackQuery.answer(_["admin_30"], show_alert=True)

        duration_played = int(playing[0]["played"])
        if int(command) in [1, 2]:
            duration_to_skip = 10
        else:
            duration_to_skip = 30
        duration = playing[0]["dur"]

        if int(command) in [1, 3]:
            if (duration_played - duration_to_skip) <= 10:
                bet = seconds_to_min(duration_played)
                return await CallbackQuery.answer(_["seek_1"].format(bet, duration), show_alert=True)
            to_seek = duration_played - duration_to_skip + 1
        else:
            if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
                bet = seconds_to_min(duration_played)
                return await CallbackQuery.answer(_["seek_1"].format(bet, duration), show_alert=True)
            to_seek = duration_played + duration_to_skip + 1

        await CallbackQuery.answer()
        mystic = await CallbackQuery.message.reply_text(_["admin_32"])
        if "vid_" in file_path:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await mystic.edit_text(_["admin_30"])
        try:
            await AltCall.seek_stream(chat_id, file_path, seconds_to_min(to_seek), duration, playing[0]["streamtype"])
        except:
            return await mystic.edit_text(_["admin_34"])
        if int(command) in [1, 3]:
            db[chat_id][0]["played"] -= duration_to_skip
        else:
            db[chat_id][0]["played"] += duration_to_skip
        string = _["admin_33"].format(seconds_to_min(to_seek))
        await mystic.edit_text(_["seek_2"].format(string, mention))


async def markup_timer():
    while not await asyncio.sleep(4):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                duration_seconds = int(playing[0]["seconds"])
                if duration_seconds == 0:
                    continue
                try:
                    mystic = playing[0]["mystic"]
                    markup = playing[0]["markup"]
                except:
                    continue
                try:
                    check = checker[chat_id][mystic.id]
                    if check is False:
                        continue
                except:
                    pass
                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except:
                    _ = get_string("en")
                try:
                    buttons = (
                        stream_markup_timer(
                            _,
                            playing[0]["vidid"],
                            chat_id,
                            seconds_to_min(playing[0]["played"]),
                            playing[0]["dur"],
                        )
                        if markup == "stream"
                        else telegram_markup_timer(
                            _,
                            chat_id,
                            seconds_to_min(playing[0]["played"]),
                            playing[0]["dur"],
                        )
                    )
                    await mystic.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
                except:
                    continue
            except:
                continue


asyncio.create_task(markup_timer())
