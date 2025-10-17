from loguru import logger
import os
import json
from enum import Enum
from dbpoint.datacapsule import DataCapsule, DataRowTuple

from dapu.process import DapuProcess
from dapu.context import DapuContext
from dapu.perks import halt, init_cache_intervals, split_task_id
from dapu.perks import get_dirs_with_definition, load_task_id_list_from_file, convert_to_bool, is_file_inside_git_area, load_yaml, make_replacements, read_sql_from_file
from dapu.jobstatus import JobStatus
from dapu.placeholder import Placeholder
from .fileops import read_content_of_file


def calculate_task_id_from_path(file_path:str) -> str | None:
    r"""
    From given filesystem (real)path last three folders make dot-separated task_id
    /home/guest/mydefs/finance/inner/income/product -> inner.income.product
    c:\code\inner\income\product -> inner.income.product
    
    Path don't need to exists (but usual input is actual path and goal is to calculate task_id from it)
    
    Let's eliminate drive letters on Windows, and starting slash/backslash on all systems 
    """
    
    file_path = os.path.realpath(file_path) # may add c: in beginning (if running on windows)
    
    # lets remove windows drive letter (strong check)
    if os.name == 'nt' and len(file_path) > 1 and file_path[1] == ':':
        # remove drive letter and colon (e.g., "C:\path" -> "\path")
        file_path = file_path[2:] # without first 2 chars
    
    # now eliminate first slahs/backslash 
    file_path = file_path[1:]
    
    parts_of_path = file_path.split(os.path.sep)
    last_three = parts_of_path[-3:]
    
    if len(last_three) < 3:
        return None
    
    return '.'.join(last_three)


def calculate_dir_hash(task_dir: str) -> str:
    import hashlib # md5 uuid jaoks
    dir_hash = ''
    for sub_name in os.listdir(task_dir):
        full_name = os.path.join(task_dir, sub_name)
        if os.path.isdir(full_name):
            file_hash = calculate_dir_hash(full_name)
        else:
            file_hash = 'aaa'
            with open(full_name, "rb") as file_handle: # binaarne avamine, et räsi arvutada (st encoding="utf-8" pole vaja)
                bytes_from_file = file_handle.read() # read file as bytes
            file_hash = hashlib.md5(bytes_from_file).hexdigest()

        dir_hash = dir_hash + file_hash
    # kuna faile võis olla mitmeid ja string tuleb pikk, siis md5-me veelkorra:
    dir_hash = hashlib.md5(dir_hash.encode('utf-8')).hexdigest()
    return dir_hash


