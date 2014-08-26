CREATE TABLE login (
    login_id integer not null primary key autoincrement,
    enabled integer default 1,      -- login is enabled

    email text not null,            -- user login
    passwd text not null,

    rights text not null,           -- json list of rights
    data text not null default '{}' -- json data
);

CREATE unique index if not exists
    login_email_idx on login (email);

-- text + salt -> password + dev
INSERT INTO login (enabled, email, passwd, rights)
    VALUES (1, 'admin@morias.dev', '36d4186adcfa2cf7d60a77ee4d18b83f95e83f05', '["super"]');
