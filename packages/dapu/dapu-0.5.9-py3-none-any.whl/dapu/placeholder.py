from enum import StrEnum

class Placeholder(StrEnum):
    """
    What are generally allowed placehodlers in text files or sql-strings 
    """
    TARGET_SCHEMA = '{{target_schema}}'
    TARGET_TABLE = '{{target_table}}'
    TARGET_TABLE_SHADOW = '{{target_table_shadow}}'
    TARGET_KEY_COLUMNS = '{{key_columns}}'
    TARGET_DATA_COLUMNS = '{{data_columns}}'
    LAST_VALUE_TS = '{{last_ts_value}}'
    SOURCE_COLUMN_TS = '{{ts_column}}'
    SOURCE_COUNT_SKIP = '{{skip_count}}' # aka OFFSET, human interpretable ("skip 3" means "start from 4th")
    SOURCE_COUNT_LIMIT = '{{limit_count}}'
    