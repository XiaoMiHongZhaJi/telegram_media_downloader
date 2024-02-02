import logging
import os
import time

import pymysql
import pyrogram
import requests
import yaml
from pyrogram import raw, utils

from utils.meta import print_meta

logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]")
logger = logging.getLogger("wild_like_message")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
with open(THIS_DIR + "/config.yaml", encoding='utf-8') as file:
    config = yaml.safe_load(file)
notice_url = config.get("notice_url")
notice_url2 = config.get("notice_url2")
chat_id = config["chat_id"]
last_like_message_id = config.get("last_like_message_id")
if last_like_message_id is None or last_like_message_id <= 1351951:
    last_like_message_id = 1351951
last_like_message_id = last_like_message_id - 500
datasource = config.get("datasource")
if datasource is not None:
    try:
        password = datasource.get("password")
        if password is not None:
            password = str(password)
        db = pymysql.connect(user=datasource["user"], password=password, host=datasource["host"],
                             database=datasource["database"], connect_timeout=2)
        logger.info("数据库连接成功")
    except Exception:
        datasource = None
        logger.error("数据库连接失败")


def get_like_messages(client, offset_id, limit):
    message_info = client.invoke(
        raw.functions.messages.GetHistory(
            peer=client.resolve_peer(chat_id),
            offset_date=utils.datetime_to_timestamp(utils.zero_datetime()),
            offset_id=offset_id, add_offset=0, limit=limit, max_id=0, min_id=0, hash=0), sleep_threshold=60)
    # print(message_info)
    last_message_id = None
    like_message_id = None
    messages = message_info.messages
    for message in messages:
        # print(message)
        message_id = message.id
        last_message_id = message_id
        if message_id <= last_like_message_id:
            return last_message_id, like_message_id
        try:
            reaction = message.reactions
        except:
            continue
        if reaction is None:
            continue
        recent_reactions = reaction.recent_reactions
        if recent_reactions is None:
            continue
        for recent_reaction in recent_reactions:
            user_id = recent_reaction.peer_id.user_id
            if user_id == 1639998668:
                if like_message_id is None or like_message_id < message_id:
                    like_message_id = message_id
                text = message.message
                if text is None or len(text) == 0:
                    if message.media is not None:
                        text = "[media]"
                if len(text) > 50:
                    text = text[:50] + "..."
                emoji_reaction = recent_reaction.reaction
                if isinstance(emoji_reaction, raw.types.ReactionEmoji):
                    emoticon = emoji_reaction.emoticon
                else:
                    emoticon = str(emoji_reaction.document_id)
                content = emoticon + "➡" + text
                logger.info(content)
                str_message_id = str(message_id)
                ten_time_array = time.localtime(message.date)
                send_time = time.strftime("%Y-%m-%d %H:%M:%S", ten_time_array)
                if datasource is not None:
                    try:
                        message_user_id = str(message.from_id.user_id)
                    except:
                        message_user_id = "null"
                    cursor = db.cursor()
                    cursor.execute("select 1 from wild_like_message where message_id = " + str_message_id)
                    result = cursor.fetchone()
                    if result is None:
                        write_to_file("wild精选：" + content, send_time)
                        if notice_url is not None and notice_url.find("xxxx") == -1:
                            requests.post(notice_url + content + "/" + "https://t.me/c/1744444199/" + str_message_id)
                        if notice_url2 is not None:
                            requests.post(notice_url2 + content + "/" + "https://t.me/c/1744444199/" + str_message_id)
                        sql = "insert into wild_like_message(message_id, link, user_id, text, sticker, send_time, create_time) values ("
                        sql += str_message_id
                        sql += ", 'https://t.me/c/1744444199/" + str_message_id + "', "
                        sql += message_user_id + ", '"
                        sql += text.replace("'", "").replace("\\", "") + "', '"
                        sql += emoticon + "', '"
                        sql += send_time + "', "
                        sql += "current_timestamp)"
                        cursor.execute(sql)
                        db.commit()
                    else:
                        logger.info("----------------------" + str_message_id + "已推送过，跳过")
                else:
                    write_to_file("wild精选：" + content, send_time)
                    if notice_url is not None and notice_url.find("xxxx") == -1:
                        requests.post(notice_url + content + "/" + "https://t.me/c/1744444199/" + str_message_id)
                        if notice_url2 is not None:
                            requests.post(notice_url2 + content + "/" + "https://t.me/c/1744444199/" + str_message_id)
    return last_message_id, like_message_id


def write_to_file(content, date):
    content += "\n"
    message_dir = THIS_DIR + "/message/"
    filename = message_dir + str(date).split(" ")[0] + ".txt"
    if not os.path.exists(message_dir):
        os.makedirs(message_dir)
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(content)


def update_config():
    with open(THIS_DIR + "/config.yaml", "w", encoding='utf-8') as yaml_file:
        yaml.dump(config, yaml_file, allow_unicode=True)
    logger.info("Updated last read message_id to config file")


def main():
    client = pyrogram.Client("media_downloader", api_id=config["api_id"], api_hash=config["api_hash"],proxy=config.get("proxy"))
    client.start()
    limit = 100
    new_like_message_id = None
    last_message_id, like_message_id = get_like_messages(client, 0, limit)
    if like_message_id is not None:
        new_like_message_id = like_message_id
    while last_message_id > last_like_message_id:
        last_message_id, like_message_id = get_like_messages(client, last_message_id, limit)
        if like_message_id is not None and (new_like_message_id is None or new_like_message_id < like_message_id):
            new_like_message_id = like_message_id
    if new_like_message_id is not None:
        config["last_like_message_id"] = new_like_message_id
        update_config()


if __name__ == "__main__":
    print_meta(logger)
    main()