class DapuRegistrar(DapuProcess):
    """
    Registers new tasks (by detecting new definition files) to Registry
    Detects changes on existing definitions
    Performs versionings (incl creation) of target tables
    """
    
    def __init__(self, args: list | DapuContext | None) -> None:
        super().__init__(args)
        self.cached_intervals = init_cache_intervals() # since we using PG to validate intervals (PG is the best), we want to minimize count of queries


    def run(self):
        logger.debug(f"Working directory is {self.context.work_dir}")
        counter = self.refresh_registry() # 
        logger.info(f"Count of added or changed tasks is {counter}")
        self.context.disconnect_target() # viisakas, aga kas hädavajalik?
        return counter
    
    
    def check_deletions_and_delete(self):
        """
        If the special file is present in work_dir then delete from registry all task mentioned in file (one line one task)
        And eliminate from Agenda idle Jobs for what Task
        Prefereably we delete this file afterwards to avoid repeating small amount of SQL-s and processing
        But if file is in dev-computer in git-area (not in deploy area), then we keep file 
        """
        inside_git_area = is_file_inside_git_area(self.context.work_dir)
        logger.debug(f'Is work_dir inside GIT area {inside_git_area}')
        please_delete = not inside_git_area
        deletion_marker_file: str = self.context.full_name_from_conf(self.context.FILENAME_FOR_DELETION) or ""
        task_list_to_delete: list[str] = load_task_id_list_from_file(deletion_marker_file, please_delete) or []

        if task_list_to_delete: # kustutame enne, et ei tekiks halbu anomaaliaid (hea anomaalia on failide allesjäämine, halb on registry ebakõla) 
            # teostada baasist/registrist kustutamine (ühe korra pärast levitamist)
            for task_id in task_list_to_delete:
                self.eliminate_idle_from_agenda(task_id)
                self.delete_task_from_registry(task_id)


    def analyze_project_sub_dirs(self) -> list[tuple[str, str]]:
        """
        Analyze work_dir (project folder) subdirs and find those al least 3rd level which have fixed-name definition file in 
        For each potential task returns task_id and summary hash for all files in subdir and below
        """
        task_list_active: list[tuple[str, str]] = []
        
        routes_dir = self.context.full_name_from_pull([])
        
        task_dirs: list[str] | None = get_dirs_with_definition(routes_dir, self.context.FILENAME_DEFINITION_FILE)
        if not task_dirs: # both None and [] must have same effect
            halt(81, "Folders and files with definitions are missing")
            return [] # just for pylance
        
        logger.info(f"Found {len(task_dirs)} possible tasks")
        
        for task_dir in task_dirs:
            task_id = calculate_task_id_from_path(task_dir)
            if task_id is None:
                halt(82, f"Dir {task_dir} is not suitable for task")
                return [] # just for pylance
            
            task_hash = calculate_dir_hash(task_dir)
            task_list_active.append((task_id, task_hash)) # tuple
        
        if len(task_list_active) == 0:
            halt(83, "There was some files but none of them are active") # quite impossible in practical sense....?

        return task_list_active
        
    
    def refresh_registry(self) -> int:
        """
        Delete, add and change tasks in Registry by scanning files of installation in local file system
        """
        counter: int = 0
        
        self.check_deletions_and_delete() # Mechanism for unregister by list in file commited by definitions developer 
        task_list_active: list[tuple[str, str]] = self.analyze_project_sub_dirs() # may halt
        
        for task_id_with_hash in task_list_active:
            # jagame tühikuga pooleks
            task_id, task_hash = task_id_with_hash # tuple unpack to vars 
            tester, _, _ = split_task_id(task_id) # first time we see task_id, lets validate using split, all parts are None if nonvalid, testing one is enough 
            if tester is None:
                logger.error(f"Skiping non-valid task ID {task_id}")
                continue
            
            try:
                counter += self.refresh_registry_with_task(task_id, task_hash) # +0 or +1 or exception
            except Exception as e1:
                logger.error(f"Task {task_id} has problems, skiping - {e1}")
                print(e1)
        return counter # number of added or changed tasks in Registry
    

    def validate_interval(self, string_expression: str) -> bool:
        """
        Is string expression legal/valid for postgres interval data type (eg, '25 hours', '1 days')
        Final validation is made using Postgre with main database connection (through context)
        """        
        if string_expression in self.cached_intervals:
            return self.cached_intervals[string_expression] # return ealier validation result
        if "'" in string_expression: # clear that nonvalid
            result_set = []
        else:
            try:
                result_set = self.context.target(f"SELECT '{string_expression}'::interval")
            except Exception as e1:
                result_set = []
        self.cached_intervals[string_expression] = True if result_set else False # assign for next validations
        return self.cached_intervals[string_expression] # return new result


    def pull_task_data(self, task_id: str) -> DataRowTuple:
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""SELECT coalesce(def_hash, ''), coalesce(table_version, 0) 
            FROM {registry} r 
            WHERE r.task_id = '{task_id}'"""
        capsule: DataCapsule = DataCapsule(sql)
        #capsule.set_flag("verbose", True)
        capsule = self.context.target(capsule)
        if len(capsule) == 0:
            return DataRowTuple() # (None, '', 0))
        return capsule[0] # first row (type of DataRowTuple)


    @DapuProcess.task_id_eventlog(flag='REGISTER')
    def add_task_to_registry(self, task_id: str) -> DataCapsule: 
        """
        Inserts row into registry. All fields are database defaults. Some of them are updated later (run conditions) from def.
        called by refresh_registry_with_task(), on problem must return None
        """
        logger.info(f'New task detected {task_id}')
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""INSERT INTO {registry} (task_id) VALUES ('{task_id}') RETURNING (task_id)"""
        try:
            capsule: DataCapsule = self.context.target(sql)
            return capsule
        except Exception as e1:
            logger.error(f"during registering {e1}")
            return DataCapsule()


    def check_for_route(self, route_code, create_if_missing: bool = True) -> bool:
        """
        Checks if folder for route is present
        Checks if route is registered on route table 
        """
        route_dir = self.find_route_dir_path(route_code, must_exists=True)
        if route_dir is None:
            logger.error(f"Route {route_code} don't have own folder")
            return False
        
        route = self.context.find_registry_table_full_name('route')
        sql = f"""SELECT 1 FROM {route} WHERE code = '{route_code}' LIMIT 1"""
        result_set = self.context.target(sql)
        if len(result_set) == 0:
            logger.warning(f"Route '{route_code}' doesn't exists in table {route}")
            if create_if_missing:
                return self.add_route(route_code, route_dir)
            else:
                return False
        else:
            return True
    
    
    def add_route(self, route_code: str, route_dir: str) -> bool:
        # tuvastada kaustast route info
        route = self.context.find_registry_table_full_name('route')
        route_def = {}
        route_def = load_yaml(route_dir, self.context.ROUTE_FILE_NAME, {})
        if not route_def:
            logger.error(f"New route '{route_code}' doesn't have route.yaml file with data to add to table")
            return False
        
        route_name = route_def.get('name', f"Unnamed {route_code}").replace("'", "-") # for human, so ok
        route_type = route_def.get('type', 'sql').replace("'", "") # default let be sql
        route_alias = route_def.get('alias', '').replace("'", "")
        if not self.check_route_alias(route_type, route_alias):
            return False
        
        sql = f"""INSERT INTO {route} (code, name, type, alias) 
            VALUES ('{route_code}', '{route_name}', '{route_type}', '{route_alias}')
            """
        capsule: DataCapsule = self.context.target(sql, False)
        if capsule.last_action_success:
            logger.info(f"Route '{route_code}' is now registered")
            return True
        logger.error(f"Route '{route_code}' cannot be registered")
        raise Exception(f"Route '{route_code}' cannot be registered")


    def check_route_alias(self, route_type: str, route_alias: str):
        if route_alias: # if alias is present, then lets check if it is present as well in main conf (by type)
            if route_type == 'sql':
                if not self.context.hub.is_profile_exists(route_alias):
                    logger.error(f"SQL route alias {route_alias} is not amoungst known connection profiles")
                    return False
            if route_type == 'file':
                ...
            if route_type == 'http':
                ... 
        return True
    
    
    def task_max_ver_file(self, task_id: str) -> int:
        task_dir = self.find_task_dir_path(task_id)
        if task_dir is None:
            return 0
        dir_path = os.path.join(task_dir, self.context.TABLE_VER_SUB_DIR) # subdir ver, with files 001.sql, 002.sql etc
        max_file_nr = 0

        # subdir may not exists, ok
        if not os.path.exists(dir_path):
            return 0

        for sub_name in os.listdir(dir_path):   # file on lühike nimi (st ilma pathita)
            #print(f'Found {sub_name} in {dir_path}, checking')
            if sub_name.endswith('.sql'):
                file_nr_str = (sub_name.split('.')[0]).split('_')[0] # "003_markus.sql" => 003
                if file_nr_str.isdigit(): # 003 is string which has digits (all chars are digits)
                    file_nr = int(file_nr_str)  # 003 => 3
                    max_file_nr = file_nr if file_nr > max_file_nr else max_file_nr
        return max_file_nr


    @DapuProcess.task_id_eventlog(flag='OUTAGENDA')
    def eliminate_idle_from_agenda(self, task_id): # same fucntion is in Manager, can we do some refactoring..
        if not task_id.strip(): 
            return []
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""DELETE FROM {agenda} WHERE task_id = '{task_id}' AND status = {JobStatus.IDLE.value} RETURNING task_id"""
        return self.context.target(sql)
    

    def lock_for_versioning(self, task_id):
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""UPDATE {registry} SET needs_versioning = TRUE WHERE task_id = '{task_id}' """
        #self.context.target(sql, False)
        capsule = DataCapsule(sql)
        capsule.set_return(False)
        self.context.target(capsule)


    def unlock_from_versioning(self, task_id):
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""UPDATE {registry} SET needs_versioning = FALSE WHERE task_id = '{task_id}' """
        self.context.target(sql, False)

        
    def clear_sync_data(self, task_id):
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""UPDATE {registry} 
            SET source_hash = NULL, synced_until_ts = NULL, synced_until_bigint 
            WHERE task_id = '{task_id}' """
        self.context.target(sql, False)

    
    def versioning_had_unsafe_steps(self, safe_steps: list[int], made_steps: list[int]) -> bool:
        # kui kasvõi üks made_steps hulgast ei ole safe_steps hulgas, siis tegu laadimist nulliva versioneerimisega
        # teisisõnu: kas safe_steps sisaldab kõiki praeguse hetke versioonisamme made_steps
        # nt [4,5,7] sisaldab [5]'t, sisaldab [4,5]'t, aga ei sisalda [5,6,7]'t
        return all(item in safe_steps for item in made_steps) # unreadable pythonic solution


    def apply_version(self, task_id, new_ver: int, sql: str) -> bool:
        try:
            self.context.target(sql, False) # apply SQL DDL
        except Exception as e1:
            logger.debug(f"{sql}")
            logger.error(f"{e1}")
            return False
        # save new version number to registry
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""UPDATE {registry} SET table_version = {new_ver} WHERE task_id = '{task_id}' """
        self.context.target(sql, False)
        return True


    def check_and_perform_versioning(self, task_id: str, start_from_version: int, up_to_version: int|None, safe_versions: list[int]) -> bool:
        if up_to_version is None:
            up_to_version = self.task_max_ver_file(task_id) # suurima numbriga ver sees oleva .sql faili number
        
        # vaatame, et ega def ei keela versioneerida nullist (nt kui tabel on registrist maha võetud (old), aga tegelikult olemas)
        # st muster: active -> old (without drop) -> active // st resume
        # sel juhul saab def abil juhtida, et versioneerida alates versioonist (st seda nr mitte, alates 1-st)
        if up_to_version > start_from_version:
            logger.debug(f"{task_id} starts versioning {start_from_version} --> {up_to_version}")
            self.eliminate_idle_from_agenda(task_id) # eemaldada kõik pooleliolevad tööd agendast, et ei juhtuks jamasid
            self.lock_for_versioning(task_id) # märkida registrisse, et vajab versioneerimist (kui nurjub, siis ei panda ka töösse)

            # teostada versioneerimine
            if not self.task_table_upgrade(task_id, start_from_version):
                logger.error(f"Versioning failed {task_id}: {start_from_version} --> {up_to_version}")
                return False

            # kas uute versioonide hulgas olid ainult "kosmeetilised" muudatused (andmete laadimise järge mitte muutvad, nt comment, create index, veerg pikemaks)
            if self.versioning_had_unsafe_steps(safe_versions, list(range(start_from_version + 1, up_to_version + 1))):
                self.clear_sync_data(task_id)
            
            self.unlock_from_versioning(task_id)
        return True
    
    
    def task_table_upgrade(self, task_id: str, start_table_version: int) -> bool:
        _, schema_name, table_name = split_task_id(task_id)
        if schema_name is None:
            logger.error(f"Task ID {task_id} is not correct")
            return False

        logger.debug(f'Upgrade {schema_name}.{table_name} from ver {start_table_version}')
        
        task_dir = self.find_task_dir_path(task_id)
        if not task_dir:
            logger.error(f"Big problem with task_id '{task_id}'")
            return False
        replacements : list[tuple[str | Enum , str]] = [(Placeholder.TARGET_SCHEMA, f'{schema_name}'), (Placeholder.TARGET_TABLE, f'{table_name}')]
        
        dir_path = os.path.join(task_dir, self.context.TABLE_VER_SUB_DIR) # subdir ver, with files 001.sql, 002.sql
        file_list = []

        for sub_name in os.listdir(dir_path):   # file on lühike nimi (st ilma pathita)
            logger.debug(f'Found {sub_name} in {dir_path}')
            if sub_name.endswith('.sql'): # (004_something.sql.bak - won't qualify)
                file_nr_str = (sub_name.split('.')[0]).split('_')[0] # "003_markus.sql" => 003
                if file_nr_str.isdigit(): # => file "_something.sql" won't qualify
                    file_nr = int(file_nr_str) # 003 => 3
                    full_name = os.path.join(dir_path, sub_name)
                    if file_nr > start_table_version and os.path.exists(full_name) and os.path.isfile(full_name):
                        file_list.append(sub_name) # long file name

        if len(file_list) == 0:
            return False # error, we assumed somehow that there is need for upgrade and now it is not
        
        # sorteerida (väiksemad ette)
        file_list.sort() # sorteerime failinimesid, aga nimed on meil sellised, et 3 esimest märki on numbrid, seega ok
        new_ver = -2 # kui näeme seda logis, siis on ver-failide loendiga midagi valesti (aga enne väljakutsumist ei olnud)
        for sub_name in file_list:
            new_ver = int( (sub_name.split('.')[0]).split('_')[0])
            sql_file_name = os.path.join(task_dir, self.context.TABLE_VER_SUB_DIR, sub_name)
            logger.info(f'{schema_name}.{table_name} version to {new_ver}')
            sql: str = make_replacements(read_content_of_file(sql_file_name) or "", replacements) or ""
            if not self.apply_version(task_id, new_ver, sql):
                return False
        return True
    
    
    def find_run_info(self, run_info: dict, has_dependancy: bool = False) -> tuple:
        # How and when to run:  validity, defaults    
        keep_pause = run_info.get('keep_pause', '23 hours') # untrusted text
        if not self.validate_interval(keep_pause):
            keep_pause = '23 hours' # if not valid then just use known valid
        
        # If dependant, then missing runtimes means all are False
        # if not dependant, then missing times means all are True
        default = not has_dependancy
        # yaml has bools, but in case of typos some simple fixs
        run_morning = convert_to_bool(run_info.get('morning', default))
        run_workhours = convert_to_bool(run_info.get('workhours', default))
        run_evening = convert_to_bool(run_info.get('evening', default))
        
        # priority must be (small) number
        priority_class = run_info.get('priority', 3)
        if not isinstance(priority_class, int):
            priority_class = 3
        
        return (keep_pause, run_morning, run_workhours, run_evening, priority_class)
    
    @DapuProcess.task_id_eventlog(flag='REREGISTER')
    def update_definition(self, task_id: str, rec_run_info: tuple, definition: str, task_dir = None):
        (keep_pause, run_morning, run_workhours, run_evening, priority_class) = rec_run_info
        surround = [surround_candidate for surround_candidate in ['$xx$', '$xiyaz$', '$sUvaLinE$'] if surround_candidate not in definition] [0]
        surrounded_serialized_definition = f"{surround}{definition}{surround}" # Postgre alternative way
        
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""UPDATE {registry} SET keep_pause = '{keep_pause}'::interval, priority_class = {priority_class}
            , run_morning = {run_morning}, run_workhours = {run_workhours}, run_evening = {run_evening}
            , actions = {surrounded_serialized_definition}
            , last_end_ts = NULL -- et soodustada uue def-i võimalikult kiiret pealeminekut
            WHERE task_id = '{task_id}' 
            RETURNING task_id"""
        return self.context.target(sql)
    
    
    def update_task_hash(self, task_id, task_hash):
        # salvestame uue räsi (taski kausta alluvate kaustade ja failide koguräsi) ja märgime def töötluse lõpuaja  
        registry = self.context.find_registry_table_full_name('registry')
        sql_upd_def_hash = f"""UPDATE {registry} SET def_hash = '{task_hash}', def_ts = clock_timestamp()
            WHERE task_id = '{task_id}'"""
        self.context.target(sql_upd_def_hash, False)
        logger.info(f"Tasks {task_id} definitions hash in registry updated")

    
    def update_dependencies(self, task_id, depend_list: list[str]) -> None:
        # dependecies if mentioned
        masters = [] # result: all masters
        masters.append("'-'") # something non-real, safe (resultless) string so IN ('-') is valid
        registry_depends = self.context.find_registry_table_full_name('registry_depends')
        registry_depends_table = registry_depends.split('.')[-1] # last part is table (not secord part)
        
        for master in depend_list:
            master_route, master_schema, master_table = split_task_id(master)
            if master_route is None or master_schema is None or master_table is None: # on any problems just skip it (TODO: less strict - lets allow 2-part (schema+table) reference too?)
                continue
            master_id = '.'.join([master_route, master_schema, master_table]) # now it is guaranteed lowercase, no apostrophes
            # nb! ülema olemasolu eelkontrolle ei tohi teha, sest vb ülema def fail laetakse nõksu hiljem
            sql_ins_dep = f"""INSERT INTO {registry_depends} (task_id_master, task_id_slave) 
                VALUES ('{master_id}', '{task_id}')
                ON CONFLICT ON CONSTRAINT ak_{registry_depends_table}_4_uniq DO NOTHING"""
            self.context.target(sql_ins_dep, False)
            masters.append(f"'{master_id}'") # for later deletion SQL (check via IN-clause)
        # delete prevoius dependecies which are not mentioned in fresh definition:
        in_expr = ', '.join(masters) 
        sql_del_dep = f"""DELETE FROM {registry_depends} 
            WHERE task_id_slave = '{task_id}' AND task_id_master NOT IN ({in_expr})""" 
        self.context.target(sql_del_dep, False)
        logger.info(f"Dependecies updated for {task_id}")
 
    
    def delete_task_from_registry(self, task_id: str):
        registry = self.context.find_registry_table_full_name('registry')
        result_set = self.context.target(f"DELETE FROM {registry} WHERE task_id = '{task_id}' RETURNING task_id")
        if result_set:
            logger.info(f"Task {task_id} deleted from registry")
        
       
    def refresh_registry_with_task(self, task_id: str, task_hash: str) -> int:
        """
        Checks task_id existence in registry, compares hashes if exists
        """
        logger.debug(f"Lets analyze {task_id}")
        
        task_file: str | None = self.find_task_file_path(task_id, self.context.FILENAME_DEFINITION_FILE) # full path
        if task_file is None: # cannot be, but for separation and fulfillness lets check once more
            logger.error(f"Cannot find file {self.context.FILENAME_DEFINITION_FILE} for task {task_id}")
            return 0

        task_def: dict = load_yaml(None, task_file, empty_as={})
        if not task_def:
            logger.error(f"Definition file {task_file} is empty")
            return 0
        
        status: str = task_def.get('status', 'active')
        if status != 'active': # not in ('draft', 'old'):
            logger.debug(f"{task_id} by status {status} don't need to be examined")
            return 0
        
        # maintain task data in registry: add, update, versioning
        reg_table_version: int = 0
        #(row_id, old_hash, reg_table_version) = self.pull_task_data(task_id) # minimal data about task (and existence)
        logger.debug(f"TASK_ID: {task_id}")
        row: DataRowTuple = self.pull_task_data(task_id)
        #logger.debug(row)
        #logger.debug(row.row_exists())
        if not row.row_exists(): #if row_id is None: # Task is not in Registry yet, all checks must be performed
            logger.debug(f"Found new task {task_id} to register")
            if not self.validate_new_task(task_id): # does reason logging inside
                return 0
            if self.add_task_to_registry(task_id) is None:
                logger.error(f"Inserting row for task {task_id} failed") 
                return 0
        else: # Task is in Registry already
            (old_hash, reg_table_version) = row
            if old_hash == task_hash: # and it is unchanged
                return 0
            else: # it has been somehow changed
                logger.debug(f"Existing task {task_id} definition have been changed")
                self.eliminate_idle_from_agenda(task_id) # if was change in files, when immediatelly eliminate from Agenda
        
        logger.debug(f"versioning line")
        # task target table versioning if needed
        start_from_version: int = task_def.get('upgrade_after', reg_table_version) # if dev wants jump or repeat
        up_to_version: int | None = task_def.get('upgrade', None) # if dev wants limit upper number (why?)
        safe_versions: list[int] = task_def.get('upgrade_nondata', []) # non-safe => delete all data and start over
        self.check_and_perform_versioning(task_id, start_from_version, up_to_version, safe_versions)
        
        logger.debug('finalizing')
        # finalizing
        has_dependancy = True if 'depends' in task_def else False # does it have dependacies
        run_info = self.find_run_info(task_def.get('run', {}), has_dependancy)
        actions = json.dumps(task_def.get('actions', []))
        self.update_definition(task_id, rec_run_info=run_info, definition=actions)
        self.update_task_hash(task_id, task_hash)
        self.update_dependencies(task_id, depend_list=task_def.get('depends', []))
        return 1

    
    def validate_new_task(self, task_id: str) -> bool:
        """
        If ID is correct (3-part)
        If target schema exists
        If route is registered (and try register using route.yaml if not)
        """
        logger.debug(f"Lets validate {task_id}")
        (route_code, target_schema, _) = split_task_id(task_id)
        if route_code is None or target_schema is None:
            logger.error(f"Cannot add task {task_id} to registry due wrong task_id (must be 3-parted, dot separated)")
            return False

        # check for existence of schema and DON'T create it - creation may need some additional work (access privileges)
        if not self.context.check_for_schema(target_schema, create_if_missing=False):
            logger.error(f"Schema is missing: {target_schema}")
            return False
        
        if not self.check_for_route(route_code, create_if_missing=True):
            logger.error(f"Route {route_code} was missing and we were not able to register it")
            return False
        
        return True
    
