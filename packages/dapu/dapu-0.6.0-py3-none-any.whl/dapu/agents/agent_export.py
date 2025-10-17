from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id, make_insert_value_part, make_insert_conflict_set_part, read_sql_from_file, make_replacements, save_data_for_postgre
from dapu.placeholder import Placeholder

class Agent(AgentGeneric):
    """
     - do: export # lubatud ka eesti keeles: eksport
       file: input.sql # SQL SELECT
       changedetection: ts # or empty
       ts_col: modified_ts # if change detection is ts. col must be amoungst cols below OR it is no-name column in input.sql after all columns 
       pkcol: # in dwh those are actually alternative key columns, in: CONSTRAINT ak_{table_name}_4_uniq (pkcolumns) 
       - id
       cols:
       - id
       - some_field
       - modified_ts
       to: direct # alt: file - temporary file to immidiate consume in next action (during same job)
    """
    
    def do_action(self) -> bool:
        file_element = 'file'
        existing_files = self.collect_files(file_element)
        if not existing_files:
            logger.error(f"No files for tag {file_element} for {self.task_id}")
            return False
        
        _, schema_name, table_name = split_task_id(self.task_id)

        all_cols_array: list[str] = self.action.get('cols', []) # can be re-done to pkcols+datacols instead of cols (better not: cols is ordered according to input.sql select, pkcols don't need to be first)
        pk_cols_array: list[str] = self.action.get('pkcols', []) # alternative key cols in CONSTRAINT ak_{table_name}_4_uniq
        
        method: str = self.action.get('changedetection', '')
        ts_col_pos: int = self.find_ts_col_pos(self.action.get('tscol', ''), all_cols_array, len(all_cols_array)) if method == 'ts' else -1
        ts_col_name: str = self.action.get('tscol', '') if method == 'ts' else ''
        destination = self.action.get('to', 'file') # default is 'file' for compatibility, use 'direct'
        task_temp_file_name: str | None = None
        if destination == 'file':
            task_temp_file_name = self.find_task_temp_file_name("dat")
            if task_temp_file_name is None:
                raise Exception("wrong name for dat file")
            logger.debug(f"Temporary file is {task_temp_file_name}")
        
        sql_template = read_sql_from_file(existing_files[0])
        
        # while + save -- 
        while True:
            try:
                replacements: list[tuple[str | Placeholder, str]] = []
                replacements.append((Placeholder.TARGET_SCHEMA, f'{schema_name}'))
                replacements.append((Placeholder.TARGET_TABLE, f'{table_name}'))
                replacements.append((Placeholder.SOURCE_COLUMN_TS, f'{ts_col_name}')) # don't need to be dynamic
                
                if method == 'ts':
                    ts_time = self.context.get_task_sync_until_ts(self.task_id, 0)
                    replacements.append((Placeholder.LAST_VALUE_TS, f'{ts_time}'))

                sql = make_replacements(sql_template, replacements) or ""
                rowset = self.context.hub.run(self.route_alias, sql)
                logger.info(f"Data loaded from source {self.route_alias} into memory, {len(rowset)} records")
            except Exception as e1:
                logger.error(f"Data pull failed ({schema_name}.{table_name})")
                logger.error(f"{e1}")
                return False # quit on first batch with error

            if destination == 'file':
                if task_temp_file_name is None:
                    raise Exception("wrong name for dat file, second")
                if len(rowset) == 0:
                    logger.info(f"No records pulled ({schema_name}.{table_name}). Making temporary file {task_temp_file_name} empty too.")
                    with open(task_temp_file_name, 'w', encoding='utf-8') as sf:
                        sf.write("")
                    return True
                else:
                    # rowset export to postgre importable data file
                    logger.info(f"Pulled {len(rowset)} records ({schema_name}.{table_name}). Saving them to temporary file {task_temp_file_name}")
                    return save_data_for_postgre(task_temp_file_name, rowset)

            if destination == 'direct':
                if len(rowset) == 0:
                    logger.info(f"No records pulled ({schema_name}.{table_name})")
                    break
                finished = self.save_rows(rowset, all_cols_array, pk_cols_array, method, ts_col_pos)
                if finished:
                    break
            if len(rowset) < 3000: # temp solution for MS SQL time problem. can be rewritten to use some key (limit_quitter_in_use, limit_quitter_limit)
                break
        return True
    
    def find_ts_col_pos(self, ts_col_name: str, all_cols_array: list[str], default: int = -1) -> int:
        """
        Find index of string in list. If not found return default (-1).
        In our case deafult can be out of list index (aka len) 
        assuming that actual select in input.sql has more columns then listed, eg calculated field at end 
        """
        ts_col_pos = default
        if ts_col_name > '':
            for pos, col in enumerate(all_cols_array):
                if col.strip() == ts_col_name:
                    ts_col_pos = pos
                    break
        return ts_col_pos # can be outside of list range 


    def save_rows(self, rowset, all_cols_array: list[str], pk_cols_array: list[str], method: str, ts_col_pos: int) -> bool:
        """
        
        Returns True then NO more rows are needed (it was final), False if not final.
        Final is if last change timestamp is near enough to current time.
        Rowset MUST be ordered by change timestamp column (older first) if method is 'ts'
        If method is 'ts' and ts column is empty then error log and final 
        
        """
        logger.debug(f"Got {len(rowset)} records, trying insert+conflict")
        if len(rowset) == 0: # hopefully we never got empty rowset
            return True # redundant
        
        nearness = '2 minutes' # PG interval literal expression
        route_code, schema_name, table_name = split_task_id(self.task_id)
        logger.debug(f"Table {table_name} must have CONSTRAINT ak_{table_name}_4_uniq")
        
        all_cols: str = ','.join(all_cols_array)
        last_ts: str | None = None

        range_end = -1
        
        for pos, this_row in enumerate(rowset):
            last_ts = None # last change timestamp of current record (for 'ts' method)
            if pos == 0: # one time calculation (on first row)
                range_end = len(this_row) - 1 # index max reasonable value (min is 0)
            if method == 'ts' and ts_col_pos >= 0 and ts_col_pos <= range_end:
                last_ts = this_row[ts_col_pos]
                if not last_ts:
                    # FATAL!?!
                    logger.error(f"Last change timestamp column value is empty/null, it is not meant to be so, cannot continue, fix input data")
                    return True # final because of errorneous data
            
            value_part_str = make_insert_value_part(this_row, len(all_cols_array))
            conflict_set_part = make_insert_conflict_set_part(all_cols_array, pk_cols_array)
            
            sql_ins_upd = f'''
                INSERT INTO {schema_name}.{table_name} ({all_cols}) VALUES ({value_part_str})
                ON CONFLICT ON CONSTRAINT ak_{table_name}_4_uniq DO UPDATE
                SET {conflict_set_part}
            '''
            self.context.target(sql_ins_upd, False)
            
            if method == 'ts': # save this row ts to rgistry (includes commit since default on_success_commit=true) 
                self.context.save_task_sync_until_ts(self.task_id, last_ts) # after each row => slower => less fragile (easier to continue)
        
        if method == 'ts' and last_ts is not None:
            sql_need = f'''SELECT CASE WHEN '{last_ts}'::timestamp + '{nearness}'::interval > clock_timestamp() THEN 0 ELSE 1 END'''
            need_for_more_rs = self.context.target(sql_need, True)
            if need_for_more_rs[0][0] == 0:
                return True # final because it is very near to current time (less then 2 minutes old, those newer can grabbed on next time) 
        else:
            return True # final because where was no intention to detect changes, one load is enought 
        return False
