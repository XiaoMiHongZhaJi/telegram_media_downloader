"""Downloads media from telegram current."""
import requests
import yaml
import logging
from pyrogram import filters, Client

from media_downloader import down_media, get_show_name, get_simple_text, write_file, insert_db
from rich.logging import RichHandler


logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger("media_downloader_current")

with open("config.yaml", encoding='utf-8') as f:
    config = yaml.safe_load(f)
handle_chat_id = config.get("chat_id")
push_users = config.get("push_users")
push_keywords = config.get("push_keywords")
notice_url = config.get("notice_url")
add_live_info_url = config.get("add_live_info_url")
app = Client("media_downloader_current", api_id=config["api_id"], api_hash=config["api_hash"], proxy=config.get("proxy"))


def keywords_notice(chat_title, show_name, message_text):
    if notice_url is None or notice_url.find("xxxx") > -1:
        return
    if push_users is not None:
        if show_name in push_users:
            data = {
                'title': chat_title,
                'body': show_name + "：" + message_text,
                'sound': 'shake'
            }
            requests.post(notice_url, data)
            return
    if push_keywords is not None:
        for push_keyword in push_keywords:
            if message_text.find(push_keyword) > -1:
                data = {
                    'title': chat_title,
                    'body': show_name + "：" + message_text,
                    'sound': 'shake'
                }
                requests.post(notice_url, data)
                break


def add_live_info(text):
    # #YouTube #直播预告 https://www.youtube.com/watch?v=eIUxtCBCVUw
    if add_live_info_url is None:
        return
    splits = text.split(" ")
    flag = False
    for split in splits:
        if split.find("直播预告") > -1 or split.find("开播通知") > -1:
            flag = True
        if split.find("https") > -1:
            url = split
    if not flag or url is None:
        return
    data = {
        "downLiveChat": True,
        "getLiveInfo": True,
        "url": url
    }
    res = requests.post(add_live_info_url, data)
    logging.info(res.text)


@app.on_message(filters.group)
async def handle_message(client, message):
    if message.empty:
        return
    chat = message.chat
    chat_id = chat.id
    if chat_id is None or handle_chat_id != chat_id:
        return
    from_user = message.from_user
    if from_user is None:
        # logger.info(message)
        return
    chat_title = chat.title
    text = None if message.text is None else message.text.replace("'", "")
    message_id = message.id
    send_time = str(message.date)
    caption = None if message.caption is None else message.caption.replace("'", "")
    sticker = message.sticker
    forward_from = get_show_name(message.forward_from)
    reply_to = get_simple_text(message.reply_to_message)
    if reply_to is not None and len(reply_to) > 20:
        reply_to = reply_to[:20] + "..."
    first_name = from_user.first_name
    last_name = from_user.last_name
    username = from_user.username
    user_id = str(from_user.id)
    phone_number = from_user.phone_number
    show_name = get_show_name(from_user)
    message_text = get_simple_text(message)
    if show_name is not None and message_text is not None:
        output = show_name + "：" + message_text
        logger.info(output)
        # 关键字提示
        keywords_notice(chat_title, show_name, message_text)

    # 记录到txt
    await write_file(caption, message, message_id, reply_to, send_time, show_name, sticker, text, '0')

    # 记录到数据库
    await insert_db(caption, chat_id, chat_title, first_name, forward_from, last_name, message_id, phone_number,
                    reply_to, send_time, None, sticker, text, user_id, username, '0')
    # 下载附件
    if message.media is not None:
        await down_media(app, message)
    # 67373工具人
    if user_id == "1994661779" and text is not None:
        await add_live_info(text)

app.run()
