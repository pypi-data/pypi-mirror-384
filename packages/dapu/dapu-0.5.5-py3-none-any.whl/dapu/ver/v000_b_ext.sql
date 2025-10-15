ALLOW EXTENSIONS
- overal good
- extremely need (depends on you data)

If extension belongs into postgre regular package and marked as trusted
you can put create extension commands into custom definitions project for that target database

Others must be turned on using superuser (postgres) connected to target database
Including postgis (for spatial calculations, if your source data has spatial info, like coordinates)


-- IF spactial computation is needed (superuser needed)
CREATE EXTENSION IF NOT EXISTS postgis SCHEMA public;

-- trusted extensions:

-- if your data model is "dynamic" (3 column model: x axis, y axis, text data-value) and you need produce wide fixed tables (for BI tools)
-- tablefuncs (like crosstab()) are must quicker then regular complicated select-commands you write yourself 
CREATE EXTENSION IF NOT EXISTS tablefunc SCHEMA public;

-- hierarhical key model (not very common)
CREATE EXTENSION IF NOT EXISTS ltree SCHEMA public;


-- those next are already allowed because they are needed internally:
-- CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA public;
-- CREATE EXTENSION IF NOT EXISTS hstore SCHEMA public;
