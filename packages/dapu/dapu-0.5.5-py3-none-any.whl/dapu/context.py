from loguru import logger
import uuid
import os
from typing import Any
from dbpoint.hub import Hub
from dbpoint.datacapsule import DataCapsule

from dapu.textops import yaml_string_to_dict
from dapu.fileops import read_content_of_file, read_content_of_package_file
from dapu.perks import prepare_schema_name
from dapu.jobstatus import JobStatus

class DapuContext():
    """
    One central class which have one instance what can be given as starting point to all next Dapu-sh components
    (Workers inits Job and Job inits Manager, using context, context values are calculated in very first process in sequence)
    """
    def __init__(self, work_dir: str, hub: Hub) -> None:

        self.work_dir: str = work_dir # target directory (=src in source code, see "layout"), must be initialized
        self.tags: list[str] = [] # clear known arguments (eg. debug)
        self.more_args: list = [] # and other unclear arguments
        self.LOG_LEVEL : int = 20 # don't use here enums directly from logging (cycle will occur!)

        # Critical version: myversion vs meta.stopper.allowed_version
        self.MYVERSION = 2 # int, increment it every time if needed to prevent previous code to start any more

        self.CONF_SUB_DIR: str = 'conf' # fixed! this folder may have conf.yaml for overriding default hard-coded here
        self.CONF_FILE_NAME: str = 'conf.yaml' # if not existing defaults are used (application level fine tuning)

        self.PACKAGE_NAME : str = 'dapu' # for dynamic loading
        self.PACKAGE_VER_SUB_DIR: str = 'ver' # has meaning of "submodule" under module above, keeps core versioning files

        self.PROJECT_VER_SUB_DIR: str = 'ver' # sub dir for custom versioning 
        self.CHANGES_INDEX_FILE_NAME = 'changes.yaml' # same name for both core and custom versioning
        self.TABLE_VER_SUB_DIR: str = 'ver' # for target tables versioning (last part in path /mytarget/ver), here no index file (just numbers)

        self.ROUTES_SUB_DIR: str = 'routes' # for target tables definitions (last part in path mytarget/routes)
        self.ROUTE_FILE_NAME = 'route.yaml' # inside dir directly under pull (mytarget/pull/from_asjur5/route.yaml)

        self.APP_NAME : str = 'dapu' # for logging and temp dir under system-wide temp dir (don't use spaces, don't live complicated life)

        self.TARGET_ALIAS: str = 'target' # main connection name/reference (to database where meta tables reside)
        self.DAPU_SCHEMA = 'meta' # the latest idea: lets call schema this way, just "meta"
        self.DAPU_PREFIX = '' # and lets prefix all tables in above mentioned schema this way (no prefix)

        self.profiles: dict = {} # mostly: dict[str, dict] (dict of dicts)
        self.hub: Hub = hub
        self.agents: dict[str, dict] = {} # agents meta will be loaded on first call of get_agents
        self.agents_loaded = False
        self.remotelog_prepared = False

        # Cleaner:
        self.DELETE_LOGS_OLDER_THEN: str = "2 months"
        self.DELETE_TRACE_LOGS_OLDER_THEN: str = "15 days"
        self.DELETE_AGENDA_OLDER_THEN: str = "14 months" # PROD keskkonnas soovituslik vähemalt aasta, nt 14 months

        # Registrar:
        self.FILENAME_DEFINITION_FILE: str = 'haulwork.yaml' # NB! lowercase!!
        self.FILENAME_FOR_DELETION = 'tasks_to_delete.txt' # file inside conf (mytarget/conf/tasks_to_delete.txt)
        
        # Manager
        self.FAILURE_LIMIT : int = 3
        self.DEFAULT_MANAGER_INTERVAL: str = '4 hours'
        self.DEFAULT_KEEP_GOING_INTERVAL: str = '5 hours' # '2 minutes' # '2 days' # valid PG interval, 

        # Worker
        self.worker_id : int | None = None
        self.WORKER_NO_NEW_HAUL_AFTER_MINUTES: int = 27
        self.AGENTS_INDEX_FILE_NAME = 'agents.yaml' # in root of dapu, in the target dir (work_dir) if custom are needed

        self.my_shift = (uuid.getnode() % 14)
        #logger.debug("Lets override configuration")
        self.override_configuration() # overriding, customization
        self.prepare_remotelog() # if env vars so, add once additional log sink (graylog)
        self.prepare_notifier()
        logger.info(f"Metadata is kept in {self.DAPU_SCHEMA}.{self.DAPU_PREFIX}...")
        
    def override_configuration(self) -> None:
        """
        If conf subfolder has conf.yaml file, let read values from where and override instance variables here
        """
        conf_file_full_name: str = self.full_name_from_conf(self.CONF_FILE_NAME) or ""
        if not conf_file_full_name:
            logger.debug("No configuration file available, conf.yaml")
            return 
        logger.debug(f"looking for conf in file {conf_file_full_name}")
        content = read_content_of_file(conf_file_full_name)
        if not content:
            logger.debug(f"No content in configuration file {conf_file_full_name}")
            return # no content, no problem (both empty content and missing of file are reasons to keep hard-coded conf) 
        reconf: dict = yaml_string_to_dict(content) or {}
        if not reconf:
            logger.warning(f"No content as dict in configuration file {conf_file_full_name}")
            return
        # TODO / FIXME make it more dynamic (but static is more secure)
        # from dict key to assign self var with same name, if key missing use original value
        # TODO / FIXME validate somehow
        self.APP_NAME = reconf.get('APP_NAME', self.APP_NAME)
        self.DAPU_SCHEMA = reconf.get('DAPU_SCHEMA', self.DAPU_SCHEMA)
        self.DAPU_PREFIX = reconf.get('DAPU_PREFIX', self.DAPU_PREFIX)
        self.FILENAME_FOR_DELETION = reconf.get('FILENAME_FOR_DELETION', self.FILENAME_FOR_DELETION)
        self.FILENAME_DEFINITION_FILE = reconf.get('FILENAME_DEFINITION_FILE', self.FILENAME_DEFINITION_FILE)
        self.FAILURE_LIMIT = reconf.get('FAILURE_LIMIT', self.FAILURE_LIMIT)
        self.DEFAULT_MANAGER_INTERVAL = reconf.get('DEFAULT_MANAGER_INTERVAL', self.DEFAULT_MANAGER_INTERVAL)
        self.DEFAULT_KEEP_GOING_INTERVAL = reconf.get('DEFAULT_KEEP_GOING_INTERVAL', self.DEFAULT_KEEP_GOING_INTERVAL)
        
    def get_agent_definition(self, agent_alias: str) -> dict | None:
        """
        For dynamical load of module which will do action we need all allowed packages/modules defined.  
        We trust our own modules (built-in dapu.agents.agent_...) and may-be some external.
        """
        if not agent_alias:
            return None
        if not self.agents_loaded:
            self.load_agents_index()
        agent: dict | None = self.agents.get(agent_alias) # või None
        return agent

    def load_agents_index(self):
        """
        If agents definitions (alias -> package & module) are not loaded yet, lets do it.
        Definitions can be locally built in or current loading project ones.
        """
        core_agents: dict = yaml_string_to_dict(read_content_of_package_file(self.PACKAGE_NAME, self.AGENTS_INDEX_FILE_NAME)) or {}
        custom_agents = {}
        try:
            with open(self.full_name_from_conf(self.AGENTS_INDEX_FILE_NAME), 'r', encoding='utf-8') as file:
                content = file.read()
            custom_agents = yaml_string_to_dict(content) or {}
        except Exception as e1:
            pass # custom agents listing file don't need to exists
        self.agents = core_agents | custom_agents # | needs 3.9+
        self.agents_loaded = True
        
    def run(self, alias: str, sql: str | DataCapsule, do_return: bool = True) -> DataCapsule:
        """ Wrapper """
        if isinstance(sql, str):
            capsule = DataCapsule(sql)
        else:
            capsule = sql
        if do_return is not None and not do_return:
            capsule.set_flag("do_return", False)
        if "verbose" in self.tags:
            capsule.set_flag("verbose", True)
            logger.debug("VERBOSE SQL")
        return self.hub.run(alias, capsule)

    def target(self, sql: str | DataCapsule, do_return: bool = True) -> DataCapsule:
        """ Wrapper """
        return self.run(self.TARGET_ALIAS, sql, do_return)
    
    def disconnect_target(self):
        """ Wrapper """
        self.hub.disconnect(self.TARGET_ALIAS)

    def disconnect_all(self):
        """ Wrapper """
        self.hub.disconnect_all()

    def disconnect_alias(self, profile_name: str):
        """ Wrapper """
        self.hub.disconnect(profile_name)

    def full_name_from_root(self, inner_part: str | list[str]):
        return self._full_name(inner_part)
    
    def full_name_from_pull(self, inner_part: str | list[str]):
        """ Project level routes root, usually mytarget/routes (old way: mytarget/pull) """
        if isinstance(inner_part, str):
            inner_part = [inner_part]
        return self._full_name([self.ROUTES_SUB_DIR, *inner_part])
    
    def full_name_from_ver(self, inner_part: str | list[str]): 
        """ Custom overall versioning, usually mytarget/ver """
        if isinstance(inner_part, str):
            inner_part = [inner_part]
        return self._full_name([self.PROJECT_VER_SUB_DIR, *inner_part])
    
    def full_name_from_conf(self, inner_part: str | list[str]): 
        """ Custom overall conf, usually /conf """
        if isinstance(inner_part, str):
            inner_part = [inner_part]
        return self._full_name([self.CONF_SUB_DIR, *inner_part])

    def _full_name(self, inner_part: str | list[str]) -> str:
        """
        Returns full name of inside file object (dir or file) short name (or list of part components).
        Don't use it directly! Private function ;)
        """
        import os
        if not self.work_dir:
            raise Exception("work_dir don't have value")
        if not inner_part:
            raise Exception("inner part is missing")
        if isinstance(inner_part, str):
            return os.path.join(self.work_dir, inner_part)
        if isinstance(inner_part, list):
            return os.path.join(self.work_dir, *inner_part)
        raise Exception(f"inner part type is wrong {type(inner_part)}")

    #@lru_cache(maxsize=120, typed=False) -> CacheInfo(hits=24, misses=19, maxsize=120, currsize=19) 
    # not very helpful: there are max 7 different arguments (table_short_name), why 19 misses?
    #@cache # now it may have point to use cache (now = after remaking this as context own function)
    def find_registry_table_full_name(self, table_short_name: str) -> str:
        #logger.debug(f"Usage of {table_short_name}")
        """
        from short name makes full table name according to system global setup (compatibility with historical ideas)
        "agenda" -> "meta.bis_agenda" or "bis.agenda" or "bis.bis_agenda"
        """
        schema_part = ''
        if self.DAPU_SCHEMA is not None and self.DAPU_SCHEMA.strip() > '': # if schema name is present
            schema_part = self.DAPU_SCHEMA.strip() + '.' # dot at end as seperator between schema name and table name      
        table_prefix = ''
        if self.DAPU_PREFIX is not None and self.DAPU_PREFIX.strip() > '':
            table_prefix = self.DAPU_PREFIX.strip()
        
        return ('').join([schema_part, table_prefix, table_short_name])
    
    def get_profile(self, profile_name: str) -> dict:
        return self.profiles.get(profile_name, {})
    
    def set_profiles(self, profiles_text: str):
        self.profiles: dict = yaml_string_to_dict(profiles_text) or {}

    def set_tags(self, tags: list):
        self.tags = tags or []
        self.more_args = tags[2:] or [] # backward compatibility
   
    def get_task_hash_from_registry(self, task_id: str) -> str:
        """
        Get the latest saved hash of source data (in case of file it is hash of file) 
        """
        registry = self.find_registry_table_full_name("registry")
        
        sql_hash = f"""SELECT r.source_hash FROM {registry} r WHERE task_id = '{task_id}'"""
        result_set = self.target(sql_hash)
        return result_set[0][0] # hash as string
       
    def save_task_hash_to_registry(self, task_id: str, new_hash: str) -> None:
        """
        Updates source_hash for task_id
        """
        registry = self.find_registry_table_full_name("registry")
        sql_hash = f"""UPDATE {registry} SET source_hash = '{new_hash}' WHERE task_id = '{task_id}'"""
        self.target(sql_hash, False)
    
    def get_task_sync_until_ts(self, task_id: str, precision: int = 6) -> str:
        """
        Returns tasks sync time (as ISO date string with seconds).
        Use of precision over 0 demands PostgreSQL version 13 // in PG12 were possible '000' as 'MS' and '000000' as 'US'
        """
        registry = self.find_registry_table_full_name("registry")
        
        expression_missing_pg: str = '1990-01-01 00:00:00' # .000000
        format_to_char = 'YYYY-MM-DD HH24:MI:SS' # .FF6
        if precision >= 1 and precision <= 6:
            expression_missing_pg += '.' + ('0' * precision)
            format_to_char += '.FF' + str(precision) 
        
        sql_last_ts = f"""SELECT to_char(coalesce(synced_until_ts, '{expression_missing_pg}'), '{format_to_char}')
            FROM {registry} WHERE task_id = '{task_id}' """
        result_set = self.target(sql_last_ts)
        return result_set[0][0] # return ISO DATE/TIME as string

    def save_task_sync_until_ts(self, task_id: str, new_ts: str | None, precision: int = 6):
        """
        new_ts must be ISO date, its precision may be higher or lower then parameter precision
        if new_ts is None, then NULL will be set to database
        """
        registry = self.find_registry_table_full_name("registry")
        if new_ts is None:
            time_expression = 'NULL'
        else:
            time_expression = f"'{new_ts}'"
        
        sql_upd = f"UPDATE {registry} SET synced_until_ts = {time_expression} WHERE task_id = '{task_id}'"
        self.target(sql_upd, False)

    def replace_compatibility(self, sql: str, local_replacements : list[tuple] = []) -> str:
        """
        Owner is nice trick here (so each new schema can be created with minimal effort (copy-paste))
        """
        replacements = []
        replacements.append(('{schema}', self.DAPU_SCHEMA))
        replacements.append(('{prefix}', self.DAPU_PREFIX))
        replacements.append(('{owner}', self.hub.get_profile(self.TARGET_ALIAS)['username'])) # after schema create
        for local_replacement in local_replacements: # orvuke tegelt (orphan, never assigned yet)
            replacements.append(local_replacement) # tuple[str, str]
        
        for replacement in replacements:
            sql = sql.replace(replacement[0], replacement[1])
        return sql
    
    def prepare_remotelog(self):
        if not self.remotelog_prepared:
            remote_host = os.getenv("REMOTE_LOG_HOST", "")
            remote_port = int(os.getenv("REMOTE_LOG_PORT", "0"))
            if remote_host and remote_port > 1023:
                if remote_host.endswith("/gelf"):
                    from pygelf import GelfHttpHandler    
                    handler = GelfHttpHandler(host=remote_host, port=remote_port)
                else:
                    from pygelf import GelfUdpHandler
                    handler = GelfUdpHandler(host=remote_host, port=remote_port)
                logger.add(sink=handler, level="DEBUG")
            self.remotelog_prepared = True # even if was empty params


    def prepare_notifier(self): # discord, email etc
        self.notifier = None
        try:
            import apprise
            discord_hook_id = os.getenv("DISCORD_HOOK_ID", "")
            discord_hook_token = os.getenv("DISCORD_HOOK_TOKEN", "")
            if discord_hook_id and discord_hook_token:
                self.notifier = apprise.Apprise()
                self.notifier.add(f"discord://{discord_hook_id}/{discord_hook_token}")
        except Exception as e1:
            logger.error(f"Discord via Apprise problem")
            logger.error(str(e1))

    def notify(self, message: str):
        try:
            if self.notifier is None:
                return
            self.notifier.notify(message, title=f"Dapu ({self.my_shift})")
        except:
            logger.error(f"Notifier problem")

    def signal_pause_switch(self, do_pause: bool):
        needed_status_for_pause = 1 if do_pause else 0
        stopper = self.find_registry_table_full_name('stopper')
        capsule: DataCapsule = DataCapsule(f"UPDATE {stopper} SET paused = {needed_status_for_pause} WHERE paused != {needed_status_for_pause}")
        capsule.set_flag("do_return", False)
        self.target(capsule)
        return True

    def check_pause(self) -> bool:
        """
        Prevents running if global pause is turned ON. Returns booleant in meaning "may continue"
        """
        stopper = self.find_registry_table_full_name('stopper')
        capsule: DataCapsule = DataCapsule(f"SELECT paused FROM {stopper} ORDER BY id DESC LIMIT 1")
        try:
            capsule = self.target(capsule)
            return (not capsule[0][0] == 1) # False if paused=1
        except Exception as e1:
            # error may happen on very first execution then tables are not present yet
            # in this case we just ignore everything and we are sure that in next run it will work
            return True

    def check_stopper(self) -> bool:
        """
        Prevents execution it newer version is unleached. 
        Current version is stored in code (context.MYVERSION) and Last version is store in database (meta.stopper.allowed_version)
        If current is lower then prevent. If current is higher then update database (so old instances in wild can be prevented).
        Can be executed before tables are done, so error in select can be interpreted as missing table and lets continue.
        If table exists we can handle both cases: no rows and one row (if more then last taken, but updated will be all)
        """
        stopper = self.find_registry_table_full_name('stopper')
        sql = f"""SELECT allowed_version FROM {stopper} ORDER BY id DESC LIMIT 1""" # there is one row actually
        try:
            capsule = DataCapsule(sql)
            capsule.set_flag("quiet", True) # to not make noise in logs
            capsule: DataCapsule = self.target(sql)
        except Exception as e1:
            # error may happen on very first execution then tables are not present yet
            # in this case we just ignore everything and we are sure that in next run it will work
            logger.info(f"No need to worry if it is first run (stopper table will be created in version 003)")
            return True
        allowed_version = 0
        no_rows = True
        if capsule.last_action_success and capsule[0]:
            allowed_version = capsule[0][0]
            no_rows = False
        if self.MYVERSION < allowed_version: # cannot execute any more
            logger.info(f"My version is {self.MYVERSION}, allowed version is {allowed_version}")
            return False
        if self.MYVERSION > allowed_version: # update database with my number
            if no_rows:
                sql_upd = f"""INSERT INTO {stopper} (allowed_version) VALUES ({self.MYVERSION})"""
            else:
                sql_upd = f"""UPDATE {stopper} SET allowed_version = {self.MYVERSION} WHERE true""" # one record
            self.target(sql_upd, False)
            logger.info(f"Stopper version updated to {self.MYVERSION}")
        return True

    def check_for_schema(self, schema_name: str, create_if_missing: bool = True) -> bool:
        """
        Using Postgre meta-knowledge to ask if schema exists, and creating it if instructed
        Wrong input (dot in name, empty name) results to False. Apostrophes will be thrown away.
        Returns True - if schema exists (already or was created now)
        """
        schema_name = prepare_schema_name(schema_name)
        if schema_name == "":
            return False
        sql_sch = f"SELECT count(*) FROM information_schema.schemata WHERE schema_name = '{schema_name}'"
        capsule: DataCapsule = self.target(sql_sch)
        if capsule[0][0] > 0: # schema exists
            return True
        if create_if_missing: # FIXME creation add-ons are needed probably
            sql_cre = f"""CREATE SCHEMA IF NOT EXISTS {schema_name}""" # FIXME we miss here: alter default priviledges, grant usage etc
            self.target(sql_cre, False) # let it crash if problem (it is really fatal)
            msg = f"Schema '{schema_name}' created"
            logger.info(msg)
            return True
        return False

    def running_jobs(self):
        agenda = self.find_registry_table_full_name('agenda')
        sql_job_busy = f"""SELECT id, created_ts, task_id, worker, last_start_ts, commander, failure_count FROM {agenda} WHERE status = {JobStatus.BUSY.value}"""
        capsule: DataCapsule = self.target(sql_job_busy)
        if capsule:
            logger.info("CURRENTLY RUNNING")
            for row in capsule:
                logger.info(f"{row}")
        else:
            logger.info("NO active runs")
        return capsule

    def waiting_jobs(self):
        agenda = self.find_registry_table_full_name('agenda')
        sql_job_busy = f"""SELECT id, created_ts, task_id, commander, failure_count FROM {agenda} WHERE status = {JobStatus.IDLE.value}"""
        capsule: DataCapsule = self.target(sql_job_busy)
        if capsule:
            logger.info("UPCOMING JOBS")
            for row in capsule:
                logger.info(f"{row}")
        else:
            logger.info("NO waiting jobs")
        return capsule

    def last_jobs(self, amount: int = 5):
        agenda = self.find_registry_table_full_name('agenda')
        sql_job_busy = f"""SELECT id, created_ts, task_id, worker, last_start_ts, last_end_ts FROM {agenda} WHERE status = {JobStatus.DONE.value} ORDER BY last_end_ts DESC LIMIT {amount}"""
        capsule: DataCapsule = self.target(sql_job_busy)
        if capsule:
            logger.info("LATEST DONE")
            for row in capsule:
                logger.info(f"{row}")
        else:
            logger.info("NO done jobs yet")
        return capsule
    