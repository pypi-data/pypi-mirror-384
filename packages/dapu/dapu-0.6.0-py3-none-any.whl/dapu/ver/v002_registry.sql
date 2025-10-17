/*
Tables for controll of pulling data (into meta schema) 
*/

drop table if exists {schema}.{prefix}worker cascade;
drop table if exists {schema}.{prefix}trace cascade;
drop table if exists {schema}.{prefix}reconf cascade;
drop table if exists {schema}.{prefix}registry_depends cascade;
drop table if exists {schema}.{prefix}registry_batch cascade;
drop table if exists {schema}.{prefix}registry cascade;
drop table if exists {schema}.{prefix}agenda cascade;
drop table if exists {schema}.{prefix}route cascade;

-- REGISTRY (TASKS)

CREATE TABLE {schema}.{prefix}route (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, code VARCHAR(50) not null
	, name VARCHAR(200) not null
	, type VARCHAR(50) not null
	, alias VARCHAR(50) not null default ''
	, disabled VARCHAR(200) not null default ''
	, CONSTRAINT pk_{prefix}route PRIMARY KEY (id)
	, CONSTRAINT ak_{prefix}route_4_code UNIQUE (code)
);
comment on table {schema}.{prefix}route is 'Pulling sources information (route-from)';
comment on column {schema}.{prefix}route.code is 'task_id 1st component. NEVER change it!';
comment on column {schema}.{prefix}route.name is 'Short descrition of source';
comment on column {schema}.{prefix}route.type is 'Most general way to start pulling, enum, one of: sql, http, file. Determines conf-file for alias';
comment on column {schema}.{prefix}route.alias is 'Pointer into conf-file';
comment on column {schema}.{prefix}route.disabled is 'Most global locks, lowercase words/tags what is disabled: manager, registrar, worker, morning, workhours, evening';


-- ab objektide nimepikkusepiirang on 63 märki PG-s (50+1+63+1+63 = 179)
CREATE TABLE {schema}.{prefix}registry (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, task_id varchar(200) not null
	, table_version smallint not null default 0
	, needs_versioning boolean default false
	, full_load integer default 0
	, synced_until_ts timestamptz
	, synced_until_bigint BIGINT
	, last_start_ts timestamptz
	, last_end_ts timestamptz
	, keep_pause interval
	, priority_class smallint not null default 5
	, run_morning boolean default true
	, run_workhours boolean default true
	, run_evening boolean default true
	, actions jsonb 
	, def_ts timestamptz default current_timestamp
	, def_hash varchar(200)
	, source_hash varchar(200)
	, disabled varchar(200)
	, CONSTRAINT pk_{prefix}registry PRIMARY KEY (id)
	, CONSTRAINT ak_{prefix}registry_4_task_id UNIQUE (task_id)
);

comment on table {schema}.{prefix}registry is 'Teadaolevad laadimised, mh viimase käivitamise jälgimiseks';
comment on column {schema}.{prefix}registry.task_id is 'laadimisülesande 3-osaline punkt-eraldatud kood';
comment on column {schema}.{prefix}registry.table_version is 'viimane nr sql-e, mis selle taski kohta käivitatud (vrdl alamkaust ver)';
comment on column {schema}.{prefix}registry.needs_versioning is 'kas registreeritud tööüleanne vajab hetkel versioneerimist (kui vajab, siis selliseid ei võteta tegevusse)';
comment on column {schema}.{prefix}registry.full_load is 'kas vaja full laadimine (ja seega ka kõige olemasoleva kustutamine tulemtabelist)';
comment on column {schema}.{prefix}registry.synced_until_bigint is 'kui kasutada mingit BIGINT veergu, mis kajastab viimast muudatust, siis viimase saadud kirje väärtus';
comment on column {schema}.{prefix}registry.synced_until_ts is 'kui kasutada mingit TS veergu, mis kajastab viimast muudatust, siis viimase saadud kirje väärtus';
comment on column {schema}.{prefix}registry.last_start_ts is 'Viimase õnnestunult lõppenud laadimise algus';
comment on column {schema}.{prefix}registry.last_end_ts is 'Viimase õnnestunud laadimise lõpp';
comment on column {schema}.{prefix}registry.keep_pause is 'PG interval avaldis, kui pikka vahet vähemalt pidada tavaoludes (sõltuvuste korral ignoreeritakse)';
comment on column {schema}.{prefix}registry.priority_class is '1 on kõrgeim (kasutada erijuhul), vaikeväärtus 5, sõltuvate korral kasutatakse selle väärtus+1 (jne)';
comment on column {schema}.{prefix}registry.run_morning is 'enne tööaega (0-8)';
comment on column {schema}.{prefix}registry.run_workhours is 'tööajal (u 8-18)';
comment on column {schema}.{prefix}registry.run_evening is 'pärast tööaega (18-24)';
comment on column {schema}.{prefix}registry.actions is 'def-i aktsioonide osa (massiiv) json kujul';
comment on column {schema}.{prefix}registry.def_ts is 'When definition was (re)loaded to here';
comment on column {schema}.{prefix}registry.def_hash is 'viimati siia laetud terve def-i räsi, et tuvastada faili muutust';
comment on column {schema}.{prefix}registry.source_hash is 'lähtebaasi/faili andmete (kõik kirjed) räsi, mida viimati nähti';
comment on column {schema}.{prefix}registry.disabled is 'locks, lowercase words/tags what is disabled: manager (no new jobs to agenda), worker (ignore existing idle job)';



