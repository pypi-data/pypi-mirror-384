/*
To avoid old versions which are not compatible with newer to run
*/

ALTER TABLE {schema}.{prefix}stopper 
	ADD COLUMN paused INT NOT NULL DEFAULT 0
;
comment on column {schema}.{prefix}stopper.paused is '0=running, 1=paused';
comment on column {schema}.{prefix}stopper.allowed_version is 'if app has smaller ver seq number then cannot run, if bigger then update is needed'; 
