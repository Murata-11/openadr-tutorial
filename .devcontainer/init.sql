-- 1) VEN
create table vens (
  ven_id varchar(255) primary key,
  ven_name varchar(255) not null,
  registration_id varchar(255) not null,
  fingerprint varchar(255) not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp on update current_timestamp
);

-- 2) ターゲット資源
create table ven_resources (
  ven_id varchar(255),
  resource_id varchar(255),
  primary key (ven_id, resource_id),
  foreign key (ven_id) references vens(ven_id) on delete cascade
);

-- 3) イベント
create table events (
  event_id varchar(255) primary key,
  ven_id varchar(255),
  modification_number int not null,
  event_status varchar(50) not null,
  market_context text,
  created_datetime timestamp,
  priority int,
  test_event boolean,
  signals json not null,  -- MySQLではJSON型
  created_at timestamp default current_timestamp,
  foreign key (ven_id) references vens(ven_id) on delete cascade
);

-- 4) オプト応答
create table event_opt_responses (
  ven_id varchar(255),
  event_id varchar(255),
  opt_type varchar(20) not null,  -- 'optIn' | 'optOut'
  responded_at timestamp not null default current_timestamp,
  primary key (ven_id, event_id),
  foreign key (ven_id) references vens(ven_id) on delete cascade,
  foreign key (event_id) references events(event_id) on delete cascade
);

-- 5) レポート（メタ）
create table report_streams (
  ven_id varchar(255),
  report_specifier_id varchar(255) not null,
  r_id varchar(255) not null,
  measurement varchar(255),
  unit varchar(50),
  -- MySQLには interval 型がないので文字列で代替
  min_sampling_interval varchar(50),
  max_sampling_interval varchar(50),
  requested_sampling_interval varchar(50),
  resource_id varchar(255),
  report_name varchar(255),
  report_type varchar(255),
  reading_type varchar(255),
  primary key (ven_id, r_id),
  foreign key (ven_id) references vens(ven_id) on delete cascade
);

create table report_requests (
  ven_id varchar(255),
  r_id varchar(255),
  report_request_id varchar(255),
  active boolean default true,
  primary key (ven_id, r_id),
  foreign key (ven_id) references vens(ven_id) on delete cascade
);

-- 6) レポート（値）
create table report_values (
  ven_id varchar(255),
  r_id varchar(255),
  resource_id varchar(255),
  measurement varchar(255),
  report_id varchar(255),
  ts timestamp not null,
  value double not null,
  primary key (ven_id, r_id, ts),
  foreign key (ven_id) references vens(ven_id) on delete cascade
);
