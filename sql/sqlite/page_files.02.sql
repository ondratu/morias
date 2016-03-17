-- servis hash for logins - for sign_up password reset
alter table page_files
    add format integer not null default 1;      -- html (1), rst (2)
