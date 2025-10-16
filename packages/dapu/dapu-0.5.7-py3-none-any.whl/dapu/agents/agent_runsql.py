from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id
from dapu.placeholder import Placeholder

class Agent(AgentGeneric):
    """
     - do: runsql
       file: somefile.sql
     - do: runsql
       file: 
        - firstfile.sql
        - secondfile.sql
    """
    myname: str = 'runsql'
    
    def do_action(self) -> bool:
        """
        Collects files (using element named "file"). If no file exists interprets as error (returns False). 
        Replaces {{target_schema}} and {{target_table}} in files. 
        Applies all files (to target database).
        """
        logger.info(f"start {self.myname} for {self.task_id}")
        file_element = 'file'
        existing_files = self.collect_files(file_element)
        if not existing_files:
            logger.error(f"No files for tag {file_element} for {self.task_id}") #  in {self.task_dir}
            return False
    
        _, schema_name, table_name = split_task_id(self.task_id)
        key_columns = ', '.join(self.action.get('key_columns', []))
        data_columns = ', '.join(self.action.get('data_columns', []))
        
        replacements: list[tuple[str | Placeholder, str]] = []
        replacements.append((Placeholder.TARGET_SCHEMA, f'{schema_name}'))
        replacements.append((Placeholder.TARGET_TABLE, f'{table_name}'))
        replacements.append((Placeholder.TARGET_KEY_COLUMNS, f'{key_columns}'))
        replacements.append((Placeholder.TARGET_DATA_COLUMNS, f'{data_columns}'))
        
        result: bool = self.apply_files_to_target(existing_files, replacements)
        logger.info(f"done {self.myname} for {self.task_id}")
        return result
