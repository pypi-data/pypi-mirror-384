from loguru import logger
import os
import sys
from typing import Callable, Any

from dbpoint.hub import Hub
from dbpoint.datacapsule import DataCapsule

from dapu.context import DapuContext
from .perks import halt, real_path_from_list, is_interactive, version_string_from_timeint
from .fileops import read_content_of_file, read_content_of_package_file


class DapuProcess:
    """
    All Dapu processes behave somehow similar way 
    """
    
    context: DapuContext # class variable, mostly for our wise decorator 

    def __init__(self, args: list | DapuContext | None):
        """
        Two correct way to initialize: using list of arguments to create Context, and using existing Context to keep it.
        list of arguments:
        1. work_dir
        2. download_dir for downloader
        """
        if args is None: # no args, lets try static (cls) context and fail if none 
            if DapuProcess.context is None:
                halt(3, "Wrong initialization") # wasn't given and we don't have it here neither
                return  # only for pylance
            self.context = DapuProcess.context
            return
        
        if isinstance(args, DapuContext): # reusing context (worker -> job -> manager chain)
            self.context = args
            logger.debug(f"from existing context, work_dir is {self.context.work_dir}")
        elif isinstance(args, list):
            # argument is not DapuContext, so context must be generated, assumably for very first process in chain
            work_dir = real_path_from_list(args, 0) # first argument is working directory
            if work_dir is None:
                halt(3, "No project (work) directory specified")
                return # only for pylance
            profiles_text: str = read_content_of_file(work_dir + "/conf/sql.yaml") or read_content_of_file(work_dir + "/conf/profiles.yaml") or "" # FIXME make it configurable...
            self.sql_drivers_text: str = read_content_of_package_file("dapu", "drivers.yaml") or "" # known SQL drivers from package
            added_and_overloaded_drivers: str = read_content_of_file(work_dir + "/conf/drivers.yaml") or ""
            self.sql_drivers_text += "\n" + added_and_overloaded_drivers  # FIXME kerge mure -- mis siis kui erinevadfailid pole sama taandega?
            # FIXME lisada /conf/driver.yaml lugemine, et nt dapu-dev1 saaks üle kirjutada ja lisada omad vajalikud (vb väljaspoolt dapu't)
            # FIXME otsustada, kas profiles on ainult sql või ka muu, nt file-tüüpi või api-tüüpi --> JAH?
            hub = Hub(profiles_text, self.sql_drivers_text) # dbpoint gets all sql-type profiles / all profiles (who cares)
            self.context = DapuContext(work_dir, hub)
            profiles_text += "\n" + (read_content_of_file(work_dir + "/conf/file.yaml") or "") # FIXME kerge mure -- mis siis kui erinevadfailid pole sama taandega?
            self.context.set_profiles(profiles_text) # text -> dict
            self.context.set_tags(args[1:] if len(args) > 1 and args[1] is not None else [])
            self.context.prepare_notifier() # rare messages only (expensive logging)
            if not self.context.check_stopper():
                halt(5, "Cannot run any more (newer version of me is present)")
            if not self.context.check_pause():
                halt(6, "Cannot run now, paused")
            logger.debug(f"from list, work_dir is {self.context.work_dir}")
        else:
            halt(4, "Very wrong initialization")
            return
        DapuProcess.context = self.context # lets remember this instance context as static context (needed for decorator)


    def notify(self, message: str):
        try:
            self.context.notify(message)
        except:
            logger.error(f"Notifier problem, cannot notify, read the logs instead")

    
    def find_task_dir_path(self, task_id: str, must_exists: bool=False) -> str | None:
        """
        Full path from task_id (gives 3 directories) and self.context root path (work_dir)
        """
        #logger.debug(f"TASK {task_id}")
        if not self.context:
            return None
        if not task_id:
            logger.error(f"Empty task_id {task_id}")
            return None
        if not self.context or self.context.work_dir is None:
            logger.error(f"Context work_dir is missing for task {task_id}")
            return None
        path_way: list = task_id.split('.')
        if len(path_way) < 3:
            logger.error(f"Too short task_id {task_id}")
            return None
        path: str = self.context.full_name_from_pull(path_way) or ""
        if must_exists and not os.path.exists(path):
            logger.error(f"Path {path} for task '{task_id}' not exists in local file system")
            return None
        return path
    

    def find_task_file_path(self, task_id: str, file_in_task: str, must_exists:bool=False) -> str | None:
        """
        Very similar to prev, but the name carries difference
        """
        #logger.debug(f"TASK {task_id}, FILE {file_in_task}")
        if not self.context:
            return None
        if not task_id:
            logger.error(f"Empty task_id {task_id}")
            return None
        if not file_in_task:
            logger.error(f"Empty file_in_task {file_in_task} fot {task_id}")
            return None
        if self.context.work_dir is None:
            logger.error(f"Context work_dir is missing for {file_in_task}")
            return None
        path_way: list = task_id.split('.')
        path_way.append(file_in_task)
        if len(path_way) < 4:
            logger.error(f"Too short task_id {task_id} OR missing file")
            return None
        path: str = self.context.full_name_from_pull(path_way) or ""
        if must_exists and not os.path.exists(path):
            return None
        return path


    def find_route_dir_path(self, route_code: str, must_exists:bool=False) -> str |None:
        # joins together working directory and route code assuming that latter is subfolder
        # returns None on errors      
        if not self.context:
            return None
        if not route_code:
            logger.error(f"Empty route_code {route_code}")
            return None
        if self.context.work_dir is None:
            logger.error(f"Context work_dir is missing for route {route_code}")
            return None
        path: str = self.context.full_name_from_pull(route_code) or ""
        if must_exists and not os.path.exists(path):
            logger.error(f"Path {path} for route '{route_code}' not exists in local file system")
            return None
        return path


    def get_database_time(self, precise_time: bool=True):
        """
        Time in target database as ISO string. 
        Non-precise time is transaction start time (current_timestamp).
        """
        if not self.context:
            return None
        if precise_time:
            sql = "SELECT clock_timestamp()" # Very current time (inside transaction)
        else:
            sql = "SELECT current_timestamp" # Transaction beginning time
        result_set = self.context.target(sql)
        if result_set:
            return result_set[0][0] # ISO string
        return None
    

    def connect_main(self):
        """
        Due connection is always automatic, for validation you must run some safe SQL Select
        """
        if self.get_database_time(False) is None:
            raise Exception("Connection validation failed")


    def disconnect_main(self):
        if self.context:
            self.context.disconnect_target()
    
    
    def disconnect_all(self):
        if self.context:
            self.context.disconnect_all()
        

    def version(self, do_log=True, do_print=False) -> str:
        if is_interactive():
            ver_info = 'noname x.x.x'
        else:
            # FIXME järgmine rida ei tööta kui on nt jupyter vms interpreeter
            path = str(sys.modules[self.__module__].__file__) # tegeliku alamklassi failinimi
            name = os.path.basename(path).split(os.path.sep)[-1]
            ver = version_string_from_timeint(os.path.getmtime(path)) # local time (good enough)
            ver_info = f"{name} {ver}"
        if do_print:
            print(ver_info)
        if do_log:
            logger.info(ver_info)
        return ver_info

    @classmethod
    def task_id_eventlog(cls, flag: str, content: str|None = None) -> Callable: # decorator! very special!
        """
        Decorator will insert worker_log record with desired flag. And return INT (number of rows got).
        Use decorator for function which returns result set (list on tuples) where 1st in tuple is task_id.
        Uses cls.context - so it must remain as class variable (somehow duplicating instance variable)
        """
        # if cls.context is None:
        #     def nonsense(func: Callable[..., list[tuple]]) -> Callable:
        #         def wrapper(*args: Any, **kwargs: Any) -> int |None:
        #             return None
        #         return wrapper
        #     return nonsense
        
        flag = flag.upper().replace("'", "").strip()
        content_literal = "NULL"
        if content is not None:
            content = content.replace("'", "").strip()
            content_literal = f"'{content}'"

        def inner(func: Callable[..., list[tuple]]) -> Callable:
            def wrapper(*args: Any, **kwargs: Any) -> int:
                result_set = func(*args, **kwargs) # moving towards DataCapsule here instead of list
                if result_set is None: # error
                    logger.warning("Unexpected None as Datacapsule")
                    return 0
                if not result_set: # empty
                    logger.debug(f"No result for {flag}, by not")
                    return 0
                if len(result_set) == 0:
                    logger.debug(f"No result for {flag}, by len")
                    return 0
                if cls.context is None:
                    logger.warning("Unexpected missing context")
                    return 0
                worker_log = cls.context.find_registry_table_full_name('worker_log')
                try:
                    for changed_row in result_set:
                        changed_row_task_id = changed_row[0]
                        if cls.context.worker_id is None:
                            worker_literal = "NULL"
                        else:
                            worker_literal = cls.context.worker_id
                        sql_reg_log = f"""INSERT INTO {worker_log} (worker, task_id, flag, content) 
                            VALUES ({worker_literal}, '{changed_row_task_id}', '{flag}', {content_literal})"""
                        cls.context.target(sql_reg_log, False)
                    count_of_logged = len(result_set)
                    logger.info(f"{count_of_logged} for {flag}") 
                    return count_of_logged
                except Exception as e1:
                    logger.error(f"during task log {e1}")
                    return 0
            return wrapper
        return inner
