-- login names
alter table logins
    add name text not null default '';
