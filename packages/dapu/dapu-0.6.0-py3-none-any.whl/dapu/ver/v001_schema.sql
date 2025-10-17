-- Data Puller Metadata 
-- Let it be quite public (if feel scared then revoke change rights from bi tools)
-- In very first SQL there must be creation of meta schema and versioning table
-- so, versioning tool can after that already register his first action (this file)

CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA public;
CREATE EXTENSION IF NOT EXISTS hstore SCHEMA public;

CREATE SCHEMA {schema};

COMMENT ON SCHEMA {schema} IS 'Data Puller metadata';

-- GRANT usage ON SCHEMA {schema} TO puller_access; -- loading software
GRANT usage ON SCHEMA {schema} TO tools_bitool; -- any consuming software (un-human)
GRANT usage ON SCHEMA {schema} TO human_developer; -- direct access humans (devs, ad hoc analytists)

-- owner is creator of future objects aka our puller (preferebly current database owner)
ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} GRANT all ON tables 
	TO tools_bitool, human_developer;
ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} GRANT all ON sequences 
	TO tools_bitool, human_developer;
ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} GRANT all ON functions 
	TO tools_bitool, human_developer;
ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} GRANT all ON types 
	TO tools_bitool, human_developer;
 
CREATE TABLE {schema}.{prefix}version (
    id serial not null
    , created_ts timestamptz not null default clock_timestamp()
    , folder_alias varchar(100) not null
    , file_name varchar(200) not null
    , remarks text
    , constraint pk_{prefix}version primary key (id)
    , constraint ak_{prefix}version_4_uniq unique (folder_alias, file_name)
);

COMMENT ON TABLE {schema}.{prefix}version IS 'General versioning, both core (Dapu) and custom';

COMMENT ON COLUMN {schema}.{prefix}version.file_name  IS 'Short file name (.sql), names are meaningless for versioning tool';
COMMENT ON COLUMN {schema}.{prefix}version.folder_alias  IS 'Unique group of files (so core and custom can be keeped in same table)';

-- now versioning tool can insert into last table (error on first reading will be ignored)
