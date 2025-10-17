"""
This is a Agent in Dapu framework, so dapu.perks is awailable
"""
from loguru import logger
import os
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id
from dapu.perks import generate, calculate_dir_hash, temporary_dir_context, content_to_file
from dapu.perks import make_column_creation_expression, type_mapper_code_2_function, compress_temp_dir


class Agent(AgentGeneric):
    """
    Generator (for hauling definitions)
    Assumes that metadata is already grabbed into PG, selects those from own database (not original source database)
    Uses two SQL: first for all tables, second for columns inside one table (by table name, markup) 
        both SQLs have schema name fixed (TODO later to variable/multi-schema) - for ASA database usually 'dba' as schema
    
    Puts result into target table as new line if there are no similar line (route_code, schema_name, table_name, package_hash)
    
    Result will be generated using 3 template files -- can we make it more dynamic?
        haulwork.yaml
        input.sql
        ver/001.sql

    And ZIP-ed into correct structure
    """
    
    def get_file_content_by_action_reference(self, key_name_in_action: str) -> str | None:
        """
        Reads text from file pointed from definition, if not str but list then first file
        """
        existing_files = self.collect_files(key_name_in_action)
        if not existing_files:
            logger.error(f"No files for tag {key_name_in_action} in {self.task_dir}")
            return None
        return self.read_sql_from_file(existing_files[0], [])


    def prechecks(self) -> bool:
        target_info : dict = self.action.get('target')
        if target_info is None:
            logger.error(f"No target info in definition")
            return False
        
        route_code = target_info.get('route') # route for generated task (not for task which uses agent_gen)
        if route_code is None:
            logger.error(f"No route info in definition")
            return False
            
        schema_name = target_info.get('schema') # schema for generated task (schema in target database)
        if schema_name is None:
            logger.error(f"No schema info in definition")
            return False
        
        if 'templates' in self.action:
            for template in ['def', 'sql', 'ver']:
                if template not in self.action['templates']:
                    logger.error(f"Missing {template}-template in definition")
                    return False
        else:
            logger.error(f"No templates info in definition")
            return False

        return True # everything looks fine


    def do_action(self) -> bool:
        # result files names
        result_name_sql = 'input.sql'
        result_name_def = 'haulwork.yaml'
        result_name_ver = '001.sql'
        ver_sub_folder = 'ver'
        _, target_schema, target_table = split_task_id(self.task_id)

        if not self.prechecks(): # checks existence next keys but dont read them, so read it after (no check needed later)
            return False

        if (tables_select := self.get_file_content_by_action_reference('table_file')) is None: # walrus operator py 3.8
            return False
        # LETS DEMAND: SELECT table_name, table_comment, table_id

        if (columns_select := self.get_file_content_by_action_reference('columns_file')) is None:
            return False
        # LETS DEMAND: SELECT col_pos, col_name, col_type, col_width, col_scale, col_primary, col_comment

        fully_excluded_file_list = [] # täielikult välistatud tabelid
        if 'exclude' in self.action:
            if 'full' in self.action['exclude']:
                fully_excluded_file_list = self.action['exclude']['full']

        route_code = self.action['target']['route'] # route to use inside generated target
        schema_name = self.action['target']['schema']
        # file names 
        template_name_def = self.action['templates']['def']
        template_name_ver = self.action['templates']['ver']
        template_name_sql = self.action['templates']['sql']
        fn_mapper = type_mapper_code_2_function(self.action.get('type_mapper'))

        result_set = self.hub.run(self.route_alias, tables_select) # result_tuples
        
        if not result_set:
            logger.warning(f"No data from {self.route_alias}")
            return True
            
        added: int = 0
        for row in result_set: # for each table
            table_name = row[0]

            if table_name in fully_excluded_file_list:
                continue
            logger.debug(f"  Working with table {table_name}")

            sql = columns_select # always take fresh one where tags are not replaced yet
            for replacement in [('{{table_name}}', table_name)]:
                sql = sql.replace(replacement[0], replacement[1])
            col_tuples = self.hub.run(self.route_alias, sql)
            select_columns_str = ", ".join([col_tuple[1] for col_tuple in col_tuples])
            create_columns_str = "\n, ".join([make_column_creation_expression(col_tuple, fn_mapper) for col_tuple in col_tuples])
            
            my_data : dict = {
                "route_code" : route_code
                , "schema_name" : schema_name
                , "table_name" : table_name
                , "columns" : col_tuples
                , "select_columns" : select_columns_str 
                , "create_columns" : create_columns_str
                , "select_file_name" : result_name_sql
                }
            content_def = generate(my_data, self.task_dir, template_name_def)
            content_ver = generate(my_data, self.task_dir, template_name_ver)
            content_select = generate(my_data, self.task_dir, template_name_sql)

            # lets make file-hierarhy
            # assuming we are in haul_dir
            # haulwork.yaml, input.sql, ver/001.sql
            package_hash = None # lõppsaaduseks oleva zip-faili räsi (mida PG insert-conflict arvestab) 
            with temporary_dir_context() as content_temp_dir:
                logger.debug(f"Source files to zip later will be put into {content_temp_dir}")
                # save prepared text-content to files in new temporary folder  
                content_to_file(content_def, content_temp_dir, result_name_def)
                content_to_file(content_select, content_temp_dir, result_name_sql)
                content_to_file(content_ver, os.path.join(content_temp_dir, ver_sub_folder), result_name_ver)
                
                package_hash = calculate_dir_hash(content_temp_dir) # always calculate hash with own method to get same hash for same content 
                logger.debug(f"Hash of temp-dir content is {package_hash}")
                package_file_hex = compress_temp_dir(content_temp_dir)
            # end with -- temporary files in temporary dir
            
            if not package_hash:
                continue
            
            sql_ins = f"""INSERT INTO {target_schema}.{target_table}
                (route_code, schema_name, table_name, package_hash, package_file) 
                VALUES ('{route_code}', '{schema_name}', '{table_name}', '{package_hash}', decode('{package_file_hex}', 'hex')::bytea) 
                ON CONFLICT ON CONSTRAINT ak_{target_table}_4_uniq DO NOTHING
                RETURNING id """ 
            new_row_with_id = self.hub.run(self.target_alias, sql_ins)
            if new_row_with_id:
                added += 1
                logger.info(f"Generation of {table_name} is done {new_row_with_id[0][0]}")
        
        logger.info(f"Done generation of {added} items")
        return True



