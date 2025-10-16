from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id
from dapu.placeholder import Placeholder
from datetime import datetime

class Agent(AgentGeneric):
    """
     - do: history
       imp: "myschema.mytable__imp" # imp or curr must point to table which has full current state
       curr: "myschema.mytable_curr" # imp or curr - if schema name is not given, target table schema is used
       key_columns:
        - id
       data_columns:
        - col1
        - col2
    NB! Target table must have full set of dwh_ columns
        dwh_effective_current, dwh_effective_from, dwh_reason_start, dwh_hash_pk, dwh_hash_data, dwh_worker_start
        dwh_effective_to, dwh_reason_end, dwh_worker_end
    Use runsql with command create table if not exists like & alter table add column if colunm not exists 
    """
    myname: str = 'history'
    
    def do_action(self) -> bool:
        logger.info(f"start {self.myname} for {self.task_id}")
        _, schema_name, table_name = split_task_id(self.task_id)

        base_table_name = None # alustabel, kus on täisseis (kas __imp või nn _curr), Esitada koos skeeminimega!
        base_table_name = self.action.get('imp')
        if base_table_name is None:
            base_table_name = self.action.get('curr')
        if base_table_name is None:
            logger.error(f'Laadimissamm on hist, aga puudu alustabel (imp aka curr)')
            return False
        if len(base_table_name.split('.')) < 2: # st koosneb ühest osast
            base_table_name = f'{schema_name}.{base_table_name}'

        all_cols_list = self.action.get('key_columns', []) + self.action.get('data_columns', []) 
        
        cols = ', '.join(all_cols_list) # list -> string
        impcols = ', '.join(map(lambda a : 'cc.' + a, all_cols_list)) # column names are prefixef with cc as table alias (cc = current)

        fixed_ts = datetime.now() # ETL masina kellaaeg järgmise SQL-ide bloki jaoks (peab olema fikseeritud, sest on piiritähiseks)
        worker_id = self.context.worker_id
        history_table = f"{schema_name}.{table_name}"
        sql_sammud = [
              fourstep_sql_step_1_update_deleted(history_table, base_table_name, fixed_ts, worker_id)
            , fourstep_sql_step_2_insert_new(history_table, base_table_name, fixed_ts, worker_id, cols, impcols)
            , fourstep_sql_step_3_update_changed(history_table, base_table_name, fixed_ts, worker_id)
            , fourstep_sql_step_4_insert_changed(history_table, base_table_name, fixed_ts, worker_id, cols, impcols)
            ]
        
        for pos, sql_step in enumerate(sql_sammud):
            logger.debug(f"{pos} for {history_table} from {base_table_name}")
            self.context.target(sql_step, False)
            
        logger.info(f"done {self.myname} for {self.task_id}")
        return True # or thrown an exception

def fourstep_sql_step_1_update_deleted(history_table: str, current_table: str, fixed_ts: str, worker_id: int) -> str:
    return f'''UPDATE {history_table} hh
        SET dwh_effective_current = FALSE, dwh_effective_to = '{fixed_ts}', dwh_reason_end = 'D', dwh_worker_end = {worker_id}
        WHERE dwh_effective_current -- siiamaani aktiivne kirje
        AND NOT EXISTS ( -- millele ei leidu vastet värskes seisus
            select * from {current_table} cc
            where cc.dwh_hash_pk = hh.dwh_hash_pk) -- seos läbi pk räside (1 veerg mõlemalt poolt)
        '''

def fourstep_sql_step_2_insert_new(history_table: str, current_table: str, fixed_ts: str, worker_id: int, cols: str, impcols: str) -> str:
    return f'''INSERT INTO {history_table} ({cols}, dwh_effective_current, dwh_effective_from, dwh_reason_start, dwh_hash_pk, dwh_hash_data, dwh_worker_start)
            SELECT {impcols}, TRUE, '{fixed_ts}', 'I', cc.dwh_hash_pk, cc.dwh_hash_data, {worker_id}
            FROM {current_table} cc LEFT JOIN {history_table} hh ON hh.dwh_effective_current AND hh.dwh_hash_pk = cc.dwh_hash_pk
            WHERE hh.dwh_hash_pk IS NULL
        '''

def fourstep_sql_step_3_update_changed(history_table: str, current_table: str, fixed_ts: str, worker_id: int) -> str:
    return f'''UPDATE {history_table} hh
            SET dwh_effective_to = '{fixed_ts}', dwh_reason_end = 'U', dwh_effective_current = FALSE, dwh_worker_end = {worker_id}
            FROM {current_table} cc
            WHERE hh.dwh_effective_current AND hh.dwh_effective_from < '{fixed_ts}'
            AND hh.dwh_hash_pk = cc.dwh_hash_pk AND hh.dwh_hash_data != cc.dwh_hash_data
        '''

def fourstep_sql_step_4_insert_changed(history_table: str, current_table: str, fixed_ts: str, worker_id: int, cols: str, impcols: str) -> str:
    return f'''INSERT INTO {history_table}
            ({cols}, dwh_effective_current, dwh_effective_from, dwh_reason_start, dwh_hash_pk, dwh_hash_data, dwh_worker_start)
            SELECT {impcols}, TRUE, '{fixed_ts}', 'I', cc.dwh_hash_pk, cc.dwh_hash_data, {worker_id}
            FROM {current_table} cc
            LEFT OUTER JOIN {history_table} hh ON hh.dwh_hash_pk = cc.dwh_hash_pk AND hh.dwh_effective_current
            WHERE hh.dwh_hash_pk IS NULL
        '''
