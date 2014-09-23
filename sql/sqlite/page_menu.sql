create table page_menu (
    item_id integer not null primary key autoincrement,
    parent integer references page_menu (item_id),
    next integer references page_menu (item_id),
    ordering integer,

    title text not null,
    link text,
    locale text,
    state integer not null default 1        -- variable state (enabled)
);

create unique index if not exists
    page_menu_next_idx on page_menu (next);
create unique index if not exists
    page_menu_ordering_idx on page_menu (ordering);
