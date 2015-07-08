create table eshop_orders (
    order_id integer null,              -- null will be replaced via trigger
    client_id integer null references logins (login_id),
    email text not null,

    create_date integer not null,       -- unix timestamp in second from 1970-01-01
    modify_date integer not null,       -- unix timestamp in second from 1970-01-01

    state integer not null default 1,   -- STATE_ACCEPT
    items text not null default '[]',
    history text not null default '[]',
    data text not null default '{}'
);

-- trigger for auto create order_id from year and last order_id in table
create trigger if not exists eshop_orders_order_id
    after insert on eshop_orders
for each row begin
    update eshop_orders set order_id = (
        ifnull((select order_id from eshop_orders
                    where order_id like printf('%d%%', strftime('%Y'))
                    order by order_id desc limit 1),
                strftime('%Y')*10000)+1)
    where rowid = NEW.rowid;
end;

create unique index if not exists
    eshop_orders_order_id_idx on eshop_orders (order_id);
create index if not exists
    eshop_orders_client_id_idx on eshop_orders (client_id);
create index if not exists
    eshop_orders_email_idx on eshop_orders (email);
create index if not exists
    eshop_orders_create_date_idx on eshop_orders (create_date);
create index if not exists
    eshop_orders_state_idx on eshop_orders (state);
