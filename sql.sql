CREATE DATABASE `tg_message` DEFAULT CHARACTER SET utf8mb4;
use tg_message;

CREATE TABLE `group_message` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `chat_id` bigint(20) DEFAULT NULL COMMENT '群聊id',
  `message_id` bigint(20) DEFAULT NULL COMMENT '消息id',
  `user_id` bigint(20) DEFAULT NULL COMMENT '用户id',
  `chat_title` varchar(60) DEFAULT NULL COMMENT '群聊名称',
  `first_name` varchar(60) DEFAULT NULL COMMENT 'first_name',
  `last_name` varchar(60) DEFAULT NULL COMMENT 'last_name',
  `username` varchar(60) DEFAULT NULL COMMENT 'username',
  `phone_number` varchar(60) DEFAULT NULL COMMENT 'phone_number',
  `text` varchar(2000) DEFAULT NULL COMMENT '消息文字内容',
  `forward_from` varchar(200) DEFAULT NULL COMMENT 'forward_from',
  `reply_to` varchar(200) DEFAULT NULL COMMENT 'reply_to',
  `caption` varchar(2000) DEFAULT NULL COMMENT 'caption',
  `sticker` varchar(200) DEFAULT NULL COMMENT 'sticker',
  `send_time` varchar(30) DEFAULT NULL COMMENT '发送时间',
  `edit_date` varchar(30) DEFAULT NULL COMMENT '编辑时间',
  `status` int(11) DEFAULT '0' COMMENT '消息状态 0：默认，1：补充，2：已被修改，4：已被删除',
  PRIMARY KEY (`id`),
  KEY `message_id` (`message_id`)
) ENGINE=InnoDB AUTO_INCREMENT=612934 DEFAULT CHARSET=utf8mb4