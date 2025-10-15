# Importing necessary modules
import os
import json
import logging
from logging import Logger
import traceback
from typing import Dict, List
from datetime import datetime, date

# Importing necessary modules for sql operations
import pandas as pd
import mysql.connector
from mysql.connector import Error

# Importing necessary logger module from 'src.emp_logger'
from emp_utl.emp_logger.utl_logger import find_project_root

# Function to disable foreign key check
def disable_fk_check(
    SCHEMA: str,
    cursor: mysql.connector,
    logger: Logger
    ) -> None:
    """
    Turns off the foreign key check of MySQL Server for more flexibility

    Args:
        SCHEMA (str): The name of the SCHEMA for an informative print-output
    """

    try:
        cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
        logger.info('Foreign Key Checks disabled')
    except Exception as e:
        logger.error(f'Error occurred in disabling foreign key check on SCHEMA \'{SCHEMA}\': {repr(e)} - Trace: {traceback.print_exc()}')
        raise

# Function to enable foreign key check
def enable_fk_check(
    SCHEMA: str,
    cursor: mysql.connector,
    logger: Logger
    ) -> None:
    """
    Turns on the foreign key check of MySQL Server for more stability
    
    Args:
        SCHEMA (str): The name of the SCHEMA for an informative print-output
    """
    
    try:
        cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
        logger.info('Foreign Key Checks enabled')
    except Exception as e:
        logger.error(f'Error occurred in enabling foreign key check on SCHEMA \'{SCHEMA}\': {repr(e)} - Trace: {traceback.print_exc()}')
        raise

