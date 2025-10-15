from loguru import logger
from dapu.process import DapuProcess
from typing import Callable
from dapu.perks import halt
from dbpoint.datacapsule import DataCapsule

from .textops import yaml_string_to_dict
from .fileops import read_content_of_package_file


class DapuEnabler(DapuProcess):
    """
    Does versioning of meta tables (registry, agenda etc) in meta schema
    Run it on after every deploy/ugrade of package dbpuller to assure thet meta structure corresponds to current version of code  
    """

    def run(self):
        #reconf_logging(self.context.LOG_LEVEL) # with some reason init-time is lost somewhere (datacontroller??)
        logger.info(f"Working directory is {self.context.work_dir}")
        
        if (start_time := self.validate_connection()) is None:
            logger.error(f"Failed to connect to database")

        logger.debug(f"Database time is '{start_time}'")
        
        # build-in (core) versioning
        core_migra_index: dict = self.read_included_toc() or {}
        core_access_function: Callable = self.read_included_file # fn which can read file content from module files
        count = self.run_migration(core_migra_index, core_access_function) # on error halts
        if count > 0:
            logger.info(f"Core versioning done")
        
        # work_dir offered (custom) versioning
        custom_migra_index: dict = self.read_custom_ver_toc() or {}
        custom_access_function: Callable = self.read_custom_file # fn which can read file from local file system
        count = self.run_migration(custom_migra_index, custom_access_function)
        if count > 0:
            logger.info(f"Project versioning done")
            self.notify("Project versioning done") # discord
        self.disconnect_main()

    def read_included_file(self, file_name: str) -> str | None:
        """
        Wrapper who knows (how to find) versioning module name. And then calls read_package_file.
        Reads file content using importlib (so actual place of file is unknown)
        """
        versioning_scripts_package = self.context.PACKAGE_NAME + '.' + self.context.PACKAGE_VER_SUB_DIR # 'dapu.ver'
        return read_content_of_package_file(versioning_scripts_package, file_name)

    def read_custom_file(self, file_name: str) -> str | None:
        """
        Read file content regular way from file system, knowing that context holds info to file path for versioning
        """
        with open(self.context.full_name_from_ver(file_name), 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    
    def read_included_toc(self) -> dict | None:
        """
        Metatables version upgrade files (sql) must reside in submodule "ver" (self.context.PACKAGE_VER_SUB_DIR)
        Index file is changes.yaml.  
        Index file points in correct order to SQL-files.  
        Index file have declared alias (so same metatable can be used for custom versioning too) 
        """
        versioning_scripts_package = self.context.PACKAGE_NAME + '.' + self.context.PACKAGE_VER_SUB_DIR # 'dapu.ver'
        return yaml_string_to_dict(read_content_of_package_file(versioning_scripts_package, self.context.CHANGES_INDEX_FILE_NAME))
    
    def read_custom_ver_toc(self) -> dict | None:
        """
        Read from self.work_dir subfolder "ver"
        """
        yaml_string = self.read_custom_file(self.context.CHANGES_INDEX_FILE_NAME) or ""
        return yaml_string_to_dict(yaml_string)

    def apply_ver(self, sql: str, folder_alias: str, file_name: str, remarks: str='') -> bool:
        """
        Applies internal (package) versioning SQL and saves/logs it
        If dry_run, then just prints out (and all if true, but no ver upgrade marks) 
        """
        if self.apply_sql(sql, with_replacements=True, with_commit=True): # MAIN WORK
            version_table = self.context.find_registry_table_full_name("version")
            file_name = file_name.replace("'", "")
            sql = f"""INSERT INTO {version_table} (folder_alias, file_name, remarks) 
                VALUES ('{folder_alias}', '{file_name}', '{remarks}')"""
            if self.apply_sql(sql, with_replacements=False, with_commit=True): # registering what was done
                logger.info(f"{sql}")
                logger.info(f"{file_name} applied")
                return True
            else:
                logger.info(f"{file_name} WAS OK, but after-actions NOT, rollbacking")
                return False
        else:
            logger.error(f"{file_name} NOT applied")
            return False
     
    def apply_sql(self, capsule: str | DataCapsule, with_replacements: bool = True, with_commit: bool = False) -> bool:
        """
        Runs one SQL file (may have many DDL commands)
        """
        if isinstance(capsule, str):
            capsule = DataCapsule(capsule)
        if with_replacements:
            capsule.set_command(self.context.replace_compatibility(capsule.sql_command))
        capsule.set_flag("on_success_commit", with_commit)
        capsule.set_flag("do_return", False)
        try:
            # apply, but not commit (commit will be after version is saved too)
            capsule = self.context.target(capsule)
            if capsule.last_action_success:
                return True
        except Exception as e1:
            logger.error(str(e1))
        logger.debug(capsule)
        return False

    def get_applied_versions(self, alias) -> list[str]:
        """
        Get short file names (for given alias) what are applied, order is not important
        """
        version_table = self.context.find_registry_table_full_name("version")
        sql = f"""SELECT file_name
            FROM {version_table}
            WHERE folder_alias = '{alias}'
            """
        try:
            return [rec[0] for rec in self.context.target(sql)]
        except Exception as e1: # ignore is needed for very first run
            logger.debug(str(e1)) # we are going to ignore it, but let output it anyway
            return []
    
    def run_migration(self, migra_index: dict, method_for_files: Callable) -> int:
        """
        Runs one migration line, either build-in (core) then files must accessed using importlib
        or custom from ver subfolder using regular file reading
        """
        if not migra_index:
            halt(91, "Nothing to do. Missing index file. This cannot be true")
        alias = migra_index.get('alias', '').replace("'", "").strip()
        if not alias: # both None and '' are bad
            halt(92, "Missing alias in index file. Big mess may happen")
        applied_files = self.get_applied_versions(alias)
        file_names: list = migra_index.get('files', [])
        if not file_names:
            halt(93, f"No files referenced from index file for alias '{alias}'. Unbelievable!")
        files_applied: int = 0 
        for pos, step_info in enumerate(file_names, 1):
            if step_info.get('file') is None:
                continue # nothing to apply
            file_name = step_info.get('file')
            if file_name in applied_files: 
                continue # already applied
            logger.debug(f"Migration for alias {alias} step {pos} file {file_name}")
            sql = method_for_files(file_name) # here is argument of function which is function
            remarks = step_info.get('remarks', '').replace("'", "").strip()
            if not self.apply_ver(sql, alias, file_name, remarks):
                halt(94, f"step {pos}, error on sql in file {file_name}")
            else:
                files_applied += 1
            
        logger.debug(f"Migration of {alias} is done, applied {files_applied} files")
        return files_applied # if any error, then global HALT, so after failing in core, custom cannot run 

    def validate_connection(self) -> str | None:
        """
        Asks current time from database = realistic connection validation (None is failure)
        """
        return self.get_database_time()
