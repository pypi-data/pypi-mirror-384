from loguru import logger
from dapu.process import DapuProcess
from dapu.jobstatus import JobStatus

class DapuObserver(DapuProcess):
    """
    Give info about tasks and jobs
    """
    def run(self):
        logger.info(f"Working directory is {self.context.work_dir}")
        info_objects = []
        options = []
        unused = self.context.more_args
        for task_id in unused:
            if self.is_existing_task_id(task_id):
                logger.info(f"asked for info about {task_id}")
                info_objects.append(task_id)
            else:
                logger.info(f"taking {task_id} as option or commandment")
                options.append(task_id)
        all_flag = False if len(info_objects) > 0 else True

        if 'task' in options:
            if not all_flag:
                logger.info(f"Info about tasks")
                for task_id in info_objects:
                    self.task_info(task_id)
            else:
                # kas tõesti taheti kõike või anti task_id osalisena
                found_objects = self.all_tasks()
                for task_id in found_objects:
                    if 'list' in options:
                        logger.info(f"TASK {task_id}")
                    else:
                        self.task_info(task_id)

        if 'agenda' in options:
            if all_flag:
                self.agenda_info(options)
            else:
                for task_id in info_objects:
                    self.agenda_job_info(task_id, options)
            
    
    def is_existing_task_id(self, task_id: str) -> bool:
        if "'" in task_id:
            return False
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""SELECT 1 FROM {registry} WHERE task_id = '{task_id}' """
        result_set = self.context.target(sql)
        if result_set:
            return True
        return False

    def all_tasks(self) -> list[str]:
        logger.info(f"FIND ALL TASKS")
        registry = self.context.find_registry_table_full_name('registry')
        sql = f"""SELECT r.task_id FROM {registry} r ORDER BY 1"""
        result_set = self.context.target(sql)
        return [row[0] for row in result_set]
        

    def task_info(self, task_id: str) -> None:
        logger.info(f"TASK {task_id}")
        registry = self.context.find_registry_table_full_name('registry')
        route = self.context.find_registry_table_full_name('route')
        agenda = self.context.find_registry_table_full_name('agenda')
        registry_depends = self.context.find_registry_table_full_name('registry_depends')
        reconf = self.context.find_registry_table_full_name('reconf')

        sql = f"""SELECT r.id, r.def_ts, r.table_version, r.needs_versioning, r.full_load
            , r.synced_until_ts, r.synced_until_bigint, last_start_ts, last_end_ts
            , r.keep_pause, r.run_morning, r.run_workhours, r.run_evening
            , r.actions, r.source_hash, r.disabled as task_disabled_for
            , rt.type, rt.alias, rt.disabled as route_disabled_for
        FROM {registry} r LEFT JOIN {route} rt ON split_part(r.task_id, '.', 1) = rt.code
        WHERE r.task_id = '{task_id}' """
        result_set = self.context.target(sql)
        if result_set:
            logger.info(f"{result_set[0]}")

            sql_reconf = f"""SELECT task_option, task_newvalue FROM {reconf} WHERE task_id = '{task_id}'"""
            result_set = self.context.target(sql_reconf)
            if result_set:
                logger.info("reconf")
                for row in result_set:
                    logger.info(f"{row}")
            else:
                logger.info("NO RECONF")

            sql_dep_master = f"""SELECT task_id_slave FROM {registry_depends} WHERE task_id_master = '{task_id}'"""
            result_set = self.context.target(sql_dep_master)
            if result_set:
                logger.info("DEPENDANTS")
                for row in result_set:
                    logger.info(f"{row}")
            else:
                logger.info("NO dependants")
            sql_dep_slave = f"""SELECT task_id_master FROM {registry_depends} WHERE task_id_slave = '{task_id}'"""
            result_set = self.context.target(sql_dep_slave)
            if result_set:
                logger.info("DEPENDS ON")
                for row in result_set:
                    logger.info(f"{row}")
            else:
                logger.info("NOT depending (independent)")
            sql_job_busy = f"""SELECT * FROM {agenda} WHERE task_id = '{task_id}' AND status = {JobStatus.BUSY.value}"""
            result_set = self.context.target(sql_job_busy)
            if result_set:
                logger.info("CURRENTLY RUNNING")
                for row in result_set:
                    logger.info(f"{row}")
            else:
                logger.info("NO active runs")
            
            sql_job_idle = f"""SELECT id, created_ts, priority, last_start_ts, failure_count, commander 
                FROM {agenda} WHERE task_id = '{task_id}' AND status = {JobStatus.IDLE.value}"""
            result_set = self.context.target(sql_job_idle)
            if result_set:
                logger.info("WAITING")
                for row in result_set:
                    logger.info(f"{row}")
            else:
                logger.info("NO waitings")
            

    def agenda_job_info(self, task_id: str, options: list|None) -> None:
        logger.info(f"Job of task {task_id} is:")


    def agenda_info(self, options: list|None) -> None:
        logger.info(f"All jobs in agenda:")

