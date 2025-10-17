from sqlalchemy.exc import SQLAlchemyError
from jsonschema import Draft7Validator
from sqlalchemy import text, MetaData
import pyarrow.parquet as pq
import pandas as pd
import logging
from . import config
import os

logger = logging.getLogger("AutoDBLoader")

logger.setLevel(logging.DEBUG)

if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class AutoDBLoaderValidation:
    
    def __init__(self, engine, json_config):
        
        self.engine = engine
        self.json_config = json_config
        self.json_tables = self.json_config["tables"]
        
        self.TYPE_COMPATIBILITY = config.TYPE_COMPATIBILITY
        self.schema_config_extract = config.SCHEMA_CONFIG_EXTRACT
        self.schema_config_insert = config.SCHEMA_CONFIG_INSET


    def _validation_structure_dict_insert(self):
        """
            Validates the structure of the configuration dictionary for the insert process.

            Uses JSON Schema Draft7Validator to check if the configuration dictionary
            adheres to the expected schema. If any validation errors are found, they
            are logged with their paths and messages, and the program exits with an error.

            Logs a success message if the structure is valid.

            Raises:
                Exits the program with status 1 if validation fails.
        """
        validator = Draft7Validator(self.schema_config_insert)
        errors = sorted(validator.iter_errors(self.json_config), key=lambda e: e.path)
        if errors:
            logger.error("\033[91m⚠️ Errors found while validating the structure of the configuration dictionary:\033[0m")
            for error in errors:
                path = " -> ".join(map(str, error.path))
                logger.error(f"\033[91mError in {path}: {error.message}\033[0m")
            exit(1)
            
        logger.info("\033[92m✅ The structure of the configuration dictionary is valid.\033[0m")


    def _validation_structure_dict_extract(self):
        """
            Validates the structure of the configuration dictionary for the data extraction process.

            Uses JSON Schema Draft7Validator to verify that the configuration dictionary
            matches the expected schema. If validation errors occur, logs each error's
            path and message as warnings, then exits the program with an error.

            Logs a success message if the structure is valid.

            Raises:
                Exits the program with status 1 if validation fails.
        """
        validator = Draft7Validator(self.schema_config_extract)
        errors = sorted(validator.iter_errors(self.json_config), key=lambda e: e.path)
        if errors:
            logger.error("\033[91m⚠️ Errors found while validating the structure of the configuration dictionary:\033[0m")
            for error in errors:
                caminho = " -> ".join(map(str, error.path))
                logger.warning(f"\033[91mError in {caminho}: {error.message}\033[0m")
            exit(1)

        logger.info("\033[92m✅ The structure of the configuration dictionary is valid.\033[0m")


    def _test_connection_and_permissions_full(self):
        """
            Tests the database connection and verifies permissions to create and modify tables.

            Attempts to execute simple SQL commands: SELECT, CREATE TABLE, ALTER TABLE, and DROP TABLE
            to ensure that the connection is active and the user has sufficient privileges.

            Logs success if all operations complete without error.
            Logs and exits with error if any operation fails.

            Returns:
                True if the connection and permissions are valid.
                Exits the program with status 1 if validation fails.
        """
        try:
            logger.info("Database connection validation:")
            with self.engine.begin() as connection:
                connection.execute(text("SELECT 1"))
                connection.execute(text("CREATE TABLE IF NOT EXISTS __teste_conexao__ (id INTEGER)"))
                connection.execute(text("ALTER TABLE __teste_conexao__ ADD COLUMN teste_coluna INTEGER"))
                connection.execute(text("DROP TABLE __teste_conexao__"))

            logger.info("\033[92m✅ Connection established and permissions to modify tables confirmed.\033[0m")
            return True

        except SQLAlchemyError as e:
            logger.error(f"\033[91m❌ Connection test failed or insufficient permissions to alter tables: {e}\033[0m")
            exit(1)
            return False


    def _test_connection_and_permissions_select(self):
        """
            Tests the database connection by executing a simple SELECT statement.

            Attempts to execute "SELECT 1" to verify that the connection to the database is active.

            Logs success if the query executes without error.
            Logs failure and exits the program if the connection test fails.

            Returns:
                True if the connection is successfully established.
                Exits the program with status 1 if the connection test fails.
        """
        try:
            logger.info("Database connection validation:")
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("\033[92m✅ Connection established successfully.\033[0m")
            return True
        except SQLAlchemyError as e:
            logger.error(f"\033[91m❌ Connection test failed: {e}\033[0m")
            exit(1)
            return False
    
    
    def parquet_in_batches(self,path, batch_size):
        """
            Reads a Parquet file in batches (chunks) and returns each batch as a pandas DataFrame.

            This method uses `ParquetFile.iter_batches` to process the file in smaller parts,
            reducing memory usage during reading.

            Parameters:
                path (str): Path to the Parquet file.
                batch_size (int): Number of rows to read per batch.

            Returns:
                generator: A generator yielding pandas DataFrames, one per batch.
        """
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=batch_size):
            yield batch.to_pandas()
    

    def _read_file(self, table_json, nrows=10000):
        """
            Reads a data file based on the specified type and returns a subset or full data.

            Parameters:
                table_json (dict): Configuration dictionary containing file details such as 
                                type_file (CSV, PARQUET, JSON), path_file, and optional file_sep.
                nrows (int, optional): Number of rows to read. Defaults to 10,000. If None or 0, reads entire file.

            Returns:
                pandas.DataFrame: Data read from the file, either a chunk of 'nrows' rows or the full dataset.

            Raises:
                TypeError: If the file type specified in table_json is not supported.
        """
        type_file = table_json["type_file"].upper()
        path = table_json["path_file"]
        sep = table_json.get("file_sep", ",")

        if type_file == "CSV":
            if nrows:
                return next(pd.read_csv(path, sep=sep, chunksize=nrows))
            return pd.read_csv(path, sep=sep)

        elif type_file == "PARQUET":
            if nrows:
                return next(self.parquet_in_batches(path, nrows))
            return pd.read_parquet(path)

        elif type_file == "JSON":
            if nrows:
                return next(pd.read_json(path, lines=True, chunksize=nrows))
            return pd.read_json(path, lines=True)

        else:
            raise TypeError(f"\033[91m❌ Invalid file type:\033[0m '{type_file}'")


    def _extract_file_columns(self, table_json):
        """
            Extracts and returns the list of column names from the specified data file.

            Parameters:
                table_json (dict): Configuration dictionary containing file details such as type_file and path_file.

            Returns:
                list: List of column names in the file.
        """
        df = self._read_file(table_json, nrows=10000)
        return list(df.columns)


    def _load_dataframe_from_file(self, table_json):
        """
            Loads data from a file into a DataFrame, removing unwanted columns and sorting columns alphabetically.

            Parameters:
                table_json (dict): Configuration dictionary containing file details and optional unwanted attributes.

            Returns:
                pandas.DataFrame: DataFrame with data loaded from the file, without unwanted columns, sorted by column names.
        """
        df = self._read_file(table_json)
        df = df.drop(columns=table_json.get("unwanted_attributes", []), errors="ignore")
        return df[sorted(df.columns)]


    def _check_tables_existence(self, table_names):
        """
            Checks if the specified tables exist in the connected database.

            Parameters:
                table_names (list): List of table names to verify.

            Raises:
                ValueError: If any table in the list does not exist in the database.
        """
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        existing_tables = metadata.tables.keys()

        missing_tables = [t for t in table_names if t not in existing_tables]

        if missing_tables:
            logger.error("\n\033[91mError in Table existence validation:\033[0m")
            raise ValueError(f"\033[91mThe following tables do not exist in the database: {missing_tables}\033[0m")


    def _check_file_paths_exist(self):
        """
            Validates the existence of files specified in the configuration for each table.

            Raises:
                FileNotFoundError: If any specified file path does not exist.
        """
        logger.info("File existence validation:")
        for table in self.json_tables:
            path = table.get("path_file")
            if not os.path.isfile(path):
                raise FileNotFoundError(f"\033[91m❌ File not found: {path}\033[0m")
            else:
                logger.info(f"\033[92m✅ File found: {path}\033[0m")
    
    
    def _check_path_exist(self):
        """
            Validates the existence of the directory path specified in the configuration.

            Raises:
                FileNotFoundError: If the specified directory path does not exist.
        """
        logger.info("Path existence validation:")
        path = self.json_config["path"]
        if not os.path.isdir(path):
            raise FileNotFoundError(f"\033[91m❌ Path not found: {path}\033[0m")
        else:
            logger.info(f"\033[92m✅ Path found: {path}\033[0m")
            
    
    def validar_queries_sqlalchemy(self):
        """
            Validates the SQL queries defined in the configuration for each table using SQLAlchemy.

            Only queries starting with SELECT are validated by executing an EXPLAIN statement.
            Logs success for valid queries and warnings for non-SELECT or missing queries.
            If any query is invalid, logs the error and exits the program.

            Raises:
                SystemExit: Exits with status 1 if any query is invalid.
        """
        IsError = False
        with self.engine.connect() as conn:
            for table in self.json_tables:
                try:
                    query = table["query"]
                    name_table = table["name_table"]

                    if query.strip().lower().startswith("select"):
                        conn.execute(text(f"EXPLAIN {query}"))
                        logger.info(f"✅ Query for table '{name_table}' is valid.")
                    else:
                        logger.info(f"⚠️  Query for table '{name_table}' was not provided or is not a SELECT. Skipped.")
                except SQLAlchemyError as e:
                    logger.error(f"\033[91m❌ Query for table '{name_table}' is invalid:\033[0m")
                    logger.error(f"   → {str(e)}")
                    IsError = True
        if IsError:
            exit(1)


    def _validate_column_types(self):
        """
            Validates if the data types of columns in the input files match the data types of the corresponding columns in the database tables.

            For each table, loads the data file into a DataFrame and compares each column's data type with the column type in the database.
            Skips the 'id_old_insert' column.
            Uses a predefined type compatibility mapping to allow compatible type matches.
            Raises a TypeError if any column type is incompatible.
            Logs successful validation for each table.
        """
        logger.info("Column type validation:")
        metadata = MetaData()
        metadata.reflect(self.engine)

        for table in self.json_tables:
            table_name = table["name_table"]
            file_path = table["path_file"]

            table_info = metadata.tables[table_name]
            db_columns = table_info.columns

            df = self._load_dataframe_from_file(table)

            for column in df.columns:
                if column not in db_columns:
                    if column == 'id_old_insert':
                        continue
                    continue

                db_type = str(db_columns[column].type).lower()
                file_type = str(df[column].dtype).lower()

                compatible = False
                for key, values in self.TYPE_COMPATIBILITY.items():
                    if key in db_type and file_type in values:
                        compatible = True
                        break

                if not compatible:
                    raise TypeError(
                        f"\033[91mType mismatch in table '{table_name}':\n"
                        f" - Column: {column}\n"
                        f" - DB Type: {db_type}\n"
                        f" - File Type: {file_type}\n"
                        f"File: {file_path}\033[0m"
                    )

            logger.info(f"\033[92m✅ Types are compatible for table '{table_name}'.\033[0m")
            
            
    def _check_required_and_all_columns_in_file(self):
        """
            Validates that all required (NOT NULL) columns and all database columns exist in the input files for each table.

            For each table, checks if the input file contains all NOT NULL columns from the database.
            Logs an error if any required columns are missing.
            Also checks if any other columns from the database are missing in the file (excluding 'id_old_insert').
            If any columns are missing, prompts the user whether to continue or abort.
            Logs success messages when validations pass.
        """
        logger.info("🔍 Validation of required (NOT NULL) columns and all DB columns in files:")
        metadata = MetaData()
        metadata.reflect(self.engine)

        for table in self.json_tables:
            table_name = table["name_table"]
            table_info = metadata.tables[table_name]

            db_columns = [col.name for col in table_info.columns]
            not_null_columns = [col.name for col in table_info.columns if not col.nullable]
            file_columns = self._extract_file_columns(table)

            missing_not_null = list(set(not_null_columns) - set(file_columns))
            if missing_not_null:
                logger.error(
                    f"\033[91m❌ Table '{table_name}' is missing required (NOT NULL) columns in the file: {missing_not_null}\033[0m"
                )
            else:
                logger.info(
                    f"\033[92m✅ Table '{table_name}' contains all required (NOT NULL) columns in the file.\033[0m"
                )

            missing_columns = [col for col in db_columns if col not in file_columns]

            if 'id_old_insert' in missing_columns:
                missing_columns.remove('id_old_insert')

            if missing_columns:
                logger.error(
                    f"\033[91m⚠️ Columns {missing_columns} from table '{table_name}' "
                    f"are missing in file: {table['path_file']}\033[0m"
                )
                answer = input("Do you want to continue anyway? (Yes/No): ").strip().lower()
                if answer not in ('y', 'yes', "ye"):
                    logger.error("\033[91m❌ Execution interrupted by the user.\033[0m")
                    exit(1)
            else:
                logger.info(
                    f"\033[92m✅ Table '{table_name}' contains all required DB columns in the file.\033[0m"
                )


    def _validate_all_before_insert(self, table_names):
        """
            Coordinates the validation of the database, files, and columns
            before the data insertion operation.

            Performs connection tests with full permissions, checks for table existence,
            verifies file paths, validates required columns, and data types.

            Args:
                table_names (list): List of table names present in the configuration JSON.
        """
        self._test_connection_and_permissions_full()
        self._check_tables_existence(table_names)
        self._check_file_paths_exist()
        self._check_required_and_all_columns_in_file()
        self._validate_column_types()


    def _validate_all_before_extract(self, table_names):
        """
            Coordinates the required validations before data extraction.

            Checks the configured path existence, tests connection with basic permissions,
            verifies table existence, and validates SQL queries.

            Args:
                table_names (list): List of table names present in the configuration JSON.
        """
        self._check_path_exist()
        self._test_connection_and_permissions_select()
        self._check_tables_existence(table_names)
        self.validar_queries_sqlalchemy()