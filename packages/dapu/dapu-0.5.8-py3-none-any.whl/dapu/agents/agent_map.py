from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id
from dapu.placeholder import Placeholder

class Agent(AgentGeneric):
    '''
    DEPRECATED!!!
    map = create table as
    niru nimi (ja kasuta parem agenti shadow)
    ja sisu on sama, mis runsql agendil (v.a nimeline drop)
    '''

#    PLACEHOLDER_TARGET_SCHEMA = '{{target_schema}}'
#    PLACEHOLDER_TARGET_TABLE = '{{target_table}}'
#    PLACEHOLDER_TARGET_TABLE_SHADOW = '{{target_table_shadow}}'
    
        
    def do_action(self) -> bool:
        file_element = 'file'
        existing_files = self.collect_files(file_element)
        if not existing_files:
            logger.error(f"No files for tag {file_element} in {self.task_dir}")
            return False
        
        _, schema_name, table_name = split_task_id(self.task_id)
        replacements: list[tuple[str | Placeholder, str]] = []
        replacements.append((Placeholder.TARGET_SCHEMA, f'{schema_name}'))
        replacements.append((Placeholder.TARGET_TABLE, f'{table_name}'))
        
        return self.apply_files_to_target(existing_files, replacements)
    
    
    