create table options (
    section text not null,
    option text not null,
    value text
);

create index if not exists
    options_section_idx on options (section);

create unique index if not exists
    options_section_option_idx on options (section, option);
