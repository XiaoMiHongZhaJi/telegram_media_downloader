"""Downloads media from telegram."""
import asyncio
import logging
import os
import re
from typing import List, Optional, Tuple, Union

import pymysql
import pyrogram
import yaml
from pyrogram.types import Audio, Document, Photo, Video, VideoNote, Voice
from rich.logging import RichHandler

from utils.file_management import get_next_name, manage_duplicate_file
from utils.log import LogFilter
from utils.meta import print_meta

logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logging.getLogger("pyrogram.session.session").addFilter(LogFilter())
logging.getLogger("pyrogram.client").addFilter(LogFilter())
logger = logging.getLogger("media_downloader")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
last_message_id = 0
with open(THIS_DIR + "/config.yaml", encoding='utf-8') as file:
    config = yaml.safe_load(file)
media_types = config.get("media_types")
max_file_size_mb = config.get("max_file_size_mb")
file_formats = config.get("file_formats")
datasource = config.get("datasource")
if datasource is not None:
    try:
        password = datasource.get("password")
        if password is not None and str.isdigit(password):
            password = str(password)
        db = pymysql.connect(user=datasource["user"], password=password, host=datasource["host"],
                             database=datasource["database"], connect_timeout=2)
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(e)
        datasource = None
        logger.error("数据库连接失败")


def update_config():
    with open(THIS_DIR + "/config.yaml", "w", encoding='utf-8') as yaml_file:
        yaml.dump(config, yaml_file, allow_unicode=True)
    logger.info("Updated last read message_id to config file")


def _can_download(_type: str, file_formats: dict, file_format: Optional[str]) -> bool:
    if file_formats is None:
        return True
    if _type in ["audio", "document", "video"]:
        allowed_formats: list = file_formats[_type]
        if file_format not in allowed_formats and allowed_formats[0] != "all":
            return False
    return True


def _is_exist(file_path: str) -> bool:
    return not os.path.isdir(file_path) and os.path.exists(file_path)


async def _get_media_meta(
    media_obj: Union[Audio, Document, Photo, Video, VideoNote, Voice],
    _type: str,
) -> Tuple[str, Optional[str]]:
    if _type in ["audio", "document", "video"]:
        file_format: Optional[str] = media_obj.mime_type.split("/")[-1]  # type: ignore
    else:
        file_format = None

    if _type in ["voice", "video_note", "animation"]:
        file_format = media_obj.mime_type.split("/")[-1]  # type: ignore
        file_name: str = os.path.join(THIS_DIR, _type,
            "{}_{}.{}".format(_type, media_obj.date.isoformat().replace(":", "-"), file_format))
    else:
        file_name = getattr(media_obj, "file_name", None) or ""
        if len(file_name) > 0 and file_name.find(".") == -1 and file_format is not None:
            file_name += "." + file_format
        file_name = os.path.join(THIS_DIR, _type, file_name)
    return file_name, file_format


async def write_file(caption, message, message_id, reply_to, send_time, show_name, sticker, text, status):
    content = "[" + str(message_id) + "] [" + send_time.split(" ")[1] + "] "
    content += "%-12s" % (show_name + "：") + "\t"
    if message.media is not None and status != '4':
        content += "[media]"
    if text is not None:
        if text.find("\n") > -1:
            content += "↓\n"
        content += text
    elif caption is not None:
        if caption.find("\n") > -1:
            content += "↓\n"
        content += caption
    elif sticker is not None:
        if sticker.emoji is not None:
            content += "[sticker]" + sticker.emoji
    else:
        content += message.link
    if reply_to is not None:
        content += "\t[Reply：" + reply_to + "]"
    content += "\n"
    if status == '1':
        content = "[已补充]" + content
        logger.warning(content)
    elif status == '2':
        content = "[已编辑]" + content
        logger.warning(content)
    elif status == '4':
        content = "[已删除]" + content
        logger.warning(content)
    # title = re.sub(r"[\\\"\sㅤ/:?!*.<>|]", "_", chat_title)
    message_dir = THIS_DIR + "/message/"
    filename = message_dir + send_time.split(" ")[0] + ".txt"
    if not os.path.exists(message_dir):
        os.makedirs(message_dir)
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(content)


