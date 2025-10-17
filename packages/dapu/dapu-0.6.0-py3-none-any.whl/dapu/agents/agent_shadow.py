from loguru import logger
from dapu.agents.agent import AgentGeneric
from dapu.perks import split_task_id
from dapu.placeholder import Placeholder
from dbpoint.datacapsule import DataCapsule

class Agent(AgentGeneric):
    """
    Instead of Agent Map. 
    Makes all calculation into shadow table and afterwards compares with existing table -- delete and rename if needed. So target table downtime time is short.
    """
    def do_action(self) -> bool:

        _, schema_name, table_name = split_task_id(self.task_id)
        _, target_schema, target_table = split_task_id(self.task_id)
        if not target_schema or not target_table:
            return False
        table_name_shadow = f'{table_name}__shadow'
        table_fullname_shadow = f'{schema_name}.{table_name_shadow}' # see ei ole tehniliselt temp tabel, seega vaja skeeminime

        replacements: list[tuple[str | Placeholder, str]] = []
        replacements.append((Placeholder.TARGET_SCHEMA, f'{schema_name}'))
        replacements.append((Placeholder.TARGET_TABLE, f'{table_name}'))
        replacements.append((Placeholder.TARGET_TABLE_SHADOW, f'{table_name_shadow}'))

        input_files = self.collect_files('input')
        if len(input_files) == 0:
            logger.error('Missing main input SQL (file with one command)')
            return False # shadow operatsioon not possibile

        pk_cols_list = self.action.get('pkcol', []) # empty list is not healthy
        # PK tühimassiivi korral tuleks aja kokkuhoiu ja ka lihtsuse mõttes jätta räsiarvutused ära ja eeldada alati muutumist
        # ja erijuht, kui pole tabelit olemaski veel, siis ka pole vaja aega kulutada
        # tabeli eksisteerimise jaoks kasutab toredat drop-lause tekitamise fn-i (tühistring tähendab, et objekti pole)
        deep_calculations = (pk_cols_list and self.make_drop_command(self.target_alias, target_schema, f'{target_table}', with_cascade=True) > '') 
        
        # võimalikud failid, millega laadimiste arendajad saavad juhtida laadimist
        before_files = self.collect_files('before') # self.check_files(task_dir, action_def, 'before') # nt temp tabelite tegemised
        update_files = self.collect_files('update') # self.check_files(task_dir, action_def, 'update') # kui vaja droppida, siis mida teha pärast
        hash_before_files = self.collect_files('hash_before') # self.check_files(task_dir, action_def, 'hash_before') # nt shadow tabeli käsud, mis ei muuda andmeid (index räsi kiirendamiseks)
        hash_after_files = self.collect_files('hash_after') # self.check_files(task_dir, action_def, 'hash_after') # nt shadow tabeli käsud, mis ei muuda andmeid (index räsi kiirendamiseks)
        afternew_files = self.collect_files('afternew') # self.check_files(task_dir, action_def, 'afternew') # kui vaja droppida, siis mida teha pärast
        afterold_files = self.collect_files('afterold') # self.check_files(task_dir, action_def, 'afterold') # kui ei ole droppi, kas on ka midagi
        after_files = self.collect_files('after') # self.check_files(task_dir, action_def, 'after') # igal juhul teha (peab arvestama mõlemast harust tulemise võimalusega)
        
        # kui sihttabel juba olemas, siis arvutada olemasoleva tabeli (sihttabeli) räsi
        row_count_before, super_hash_before = (-1,"") # only for pylance (those vars are assigned and used only inside check "deep_calculations")
        if deep_calculations:
            row_count_before, super_hash_before = self.calc_table_hash(f'{schema_name}.{table_name}', pk_cols_list)
        
        # eeltöö, nt temp tabelid (jäävad alles, kuna ühendus/sessioon vahepeal (ühe operatsiooni sees) ei muutu) ja nende indeksid
        if len(before_files) > 0:
            self.apply_files_to_target(before_files, replacements)
        
        # põhitöö ehk "create table as"
        with open(input_files[0], 'r', encoding="utf-8") as sf:
            sql_input = sf.read()
        for replacement in replacements: # see osa ei peaks ideeliselt sisaldama asendusi, aga jätame võimaluse valla
            sql_input = sql_input.replace(replacement[0], replacement[1])
        
        sql_sh_drop = self.make_drop_command(self.target_alias, target_schema, f'{table_name_shadow}', with_cascade=True)
        if sql_sh_drop > '': # kui on vajadus droppimiseks -- kui eelmine kord lõppes korralikult, siis pole vaja
            logger.debug(f'Teeme eelneva dropi vahetabelile viimasest nurjumisest: {sql_sh_drop}')
            self.context.target(sql_sh_drop, False) # siin on commit
        
        sql_sh_cre = f'''CREATE TABLE {table_fullname_shadow} AS ({sql_input}\n)'''
        self.context.target(sql_sh_cre, False) # siin on commit, see võib aega võtta
        
        # update_files (nt update'd, mis võivad muuta tabeli summat ja seega tuleb teha enne calci)
        if len(update_files) > 0:
            self.apply_files_to_target(update_files, replacements)
        
        if deep_calculations:
            if len(hash_before_files) > 0: # shadow tabelile indekseid, mis tuleb kindlasti hash_afteris maha võtta (tuletan meelde: rename ju) 
                self.apply_files_to_target(hash_before_files, replacements)

            # arvutame vahetabeli räsi
            row_count_after, super_hash_after = self.calc_table_hash(f'{table_fullname_shadow}', pk_cols_list)
            logger.debug(f'{row_count_before} rows, {super_hash_before} old')
            logger.debug(f'{row_count_after} rows, {super_hash_after} new')
            changes_detected = (row_count_before != row_count_after or super_hash_before != super_hash_after)
            
            if len(hash_after_files) > 0: # kui oli shadow räsi jaoks optimeerimisi indeksite loomise näol, siis need maha
                self.apply_files_to_target(hash_after_files, replacements)

        else:
            changes_detected = True # kui pole süviti analüüsi, siis loeme muutunuks ja vaja teha rename 
            
        ok_till_now = True # jääb nii, kui pole vaja rakendada lisakäske. lisakäskude nurjumine muudab false-ks
        
        if changes_detected: # drop siht, rename vahe to siht, rakendada aftercreate kui on
            logger.debug('drop-rename-olukord')
            # drop 
            sql_drop = self.make_drop_command(self.target_alias, target_schema, f'{table_name}', with_cascade=True)
            if sql_drop > '': # kui drop-käsk on tühi, siis puudub vajadus dropida
                logger.debug('hakkab drop')
                self.context.target(sql_drop, False)
                logger.debug('lõppes sisuline drop')
            # rename
            try:
                logger.debug('hakkab alter rename')
                sql_ren = f'''ALTER TABLE {schema_name}.{table_name_shadow} RENAME TO {table_name}'''
                self.context.target(sql_ren, False)
                logger.debug('lõppes rename')
            except Exception as e1:
                logger.error('rename probleem')
                logger.error(str(e1))
            # 
            if len(afternew_files) > 0:
                ok_till_now = self.apply_files_to_target(afternew_files, replacements)
        else: # rakendada insteadcreate kui on, drop shadow
            logger.debug('ignore-olukord (meile tundub, et muudatusi polnud)')
            sql_sh_drop = self.make_drop_command(self.target_alias, target_schema, f'{table_name_shadow}', with_cascade=True)
            if sql_sh_drop > '': # kui drop-käsk on tühi, siis puudub vajadus dropida
                self.context.target(sql_sh_drop, False)
            if len(afterold_files) > 0:
                ok_till_now = self.apply_files_to_target(afterold_files, replacements)
        
        # mõlemal juhul rakendamist vajavad käsud (ideeliselt võiks need olla ka järgmises lihtsas run-operatsioonis)
        if not ok_till_now:
            logger.error('Oli probleem mingis after osas')
            return False
        else:
            if len(after_files) > 0:
                ok_till_now = self.apply_files_to_target(after_files, replacements)
        logger.debug('shadow lahendus lõpetas')
        return ok_till_now # eelmise kõrgema else tulemus, st kui sisemine if annab false, siis mittenähtav else jätab true 

    
    # FIXME: repeats in drop-agent => find reuse solution    
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
                logger.warning(f"Unclear tabular type: {result_set[0][1]}")

        return command
    

    def calc_table_hash(self, full_table_name, pk_cols_list):
        """
        Here those calcs are made in target database only
        """
        
        sql = f'SELECT * FROM {full_table_name}'
        if len(pk_cols_list) == 1:
            pk = pk_cols_list[0].strip()
        else:
            if len(pk_cols_list) == 0:
                pk = 'md5(g::text)'
            else:
                textified_list = []
                for pk_col in pk_cols_list:
                    textified_list.append(pk_col.strip() + '::text')
                pk = "md5(concat_ws('***', " + (', '.join(textified_list)) + "))"
        
        change_count = 8000 # üsna hea konstant
        
        # teeme 3 temp tabelit (__fixTempsSet1(idx_src)) // temp1 = pk, batch (idx), räsi, jrk (row_number(*))
        # võtame kogu SQL-i ja teeme selle insert into ja alampäringuga lisaräsiveeruga ja jrk veeruga ja paneme temp tabelisse 1 (idx_src)
        #    row_number(*) võime hetkel arvestada PG kiiksudega (tühi over vajalik) ja jrk vahele jätta => kohe kimp (batch) ära arvutada
        # leiame temp1 tabelile idx_src batch-id (jrk abil, 10K kaupa)
        # arvutame temp2 tabeli portsude kaupa kirjed ja räsid
        # arvutame temp3 ehk tabeli koguräsi
        sql_drops: list[str] = ["drop table if exists t1", "drop table if exists t2", "drop table if exists t3"]
        for pos, sql_drop in enumerate(sql_drops, 1):
            capsule = DataCapsule(sql_drop)
            capsule.set_flag("commit_on_success", False)
            capsule = self.context.target(capsule, False)
            if not capsule.last_action_success:
                raise Exception(f"temp-error, pos {pos}")
        
        sql_fill_temp = f'''create temp table t1 (pk, kimp, rasi) as (
            select {pk}, (((row_number(*) over (order by {pk})) -1) / {change_count}) + 1, md5(g::text) from ({sql}\n) as g
        )'''
        try:
            capsule = DataCapsule(sql_fill_temp)
            capsule.set_flag("commit_on_success", False)
            capsule = self.context.target(capsule, False)
        except Exception: # esimesel korral, kui tabelit pole olemas juhtub see
            # self.log('ERROR', f'{e1}')
            return (-1, 'y')

        sql_fill_temp = f'''create temp table t2 (kimp, ridu, rasi) as (
            select kimp, count(*), md5(string_agg(rasi, '.'))
            from t1 group by kimp
        )'''
        capsule = DataCapsule(sql_fill_temp)
        capsule.set_flag("commit_on_success", False)
        capsule = self.context.target(capsule, False)

        sql_fill_temp = f'''create temp table t3 (ridu, kimpe, rasi) as (
            select sum(ridu), count(*), md5(string_agg(rasi, '.')) from t2
        )'''
        capsule = DataCapsule(sql_fill_temp)
        capsule.set_flag("commit_on_success", False)
        capsule = self.context.target(capsule, False)
        #' self.log('WARNING', 't1..t3 täidetud')

        sql_table_hash = f'select ridu, kimpe, rasi from t3'
        capsule = DataCapsule(sql_table_hash)
        capsule.set_flag("commit_on_success", False)
        capsule = self.context.target(capsule)

        if not capsule or len(capsule) == 0:
            hash_remote = 'x'
            ridu_remote = -1
        else:
            hash_remote = capsule[0][2] # rasi
            ridu_remote = capsule[0][0] # ridu        
        return (ridu_remote, hash_remote)
    