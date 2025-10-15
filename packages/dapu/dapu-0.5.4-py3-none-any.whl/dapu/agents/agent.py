from loguru import logger
import os
import tempfile
from dapu.context import DapuContext
from dapu.perks import make_replacements, read_sql_from_file
from dapu.placeholder import Placeholder

class AgentGeneric:

    def __init__(self, task_id: str, action: dict, context: DapuContext, route_alias: str):
        self.task_id: str = task_id
        self.action: dict = action
        self.context: DapuContext = context
        self.target_alias: str = self.context.TARGET_ALIAS
        self.route_alias: str = route_alias
        self.temp_dir: str = self.find_temp_dir_path()
        self.task_dir: str|None = self.find_task_dir_path(must_exists=True) # {work_dir}/routes/{route}/{schema}/{table}, where resides haulwork.yaml

    def do_action(self) -> bool:
        """
        Main action. Must be defined in subclass.
        """
        logger.error("You are using too general class or subclass don't have do_action() implemented")
        return False

    def collect_files(self, file_element: str='file') -> list[str]:
        """
        Collects files mentioned in self.action from some tag/element (which values are dual-type: string or list of strings)
        File_element name from YAML definition, usually "file". If agents supports files for different purposes then more clear name
        eg. "create", "imput", "pre_shadow", "post_process"
        Order of files (full path) is as in definition file
        """
        existing_files = [] # return list, may remine empty
        if file_element not in self.action:
            logger.debug(f"No element {file_element} in action definition") # don't need to be error (consumer decides)
            return []
        def_files = []
        def_files_part = self.action.get(file_element, None) # short names
        if def_files_part is not None:
            if isinstance(def_files_part, str):
                def_files.append(def_files_part) # teeme stringist listi
            else:
                if isinstance(def_files_part, list):
                    def_files = def_files_part
        
        for file_name in def_files:
            file_local = os.path.join(self.task_dir or ".", file_name)
            if os.path.exists(file_local):
                existing_files.append(file_local) # full file name
        
        return existing_files # samas järjekoras, mis def failis, aga ainult need, mis eksisteerivad ka

    def apply_files_to_target(self, existing_files: list[str], replacements: list[tuple[str | Placeholder, str]] | None) -> bool:
        """ 
        Name makes very clear that we never apply changes to source-databases, only to one single target-database
        Files are applied in order they are in list.
        List contains full paths of file names.
        Empty and problematic files return False as failure. First error breaks (returns False)
        Replacements is list of tuples (find -> replace)
        '"""
        for file_full_name in existing_files:
            # Read file and make replacements
            sql: str | None = make_replacements(read_sql_from_file(file_full_name), replacements)# does logging
            if sql is None:
                return False # break on first error
            
            try:
                logger.debug(f"Will apply SQL from file {file_full_name}")
                self.context.target(sql, False)
            except Exception as e1:
                logger.error(f"Applying SQL file failed ({file_full_name})")
                #logger.error(f"{sql}") # deep logging or local logging only (too unsafe for remote logging)
                logger.error(e1)
                return False # break on first error
            logger.debug(f"SQL file {file_full_name} applied")
        return True

    def find_temp_dir_path(self) -> str:
        """
        Encapsulated logic for calculating project temp-dir. It may reside inside target-dir (work_dir),
        # os.path.realpath(os.path.join(self.context.work_dir, 'tmp'))
        which is good for maintenance (quickly finding files) and cleaning process (delete all temp files for target),
        but so this may spoil files for local (dev, which is git-based) and git-based deploy, so conflicts may emerge.
        May-be we stick op.system temp directory and create under it app-named (dapu) and target-named dir
        assuming, that actual deploys are with short living hard-disks (like pods). So we don't need to worry much about 
        files remaining there due failures.
        Just remember that our temp-files must be accessible inside one process 
        (we dont need to keep them after failure or any other possible ends)
        but one process may execute many independent Agents, so they all must know path same way.
        Files inside temp dir are named as {task_id}.dat -> one temp dir for target, all dat-files inside
        """
        system_temp_dir = tempfile.gettempdir() # https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir
        target_name = os.path.split(self.context.work_dir)[1] # 2nd element is "tail" - everything after last (back)slash
        # temp_path_for_app = os.path.join(system_temp_dir, self.context.APP_NAME)
        # should we need to create intermediate dir? no, we are using os.makedirs later
        temp_path_for_target = os.path.join(system_temp_dir, self.context.APP_NAME, target_name)
        logger.debug(f"Temporary directory path for target is {temp_path_for_target}, if needed")
        return temp_path_for_target

    def find_task_dir_path(self, must_exists: bool=False) -> str|None:
        """
        Full path from current (internal) task_id (gives 3 directories) and self.context root path (work_dir)
        """
        if not self.task_id:
            logger.error(f"Empty task_id {self.task_id}")
            return None
        if self.context.work_dir is None:
            logger.error(f"Context work_dir is missing for task {self.task_id}")
            return None
        path_way: list = self.task_id.split('.')
        if len(path_way) < 3:
            logger.error(f"Too short task_id {self.task_id}")
            return None
        path: str = self.context.full_name_from_pull(path_way)
        if must_exists and not os.path.exists(path):
            logger.error(f"Path {path} for task '{self.task_id}' not exists in local file system")
            return None
        logger.debug(f"Dir for task {self.task_id} is {path}")
        return path

    def make_temp_dir(self) -> bool:
        """
        Lets make temp dir on first demand using system-wide logic for path
        Returns False only if creation failed silently 
        """
        if os.path.exists(self.temp_dir):
            return True
        # Not exists, lets create
        nix_mode_owner_group: int = 0o770 # Lets the new dir have full rights for process and its group
        #os.mkdir(self.temp_dir, mode=nix_mode_owner_group) -- this one dont make missing dirs
        os.makedirs(self.temp_dir, mode=nix_mode_owner_group, exist_ok=True)
        return os.path.exists(self.temp_dir) # Does it exists after creation
    
    def find_task_temp_file_name(self, extension:str ="dat") -> str | None:
        """
        Temporary file for external data outside of git-dir for task_id that current object already knows
        """
        if self.make_temp_dir(): # checks if temp-dir exists, creates
            if extension is None:
                extension = ''
            file_name = self.task_id + '.' + extension
            return os.path.join(self.temp_dir, file_name)
        else:
            return None
