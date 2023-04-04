CREATE DATABASE tg_message DEFAULT CHARACTER SET utf8mb4;
use tg_message;

CREATE TABLE group_message (
  id int(11) unsigned auto_increment COMMENT '主键id' primary key,
  chat_id bigint(20) DEFAULT NULL COMMENT '群聊id',
  message_id bigint(20) DEFAULT NULL COMMENT '消息id',
  user_id bigint(20) DEFAULT NULL COMMENT '用户id',
  chat_title varchar(60) DEFAULT NULL COMMENT '群聊名称',
  first_name varchar(60) DEFAULT NULL COMMENT 'first_name',
  last_name varchar(60) DEFAULT NULL COMMENT 'last_name',
  username varchar(60) DEFAULT NULL COMMENT 'username',
  phone_number varchar(60) DEFAULT NULL COMMENT 'phone_number',
  text varchar(2000) DEFAULT NULL COMMENT '消息文字内容',
  forward_from varchar(200) DEFAULT NULL COMMENT 'forward_from',
  reply_to varchar(200) DEFAULT NULL COMMENT 'reply_to',
  caption varchar(2000) DEFAULT NULL COMMENT 'caption',
  sticker varchar(200) DEFAULT NULL COMMENT 'sticker',
  send_time varchar(30) DEFAULT NULL COMMENT '发送时间',
  edit_date varchar(30) DEFAULT NULL COMMENT '编辑时间',
  status int(11) DEFAULT '0' COMMENT '消息状态 0：默认，1：补充，2：已被修改，4：已被删除'
);
create index message_id
    on tg_message.group_message (message_id);

create table tg_message.wild_like_message
(
    id int(11) unsigned auto_increment comment '主键id' primary key,
    sticker      varchar(200)  null comment '点赞表情',
    text         varchar(2000) null comment '消息内容',
    send_time    varchar(30)   null comment '发送时间',
    link         varchar(50)   null comment '消息链接',
    message_id   bigint        null comment '消息id',
    user_id      bigint        null comment '用户id',
    create_time  varchar(30)   null comment '更新时间'
);
create index message_id
    on tg_message.wild_like_message (message_id);
