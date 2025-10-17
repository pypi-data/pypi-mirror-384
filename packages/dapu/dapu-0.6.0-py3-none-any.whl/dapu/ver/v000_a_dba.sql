
READ THIS!! These lines are intentionally non-comments so you just cant run this file blindly. 
Using postgres superuser (postgres) connect to master database (postgres) and prepare roles.
In file system level allow access to root groups (or be more precise if inhouse rules are more strict).     


-- Root groups for easy config in pg_hba.conf (use: +humam_access)
-- https://www.postgresql.org/docs/current/auth-pg-hba-conf.html
-- Those groups are only for controlling network access
CREATE ROLE puller_access NOLOGIN;
CREATE ROLE tools_access NOLOGIN; -- CREATE ROLE report_access NOLOGIN;
CREATE ROLE human_access NOLOGIN;

-- subgroups are in control real access to data
CREATE ROLE tools_bitool NOLOGIN IN ROLE tools_access; -- into this group put PowerBI/Tableau/ClickSence as product-wide user (non-human), (and documentation tools)
CREATE ROLE human_developer NOLOGIN IN ROLE human_access; -- into this group put real persons who need access to every piece (to develop solutions for others who use BI tools)  

-- real users !!! give them secure passwords !!!
-- if you plan make many independent target databases, suggestion is to create different admin for each one (like: dapu_finances_admin, dapu_production_admin)
CREATE ROLE dapu_base_admin WITH LOGIN PASSWORD '****' IN ROLE puller_access CREATEDB CREATEROLE; -- very special user, can create and drop, used by our puller application Dapu  
-- CREATE ROLE indrek_dev WITH LOGIN PASSWORD '****' IN ROLE human_developer
-- CREATE ROLE indrek_admin WITH LOGIN PASSWORD '****' IN ROLE human_developer CREATEROLE 
-- GRANT human_developer TO indrek_admin WITH ADMIN 

CREATE DATABASE dapu_base WITH OWNER dapu_base_admin 
	TEMPLATE template0 ENCODING 'utf8' LC_COLLATE 'et_EE.utf8'; 

-- preapare pg_hba.conf
-- and SELECT pg_reload_conf();

-- now, disconnect from postgres master database (postgres) and connect to new database

