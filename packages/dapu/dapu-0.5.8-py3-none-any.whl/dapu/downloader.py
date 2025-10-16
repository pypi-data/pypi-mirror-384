from loguru import logger
import os
import zipfile
import io
import shutil

from dapu.process import DapuProcess

def unzip_from_memory(zip_bytes, extract_to: str):
    # Create a BytesIO object from the zip bytes
    with io.BytesIO(zip_bytes) as zip_buffer:
        # Open the in-memory zip archive
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # Extract all the files to the specified directory
            zip_ref.extractall(extract_to)
            
def unzip_from_buffer(zip_buffer, extract_to: str):
    # Open the in-memory zip archive
    with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
        # Extract all the files to the specified directory
        zip_ref.extractall(extract_to)
            
def make_dir_empty(folder: str):
    """
    Keeps folder
    """
    logger.info(f"Lets delete all from {folder}")
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                logger.info(f"Deleting file {file_path}")
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                logger.info(f"Deleting subfolder {filename}")
                shutil.rmtree(file_path)
        except Exception as e1:
            print(e1)

class DapuDownloader(DapuProcess):
    
    def run(self) -> int:
        """
        Project gives target connection. Additionally we need some (empty) folder to unpacked files.
        Connect to gen.asjur5 or some other source shapshot meta. Download zip and unpack it. Repeat.  
        """
        logger.info(f"Working directory is {self.context.work_dir}")
        extract_to = self.context.more_args[0][0]
        logger.info(f"Extraction directory in {extract_to}")
        
        # make target dir empty?
        make_dir_empty(extract_to)
        
        sql = """SELECT route_code, schema_name, table_name, package_file, id
            FROM (
                SELECT route_code, schema_name, table_name, package_file, id, row_number() OVER w1 as pos
                FROM gen.asjur5
                WINDOW w1 AS (PARTITION BY route_code, schema_name, table_name ORDER BY created_ts DESC)
            ) as h 
            WHERE pos = 1
            ORDER BY id DESC"""
        
        result_set = self.context.target(sql) 
        count = 0
        zip_error_ids = []
        for row in result_set:
            logger.info(f"{row[4]} - {row[2]}")
            zip_binary = bytes(row[3])
            try:
                unzip_from_memory(zip_binary, os.path.join(os.path.realpath(extract_to), row[0], row[1], row[2]))
                count += 1
            except Exception as e1:
                zip_error_ids.append(str(row[4]))
                print(e1)
        
        id_str = ', '.join(zip_error_ids)
        if id_str:
            sql_del = f"DELETE FROM gen.asjur5 WHERE id IN ({id_str})"
            self.context.target(sql_del, False)
            
        self.context.disconnect_target()
        
        return count
