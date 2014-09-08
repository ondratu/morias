create table logins_01 (
    login_id integer not null primary key autoincrement,
    enabled integer default 1,          -- login is enabled

    email text not null,                -- user login
    passwd text not null,

    rights text not null default '[]',  -- json list of rights
    data text not null default '{}'     -- json data
);

insert into logins_01 (login_id, enabled, email, passwd, rights)
    select login_id, enabled, email, passwd, rights from login;

drop table if exists login;

alter table logins_01 rename to logins;
create unique index if not exists
    logins_email_idx on logins (email);
