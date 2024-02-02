create or replace view v_group_message as
select send_time                                                            '时间',
       concat(ifnull(first_name, ''), ifnull(last_name, ''))                '用户名',
       concat(ifnull(g.text, ''), ifnull(caption, ''), ifnull(sticker, '')) '内容',
       reply_to                                                             '回复',
       case g.status when 1 then '已补充' when 2 then '已编辑' when 4 then '已删除' else '实时' end '状态',
       concat('https://t.me/c/', substr(chat_id, 5), '/', message_id)       'url'
from group_message g
order by message_id desc;

create or replace view v_group_message_delete as
select send_time                                                            '时间',
       concat(ifnull(first_name, ''), ifnull(last_name, ''))                '用户名',
       concat(ifnull(g.text, ''), ifnull(caption, ''), ifnull(sticker, '')) '内容',
       reply_to                                                             '回复',
       '已删除' as                                                          '状态',
       concat('https://t.me/c/', substr(chat_id, 5), '/', message_id)       'url'
from group_message g
where g.status = 4
  and user_id not in ('5960194565', '6226014461')
order by message_id desc;

create or replace view v_group_message_edit as
select edit_date                                                            '时间',
       concat(ifnull(first_name, ''), ifnull(last_name, ''))                '用户名',
       concat(ifnull(g.text, ''), ifnull(caption, ''), ifnull(sticker, '')) '内容',
       reply_to                                                             '回复',
       '已编辑' as                                                          '状态',
       concat('https://t.me/c/', substr(chat_id, 5), '/', message_id)       'url'
from group_message g
where g.status = 2
  and g.id > (select max(id) from group_message) - 3000
union
select send_time                                                            '时间',
       concat(ifnull(first_name, ''), ifnull(last_name, ''))                '用户名',
       concat(ifnull(g.text, ''), ifnull(caption, ''), ifnull(sticker, '')) '内容',
       reply_to                                                             '回复',
       '实时' as                                                            '状态',
       concat('https://t.me/c/', substr(chat_id, 5), '/', message_id)       'url'
from group_message g
where g.status = 0
  and exists(select 1 from group_message g1 where g1.message_id = g.message_id and g1.status = 2)
  and g.id > (select max(id) from group_message) - 3000
order by url desc;