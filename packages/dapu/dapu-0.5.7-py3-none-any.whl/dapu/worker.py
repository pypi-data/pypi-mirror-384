from loguru import logger
import sys
import os
import hashlib # md5 uuid jaoks
import uuid # worker saab unikaalse koodi (suva, aga midagi peab olema)
from datetime import datetime, timedelta # siin-seal ajakulu mõõtmiseks, uuid jaoks
from dbpoint.datacapsule import DataCapsule

from dapu.process import DapuProcess
from dapu.jobstatus import JobStatus
from dapu.job import DapuJob

class DapuWorker(DapuProcess):
       
    def run(self) -> int:
        jobs_finished = 0
        jobs_failed = 0
        logger.debug(f"Working directory is {self.context.work_dir}")

        self.worker_create() # throws exception if registration of new worker fails
        
        t1 = datetime.now() # worker starting time 
        while (datetime.now() - t1 < timedelta(minutes=self.context.WORKER_NO_NEW_HAUL_AFTER_MINUTES) ): # repeat until worker yet has time
            
            job : DapuJob | None = self.next_job_from_agenda()
            
            if job is None:
                logger.info(f"No{' more' if jobs_finished + jobs_failed > 0 else ''} jobs")
                break
            if job.run(): 
                jobs_finished += 1
            else:
                jobs_failed += 1
        #endloop
        self.disconnect_main()
        return self.run_return_value_by_two_numbers(jobs_finished, jobs_failed)
        

    def run_return_value_by_two_numbers(self, tasks_finished, tasks_failed):
        tasks_runned = tasks_finished + tasks_failed
        if tasks_runned == 0:
            return 0 # there was nothing to do for this worker
        else:
            if tasks_failed > 0:
                self.notify(f"Failed {tasks_failed} jobs, succeeded {tasks_finished} jobs") # discord
                return -1 # there was at least one error
            else:
                return 1 # everything is ok and was done at least one task 
    
    
    def next_job_from_agenda(self) -> DapuJob | None :
        # Find first task to run, including tasks skipped by others
        # if no work found return None, otherwise return Tasker object (task data + run method)
        
        if self.context.worker_id is None:
            msg = "Somehow workers ID is missing, anomaly..."
            logger.warning(msg)
            return None
        
        agenda = self.context.find_registry_table_full_name('agenda')
        route = self.context.find_registry_table_full_name('route')
        
        # safe sql (InS 2024-08-26): used values for substitutes are python integers
        sql = f"""SELECT a.id
            FROM {agenda} a
            JOIN {route} rt ON split_part(a.task_id, '.', 1) = rt.code AND rt.disabled not ilike '%worker%'
            WHERE a.status in ({JobStatus.IDLE.value}, {JobStatus.SKIPPED.value}) -- two allowed statuses
                AND (a.worker != {self.context.worker_id} OR a.worker IS NULL) -- not seen lastly by myself (this process)
                AND a.failure_count < {self.context.FAILURE_LIMIT} -- too many times failed wont count as tasks to do (even if status matches)
            ORDER BY a.priority ASC, a.failure_count ASC, a.id ASC
            LIMIT 1 """
        result_set = self.context.target(sql)
        
        if not result_set:
            return None # no more jobs in Agenda
        
        candidate_id = result_set[0][0] # candidate may not pass on next conditions
        
        # FIXME -- siia uus init
        try:
            job = DapuJob(candidate_id, self.context)
        except Exception as e1: # any problem in init and we land here
            return None
        
        if self.task_is_listed_later(job.task_id, job.agenda_id):
            msg = f"Job {job.task_id} will be skipped ({job.agenda_id})"
            logger.info(msg)
            # mark as skipped
            self.mark_as_skipped(job.agenda_id)
            # find next 
            return self.next_job_from_agenda() # reassign, may return None
        
        if self.task_files_are_lost(job.task_id):
            msg = f"Job {job.task_id} files are lost ({job.agenda_id})"
            logger.warning(msg)
            # mark this as lost one so no more trials on this
            self.mark_as_lost(job.agenda_id)
            # find next
            return self.next_job_from_agenda() # reassign, may return None
            
        if self.task_is_in_work(job.task_id, job.agenda_id):
            msg = f"Job {job.task_id} is in work by some other worker ({job.agenda_id})"
            logger.warning(msg)
            # teine instants sellest samast ülesandest on töös
            # vana mõte oli panna ta mälus (mitte baasis) nurjunuks ja minna edasi
            # aga õigem oleks siin totaalselt loobuda (ei katseta ka järgmist enam) ja lasta teisel oma töö lõpetada
            return None # let us be cautious and finish now this instance
        
        if self.task_dependent_is_in_work(job.task_id):
            msg = f"Jobs {job.task_id} prerequisite job is in work by some other worker ({job.agenda_id})"
            logger.warning(msg)
            return None # let us be cautious and finish now this instance
        
        # if first found task remains lets return that and log info
        msg = f"Next task is {job.task_id} (job={job.agenda_id})"
        logger.info(msg)
        return job
    
    
    def task_is_in_work(self, task_id, agenda_id):
        # task on kellegi poolt juba töös (mis tähendab, et ta sai selle moment enne kätte)
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""SELECT 1 FROM {agenda} a 
        WHERE a.status = {JobStatus.BUSY.value}
            AND a.id != {agenda_id}
            AND a.task_id = '{task_id}'
            AND a.worker != {self.context.worker_id}
        LIMIT 1
        """
        result_set = self.context.target(sql)
        # return len(result_set) > 0
        if not result_set: # ei saadud ühtegi kirjet
            return False
        return True # saadi üks kirje
    
    
    def task_dependent_is_in_work(self, task_id):
        agenda = self.context.find_registry_table_full_name('agenda')
        registry_depends = self.context.find_registry_table_full_name('registry_depends')
        sql = f"""SELECT 1 FROM {agenda} a 
        WHERE a.status = {JobStatus.BUSY.value}
            AND a.worker != {self.context.worker_id}
            AND a.task_id IN (
                SELECT task_id_master 
                FROM {registry_depends} d2
                WHERE d2.task_id_slave = '{task_id}'
            )
        LIMIT 1 
        """
        result_set = self.context.target(sql)
        # return len(result_set) > 0
        if not result_set: # ei saadud ühtegi kirjet
            return False
        return True # saadi üks kirje
    
    
    def task_files_are_lost(self, task_id):
        task_dir = self.find_task_dir_path(task_id, must_exists=True)
        if task_dir is None:
            return True
        return False
    
    
    def task_is_listed_later(self, task_id: str, agenda_id: int) -> bool:
        # kas sama task (task_id) on tööootel (tagapool = üldse) tegemata olekus
        # ja pole selle workeri poolt (viimati) tehtud (=katsetatud aga nurjunud)
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""SELECT 1
            FROM {agenda} a
            WHERE a.status in ({JobStatus.IDLE.value}, {JobStatus.COMING.value})
                AND (a.worker != {self.context.worker_id} OR a.worker IS NULL)
                AND a.failure_count < {self.context.FAILURE_LIMIT} -- palju kordi nurjunud välistame
                AND a.id != {agenda_id}
                AND a.task_id = '{task_id}'
            LIMIT 1
            """
        result_set = self.context.target(sql)
        # return len(result_set) > 0
        if not result_set: # ei saadud ühtegi kirjet
            return False
        return True # saadi üks kirje, seega on tagapool olemas


    @DapuProcess.task_id_eventlog(flag='SKIPPED') # returns int
    def mark_as_skipped(self, agenda_id: int) -> DataCapsule:
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""UPDATE {agenda} 
                SET status = {JobStatus.SKIPPED.value} 
                WHERE id = {agenda_id}
                RETUNING task_id"""
        return self.context.target(sql)


    @DapuProcess.task_id_eventlog(flag='LOST') # returns int
    def mark_as_lost(self, agenda_id: int) -> DataCapsule:
        agenda = self.context.find_registry_table_full_name('agenda')
        sql = f"""UPDATE {agenda} 
                SET status = {JobStatus.LOST.value} 
                WHERE id = {agenda_id}
                RETUNING task_id"""
        return self.context.target(sql)        
    
    def generate_uuid(self):
        aeg = datetime.now()
        kood = str(uuid.uuid4())
        tulem = hashlib.md5(f'{kood}{aeg}'.encode()).hexdigest()
        return tulem

    
    def worker_create(self, repeat: int = 1) -> bool:
        # loob kirje tabelisse bis_worker ja annab tagasi selle ID, mida tuleks kasutada tabelis bis_agenda (seal pole FK nõuet, aga jälgimist on vaja)
        worker = self.context.find_registry_table_full_name('worker') # tabeli nimi koos skeemiga
        worker_code = self.generate_uuid() # kas seda läks vaja ainult seepärast, et workeri tabelis polegi midagi?
        sql = f"""INSERT INTO {worker} (code) VALUES ('{worker_code}') RETURNING (id)"""
        try:
            result_set = self.context.target(sql)
        except Exception as e1:
            # kordame juhuks, kui uuid kordus (repeat abil väldime lõpmatut tsüklit)
            if repeat > 0:
                self.worker_create(repeat - 1)
                return True
            else:
                raise e1 # kui kordusi liiga palju, siis viskame välja viimase veaga

        if result_set:
            self.context.worker_id = result_set[0][0]
        return True

