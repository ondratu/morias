create table jobs (
    path text not null,
    timestamp integer not null,
    singleton integer,
    pid integer not null,
    login_id integer references logins (login_id),
    data text not null default '{}'
);

create index if not exists
    jobs_path_idx on jobs (path);
create index if not exists
    jobs_timestamp_idx on jobs (timestamp);
create unique index if not exists
    jobs_path_singleton_idx on jobs (path, singleton);
create unique index if not exists
    jobs_pid_idx on jobs (pid);
