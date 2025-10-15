from loguru import logger
from dbpoint.datacapsule import DataCapsule
from dapu.process import DapuProcess
from dapu.jobstatus import JobStatus
from dapu.perks import lookup_first, sum_column


class DapuManager(DapuProcess):
    """
    From Registry add to Agenda new task instances to execute (by time and by dependencies)  
    """
    
    def run(self) -> int:
        """
        Entry point
        """
        logger.debug(f"Working directory is {self.context.work_dir}")
        
        self.clear_fantoms() # väga pikalt käimasolevad, mis usutavasti enam ei käi (pigem katkesid hoiatamata), märkida jäätunuiks (STALLED)
        self.clear_manager_fantoms() # Manager "power cuts" mark as UNMANAGED   
        self.clear_failed_from_agenda() # those who are failed some amount of times mark as failed
        
        # leida agendasse pandavad
        new_count = self.add_jobs_to_agenda('Manager') # kui tekivad ülesanded, siis kes märkida laadimiskäsu andjaks
        logger.info(f"Added {new_count} jobs into Agenda")
        total_count, busy_count, _ = self.count_jobs_in_agenda()
        add_text = ""
        if busy_count > 0:
            start_ts = self.get_oldest_busy_start_time() # her will be None, if job is meanwhile finished
            add_text = f", {busy_count} is running now, the earliest from {start_ts}"
        logger.info(f"There are {total_count} jobs in Agenda{add_text}") # if busy
        return new_count


    @DapuProcess.task_id_eventlog(flag='OUTAGENDA') # returns int
    def eliminate_idle_from_agenda(self, task_id) -> DataCapsule:  # same function is in Registrar, can we do some refactoring..
        """
        In some reregistering process for task_id eliminate all waiting instances of this task_id from Agenda
        to prevent accidental execution at very same time when versioning is in progress  
        """
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""DELETE FROM {agenda} WHERE task_id = '{task_id}' AND status = {JobStatus.IDLE.value} RETURNING task_id"""
        return self.context.target(sql)


    @DapuProcess.task_id_eventlog(flag='MULTIFAILED') # returns int
    def clear_failed_from_agenda(self) -> DataCapsule:
        """
        Those jobs that are failed more then allowed, mark as clearly as failed (they are idle)
        """
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""UPDATE {agenda} SET status = {JobStatus.FAILED.value}, last_end_ts = clock_timestamp() 
            WHERE failure_count >= {self.context.FAILURE_LIMIT} AND status = {JobStatus.IDLE.value}
            RETURNING task_id"""
        return self.context.target(sql)


    @DapuProcess.task_id_eventlog(flag='FANTOMCLEAN') # returns int
    def clear_fantoms(self) -> DataCapsule:
        """
        If machine dies without any warning then job status stays -1 (in progress)
        They are un-distintables from real in progress jobs... only by time ... and here we catch them
        If some task must run really long then mark it in reconf (keep_going_interval)
        Default is '5 hours' (during this time the task is considered running and no new runs for it)
        NB! Check value from context.py !
        """
        agenda = self.context.find_registry_table_full_name('agenda')
        reconf = self.context.find_registry_table_full_name('reconf')
        sql_san = f'''
            UPDATE {agenda} as a
            SET status = {JobStatus.STALLED.value}
                , failure_count = failure_count + 1
            WHERE a.status = {JobStatus.STARTED.value}
            AND a.last_start_ts < current_timestamp - ( COALESCE( 
                    -- {self.context.DEFAULT_KEEP_GOING_INTERVAL} old unless reconf says something
                    (
                        SELECT rc.task_newvalue
                        FROM {reconf} rc
                        WHERE rc.task_id = a.task_id AND rc.task_option = 'keep_going_interval'
                        ORDER BY rc.id DESC LIMIT 1
                    ),  '{self.context.DEFAULT_KEEP_GOING_INTERVAL}') ::INTERVAL
                )
            RETURNING task_id
        '''
        return self.context.target(sql_san)


    @DapuProcess.task_id_eventlog(flag='MANAGERDEAD') # returns int
    def clear_manager_fantoms(self) -> DataCapsule:
        """
        In case managar got killed then jobs status stays in COMING (=21) and it prevents new jobs too
        Lets eliminate those after 4 hours
        PS! status COMING is not in use any more! Zero-work here.
        """
        agenda = self.context.find_registry_table_full_name('agenda')
        sql_san = f'''
            UPDATE {agenda} as a
            SET status = {JobStatus.STALLED.value}
            WHERE a.status = {JobStatus.COMING.value}
            AND a.created_ts < current_timestamp - ('{self.context.DEFAULT_MANAGER_INTERVAL}')::INTERVAL
            RETURNING task_id
        '''
        return self.context.target(sql_san)


    def add_jobs_to_agenda(self, commander: str='Manager') -> int:
        """
        Find all possible task (by all rules like day divison, interval from last run finish etc) to run with one SQL query
        and add them one-by-one into agenda
        """
        registry = self.context.find_registry_table_full_name('registry')
        agenda = self.context.find_registry_table_full_name('agenda')
        registry_depends = self.context.find_registry_table_full_name('registry_depends')
        reconf = self.context.find_registry_table_full_name('reconf')
        route = self.context.find_registry_table_full_name('route')
     
        # NO overlapings in day divisions (cte_paevaaeg)
        sql_reg = f"""WITH cte_paevaaeg (klass, alates, kuni) AS (
            SELECT 'a', '00:00:00'::time, '07:59:59.999'::time union
            SELECT 'b', '08:00:00'::time, '17:59:59.999'::time union
            SELECT 'c', '18:00:00'::time, '23:59:59.999'::time
        ), cte_praegu (klass, alates, kuni, praegu) AS (
            SELECT klass, alates, kuni, CASE WHEN current_time between alates and kuni THEN true ELSE false END
            FROM cte_paevaaeg
        )
        SELECT t.task_id
        FROM (
            SELECT r.id, r.task_id, r.table_version, r.priority_class
                , coalesce(r.last_end_ts, '2000-01-01 00:00:00'::timestamp) as viimane_lopp
                , coalesce(rcpause.task_newvalue::interval, r.keep_pause, '23 hours'::interval) as vahe_pikkus
                , CASE WHEN coalesce(case when rctime1.task_newvalue is null then null when rctime1.task_newvalue ilike 'yes' then true else false end, r.run_morning) 
                    THEN 'a' ELSE '' END 
                || CASE WHEN coalesce(case when rctime2.task_newvalue is null then null when rctime2.task_newvalue ilike 'yes' then true else false end, r.run_workhours) 
                    THEN 'b' ELSE '' END
                || CASE WHEN coalesce(case when rctime3.task_newvalue is null then null when rctime3.task_newvalue ilike 'yes' then true else false end, r.run_evening) 
                    THEN 'c' ELSE '' END as inday
            FROM {registry} r
            LEFT JOIN {reconf} rcpause ON rcpause.task_id = r.task_id AND rcpause.task_option = 'keep_pause'
            LEFT JOIN {reconf} rctime1 ON rctime1.task_id = r.task_id AND rctime1.task_option = 'morning'
            LEFT JOIN {reconf} rctime2 ON rctime2.task_id = r.task_id AND rctime2.task_option = 'workhours'
            LEFT JOIN {reconf} rctime3 ON rctime3.task_id = r.task_id AND rctime3.task_option = 'evening'
            WHERE NOT r.needs_versioning -- not middle of something
        ) as t
        JOIN cte_praegu p ON t.inday LIKE '%' || p.klass || '%' AND p.praegu -- kas lubatud päevaajas ja kas mõni neist aegadest on praegu
        JOIN {route} r ON t.task_id LIKE r.code || '.%' AND r.disabled NOT ILIKE '%manager%'
        WHERE t.viimane_lopp + t.vahe_pikkus::interval < current_timestamp
        AND NOT EXISTS (
                SELECT * FROM {agenda} a WHERE a.task_id = t.task_id
                    AND (a.status IN ({JobStatus.IDLE.value}, {JobStatus.BUSY.value}, {JobStatus.COMING.value}) )
            )
        -- ei leidu mastereid, millel ei leidu reaalset tabelit (kahekordne eitus) -- st kõik sõltarid (masterid) peavad PG arvates eksisteerima
        AND NOT EXISTS (
            -- selle leitud slave (sõltuva) kõik muud eeldustabelid (sõltarid) peavad PG-s eksisteerima (vb pole struct sobilik, aga peab leiduma)
            -- ALT: eeldusülesanded peavad olema vähemalt korra positiivselt läbitud (nii peaks tegema kui arendada, et ülesanne ei võrdu tabeliga)
            -- aga võib olla ka oluukord, et tabel on juba tehtud, aga pole veel täidetud (seega tabeli füüsiline kontroll on parem, või läbi OR-i)
            SELECT * FROM {registry_depends} d2 -- leitud tabeli eeldustabelid
            WHERE d2.task_id_slave = t.task_id -- kus leitud tabel on sõltuv
            AND NOT EXISTS ( -- hetkel seega jõuline tabeli kontroll
                SELECT *
                FROM pg_class tt join pg_namespace ns on ns.oid = tt.relnamespace
                WHERE ns.nspname = split_part(d2.task_id_master, '.', 2) -- task_id teine osa on skeeminimi
                AND tt.relname =  split_part(d2.task_id_master, '.', 3) -- task_id kolmas osa on tabelinimi
                AND tt.relkind in ('r', 'm', 'v') -- tabel (relatsioon), materialiseeritud vaade, vaade
            )
            AND array_length(string_to_array(d2.task_id_master, '.'), 1) - 1 >= 2 -- vähemalt 2 punkti koodis
        )
        -- ja pole ajutiselt peatatud
        AND NOT EXISTS (SELECT * FROM {reconf} rc 
            WHERE rc.task_id = t.task_id AND rc.task_option = 'blacklist' AND rc.task_newvalue ilike 'yes'
        )
        ORDER BY t.priority_class ASC, t.viimane_lopp ASC
        """
        result_set_tasks_to_add: DataCapsule = self.context.target(sql_reg)
        new_count: int = 0
        # here the code is little bit general (historical reasons) and probably can be simplified
        for rec_new_task in result_set_tasks_to_add:  # add to Agenda one-by-one
            (task_id, *_) = rec_new_task # unpack first (now we already have just one column)
            added_count: int = self.add_task_to_agenda(task_id, commander, False, 0, JobStatus.IDLE.value) # type: ignore -- via decorator it returns INT 
            new_count += added_count
        #
        if new_count > 0:
            self.notify(f"Agenda got {new_count} new jobs") # discord
        return new_count


    @DapuProcess.task_id_eventlog(flag='AGENDA') # returns INT
    def add_task_to_agenda(self, task_id: str, commander:str, run_all_checks:bool = True, task_priority_shift: int=0, task_status:int = JobStatus.IDLE.value) -> DataCapsule:
        """
        Return 1 if succeeded, 0 if not
        run_all_check is not needed, because of our big SQL detects only possible tasks, but later if some other way emerges...
        Attempt to add tasks which are not in Registry gives 0 new rows
        """
        registry = self.context.find_registry_table_full_name('registry')
        agenda = self.context.find_registry_table_full_name('agenda')
        commander = commander.replace("'", "")
        try:
            sql_add_task = f"""INSERT INTO {agenda} (task_id, priority, commander, status)
                SELECT '{task_id}', r.priority_class + {task_priority_shift}, '{commander}', {task_status}
                FROM {registry} r WHERE r.task_id = '{task_id}'
                RETURNING task_id
                """
            return self.context.target(sql_add_task) # thanks to decorator it returns int

        except Exception as e1:
            logger.error(f"Problem with adding task '{task_id}' into Agenda")
            logger.error(f"{e1}")
            return DataCapsule()


    @DapuProcess.task_id_eventlog(flag='DEPENDANT') # returns INT
    def add_dependent_tasks_to_agenda(self, task_id: str, task_priority: int) -> DataCapsule:
        """
        Used by Job -- after performing its job Job will ask Manager to find dependants and add them to Agenda
        """
        agenda = self.context.find_registry_table_full_name('agenda')
        registry_depends = self.context.find_registry_table_full_name('registry_depends')
        registry = self.context.find_registry_table_full_name('registry')
        route = self.context.find_registry_table_full_name('route')
        reconf = self.context.find_registry_table_full_name('reconf')
         
        # see loogika paneb ainult need, kus terve route on olemas ja enabled olekus
        # ja ei hooli päevaajast (sest on sõltlane ja vajab seega kiiremat äralahendamist/laadimist)
        # prioriteedi annab väljakutsuja (ja selleks on sõltari enda prioriteet + 1)
        # ja ei lisata, kui sama prioriteediga on juba ootel (või peaaegu ootel) 
        sql = f"""
            INSERT INTO {agenda} (task_id, status, priority, commander) -- FIXME worker asemele manager (mõlemad väljad peavad olema)
            
            SELECT d.task_id_slave, {JobStatus.IDLE.value}, {task_priority}, d.task_id_master
            FROM {registry_depends} d 
            JOIN {registry} r ON r.task_id = d.task_id_slave
            JOIN {route} rt ON split_part(r.task_id, '.', 1) = rt.code AND rt.disabled NOT ILIKE '%manager%'
            WHERE d.task_id_master = '{task_id}'
            AND NOT EXISTS (
                SELECT * 
                FROM {agenda} ba
                WHERE ba.task_id = d.task_id_slave
                AND ba.status in ({JobStatus.IDLE.value}, {JobStatus.COMING.value})
                AND ba.priority = {task_priority}
            )
            -- ei leidu mastereid, millel ei leidu reaalset tabelit (kahekordne eitus) -- st kõik sõltarid (masterid) peavad PG arvates eksisteerima
            AND NOT EXISTS (
                -- selle leitud slave (sõltuva) kõik muud eeldustabelid (sõltarid) peavad PG-s eksisteerima (vb pole struct sobilik, aga peab leiduma)
                -- ALT: eeldusülesanded peavad olema vähemalt korra positiivselt läbitud (nii peaks tegema kui arendada, et ülesanne ei võrdu tabeliga)
                -- aga võib olla ka olukord, et tabel on juba tehtud, aga pole veel täidetud (seega tabeli füüsiline kontroll on parem, või läbi OR-i)
                SELECT * 
                FROM {registry_depends} d2 -- lõpetanud ülesande tabeli järglase teised eeldused (incl see lõpetanud ise, aga see on ok)
                WHERE d2.task_id_master = d.task_id_master AND d2.task_id_slave != d.task_id_slave
                AND NOT EXISTS ( -- hetkel seega jõuline tabeli kontroll
                    SELECT *
                    FROM pg_class t join pg_namespace ns on ns.oid = t.relnamespace
                    WHERE ns.nspname = split_part(d2.task_id_master, '.', 2) -- task_id teine osa on skeeminimi
                    AND t.relname =  split_part(d2.task_id_master, '.', 3) -- task_id kolmas osa on tabelinimi
                    AND t.relkind in ('r', 'm', 'v') -- tabel (relatsioon), materialiseeritud vaade, vaade
                )
                AND array_length(string_to_array(d2.task_id_master, '.'), 1) - 1 >= 2 -- vähemalt 2 punkti task_id-s
            )
            -- ja pole ajutiselt peatatud
            AND NOT EXISTS (SELECT * FROM {reconf} rc 
                WHERE rc.task_id = d.task_id_slave AND rc.task_option = 'blacklist' AND rc.task_newvalue ilike 'yes'
            )
            RETURNING task_id
        """
        return self.context.target(sql)


    def count_jobs_in_agenda(self) -> tuple[int|float, int, int]:
        """
        Return tuple (total_count, busy_count, idle_count)
        Does one SQL query and gets 0-3 rows. Finds tuple elements using lookup
        """
        agenda = self.context.find_registry_table_full_name('agenda')

        sql = f"""SELECT a.status, count(*) as cnt
        FROM {agenda} a
        WHERE a.status in ({JobStatus.BUSY.value}, {JobStatus.IDLE.value}, {JobStatus.COMING.value})
        AND a.failure_count < {self.context.FAILURE_LIMIT}
        GROUP BY a.status
        ORDER BY a.status
        """
        result_set = self.context.target(sql)
        # where status (col=0) = xx return count (col=1), lookup returns None if no good row
        busy_count = lookup_first(result_set, 0, JobStatus.BUSY.value, 1) or 0 # so None -> 0 as we have countables
        idle_count = lookup_first(result_set, 0, JobStatus.IDLE.value, 1) or 0
        total_count = sum_column(result_set, 1) # summarize counts (col index = 1)
        return (total_count, busy_count, idle_count)
    

    def get_oldest_busy_start_time(self) -> str | None:
        """
        Find starting time of most longer running job that is currently running
        """
        agenda = self.context.find_registry_table_full_name('agenda')

        sql = f"""SELECT min(a.last_start_ts) as oldest_ts
        FROM {agenda} a
        WHERE a.status = {JobStatus.BUSY.value}
        """
        result_set = self.context.target(sql)
        if result_set:
            return result_set[0][0]
        return None
    
