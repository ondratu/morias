create table attachments_01 (
    attachment_id integer not null primary key autoincrement,
    uploader_id integer not null references logins (login_id),

    timestamp integer not null,     -- unix timestamp of upload

    mime_type text not null,        -- image/jpeg ...
    file_name text not null,        -- original file name
    md5       text not null,        -- md5 of upload timestamp

    data text not null default '{}' -- additional data (description, downloads...)
);

insert into attachments_01
        (attachment_id, uploader_id, timestamp, mime_type, file_name, md5, data)
    select attachment_id, uploader_id, timestamp, mime_type, file_name, '', data
        from attachments;

pragma foreign_keys = off;

drop table attachments;
alter table attachments_01 rename to attachments;

create index if not exists
    attachments_uploader_id_idx on attachments (uploader_id);
create index if not exists
    attachments_timestamp_idx on attachments (timestamp);
create index if not exists
    attachments_mime_type_idx on attachments (mime_type);
create index if not exists
    attachments_file_name_idx on attachments (file_name);

pragma foreign_keys = on;
