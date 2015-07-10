create table eshop_store (
    item_id integer not null primary key autoincrement,

    modify_date integer not null,       -- unix timestamp in second from 1970-01-01

    name text not null,                 -- item's name
    price float not null default 0.0,   -- item's price with or without VAT

    description text not null,          -- items's text description
    count integer not null default 0,   -- items's count at store

    state integer not null default 1,
    data text not null default '{}'     -- additional item's data (color, size, etc)
);

create index if not exists
    eshop_store_id_idx on eshop_store (item_id);
create index if not exists
    eshop_store_count_idx on eshop_store (count);
create index if not exists
    eshop_store_price_idx on eshop_store (price);
create index if not exists
    eshop_store_name_idx on eshop_store (name);

-- count trigger
create trigger eshop_store_count_tg update of count on eshop_store when new.count < 0
    begin
        select raise(ABORT, "@less_then_zero: Can't be count less then zero!");
    end;

-- incrase/decrase/price modification
create table eshop_store_action (
    item_id integer not null references eshop_store (item_id),
    timestamp integer not null,
    action_type text not null,      -- inc | dec | pri
    data text not null default ''
);

create index if not exists
    eshop_store_action_id_idx on eshop_store_action (item_id);
create index if not exists
    eshop_store_action_timestamp_idx on eshop_store_action (timestamp);

