from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id

class Agent(AgentGeneric):
    """
    drop - töötab tulemtabeliga ja teeb Postgre kiiksuga 
    """
        
    def do_action(self) -> bool:
        _, target_schema, target_table = split_task_id(self.task_id)
        if not target_schema or not target_table:
            return False
        sql = self.make_drop_command(self.target_alias, target_schema, target_table, with_cascade=True)
        if sql > '':
            try:
                logger.info(f"DROP current structure (in target base)")
                self.context.target(sql, False)
            except Exception as e1:
                msg = f"Failed DROP command: {sql}"
                self.last_error = msg
                logger.error(msg)
                return False
        
        # tühja SQL-i ei rakenda ja loeme selle õnnestumiseks
        return True

    # FIXME: repeats in shadow-agent => find reuse solution    
    def make_drop_command(self, target_alias, target_schema: str, target_table: str, with_cascade: bool=False) -> str:
        """
        If object exists in postgre database then return sql command for drop corresponding to object type (table, view, etc)
        Needs database alias
        """
        # Tulembaasis (alati PostrgeSQL) vaja minev tegevus (õiget tüüpi drop käsk) 
        # Postgre metainfo päring, kas objekt on olemas ja mis tüüpi
        
        command = ''  # jääb tühjaks, kui pole vaja droppida
        
        sql = f"""
            SELECT
                CASE 
                    WHEN c.relkind = 'r' THEN 'TABLE' 
                    WHEN c.relkind = 'v' THEN 'VIEW' 
                    WHEN c.relkind = 'm' THEN 'MATERIALIZED VIEW' 
                    ELSE 'ZZ' -- our uncleariness-marker
                END
                , c.relkind -- for debuging unclear state in far future
            FROM pg_class c 
            JOIN pg_namespace tns ON tns.oid = c.relnamespace 
            WHERE tns.nspname = '{target_schema}' AND c.relname = '{target_table}' 
            UNION 
            SELECT 'XX' -- our non-existence marker
                , NULL
            ORDER BY 1
        """
        result_set = self.context.target(sql)
        
        if result_set:
            unit = (result_set[0][0]).upper()  # unit on "TABLE", "VIEW", "MATERIALIZED VIEW" 
            if unit not in ('XX', 'ZZ'):
                command = f'DROP {unit} IF EXISTS {target_schema}.{target_table}'
                if with_cascade:
                    command = command + ' CASCADE'
            if unit == 'ZZ':
                logger.warning("Unclear tabular type: {result_set[0][1]}")

        return command

    