def query_msg(chat_id, message_id):
    sql = "select text,caption,message_id,concat(ifnull(first_name,''),ifnull(last_name,'')) first_name,ifnull(username,'') username from group_message where chat_id = " + str(chat_id) + " and message_id = " + str(message_id) + " order by id desc"
    try:
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is None:
            return None, None, None, ''
        text = None if result[0] is None else result[0].replace("'", "").replace("\\", "")
        caption = None if result[1] is None else result[1].replace("'", "").replace("\\", "")
        message_id = result[2]
        first_name = result[3] if len(result[3]) > 0 else result[4]
        return text, caption, message_id, first_name
    except Exception as e:
        logger.error("sql执行出错：" + sql)
        logger.error(e)
    pass


def update_status(message_id, status):
    sql = "update group_message set status = " + status + " where message_id = " + str(message_id)
    try:
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        logger.error("sql执行出错：" + sql)
        logger.error(e)
    pass


async def insert_db(caption, chat_id, chat_title, first_name, forward_from, last_name, message_id, phone_number,
                    reply_to, send_time, edit_date, sticker, text, user_id, username, status):
    if datasource is None:
        return
    sql = "INSERT INTO group_message(chat_id,message_id,user_id,chat_title,first_name,last_name,username,phone_number,text,forward_from,reply_to,caption,sticker,send_time,edit_date,status) VALUES ("
    sql += str(chat_id) + ","
    sql += str(message_id) + ","
    sql += user_id + ",'"
    sql += chat_title + "',"
    sql += "null," if first_name is None else "'" + first_name + "',"
    sql += "null," if last_name is None else "'" + last_name + "',"
    sql += "null," if username is None else "'" + username + "',"
    sql += "null," if phone_number is None else "'" + phone_number + "',"
    sql += "null," if text is None else "'" + text[:2000] + "',"
    sql += "null," if forward_from is None else "'" + forward_from + "',"
    sql += "null," if reply_to is None else "'" + reply_to + "',"
    sql += "null," if caption is None else "'" + caption[:2000] + "',"
    sql += "null,'" if sticker is None or sticker.emoji is None else "'" + sticker.emoji + "','"
    sql += send_time + "',"
    sql += "null," if edit_date is None else "'" + edit_date + "',"
    sql += status + ")"
    try:
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        logger.error("sql执行出错：" + sql)
        logger.error(e)


def get_show_name(user):
    if user is None:
        return None
    first_name = user.first_name
    last_name = user.last_name
    username = user.username
    show_name = ""
    if first_name is not None:
        show_name += re.sub(r"[\\\"\sㅤ/:?!*.<>|]", "", first_name)
    if last_name is not None:
        show_name += re.sub(r"[\\\"\sㅤ/:?!*.<>|]", "", last_name)
    length = len(show_name)
    if length == 0:
        show_name = "已注销 " + str(user.id) if username is None else username
    elif length > 12:
        show_name = show_name[:12]
    return show_name


def get_simple_text(message):
    if message is None:
        return None
    text = message.text
    if text is not None:
        return text.replace("'", "")
    caption = message.caption
    if caption is not None:
        return caption.replace("'", "")
    if message.sticker is not None and message.sticker.emoji is not None:
        return message.sticker.emoji
    if message.media is not None:
        return "[media]" + str(message.id)
    return str(message.id)


