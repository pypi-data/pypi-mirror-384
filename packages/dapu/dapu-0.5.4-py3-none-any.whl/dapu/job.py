from loguru import logger
import importlib # for using Agents from package dynamically
import json
from types import ModuleType
from dbpoint.datacapsule import DataCapsule

from dapu.process import DapuProcess # decorator
from dapu.jobstatus import JobStatus
from dapu.manager import DapuManager
from dapu.context import DapuContext
from dapu.agents.agent import AgentGeneric
from dapu.perks import clean_log_message

class DapuJob():

    def __init__(self, agenda_id: int, context: DapuContext):
        self.agenda_id: int = agenda_id
        self.context: DapuContext = context
        self.cached_modules: dict[str, ModuleType] = {} # to avoid double load of module
        # NEXT ones will be loaded from database using agenda_id
        self.task_id: str = '' 
        self.actions: list[dict] = []
        self.priority: int = 6 # let default be something bigger
        self.route_alias: str | None = None 
        self.route_type: str | None = None
        self.route_code: str | None = None
        # 
        self.start_str_iso_ts: str | None = None # TS as ISO formatted string
        if not self.load_agenda_details(): # uses self.agenda_id
            raise Exception("Bad initialization of job")
    

    def load_agenda_details(self) -> bool: # runs at end of INIT
        """
        Using self.agenda_id grab job details from database
        """
        agenda: str = self.context.find_registry_table_full_name('agenda')
        route: str = self.context.find_registry_table_full_name('route')
        registry: str = self.context.find_registry_table_full_name('registry')
        
        # safe sql (InS 2024-08-26): agenda_id is garanteed always as py int 
        sql = f"""SELECT a.task_id
                , r.actions as actions
                , a.priority -- to give priority +1 to dependants
                , rt.alias as route_alias 
                , coalesce(rt.type, 'sql') as route_type
                , rt.code as route_code
            FROM {agenda} a
            JOIN {registry} r ON r.task_id = a.task_id 
            JOIN {route} rt ON split_part(a.task_id, '.', 1) = rt.code AND rt.disabled not ilike '%worker%'
            WHERE a.id = {self.agenda_id} """
        
        result_set = self.context.target(sql)
        if result_set:
            (self.task_id, actions_str, self.priority, self.route_alias, self.route_type, self.route_code) = result_set[0]
            self.actions = json.loads(actions_str)
            return True
        else:
            logger.error(f"No job with agenda_id {self.agenda_id} amoungst enabled routes for worker. Ignore if does not repeat.")
            return False


    def run(self) -> bool:
        """
        Entry point: do some logging and housekeeping before and after main point
        and inside execute all actions from task definition for that job
        """
        logger.debug(f"Working directory is {self.context.work_dir}")
        self.mark_job_start() # started marker and database loging
        try:
            was_success = self.task_actions_execute() # MAIN POINT FOR ALL
        except Exception as e1:
            was_success = False
            logger.error(f"{e1}")
    
        self.mark_job_end(was_success) # mark end of job before finding dependant tasks - updates 3 tables

        if was_success:
            self.dependents_to_agenda() # find depending tasks and put them info agenda
            logger.info(f"{self.task_id} succeeded (job={self.agenda_id})")
        return was_success
    
    
    def dependents_to_agenda(self) -> None:
        """
        Using DapuManager for finding dependant tasks and puting them to agenda for next workers
        Manager will be initialized using current context object
        """
        logger.debug(f"Managers sidequest has started")
        dm = DapuManager(self.context)
        dm.add_dependent_tasks_to_agenda(self.task_id, self.priority + 1)
        logger.debug(f"Managers sidequest has ended")
        
        
    def prepare_agent(self, action_def: dict) -> AgentGeneric | None:
        """
        Returns object of type Agent, from very different modules
        """
        command: str = action_def.get('do', "")
        agent_module: ModuleType | None = self.prepare_agent_module(command)
        if agent_module is None:
            return None
        return agent_module.Agent(self.task_id, action_def, self.context, self.route_alias)


    def prepare_agent_module(self, command_name: str) -> ModuleType | None:
        """
        Imports module where agent resides, if not already loaded
        Parameter module_name is alias for module (used as command name in action def)
        Returns module
        Read https://docs.python.org/3/library/importlib.html
        """
        if command_name in self.cached_modules: # if just used (usually runsql)
            return self.cached_modules[command_name]
        
        long_module_name = self.find_module_name(command_name)
        if long_module_name is None or long_module_name.startswith('.') or long_module_name.endswith('.'):
            msg = f"Module for {command_name} is not defined or is not allowed"
            logger.error(msg)
            return None
        try: # lets try to import module
            agent_module: ModuleType = importlib.import_module(long_module_name)
            self.cached_modules[command_name] = agent_module # register found module into dict for reuse
        except Exception as e1:
            msg = f"Cannot import module {long_module_name}"
            logger.error(msg)
            return None
        return agent_module
    
    
    def find_module_name(self, action_alias: str) -> str:
        """
        From action alias calculates somehow module full name.
        Eg. 'runsql' -> 'dapu.agents.agent_runsql'
        Via context uses built in dapu/agent.yaml (way to turn on new agents)
        and possible override/extend for current target: targets/my_target_1/agents.yaml
        """
        trusted_agent: dict = self.context.get_agent_definition(action_alias) or {}
        if not trusted_agent:
            return ""
        if warning := trusted_agent.get('warning', ''): # eg. deprecation warning
            warning = clean_log_message(warning) # cleaning because it comes to us from custom file
            logger.warning(f"{action_alias} says {warning}")
        return f"{trusted_agent['package']}.{trusted_agent['module']}"


    def get_database_time(self, precise_time: bool=True) -> str | None:
        """
        Time in target database as ISO string
        """
        if precise_time:
            sql = "SELECT clock_timestamp()" # Very current time (inside transaction)
        else:
            sql = "SELECT current_timestamp" # Transaction beginning time
        result_set = self.context.target(sql)
        if result_set:
            return result_set[0][0] # ISO string
        return None
    
    
    def task_actions_execute(self) -> bool:
        """
        Job run = execute all actions defined in Task, until first error
        """
        for pos, action_def in enumerate(self.actions, start=1):
            command: str = action_def.get('do', "") # for pre-validation and logging
            if not command:
                logger.warning(f"Action step number {pos} is without command, skiping")
                continue
            logger.debug(f"Action step number {pos} is {command}")
            agent: AgentGeneric | None = self.prepare_agent(action_def)
            if agent is None:
                logger.error(f"Cannot work with {command}")
                return False
            
            try:
                step_was_success = agent.do_action() # MAIN POINT FOR ONE ACTION
                if not step_was_success: # AND action.get('fatal', True) <- idea of extension
                    logger.error(f"Step number {pos} {command} failed")
                    return False  # first error quits
            except Exception as e1:
                logger.exception(f"Agent {command} failed, {e1}")
                return False
        # next
        return True # if no failure (incl "no steps no failure")


    @DapuProcess.task_id_eventlog(flag='START') # returns int
    def mark_job_start(self) -> DataCapsule:
        """
        Mark job in Agenda as started, use update/returning and decorator does rest
        """
        self.start_str_iso_ts = self.get_database_time(True)
        agenda: str = self.context.find_registry_table_full_name('agenda')
        
        sql: str = f"""UPDATE {agenda} 
            SET status = {JobStatus.BUSY.value}
            , worker = {self.context.worker_id}
            , last_start_ts = clock_timestamp()
            WHERE id = {self.agenda_id}
            RETURNING task_id
            """
        return self.context.target(sql)

    
    def mark_job_end(self, was_success: bool) -> None:
        """
        After job is done (successfully of not) do housekeeping
        End Worker record, mark Agenda ended/failed, refresh jobs Task Registry record
        """
        worker: str = self.context.find_registry_table_full_name('worker')
        registry: str = self.context.find_registry_table_full_name('registry')
        
        add_done: int = 1 if was_success else 0
        add_fail: int = 1 - add_done
        
        # workeri (tegelikult mitte) lõpp (järgmine sama workeri task kirjutab üle)
        sql: str = f"""UPDATE {worker} 
            SET end_ts = current_timestamp
            , count_done = coalesce(count_done, 0) + {add_done} 
            , count_fail = coalesce(count_fail, 0) + {add_fail}
            WHERE id = {self.context.worker_id}"""
        self.context.target(sql, False)
        
        # agendas taski lõpu markeerimine
        if was_success:
            self.save_end()
        else: # kui oli viga, siis tagasi ootele panna (manager tegeleb juba nurjumiste arvuga)
            self.save_error()

        # registris taski viimase jooksu markeerimine
        start_time_literal: str = f"'{self.start_str_iso_ts}'"
        if start_time_literal is None: # 0,001% tõenäosus
             start_time_literal = 'NULL'
        sql: str = f"""UPDATE {registry} 
                SET last_start_ts = {start_time_literal}
                , last_end_ts = clock_timestamp()
            WHERE task_id = '{self.task_id}' """
        self.context.target(sql, False)


    @DapuProcess.task_id_eventlog(flag='END') # returns int
    def save_end(self) -> DataCapsule:
        """
        Mark job in Agenda as ended, use update/returning and decorator does rest
        """
        agenda: str = self.context.find_registry_table_full_name('agenda')
        status: int = JobStatus.DONE.value
        sql: str = f"""UPDATE {agenda} 
            SET status = {status}
            , last_end_ts = clock_timestamp()
            WHERE id = {self.agenda_id}
            RETURNING task_id
            """
        return self.context.target(sql)


    @DapuProcess.task_id_eventlog(flag='ERROR') # returns int
    def save_error(self) -> DataCapsule:
        """
        Mark job in Agenda as failed, increment failure count, use update/returning and decorator does rest
        """
        agenda: str = self.context.find_registry_table_full_name('agenda')
        status: int = JobStatus.IDLE.value
        sql: str = f"""UPDATE {agenda} 
            SET status = {status}
            , last_end_ts = NULL
            , failure_count = failure_count + 1
            WHERE id = {self.agenda_id}
            RETURNING task_id
            """
        return self.context.target(sql)
