-- auto-generated definition
create table api_log
(
    id          serial
        constraint api_log_pk
            primary key,
    client_id   text,
    user_id     integer,
    path        text,
    headers     json,
    args        json,
    method      text,
    status      integer,
    create_time timestamp default CURRENT_TIMESTAMP,
    remote_addr text
);

comment on table api_log is '接口日志';

alter table api_log
    owner to postgres;

create index api_log_client_id_index
    on api_log (client_id);

create index api_log_path_index
    on api_log (path);

create index api_log_remote_addr_index
    on api_log (remote_addr);

create index api_log_status_index
    on api_log (status);

create index api_log_user_id_index
    on api_log (user_id);