CREATE TABLE {schema}.{prefix}registry_batch (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, task_id varchar(200) not null
	, batch_number integer not null
	, remote_hash varchar(200) 
	, remote_count integer
	, last_ts timestamptz
	, constraint pk_{prefix}registry_batch primary key (id)
	, constraint ak_{prefix}registry_batch_4_uniq UNIQUE (task_id, batch_number)
);
comment on table {schema}.{prefix}registry_batch is 'remote räsi abil juhitud laadimiste jaoks reablokkide (8K rida) räside hoidmiseks';                    


CREATE TABLE {schema}.{prefix}registry_depends (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, task_id_master varchar(200) not null
	, task_id_slave varchar(200) not null
	, constraint pk_{prefix}registry_depends primary key (id)
	, constraint ak_{prefix}registry_depends_4_uniq UNIQUE (task_id_master, task_id_slave)
);
comment on table {schema}.{prefix}registry_depends is 'laadimistulemuste tugevad sõltuvused (masteri laadimine NÕUAB pärast slave laadimist)';                    


CREATE TABLE {schema}.{prefix}reconf (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, task_id varchar(200)
	, task_option varchar(200)
	, task_newvalue varchar(200)
	, CONSTRAINT pk_{prefix}reconf PRIMARY KEY (id)
);
comment on table {schema}.{prefix}reconf is 'Laadimisülesande definitsiooni osaline ülekirjutus (nt keep_pause)';
CREATE INDEX ix_{prefix}reconf_4_task_id_option ON {schema}.{prefix}reconf (task_id, task_option);




-- AGENDA (JOBS)

CREATE TABLE {schema}.{prefix}agenda (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, task_id varchar(200) not null
	, status smallint not null default 0
	, priority smallint not null default 3
	, worker integer 
	, last_start_ts timestamptz
	, last_end_ts timestamptz
	, failure_count smallint default 0
	, commander varchar(200)
	, CONSTRAINT pk_{prefix}agenda PRIMARY KEY (id)
);
 
comment on table  {schema}.{prefix}agenda is 'Korraldused';
comment on column {schema}.{prefix}agenda.task_id is 'task_id (liin.skeem.tabel) mille kohta korraldus';
comment on column {schema}.{prefix}agenda.commander is 'korralduse andja, nt protsessi nimi, isiku nimi';
comment on column {schema}.{prefix}agenda.worker is 'korralduse täitja, protsessi id (tabel ... või seq ...)';
comment on column {schema}.{prefix}agenda.status is '0-teha, 1-tehtud, -1=töös, 21=ettevalmistamisel manageri käes, 30=skipped, look manual';

CREATE INDEX ix_{prefix}agenda_4_time ON {schema}.{prefix}agenda (created_ts);
CREATE INDEX ix_{prefix}agenda_4_task_id ON {schema}.{prefix}agenda (task_id);
CREATE INDEX ix_{prefix}agenda_4_status ON {schema}.{prefix}agenda (status);
CREATE INDEX ix_{prefix}agenda_4_worker ON {schema}.{prefix}agenda (worker);


CREATE TABLE {schema}.{prefix}worker (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, code varchar(100)
	, end_ts timestamptz
	, count_done INT default 0
	, count_fail INT default 0
	, CONSTRAINT pk_{prefix}worker PRIMARY KEY (id)
	, CONSTRAINT ak_{prefix}worker_4_uniq UNIQUE (code) 
);
comment on table  {schema}.{prefix}worker is 'korralduste täideviimisprotsessid';
comment on column {schema}.{prefix}worker.code is 'midagi unikaalset, tähenduseta, nt UUID'; 
comment on column {schema}.{prefix}worker.created_ts is 'kirje loomine on üksiti ka täideviija käivitusaeg';
comment on column {schema}.{prefix}worker.end_ts is 'täideviija lõppaeg';
comment on column {schema}.{prefix}worker.count_done is 'mitu laadimisüleannet õnnestus kenasti täita';
comment on column {schema}.{prefix}worker.count_fail is 'mitu laadimisülesannet nurjus';

CREATE INDEX ix_{prefix}worker_4_time ON {schema}.{prefix}worker (created_ts); -- for delete of old records


CREATE TABLE {schema}.{prefix}worker_log (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, worker integer
	, task_id varchar(200)
	, flag varchar(50)
	, content text
	, CONSTRAINT pk_{prefix}worker_log PRIMARY KEY (id)
);
comment on table {schema}.{prefix}worker_log is 'Whet happened during Worker';
comment on column {schema}.{prefix}worker_log.worker is 'if NULL then manager';
comment on column {schema}.{prefix}worker_log.flag is 'type of happening: START/END (of task_id), ERROR, INFO, AGENDA, REG';
comment on column {schema}.{prefix}worker_log.content is 'freeform additional info';

CREATE INDEX ix_{prefix}worker_log_4_flag ON {schema}.{prefix}worker_log (flag);
CREATE INDEX ix_{prefix}worker_log_4_task_id ON {schema}.{prefix}worker_log (task_id);
CREATE INDEX ix_{prefix}worker_log_4_time ON {schema}.{prefix}worker_log (created_ts); -- for delete of old records




