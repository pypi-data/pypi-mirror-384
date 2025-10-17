/*
To avoid old versions which are not compatible with newer to run
*/

CREATE TABLE {schema}.{prefix}stopper (id serial not null
	, created_ts timestamptz not null default clock_timestamp()
	, allowed_version int not null 
	, CONSTRAINT pk_{prefix}stopper PRIMARY KEY (id)
);
comment on table  {schema}.{prefix}stopper is 'One-record table';
comment on column {schema}.{prefix}stopper.allowed_version is 'if app has smaller ver seq number then cannot ru, if bigger must update'; 

-- starting record, only update it
INSERT INTO {schema}.{prefix}stopper (allowed_version) VALUES (1);
