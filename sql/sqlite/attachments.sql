create table attachments (
    attachment_id integer not null primary key autoincrement,
    uploader_id integer not null references logins (login_id),

    timestamp integer not null,     -- unix timestamp of upload

    mime_type text not null,        -- image/jpeg ...
    file_name text not null,        -- original file name

    data text not null default '{}' -- additional data (description, downloads...)
);

create index if not exists
    attachments_uploader_id_idx on attachments (uploader_id);
create index if not exists
    attachments_timestamp_idx on attachments (timestamp);
create index if not exists
    attachments_mime_type_idx on attachments (mime_type);
create index if not exists
    attachments_file_name_idx on attachments (file_name);


create table object_attachments (
    attachment_id integer not null references attachments (attachment_id),
    object_type text not null,
    object_id integer not null
);

create unique index if not exists
    object_attachments_idx on object_attachments (attachment_id, object_type, object_id);
create index if not exists
    object_attachments_object_typ on object_attachments (object_type);
