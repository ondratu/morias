-- servis hash for logins - for sign_up password reset
alter table logins
    add service_hash text null;
alter table logins
    add history text not null default '[]';

create unique index logins_service_hash_idx on logins(service_hash);
