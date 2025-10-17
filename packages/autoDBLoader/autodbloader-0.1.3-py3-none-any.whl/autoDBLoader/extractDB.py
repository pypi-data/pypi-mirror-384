from autoDBLoader.validation import AutoDBLoaderValidation
from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import pandas as pd
import logging
import json
import os


logger = logging.getLogger("AutoDBLoader")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class AutoDBLoaderExtractDate:
    
    def __init__(self, json_config):
    
        self.json_config = json_config
        self.tables_finished = []
        self.tables_finished_config = {}
        self.json_tables = self.json_config["tables"]
        self.total_tables = len(self.json_tables)
        self.dict_path = self.json_config["path"].rstrip("/") + "/"
        self.dict_path_log = f"{self.dict_path}log_tables_extract.json"

        self.metadata = MetaData()
        self.engine, self.session = self.__db_conect(self.json_config)

        self.validation = AutoDBLoaderValidation(self.engine, self.json_config)
  

    def __db_conect(self, db_json):
        """
            Establish a database connection based on the given configuration.

            This method determines the type of database (MySQL, PostgreSQL, Oracle) 
            from the configuration and delegates the connection to the appropriate method.

            Args:
                db_json (dict): A dictionary containing database connection parameters, including SGBD type.

            Returns:
                tuple: A tuple containing the SQLAlchemy engine and session objects.

            Raises:
                ValueError: If the SGBD specified is not supported.
            Exception: For any connection errors, which are logged.
        """
        try:
            db = db_json["db"]
            sgbd = db["sgbd"].lower()
            
            if sgbd == "mysql":
                return self.__db_conect_mysql(db_json)
            elif sgbd == "postgres":
                return self.__db_conect_postgre(db_json)
            elif sgbd == "oracle":
                return self.__db_conect_oracle(db_json)
            else:
                raise ValueError("\033[91m❌ The SGBD informed is invalid.\033[0m")

        except Exception as e:
            logger.error(e)
            logger.error("\033[91m❌ Error connecting to database, incorrect parameter.\033[0m")


    def __db_conect_mysql(self, db_json):
        """
            Create a connection to a MySQL database using pymysql.

            Args:
                db_json (dict): A dictionary containing MySQL connection parameters.

            Returns:
                tuple: SQLAlchemy engine and session for the MySQL connection.

            Logs:
                Errors during connection attempts.
        """
        try:
            db = db_json["db"]
            url = f"mysql+pymysql://{db['username']}:{db['password']}@{db['hostname']}:{db['port']}/{db['database']}?charset=utf8mb4"
            engine = create_engine(url, connect_args={"connect_timeout": 300})
            Session = sessionmaker(bind=engine)
            session = Session()
            return engine, session
        except Exception as e:
            logger.error(e)
            logger.error("\033[91m❌ Error connecting to database.\033[0m")
    

    def __db_conect_postgre(self, db_json):
        """
            Create a connection to a PostgreSQL database using psycopg2.

            Args:
                db_json (dict): A dictionary containing PostgreSQL connection parameters.

            Returns:
                tuple: SQLAlchemy engine and session for the PostgreSQL connection.

            Logs:
                Errors during connection attempts.
        """
        try:
            db = db_json["db"]
            url = f"postgresql+psycopg2://{db['username']}:{db['password']}@{db['hostname']}:{db['port']}/{db['database']}?sslmode=require"
            engine = create_engine(url, connect_args={"connect_timeout": 300})
            Session = sessionmaker(bind=engine)
            session = Session()
            return engine, session
        except Exception as e:
            logger.error(e)
            logger.error("\033[91m❌ Error connecting to database.\033[0m")
          
      
    def __db_conect_oracle(self, db_json):
        """
            Create a connection to an Oracle database using oracledb.

            Args:
                db_json (dict): A dictionary containing Oracle connection parameters.

            Returns:
                tuple: SQLAlchemy engine and session for the Oracle connection.

            Logs:
                Errors during connection attempts.
        """
        try:
            db = db_json["db"]
            url = f"oracle+oracledb://{db['username']}:{db['password']}@{db['hostname']}:{db['port']}/{db['database']}"
            engine = create_engine(url, connect_args={"timeout": 300})
            Session = sessionmaker(bind=engine)
            session = Session()
            return engine, session
        except Exception as e:
            logger.error(e)
            logger.error("\033[91m❌ Error connecting to Oracle database.\033[0m")


    def __extract_tables_name(self):
        """
            Extracts and returns the list of table names from the JSON table configurations.

            Returns:
                list: A list of table names (strings) extracted from self.json_tables.
        """
        tebles_name = []
        for table in self.json_tables:
            tebles_name.append(table["name_table"])
        return tebles_name


    def salvar_log_tabelas(self):
        """
            Saves the log of tables that have already been extracted from the database to a JSON file.

            The log is saved to the file path specified by self.dict_path_log, 
            containing the list or dictionary of finished tables stored in self.tables_finished.

            Logs an info message upon successful saving of the log file.
        """
        with open(self.dict_path_log, "w", encoding="utf-8") as f:
            json.dump(self.tables_finished, f, indent=4)
        logger.info("\033[92mLog of populated tables saved successfully.\033[0m")


    def carregar_log_tabelas(self):
        """
            Loads the log of tables that have already been extracted from a JSON file into the tables_finished variable.

            If the log file specified by self.dict_path_log exists, the content is loaded into self.tables_finished.
            Logs an info message listing the tables already processed.
            If the log file does not exist, logs an info message indicating that processing will start from scratch.
        """
        if os.path.exists(self.dict_path_log):
            with open(self.dict_path_log, "r", encoding="utf-8") as f:
                self.tables_finished = json.load(f)
            logger.info(f"Log found. Tables already populated: {self.tables_finished}")
        else:
            logger.info("No previous logs found. Starting from scratch.")


    def deletar_log_tabelas(self):
        """
            Deletes the JSON log file of tables if it exists.

            Checks if the log file specified by self.dict_path_log exists. 
            If it does, the file is removed and a success message is logged.
            If the file does not exist, an informational message is logged stating that no deletion occurred.
        """
        if os.path.exists(self.dict_path_log):
            os.remove(self.dict_path_log)
            logger.info("\033[92mLog file deleted successfully.\033[0m")
        else:
            logger.info("\033[93mLog file not found. Nothing was deleted.\033[0m")


    def __extract_data_tables(self):
        """
            Main method responsible for extracting data from the database tables.

            Iterates over the list of tables defined in self.json_tables and executes the associated SQL queries 
            to retrieve their data. If no custom query is provided or if the query does not start with 'SELECT', 
            a default 'SELECT * FROM <table>' query is used.

            Steps:
                1. Opens a database connection using the SQLAlchemy engine.
                2. Skips tables already listed in self.tables_finished to avoid reprocessing.
                3. Executes the SQL query for each table.
                4. Loads the retrieved data into a DataFrame via __load_file_to_dataframe().
                5. Updates the log of processed tables by appending to self.tables_finished.
                6. Saves the log and exits on SQLAlchemy errors.

            Error Handling:
                - Catches SQLAlchemyError when executing queries for a specific table, logs the error, 
                saves the processed tables log, and terminates execution.
                - Catches any other unexpected exceptions during the overall extraction process, logs the error, 
                and terminates execution.
        """
        try:
            with self.engine.begin() as conn:
                for table in self.json_tables:
                    name_table = table["name_table"]
                    query = table["query"].strip()
                    
                    if name_table in self.tables_finished:
                        continue
                    
                    if not query.strip().lower().startswith("select"):
                        query = f"SELECT * FROM {name_table}"
                        
                    try:
                        df_data = pd.read_sql_query(query, conn)
                        self.__load_file_to_dataframe(table, df_data)
                        self.tables_finished.append(name_table)
                        logger.info(f"\033[92m✅ Data from table {name_table} successfully extracted.\033[0m")
                        
                    
                    except SQLAlchemyError as e:
                        logger.error(e)
                        logger.error(f"\033[91m❌ Error extracting data from table {name_table}.\033[0m")
                        self.salvar_log_tabelas()
                        exit(1)
                    
        except Exception as e:
            logger.error(e)
            logger.error(f"\033[91m❌ Error extracting data.\033[0m")
            exit(1)


    def __load_file_to_dataframe(self, table_json, df_data):
        """
            Saves the provided DataFrame to a file in the specified format and directory.

            Args:
                table_json (dict): Dictionary containing metadata about the table, including:
                    - "type_file": The desired file format to save the data ("CSV", "PARQUET", or "JSON").
                    - "name_table": The name of the table, used as the filename.
                df_data (pandas.DataFrame): The DataFrame containing the data to be saved.

            Behavior:
                - Saves the DataFrame to a file in the directory specified by self.dict_path.
                - Supported file formats are CSV, Parquet, and JSON (newline-delimited records).
                - Raises a TypeError if the specified file type is unsupported.
        """
        type_file = table_json["type_file"]
        name_table = table_json["name_table"]

        if type_file.upper() == "CSV":
            df_data.to_csv(f"{self.dict_path}{name_table}.csv", index=False)
        elif type_file.upper() == "PARQUET":
            df_data.to_parquet(f"{self.dict_path}{name_table}.parquet", index=False)
        elif type_file.upper() == "JSON":
            df_data.to_json(f"{self.dict_path}{name_table}.json", orient="records", lines=True)
        else:
            raise TypeError(f'File type "{type_file}" is not valid.')


    def _extractDate(self, json):
        """
            Coordinates the full extraction process, including validations, data retrieval, and cleanup.

            Args:
                json (dict): Configuration dictionary containing all required parameters for extraction.

            Workflow:
                1. Validates the structure of the extraction configuration.
                2. Retrieves all table names from the configuration.
                3. Runs all pre-extraction validations for the specified tables.
                4. Loads the log of previously extracted tables to skip them if needed.
                5. Extracts data from the configured tables and saves them to the specified file formats.
                6. Deletes the extraction log file after completion.
                7. Logs a success message upon completion of the process.
        """
        self.validation._validation_structure_dict_extract()

        teble_names = self.__extract_tables_name()
        
        self.validation._validate_all_before_extract(teble_names)
        self.carregar_log_tabelas()
        self.__extract_data_tables()
        self.deletar_log_tabelas()
        
        logger.info("\033[92m==================================================\033[0m")
        logger.info("\033[92m==================================================\033[0m")
        logger.info("\033[92m============= SUCCESSFULL EXTRACTION =============\033[0m")
        logger.info("\033[92m==================================================\033[0m")
        logger.info("\033[92m==================================================\033[0m")