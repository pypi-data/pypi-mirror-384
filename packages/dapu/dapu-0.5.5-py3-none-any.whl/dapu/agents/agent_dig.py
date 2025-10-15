from loguru import logger

from dapu.agents.agent import AgentGeneric
from dapu.process import logging
from dapu.perks import split_task_id

class Agent(AgentGeneric):
    """
    Dig - dig source database to find possible tables to import and prepare definitions and files (those must put to target database (in meta) as blob with zip
    Needs: task_id => schema.table, eg. dig_asjur5.the_table, dig_asjur5.the_column
            => route (from_asjur5) => route_alias 
        first "file" (tabels.sql) -- select for ASA metaquery (columns must correspond to the_table structure)
    
    NB! See dig, mis võtab ja panem metadata kirjetena 2-3 tabelisse on tegelikult tehtav tavalise pump abil
    St tuleb teha iga src baasi jaoks 2-3 tabelit ja 2-3 laadimisülesannet
    saame tuvastada muudatused (__hist tabelisse nt, või changes tabelisse)
    -- see võib olla hea enda juurde muudtuste tegemiseks
    Aga dig tuleks teha ümber selleks, et kes võtab õiged metatabelid ja loob failide kupatuse... mille paneme... kuhu? meta.file_like   
    
    
    yaml:
    once: true
    until_first_error: true
    schemas_cmd: schemas.sql
    tables_in_schema_cmd: tables.sql
    columns_in_table_cmd: columns.sql
    
    """
    
    
    def do_action(self) -> bool:
        
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



    