async def download_message(app: pyrogram.client.Client,message: pyrogram.types.Message):
    message_id = message.id
    try:
        if message.empty:
            return message_id
        chat = message.chat
        chat_id = chat.id
        from_user = message.from_user
        if chat_id is None or from_user is None:
            # logger.info(message)
            return message_id
        chat_title = chat.title
        text = None if message.text is None else message.text.replace("'", "").replace("\\", "")
        send_time = str(message.date)
        edit_date = None if message.edit_date is None else str(message.edit_date)
        caption = None if message.caption is None else message.caption.replace("'", "").replace("\\", "")
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
        status = '0' # 消息状态 0：默认，1：补充，2：已被修改，4：已被删除
        if datasource is not None:
            exist_text, exist_caption, exist_message_id, exist_first_name = query_msg(chat_id, message_id)
            if exist_message_id is None:
                status = '1'
            else:
                global last_message_id
                while last_message_id > 0 and message_id < last_message_id - 1:
                    # 有疑似被删除的消息
                    last_message_id -= 1
                    last_text, last_caption, last_id, last_first_name = query_msg(chat_id, last_message_id)
                    if last_id is not None:
                        update_status(last_id, '4')
                        await write_file(last_caption, message, last_id, None, send_time, last_first_name, None, last_text, '4')
                last_message_id = message_id
                if exist_text == text and exist_caption == caption:
                    # 消息已存在且未被修改
                    return message_id
                else:
                    # 消息已存在但被修改
                    status = '2'
                    await write_file(exist_caption, message, message_id, reply_to, send_time, show_name, sticker, exist_text, status)
            # 记录到数据库
            await insert_db(caption, chat_id, chat_title, first_name, forward_from, last_name, message_id, phone_number,
                            reply_to, send_time, edit_date, sticker, text, user_id, username, status)
        # 记录到txt
        await write_file(caption, message, message_id, reply_to, send_time, show_name, sticker, text, status)
        # 下载附件
        if message.media is not None:
            await down_media(app, message)
    except pyrogram.errors.exceptions.bad_request_400.BadRequest as e:
        logger.error("Message[%d]: file reference expired, refetching...", message_id, e, exc_info=True)
    except TypeError as e:
        logger.error("Timeout Error occurred when downloading Message[%d]", message_id, e, exc_info=True)
    except Exception as e:
        logger.error("Message[%d]: could not be downloaded due to following exception:\n[%s].", message_id, e, exc_info=True)
    return message_id


async def process_messages(client: pyrogram.client.Client, messages: List[pyrogram.types.Message]) -> int:
    message_ids = await asyncio.gather(*[download_message(client, message) for message in messages])
    last_read_message_id: int = max(message_ids)
    return last_read_message_id


async def down_media(app, message):
    if media_types is None or len(media_types) == 0:
        return
    for _type in media_types:
        _media = getattr(message, _type, None)
        if _media is None:
            continue
        file_name, file_format = await _get_media_meta(_media, _type)
        if max_file_size_mb is not None and max_file_size_mb > 0:
            file_size = _media.file_size
            if file_size > max_file_size_mb * 1024 * 1024:
                logger.warning(file_name.split("\\")[-1] + " 文件大小：" + str(round(file_size / 1024 / 1024, 1)) + "MB，超出限制，跳过下载")
                return
        if _can_download(_type, file_formats, file_format):
            if _is_exist(file_name):
                file_name = get_next_name(file_name)
                download_path = await app.download_media(message, file_name=file_name)
                download_path = manage_duplicate_file(download_path)
            else:
                download_path = await app.download_media(message, file_name=file_name)
            if download_path:
                logger.info("Media downloaded - %s", download_path)


async def begin_import(pagination_limit: int) -> dict:
    app = pyrogram.Client("media_downloader", api_id=config["api_id"], api_hash=config["api_hash"], proxy=config.get("proxy"))
    await app.start()
    last_read_message_id: int = config.get("last_read_message_id")
    if last_read_message_id is None:
        last_read_message_id = 0
    elif last_read_message_id > 500:
        last_read_message_id -+ 500
    messages_iter = app.get_chat_history(config["chat_id"])
    messages_list: list = []
    lastest_message_id = 0
    pagination_count: int = 0
    async for message in messages_iter:
        message_id = message.id
        if lastest_message_id < message_id:
            lastest_message_id = message_id
        messages_list.append(message)
        pagination_count += 1
        if message_id <= last_read_message_id + 1:
            await process_messages(app, messages_list)
            config["last_read_message_id"] = lastest_message_id
            update_config()
            await app.stop()
            return config
        elif pagination_count >= pagination_limit:
            await process_messages(app, messages_list)
            pagination_count = 0
            messages_list.clear()

    await app.stop()
    return config


def main():
    asyncio.get_event_loop().run_until_complete(begin_import(pagination_limit=500))
    update_config()


if __name__ == "__main__":
    print_meta(logger)
    main()
