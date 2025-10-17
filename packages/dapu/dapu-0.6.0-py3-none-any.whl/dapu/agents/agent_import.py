from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id
from dapu.placeholder import Placeholder

class Agent(AgentGeneric):
    """
    Take all data from source and ...
    a) put into temp file
    b) stream into target table -> for that is agent_stream
    

FIXME - FIXME - FIXME 
    """
    
    def do_action(self, task_id, action_def, task_dir): # FIXME -- 2 do_Action fn!!! which one is correct??
        _, target_schema, target_table = split_task_id(self.task_id)
        file_element = 'file'
        existing_files = self.collect_files(file_element)
        if not existing_files:
            logger.error(f"No files for tag {file_element} in {self.task_dir}")
            return False
        
        replacements = []
        # this select query can be modified knowing source stuff (pagination? start TS?)
        # for ts we need last ts saved to us
        # for maxid we need ...
        # for hash source should be pg? why? sql must include hash expression of source dbms
        method = self.action.get('changedetection', None)
        # method determines what data we need from our side before to start asking from source
        match method: # 3.10+
            case 'ts': # we need last sync ts and put it sql in place of ts_time
               ts_time = self.context.get_task_sync_until_ts(self.task_id, 0)
               replacements.append(('{ts_time}', ts_time))
            case _:
                ...      
        
        
        
        source_select = self.read_sql_from_file(existing_files[0], replacements)
        result_set = self.hub.run(self.route_alias, source_select) # SIIA run asemel savetofile + filename
        # ja sellel pole väljundit (või siis on true false või kirjete arv)
        if not result_set:
            logger.warning(f"No data from {self.route_alias}")
            return True
        
        _, schema_name, table_name = split_task_id(self.task_id)


        pure_sql = sql

        destination = 'file'
        if 'to' in action_def:
            destination = action_def['to']

        # ajutine fail, kuhu panna tõmmatud andmed
        if destination == 'file':
            task_temp_file_name = self.find_task_temp_file_name()
            self.log('DEBUG', f'ajutine fail saab olema {task_temp_file_name}')

        tulem = True
        while True:
            try:
                sql = pure_sql
                replacements = [(Placeholder.TARGET_SCHEMA, f'{schema_name}'), (Placeholder.TARGET_TABLE, f'{table_name}')]
                
                rs = bm.run(idx, sql, True, True) # commit pole vist oluline
                self.log('INFO', f'Andmed mälus ({len(rs)} kirjet)')
            except Exception as e1:
                self.log('ERROR', f'Andmete tõmbamine nurjus ({schema_name}.{table_name}): {bm.last_error}')
                self.log('ERROR', f'{e1}')
                return False # esimese vigase faili peale katkestame

            if len(rs) == 0:
                self.log('INFO', f'Polnud kirjeid ({schema_name}.{table_name})')
                # teeme tühja faili kui on kartus, et keegi järgmisena tahab seda faili kasvõi näha
                if destination == 'file':
                    with open(task_temp_file_name, 'w') as sf:
                        sf.write("")
                break # kui ei saadud kirjeid, siis näib kõik kena ja läheme tsüklist välja

            if destination == 'file':
                # rs on nüüd data-ga, vaja salvestada PG jaoks sobivale kujule
                self.log('INFO', f'salvestame andmed ({len(rs)}) ajutisse faili')
                tulem = self.save_data_for_postgre(task_temp_file_name, rs) # kas see on piisav info, vb on vaja null jms?
                break # failikirjutamisel ei ole korduseid

            if destination == 'direct':
                self.log('INFO', f'käime saadud kirjed ({len(rs)}) insert+conflict abil üle')
                all_cols_array = action_def['cols']
                all_cols = ','.join(all_cols_array)
                #all_cols_array = all_cols.split(',') # tühiku trimime/stripime hiljem võrdluse ajal
                # mitmes veerg on ts_col kõigi hulgast (tegelikult mitte kõigi hulgast, vaid input.sql sees oleva selecti veergude hulgast, aga püüame ühtsena hoida
                ts_col_pos = -1
                if method == 'ts':
                    all_col_pos = 0
                    for col in all_cols_array:
                        if col.strip() == ts_col:
                            ts_col_pos = all_col_pos # progr-indeks (st algab 0-st, increment toimub lõpus)
                        all_col_pos = all_col_pos + 1
                    if ts_col > '' and ts_col_pos == -1:
                        ts_col_pos = all_col_pos # viimane veerg, peale sisulisi data veerge, mis kantakse meile
                esimene = True
                for jarjekorranumber, this_row in enumerate(rs):
                    if method == 'ts':
                        # mitmes veerg on TS veerg? eh?
                        last_ts = this_row[ts_col_pos]
                        if last_ts is None:
                            # FATAL!?!
                            self.log('ERROR', f'Viimase muutuse veeru väärtus on NULL, mida ei saa mitte heaks kiita')
                            continue # või break, või return???
                    value_part_str = self.make_insert_value_part(this_row, len(all_cols_array), esimene)
                    conflict_set_part = self.make_insert_conflict_set_part(all_cols_array) # panna välistamise massiiv ka? pkColsArray
                    sql_ins_upd = f'''
                        INSERT INTO {schema_name}.{table_name} ({all_cols}) VALUES ({value_part_str})
                        ON CONFLICT ON CONSTRAINT ak_{table_name}_4_uniq DO UPDATE
                        SET {conflict_set_part}
                    '''
                    bm.run(idx_trg, sql_ins_upd, False, True)
                    if method == 'ts':
                        self.context.save_task_sync_until_ts(self.task_id, last_ts) # after each row => slower => less fragile (easier to continue)
                    esimene = False
                
                if method == 'ts':
                    sql_need = f'''SELECT case when '{last_ts}'::timestamp + '2 minutes'::interval > current_timestamp THEN 0 ELSE 1 END'''
                    need_for_more_rs = bm.run(idx_trg, sql_need, True, True)
                    if need_for_more_rs[0][0] == 0:
                        break
                else:
                    break   # kui ei olnud ajaveergu olemas (ei soovitud tuvastada aja abil muutusi), siis väljume tsüklist peale esimest läbimist 

            if len(rs) < 3000: # esialgne ümbertee MS SQL ajamuredele
                break

        self.log('INFO', f'ekspordisamm on tehtud')
        return tulem
    
    
    def do_action(self) -> bool:
        
        self.last_error = None
        
        _, target_schema, target_table = split_task_id(self.task_id)
        file_element = 'file'
        existing_files = self.collect_files(file_element)
        if not existing_files:
            logger.error(f"No files for tag {file_element} in {self.task_dir}")
            return False
        
        source_select = self.read_sql_from_file(existing_files[0], []) # siin on asenduseks nt in schema names -- millistest vaja, või kõik?
        
        result_set = self.hub.run(self.route_alias, source_select)
        
        if not result_set:
            logger.warning(f"No data from {self.route_alias}")
            return True
        
        
        prepare_temp = f"""DROP TABLE IF EXISTS current_import"""
        logger.debug(prepare_temp)
        self.hub.run(self.target_alias, prepare_temp, False)
        
        create_temp = f"""CREATE TEMP TABLE current_import 
            (schema_id integer, schema_name varchar(100), table_id integer, table_name varchar(100), table_comment text)"""
        logger.debug(create_temp)
        self.hub.run(self.target_alias, create_temp, False)
        
        for row in result_set:
            sql_ins = f"""INSERT INTO current_import(schema_id, schema_name, table_id, table_name, table_comment) 
                VALUES ({row[0]}, '{row[1]}', {row[2]}, '{row[3]}', '{row[4]}') """ 
            self.hub.run(self.target_alias, sql_ins, False)
        
        # compare -- simple variant (delete and insert)
        sql_truncate = f"""DELETE FROM {target_schema}.{target_table} WHERE true"""
        logger.debug(sql_truncate)
        self.hub.run(self.target_alias, sql_truncate, False)
        
        sql_refresh = f"""INSERT INTO {target_schema}.{target_table} (schema_id, schema_name, table_id, table_name, table_comment) 
            SELECT schema_id, schema_name, table_id, table_name, table_comment FROM current_import"""
        logger.debug(sql_refresh)
        self.hub.run(self.target_alias, sql_refresh, False)
        
        logger.debug(prepare_temp)
        self.hub.run(self.target_alias, prepare_temp, False) # polite!
        
        logger.info('done')
        return True



    