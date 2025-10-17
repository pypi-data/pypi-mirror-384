from loguru import logger
from dapu.agents.agent import AgentGeneric
from typing import Callable
from dapu.perks import split_task_id
from dapu.perks import make_replacements, read_sql_from_file
from dbpoint.datacolumn import DataColumn

class Agent(AgentGeneric):
    '''
    stream - uses dbpoint/hub copy feature (currently, 09.02.2025, broken)
    '''
       
    def do_action(self) -> bool:
        _, target_schema, target_table = split_task_id(self.task_id)

        file_element = 'file'
        existing_files = self.collect_files(file_element)
        if not existing_files:
            logger.error(f"No files for tag {file_element} in {self.task_dir}")
            return False
        full_file_name = existing_files[0]

        sql: str = read_sql_from_file(full_file_name) # no replacements here (reason is...?)
        
        map_columns: dict = None # FIXME
        
        # columns tuleb lähtebaasi päringust
        #truncate_table = True
        #create_table = True
        full_table_name = f"{target_schema}.{target_table}"
        temp_name = 'juu'
        logger.debug(f"STREAMING...from {self.route_alias}")
        
        if sql: # empty sql is ok and returns True
            logger.debug(f"{self.task_id} stream import step")
            #print(f"striiming... from {self.route_alias}")
            #flow : Iterable = self.context.hub.get_driver(self.route_alias).stream
            
            fn_once : Callable = self.fn_once()
            fn_once = None # reeeeeeeeeeeeeeeeeeeeeeeeeee gggggggggggggggggggg
            fn_prep_cmd : Callable = self.fn_prepare_insert_to_target(target_schema, target_table)
            fn_before : Callable = self.fn_side_effects_truncate_target(target_schema, target_table)
            fn_save : Callable = self.fn_save()
            
            cnt = self.context.hub.copy_to(sql, self.route_alias, fn_once, fn_before, fn_prep_cmd, fn_save)
            if cnt < 0:
                logger.error(f"{self.task_id} has error on import")
                if cnt < -1: # at least one row was saved (-2 means that error was in second row)
                    # we may want save pointer (last ts, last id etc)
                    ...
                    logger.warning(f"{self.task_id} failed, but some rows were imported, {(-cnt) -1}")
                return False
            if cnt == 0:
                logger.warning(f"{self.task_id} did not import rows!")
            else:
                logger.info(f"{self.task_id} imported {cnt} rows")
        
        self.context.disconnect_alias(self.route_alias)
        logger.debug(f"STREAMING anyway ended and {self.route_alias} is disconnected now")
        return True

    
    def fn_once(self):
        def dummy():
            return None
        
        def do_once():
            route_alias = self.route_alias
            cols_def = self.context.hub.get_columns_definition(route_alias) # last query, was just executed..
            map_columns = None # FIXME
            if map_columns is None:
                list_columns = ', '.join([col_def['name'] for col_def in cols_def])
                posinfo = [jrk for jrk, col_def in enumerate(cols_def)]
            else:
                list_columns = ', '.join([map_columns[col_def['name']] for col_def in cols_def if col_def['name'] in map_columns and map_columns[col_def['name']] != ''])
                posinfo = [jrk for jrk, col_def in enumerate(cols_def) if col_def['name'] in map_columns and map_columns[col_def['name']] != '']
            typeinfo = [(col_def['class'], col_def['needs_escape']) for col_def in cols_def]
            #logger.debug(f"Columns are {list_columns}")
            return {"columns" : list_columns, "pos" : posinfo, "type" : typeinfo}
        #return do_once
        return dummy

    
    def fn_side_effects_drop_temp(self, temp_name) -> Callable:
        def do_side_effects():
            sql = f"DROP TABLE IF EXISTS {temp_name}"
            self.context.target(sql, False)
            return True
        return do_side_effects


    def fn_side_effects_truncate_target(self, target_schema, target_table) -> Callable:
        def do_side_effects():
            sql = f"TRUNCATE TABLE {target_schema}.{target_table}"
            self.context.target(sql, False)
            return True
        return do_side_effects


    def fn_side_effects_drop_target(self, target_schema, target_table) -> Callable:
        def do_side_effects():
            sql = f"DROP TABLE IF EXISTS {target_schema}.{target_table}"
            self.context.target(sql, False)
            return True
        return do_side_effects
    
    
    def fn_side_effects_truncate_temp(self, temp_name) -> bool:
        def do_side_effects():
            sql = f"TRUNCATE TABLE {temp_name}"
            self.context.target(sql, False)
            return True
        return do_side_effects
    
    
    def fn_save(self) -> Callable: # one save command (usually on row insert)
        def do_save(cmd, pos):
            logger.info(f"in save row, {cmd}")
            try:
                self.context.target(cmd, False)
            except Exception as e1:
                logger.error(f"Pos {pos} has error")
                logger.error(f"{cmd}")
                return False
            return True # if not exception
        return do_save


    def fn_escape_old(self) -> Callable :
        def do_escape(cell_value, v2, v3):
            logger.info("escape - old")
            ## v2 = typeinfo[cell_pos][0]
            ## v3 = typeinfo[cell_pos][1]
            return self.context.hub.prepare(self.context.TARGET_ALIAS, cell_value, v2, v3)
        return do_escape

    
    def fn_escape(self) -> Callable :
        def do_escape(value, definition: DataColumn):
            return self.context.hub.sql_string_value(self.context.TARGET_ALIAS, value, definition)
        return do_escape

    def fn_prepare_insert_to_temp(self, temp_table):
        def prepare_row_for_insert(row : list | tuple, perma : dict) -> str:
            logger.info("in prepare row for insert - temp")
            list_columns = perma.get('columns')
            if list_columns is None:
                logger.error(f"No columns ?!?!")
                return ''
            posinfo = perma['pos']
            typeinfo = perma['type']
            esca = self.fn_escape()
            row_insert_values = ", ".join([esca(cell_value, typeinfo[cell_pos][0], typeinfo[cell_pos][1]) for cell_pos, cell_value in enumerate(row) if cell_pos in (posinfo)])
            cmd = f"INSERT INTO {temp_table} ({list_columns}) VALUES ({row_insert_values})"
            return cmd
        return prepare_row_for_insert


    def fn_prepare_insert_to_target_old(self, target_schema, target_table):
        def prepare_row_for_insert(row : list | tuple, perma : dict) -> str:
            logger.info("in prepare row for insert - old")
            if perma is None:
                logger.error(f"No no no ??!")
                return ''
            list_columns = perma.get('columns')
            if list_columns is None:
                logger.error(f"No columns ?!?!")
                return ''
            posinfo = perma['pos']
            typeinfo = perma['type']
            esca = self.fn_escape()
            #row_insert_values = ", ".join([esca(cell_value, typeinfo[cell_pos]) for cell_pos, cell_value in enumerate(row) if cell_pos in (posinfo)])
            row_insert_values = ", ".join([esca(cell_value, typeinfo[cell_pos][0], typeinfo[cell_pos][1]) for cell_pos, cell_value in enumerate(row) if cell_pos in (posinfo)])
            cmd = f"INSERT INTO {target_schema}.{target_table} ({list_columns}) VALUES ({row_insert_values})"
            return cmd
        return prepare_row_for_insert
    
    def fn_prepare_insert_to_target(self, target_schema, target_table):
        def prepare_row_for_insert(row : list | tuple, definitions: list[DataColumn]) -> str:
            logger.info("in prepare row for insert - target")
            if definitions is None:
                logger.error(f"No no no ??!")
                return ''
            list_columns = ', '.join([col_def.colname for col_def in definitions])
            row_insert_values = ', '.join([sql_string_value(row[pos], definitions[pos]) for pos, row_data in enumerate(row)]) # row[pos] == row_data
            cmd = f"INSERT INTO {target_schema}.{target_table} ({list_columns}) VALUES ({row_insert_values})"
            logger.error(cmd)
            print(cmd)
            return cmd
        return prepare_row_for_insert


def sql_string_value(value, datacolumn: DataColumn, for_null: str = 'NULL') -> str:
    """
    Knowing value and some info about its general type, return string which will be part of SQL command (eg INSERT) 
    where texts and times are surrounded with apostrophes and empty strings are replaced with nulls for numbers and dates
    and texts are escaped (this one is made using by profile name what is wrong -- taking data from source and saving to target the target rules must be followed)
    """
    #logger.info(value)
    logger.info(datacolumn)
    if value is None:
        return for_null # NULL (without surronding apostrophes)
    if datacolumn.is_literal_type():
        return str(value) if value else for_null
    if datacolumn.class_name == 'TIMESTAMP':
        return f"'{value}'" if value else for_null # if value then with surroundings, otherwise NULL without
    #driver_module: ModuleType = self.get_driver(profile_name)
    #escaped_value = driver_module.escape(value) or value
    #f"'{escaped_value}'"
    escaped = value.replace("'", "''") # ' -> ''
    return f"'{escaped}'"