# Function to execute sql script
def run_sql_script(
    cursor: mysql.connector,
    logger: Logger
    ) -> None:
    '''
    Execute SQL queries from a file in a MySQL database.

    Parameters:
    sql_file (str): The content of the SQL file to execute.
    title (str): A title or description of the SQL file for logging purposes.

    This function takes a SQL file as a string and a title to execute a series of SQL queries
    in a MySQL database. The SQL file content should contain one or more SQL queries separated by semicolons.

    Example:
    run_mysql_file("CREATE TABLE ...; INSERT INTO ...;", "Table Creation and Data Insertion")
    
    Note:
    - The function splits the SQL content into individual queries and executes them sequentially.
    - Any exceptions during SQL execution are logged as errors, and successful execution is logged as info.
    - Make sure to handle database connection and cursor outside of this function.

    Returns:
    None
    '''
    # Find the project root
    root_dir = find_project_root()
    if root_dir is None:
        root_dir = os.getcwd()  # Default to current working directory if no root is found

    sql_folder = os.path.join(root_dir, 'sql')
    if not os.path.exists(sql_folder):
        logger.error(f"SQL directory not found at: {sql_folder}")
        raise FileNotFoundError(f"SQL directory not found at: {sql_folder}")

    sql_files = [os.path.join(sql_folder, f) for f in os.listdir(sql_folder) if f.endswith('.sql') and 'dummy' not in f.lower()]

    # Sort files for consistent execution order
    sql_files.sort()

    for sql_file in sql_files:
        try:
            # Extract the filename without extension for logging
            filename = os.path.splitext(os.path.basename(sql_file))[0]
            logger.info(f"Executing SQL file: {filename}")

            queries = []
            delimiter = ';'
            query = ''

            # Read and parse the SQL file
            with open(sql_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('DELIMITER'):
                        delimiter = line.split()[1]  # Update the delimiter
                    else:
                        query += line + '\n'
                        if line.endswith(delimiter):
                            queries.append(query.strip().strip(delimiter))
                            query = ''

            # Execute queries
            for _, query in enumerate(queries):
                if query.strip():  # Skip empty queries
                    cursor.execute(query)

            logger.info(f"Successfully executed SQL file: {filename}")

        except Error as e:
            logger.error(f"Error executing SQL file: {filename}. Error: {e}")
            raise
    
# Function to extract dataframe rows into VALUE string
def get_values(df: pd.DataFrame) -> str:
    '''
    Extract and format values from a Pandas DataFrame for SQL insertion.

    Parameters:
    df (pd.DataFrame): The Pandas DataFrame containing the data to extract.

    This function takes a Pandas DataFrame and extracts its values, formatting them for SQL insertion.
    Any NaN values in the DataFrame are replaced with a specified null value ('1900-01-01 00:00:00').

    Example:
    df = pd.DataFrame({'column1': [1, 2, np.nan], 'column2': ['A', 'B', 'C']})
    values = get_values(df)

    Note:
    - The function iterates through the rows of the DataFrame, processing each row's values.
    - The resulting values are formatted as SQL-ready tuples.
    - Any exceptions during value extraction are logged as errors, and successful extraction is logged as info.

    Returns:
    str: A formatted string containing the extracted values for SQL insertion.
    '''
    
    null_val = '1970-01-01 00:00:01'
    vals = ''

    for _, row in df.iterrows():
        row_values = [
            json.dumps(val) if isinstance(val, dict) else
            f"{val.strftime('%Y-%m-%d')}" if isinstance(val, (date, datetime)) and pd.notnull(val) else
            val if pd.notnull(val) else
            null_val
            for val in row
        ]
        row_string = str(tuple(row_values)) + ', '
        vals += row_string

    return vals[:-2]

# Function to reset null_values
def update_null_values(
    SCHEMA: str,
    table_name: str,
    cursor: mysql.connector,
    connection: mysql.connector,
    logger: Logger
    ) -> None:
    '''
    Update null values in specified columns of a MySQL table.

    Parameters:
    table_name (str): The name of the MySQL table to update.

    This function queries the information schema to retrieve column names and data types
    for the specified MySQL table and then updates null values in columns of type 'date' or 'varchar'.
    It replaces values matching '1900-01-01%' with NULL.

    Example:
    update_null_values("employee_data")

    Note:
    - The function constructs SQL UPDATE queries for each eligible column.
    - It iterates through the columns, executing the update queries as needed.
    - Any exceptions during SQL execution are logged as errors.

    Returns:
    None
    '''
    try:
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_schema.COLUMNS WHERE TABLE_schema='{SCHEMA}' AND TABLE_NAME = '{table_name}';")
        column_info = cursor.fetchall()
    except Error as e:
        logger.error(f'Error occured in selecting column definition for table \'{table_name}\': {repr(e)} - Trace: {traceback.print_exc()}')
        raise

    for col in column_info:
        col_name = col[0]
        data_type = col[1]  

        # Building UPDATE statement for specific data types
        if data_type in ['date', 'datetime', 'timestamp', 'varchar', 'text']:
            update_query = f"UPDATE `{SCHEMA}`.`{table_name}` SET `{col_name}` = NULL WHERE `{col_name}` LIKE '1970-01-01%';"

            try:
                cursor.execute(update_query)
                connection.commit()
            except Error as e:
                logger.error(f'Error occurred while updating column \'{col_name}\' in table \'{table_name}\': {repr(e)} - Trace: {traceback.print_exc()}')
                raise
            
# Function to build load dataframe into tables
def insert_into_table(
    SCHEMA: str, df: pd.DataFrame,
    table_name: str,
    cursor: mysql.connector,
    connection: mysql.connector,
    logger: logging.Logger
    ) -> None:
    '''
    Insert data from a Pandas DataFrame into a MySQL table.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the data to insert.
    table_name (str): The name of the MySQL table.

    This function formats the DataFrame values for SQL insertion, inserts the data into the table,
    and updates specific null values. 

    Inner Functions:
    - get_values(df: pd.DataFrame) -> str:
        Extracts and formats DataFrame values for SQL insertion, replacing NaNs with '1970-01-01 00:00:01'.

    - update_null_values(table_name: str) -> None:
        Updates null values in date, datetime, timestamp, varchar, and text columns, setting them to NULL.

    Example:
    insert_into_table(df_country, 'country')

    Returns:
    None
    '''
    
    df_cols: str = '`' + '`, `'.join(df.columns) + '`'
    insert_statement: str = f'INSERT INTO `{SCHEMA}`.`{table_name}` ({df_cols}) VALUES {get_values(df = df)};'

    try:    
        cursor.execute(insert_statement)
        result = cursor.rowcount
        update_null_values(
            SCHEMA = SCHEMA,
            table_name = table_name,
            cursor = cursor,
            connection = connection,
            logger = logger)
    except Error as e:
        logger.error(f'Error occured while inserting into table \'{table_name.title()}: {repr(e)} - Trace: {traceback.print_exc()} - Trace: {traceback.print_exc()}')
        raise
    else:
        logger.info(f'{result} affected rows on table \'{table_name.title()}\'')
    finally:
        connection.commit()
       
# Function to invoke all functions for MySQL Server interactions
def load_mysql(
    env_vars: Dict[str, str],
    schema: str,
    df_dict: Dict[str, pd.DataFrame],
    logger: Logger
    ) -> None:
    """
    Loads data from provided dataframes into MySQL Database after creating schema by executing provided sql scripts
    This function performs the following steps by executing functions above
    
    Steps:
    1. Connecting to MySQL Server using provided environment variables
    2. Disabling foreign key checks to allow flexible table creation and data insertion
    3. Executing sql scripts from directory 'sql' to create schema and tables (if provided also stored functions/procedured and triggers)
    4. Inserting data from the provided dataframes in 'df_dict' Dictionary <table_name (str) / datafram (pandas)> into corresponding table
    5. Re-enables foreign key checks to ensure database integrity and stability
    6. Closing cursor and connection
    
    Args:
        env_vars (Dict[str, str]): A dictionary which holds the configuration- & environment variables loaded priorily from Spring Config Server (CNF-S) or from local OS / Profile
        df_dict (Dict[str, pd.DataFrame]): A dictionary which holds the created dataframes that maps the tables in schema `EMP_SCHEMA_<SERIVCE>`
        
    Raises:
        Exception: If an error occurres during the database connection, sql script execution of data insertion process - MySQL Error is raised
    """
    
    environment: str = env_vars['ENVIRONMENT']
    schema: str = schema
    
    try:
        # Establishing connection to MySQL Server
        connection = mysql.connector.connect(
            host = env_vars['DB_HOST'],
            port = env_vars['DB_PORT'],
            user = env_vars['DB_USER'],
            password = env_vars['DB_PASSWORD']
        )
        
        if connection.is_connected():
            logger.info(f'Connection to MySQL Server on Environment \'{environment}\' successfully established')
            cursor = connection.cursor(buffered = True)
            
            # Executing SQL scripts with function 'run_sql_script'
            disable_fk_check(SCHEMA = schema, cursor = cursor, logger = logger)
            run_sql_script(cursor = cursor, logger = logger)
            
            # Loading dataframes to tables - Perform insert into statement/command
            for table_name, df in df_dict.items():
                insert_into_table(
                    SCHEMA = schema,
                    df = df,
                    table_name = table_name,
                    cursor = cursor,
                    connection = connection,
                    logger = logger
                    )
               
            enable_fk_check(SCHEMA = schema, cursor = cursor, logger = logger)
            cursor.close()
            connection.close()
    except Error as e:
        logger.error(f'Error occurred while connecting to MySQL Server on Environment \'{environment}\': {repr(e)} - Trace: {traceback.print_exc()}')
        raise