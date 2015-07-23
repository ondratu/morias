-- image values was set by trigger when object_attchment was change
alter table eshop_store
    add image_id integer null references attachments (attachment_id);
alter table eshop_store
    add image_md5 text;             -- copy for fast use in list, no join need
alter table eshop_store
    add image_mime_type text;       -- copy for fast use in list

-- when new attachment is attach, to eshop_store item, or ordering of it's
-- attachmens was change, update eshop_store item's first attachment
create trigger object_attachments_update_eshop_store_tg
    after update of ordering on object_attachments
for each row when old.object_type = 'eshop_item'
begin
    update eshop_store set
        image_id = (
            select a.attachment_id
                from attachments a
                    left join object_attachments o on (a.attachment_id = o.attachment_id)
                where old.object_id = o.object_id and a.mime_type like 'image/%'
                order by o.ordering  limit 1)
    where item_id = old.object_id;
    update eshop_store set
        image_md5 = (select md5 from attachments where attachment_id = image_id),
        image_mime_type = (select mime_type from attachments where attachment_id = image_id)
    where item_id = old.object_id;
end;

-- when some attachment is detach, from eshop_store item, update eshop_store
-- item's first attachment
create trigger object_attachments_delete_eshop_store_tg
    after delete on object_attachments
for each row when old.object_type = 'eshop_item'
begin
    update eshop_store set
        image_id = (
            select a.attachment_id
                from attachments a
                    left join object_attachments o on (a.attachment_id = o.attachment_id)
                where old.object_id = o.object_id and a.mime_type like 'image/%'
                order by o.ordering  limit 1)
    where item_id = old.object_id;
    update eshop_store set
        image_md5 = (select md5 from attachments where attachment_id = image_id),
        image_mime_type = (select mime_type from attachments where attachment_id = image_id)
    where item_id = old.object_id;
end;


-- first time setting image for all items in eshop_store
update eshop_store set
        image_id = (
            select a.attachment_id
                from attachments a
                    left join object_attachments o on (a.attachment_id = o.attachment_id)
                where item_id = o.object_id and a.mime_type like 'image/%'
                order by o.ordering  limit 1);
update eshop_store set
        image_md5 = (select md5 from attachments where attachment_id = image_id),
        image_mime_type = (select mime_type from attachments where attachment_id = image_id);
