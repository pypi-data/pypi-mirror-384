from sqlalchemy import create_engine, text, Column, Text, Integer, insert, MetaData, Table, inspect
from sqlalchemy.exc import SQLAlchemyError, NoSuchTableError
from sqlalchemy.orm import sessionmaker
from autoDBLoader.validation import AutoDBLoaderValidation
from autoDBLoader.SystemLogs import AutoDBLoaderLogs
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import logging
import psutil
from . import config
import json
import re


logger = logging.getLogger("AutoDBLoader")

logger.setLevel(logging.DEBUG)

if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class AutoDBLoaderInsertDate:
    
    def __init__(self, json_config):
        
        self.json_config = json_config
        self.df_forengKey = None
        self.tables_finished = []
        self.tables_finished_config = {}
        self.total_tables = 0
        self.json_tables = self.json_config["tables"]
        self.nome_tables = [t["name_table"] for t in self.json_tables]

        self.metadata = MetaData()
        self.engine, self.session = self.__db_conect(self.json_config)
        self.sgbd = self.json_config["db"]["sgbd"].lower()
        
        self.log_table = Table(
            "log_AutoDBLoader",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("log", Text, nullable=False)
        )

        self.dbLoader = AutoDBLoaderLogs(self.total_tables, self.engine, self.json_tables)
        self.validation = AutoDBLoaderValidation(self.engine, self.json_config)
        
        self.MAP_LENGTH_TYPE = config.MAP_LENGTH_TYPE

    
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


    def _load_completed_tables_log_from_db(self):
        """
            Checks for the existence of a log table in the database and loads the list of completed tables.

            The method uses SQLAlchemy's inspector to verify if a table named 'log_AutoDBLoader' (case-insensitive) exists.
            If found, it queries the log table to retrieve a JSON list of tables that have already been processed.
            This list is assigned to the instance attribute 'tables_finished'.

            If the log table exists but is empty, or if it does not exist at all, 'tables_finished' is set to an empty list.

            Logs informative messages regarding the presence and contents of the log table.
        """
        inspector = inspect(self.engine)
        if any(t in inspector.get_table_names() for t in ["log_AutoDBLoader", "log_autodbloader"]):
            with self.engine.connect() as conn:
                result = conn.execute(self.log_table.select()).fetchone()
                if result and result[0]:
                    self.tables_finished = json.loads(result[1])
                    logger.info(f"\033[92m✅ Log found in the database. Tables already completed: {self.tables_finished}\033[0m")
                else:
                    self.tables_finished = []
                    logger.info("\033[93m⚠️ Log table found, but it is empty.\033[0m")
        else:
            self.tables_finished = []
            logger.info("\033[93m⚠️ Log table not found. Starting from scratch.\033[0m")


    def __extract_foreign_keys(self):
        """
            Extracts foreign key relationships from the database and returns related tables.

            This method uses SQLAlchemy's inspector to retrieve foreign key metadata for all tables in the connected database.
            It constructs a pandas DataFrame containing details about each foreign key relationship, including:
            - source_table: the table containing the foreign key
            - foreign_key: the column in the source table acting as the foreign key
            - foreign_table: the referenced table
            - foreign_table_key: the referenced column in the foreign table

            The resulting DataFrame is stored in the instance attribute 'df_forengKey'.

            Additionally, it returns a list of all tables that have at least one foreign key defined.

            Returns:
                list: List of table names that contain foreign key constraints.
        """
        inspector = inspect(self.engine)
        tables = []
        tables_list = set([])

        for table in inspector.get_table_names():
            fks = inspector.get_foreign_keys(table)
            for fk in fks:
                tables.append({
                    "source_table": table,
                    "foreign_key": fk["constrained_columns"][0],
                    "foreign_table": fk["referred_table"],
                    "foreign_table_key": fk["referred_columns"][0]
                })
                tables_list.add(table)

        self.df_forengKey = pd.DataFrame(tables)
        return list(tables_list)


    def __verification_tables_finished(self, table_name):
        """
            Checks if all foreign key related tables for the given table have been inserted.

            This method verifies whether all tables that the specified table depends on via foreign keys
            have already been processed and inserted. It does so by comparing the foreign tables linked
            to `table_name` against the list of tables marked as finished (`self.tables_finished`).

            It returns True if either:
            - All foreign key related tables have been inserted (i.e., are in `self.tables_finished`), or
            - The foreign key related tables are not part of the known table set (`self.nome_tables`), 
            indicating no dependency within the current dataset.

            Args:
                table_name (str): The name of the table to verify foreign key dependencies for.

            Returns:
                bool: True if all dependent foreign key tables are finished or not relevant, False otherwise.
        """
        df = self.df_forengKey[self.df_forengKey["source_table"] == table_name]
        list_tables_foreng = df["foreign_table"].unique().tolist()
        return set(list_tables_foreng).issubset(set(self.tables_finished)) \
                or not set(list_tables_foreng).issubset(set(self.nome_tables))


    def __find_unique_index_columns(self, table_name):
        """
            Checks the database for columns with a unique index in a specific table
            and returns a list with the names of those columns.

            The method ignores columns that are part of the primary key or foreign keys,
            returning only the columns that have a uniqueness constraint via a unique index.

            Args:
                table_name (str): Name of the table to analyze.

            Returns:
                list: List containing the names of columns with a unique index.
        """
        insp = inspect(self.engine)
        self.metadata.reflect(bind=self.engine, only=[table_name])
        table = self.metadata.tables[table_name]

        pk_cols = set(col.name for col in table.primary_key)

        fk_cols = set()
        for fk in insp.get_foreign_keys(table_name):
            fk_cols.update(fk['constrained_columns'])

        unique_colls = set()
        for index in insp.get_indexes(table_name):
            if index.get('unique', False):
                col_names = index.get('column_names', [])
                for col in col_names:
                    if col not in pk_cols and col not in fk_cols:
                        unique_colls.add(col)

        return list(unique_colls)


    def __extract_unique_attributes(self, table_name, connection, list_atributos):
        """
            Extracts from the database the values of the unique columns of a specific table
            and returns them as a Pandas DataFrame.

            Args:
                table_name (str): Name of the table to query.
                connection (sqlalchemy.engine.base.Connection): Active connection to the database.
                list_atributos (list): List containing the names of the unique columns to be extracted.

            Returns:
                pandas.DataFrame: DataFrame containing the values of the extracted unique columns.
        """
        try:
            stmt = text("""
                SELECT {colunas_unicas}
                FROM {tabela}
            """.format(
                colunas_unicas=",".join(list_atributos),
                tabela=table_name
            ))
            result = connection.execute(stmt)
            
            unique = result.fetchall()
            
            df_unique = pd.DataFrame(unique)
            return df_unique
        
        except SQLAlchemyError as e:
            self.dbLoader._except_logs(self.tables_finished, table_name, e,"__extract_unique_attributes")
            

    def __validate_unique_values(self, table_name, connection, list_atributos, table_json):
        """
            Checks for duplicate values in unique columns between the data to be inserted
            and the data already present in the database. If duplicates are found, logs the
            error and stops the execution.

            Args:
                table_name (str): Name of the table being validated.
                connection (sqlalchemy.engine.base.Connection): Active connection to the database.
                list_atributos (list): List of unique columns to be checked.
                table_json (dict): Table configuration structure containing metadata needed for loading.

            Raises:
                ValueError: If duplicate values are found.
        """
        try:
            df_db_unique = self.__extract_unique_attributes(table_name, connection, list_atributos)
            not_primary_key = self.__is_not_primary_key_table(table_json)

            for chunk in self.__load_file_to_dataframe(table_json, connection, not_primary_key, table_json["unwanted_attributes"]):
                df_chunk_unique = chunk[list_atributos]


                df_db_unique_str = df_db_unique.astype(str)
                df_chunk_unique_str = df_chunk_unique.astype(str)

                if not df_db_unique_str.empty and table_name not in self.tables_finished:
                    duplicates = pd.merge(df_db_unique_str, df_chunk_unique_str, how='inner')
                    if not duplicates.empty:
                        logger.error(
                            f"\033[91m❌ Duplicate values found in the database and file for table '{table_name}' "
                            f"on unique attributes: {list_atributos}\033[0m"
                        )
                        logger.error(f"\033[91m{duplicates}\033[0m")
                        raise ValueError(f"\033[91mError: Duplicate values found in table '{table_name}'\033[0m")
        except ValueError as e:
            self.dbLoader._except_logs(self.tables_finished, table_name, e,"__validate_unique_values")



    def __identify_primary_key_and_auto_increment(self, conn, table_name):
        """
            Identifies the primary key and whether it is auto-increment for a specific table,
            updating the table configuration by adding the 'primary_key' and 'autoIncrement' fields.

            The method checks the columns that make up the primary key, excluding those
            that are also foreign keys. If all primary key components are foreign keys,
            it marks the table as 'not_primary_key' and sets 'autoIncrement' to False.
            Otherwise, it sets the primary key name and whether the column is auto-increment
            in the table configuration.

            Args:
                conn: Active database connection.
                table_name (str): Name of the table to analyze.

            Returns:
                None
        """
        insp = inspect(conn)
        pks = insp.get_pk_constraint(table_name)["constrained_columns"]
        fks = insp.get_foreign_keys(table_name)

        fk_cols = set()
        for fk in fks:
            fk_cols.update(fk["constrained_columns"])

        pk = list(set(pks) - fk_cols)

        if all(item in fk_cols for item in pks):
            for table in self.json_tables:
                if table["name_table"] == table_name:
                    table["not_primary_key"] = True
                    table["autoIncrement"] = False
            return None

        self.metadata.reflect(conn, only=[table_name])
        table = self.metadata.tables[table_name]
        col = table.columns[pks[0]]

        for table in self.json_tables:
            if table["name_table"] == table_name:  
                table["primary_key"] = pk[0]
                table["autoIncrement"] = col.autoincrement is True
                
    
    def __add_old_id_column_to_tables(self):
        """
            Adds a new column 'id_old_insert' to the database tables.
            This column stores the original ID from the legacy database records, 
            used to maintain consistency of relationships between tables.  
            With this value, it is possible to identify the old ID and map it to the 
            new ID generated upon insertion, ensuring that relationships are created correctly.

            For each configured table:
            - Identifies the primary key and checks if it is auto-increment.
            - Checks whether the column already exists.
            - Validates if there are unique values in the file to be inserted that already exist in the database.
            - Adds the column if it does not exist and the table meets the criteria.

            Raises:
                SQLAlchemyError: In case of an error executing SQL commands.
                Exception: For other unexpected errors.
        """
        try:
            with self.engine.begin() as conn:
                for table_json in self.json_tables:
                    try:
                        table_name = table_json["name_table"]
                        not_primary_key = self.__is_not_primary_key_table(table_json)
                        self.__identify_primary_key_and_auto_increment(conn, table_name)
                        try:
                            table = Table(table_name, self.metadata, autoload_with=conn)
                        except NoSuchTableError:
                            logger.error(f"\033[91m❌Table {table_name} not found in database.\033[0m")
                            continue
                        
                        column_exists = 'id_old_insert' in table.columns.keys()
                        
                        unique_columns = self.__find_unique_index_columns(table_name)
                        if len(unique_columns) > 0 and table_name not in self.tables_finished:
                            self.__validate_unique_values(table_name, conn, unique_columns, table_json)
                        
                        if not not_primary_key and table_json.get("autoIncrement", False) and not column_exists:
                            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN id_old_insert INTEGER'))

                    except SQLAlchemyError as e:
                        self.dbLoader._except_logs(self.tables_finished, table_name, e,"__add_old_id_column_to_tables")
                        
        except Exception as e:
            logger.error(e)
            logger.error("\033[91m❌ error creating id_old_insert columns in database.\033[0m")


    def __is_not_primary_key_table(self, table):
        """
            Checks if the table does not have a primary key.

            This function checks whether the key "not_primary_key" is present in the `table` dictionary
            and returns its value. If the key does not exist, it returns False by default.

            Parameters:
                table (dict): Dictionary containing information about the table.

            Returns:
                bool: True if the table does not have a primary key, False otherwise.
        """
        not_primary_key = False
        if "not_primary_key" in table:
            not_primary_key = table["not_primary_key"]
        return not_primary_key


    def __update_foreign_keys_with_old_ids(self, df, table_name, connection, not_primary_key, table_json):
        """
            Updates the table's foreign keys using `id_old_insert`.

            This method updates the foreign key column values in the DataFrame
            based on the `id_old_insert` found in related tables.  
            It performs a merge between old values and the new IDs to ensure
            referential integrity, replacing old references with the new IDs
            generated in the database.

            Parameters:
                df (pandas.DataFrame): DataFrame containing the data to be inserted or updated.
                table_name (str): Name of the current table.
                connection (sqlalchemy.engine.Connection): Active database connection.
                not_primary_key (bool): Indicates whether the table has no primary key.
                table_json (dict): Dictionary containing table configuration and metadata.

            Returns:
                pandas.DataFrame: DataFrame updated with corrected foreign keys.
        """
        try:
            df_filter = self.df_forengKey[self.df_forengKey["source_table"] == table_name]
            for row in df_filter.itertuples(index=False):

                if not table_json["autoIncrement"] and not not_primary_key:
                    continue

                check_stmt = text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = :table_name 
                    AND COLUMN_NAME = 'id_old_insert'
                """)
                
                col_exists = connection.execute(
                    check_stmt, {"table_name": row.foreign_table}
                ).scalar()
                if col_exists == 0:
                    break

                menor_id = df[row.foreign_key].min()
                maior_id = df[row.foreign_key].max()

                stmt = text(f"""
                    SELECT {row.foreign_table_key}, id_old_insert
                    FROM {row.foreign_table}
                    WHERE id_old_insert IS NOT NULL
                    AND id_old_insert >= {menor_id}
                    AND id_old_insert <= {maior_id}
                """)
                result = connection.execute(stmt)

                ids_old = result.fetchall()
                df_ids_old = pd.DataFrame(ids_old, columns=["primary_id_query", "id_old_insert"])

                df = df.merge(df_ids_old, left_on=row.foreign_key, right_on='id_old_insert', how='left')
                df['primary_id_query'] = df['primary_id_query'].fillna(df[row.foreign_key]).astype(int)
                df = df.drop(columns=[row.foreign_key, 'id_old_insert']).rename(columns={"primary_id_query": row.foreign_key})

            return df

        except SQLAlchemyError as e:
            self.dbLoader._except_logs(self.tables_finished, table_name, e, "__update_foreign_keys_with_old_ids")


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


    def __load_file_to_dataframe(self, table_json, connection, not_primary_key, unwanted_attributes, has_foregkey=False, chunksize=500000):
        """
            Loads a file in batches into a list of pandas DataFrames.

            This method reads CSV, Parquet, or JSON files in chunks, enabling the processing of large datasets
            without exhausting memory.  
            It can also update foreign keys based on the `id_old_insert` column,  
            remove unwanted attributes, and replace NaN values with None.

            Parameters:
                table_json (dict): Dictionary with table and file configuration (type, path, separator, etc.).
                connection (sqlalchemy.engine.Connection): Active database connection.
                not_primary_key (bool): Indicates whether the table has no primary key.
                unwanted_attributes (list): List of columns to be removed from the DataFrame.
                has_foregkey (bool, optional): Whether to update foreign keys based on `id_old_insert`.  
                                            Defaults to False.
                chunksize (int, optional): Number of rows per batch. Defaults to 500,000.

            Returns:
                list[pd.DataFrame]: List of DataFrames containing the data loaded in batches.
        """
        try:
            type_file = table_json["type_file"].upper()
            path = table_json["path_file"]
            sep = table_json.get("file_sep", ",")
            file_chunks = []

            if type_file == "CSV":
                reader = pd.read_csv(path, sep=sep, chunksize=chunksize)
            elif type_file == "PARQUET":
                reader = self.parquet_in_batches(path, chunksize)
            elif type_file == "JSON":
                reader = pd.read_json(path, lines=True, chunksize=chunksize)
            else:
                raise TypeError(f'File type "{type_file}" is not valid.')

            for chunk in reader:
                chunk = chunk[sorted(chunk.columns)]
                if has_foregkey:
                    chunk = self.__update_foreign_keys_with_old_ids(chunk, table_json["name_table"], connection, not_primary_key, table_json)
                chunk = chunk.drop(columns=unwanted_attributes)
                chunk = chunk.replace({np.nan: None}).where(pd.notnull(chunk), None)
                file_chunks.append(chunk)

            return file_chunks
        
        except Exception as e:
            self.dbLoader._except_logs(self.tables_finished, table_json["table_name"], e, "__load_file_to_dataframe")
            

    
    def __insert_data_into_tables_relational(self):
        """
            This method executes the entire process of inserting data into tables that have relationships
            with other tables in the database. It performs the following steps:

            1. Iterates over all configured tables in the process.
            2. Checks whether all related foreign key tables have already been populated,
            ensuring the correct loading order.
            3. For each table eligible for insertion:
                - Determines whether the table has a primary key or not.
                - Calculates the maximum rows per batch and per chunk to optimize insertion.
                - Loads data from the source file (CSV, Parquet, or JSON) in chunks, updating
                foreign keys based on the `id_old_insert` value.
                - Renames the primary key to `id_old_insert` when necessary to maintain the
                mapping of the original ID.
                - Converts the data into dictionaries and inserts it into the database in batches.
            4. Marks the table as completed in the process.
            5. Repeats the cycle until all tables have been inserted, respecting referential
            integrity and avoiding duplicates.

            If an error occurs, the method logs detailed messages for troubleshooting.
        """
        try:
            metadata = MetaData()

            while len(self.tables_finished) != self.total_tables:
                for table in self.json_tables:
                    with self.engine.begin() as connection:

                        if (table["name_table"] not in self.tables_finished and self.__verification_tables_finished(table["name_table"])):
                            not_primary_key = self.__is_not_primary_key_table(table)
                            table_name = table["name_table"]
                            unwanted_attributes = table["unwanted_attributes"]

                            linhas_por_lote, linhas_por_chunk = self.estimate_max_row_size_and_chunk(table_name)
                            
                            file_chunks = self.__load_file_to_dataframe(table, connection, not_primary_key, unwanted_attributes, has_foregkey=True, chunksize=linhas_por_chunk)
                            try:
                                table_sql = Table(table_name, metadata, autoload_with=self.engine)

                                for chunk in file_chunks:
                                    if not not_primary_key and table["autoIncrement"]:
                                        chunk = chunk.rename(columns={table["primary_key"]: 'id_old_insert'})
                                    
                                    registros = chunk.to_dict(orient='records')
                                    self.__insert_in_batches(connection, table_sql, registros, lote=linhas_por_lote, table_name=table_name)

                                self.tables_finished.append(table_name)

                            except SQLAlchemyError as e:
                                self.dbLoader._except_logs(self.tables_finished, table["name_table"], e, "__insert_data_into_tables_not_relational")

        except Exception as e:
            self.dbLoader._except_logs(self.tables_finished, None, e, "__insert_data_into_tables_relational")
            logger.error(e)
            logger.error("\033[91m❌ Unknown error when trying to insert data into tables containing foreign keys.\033[0m")


    def __insert_data_into_tables_not_relational(self, list_not_forengKey_tables):
        """
            This method performs data insertion into tables that do not have relationships with other tables.

            For each table in the provided list that has not been processed yet:
            - Calculates the optimal maximum number of rows per batch and per chunk to optimize insertion.
            - Loads data from the source file (CSV, Parquet, or JSON) in chunks.
            - Renames the primary key to 'id_old_insert' if the table has auto-increment, to keep track of the original ID.
            - Handles null values by replacing them with None.
            - Inserts the data into the database in batches using the batch insertion method.
            - Marks the table as completed after insertion.

            In case of an error, detailed logs are recorded for troubleshooting.
        """
        try:
            metadata = MetaData()

            for table in self.json_tables:
                try:
                    if table["name_table"] in list_not_forengKey_tables and table["name_table"] not in self.tables_finished:
                        table_name = table["name_table"]
                        primaryKey = table["primary_key"]
                        unwanted_attributes = table["unwanted_attributes"]
                        linhas_por_lote, linhas_por_chunk = self.estimate_max_row_size_and_chunk(table_name)
                        
                        with self.engine.begin() as connection:
                            for df in self.__load_file_to_dataframe(table, connection, False, unwanted_attributes, chunksize=linhas_por_chunk):
                                if table["autoIncrement"]:
                                    df = df.rename(columns={primaryKey: 'id_old_insert'})

                                df = df.replace({np.nan: None})
                                df = df.where(pd.notnull(df), None)

                                table_sql = Table(table_name, metadata, autoload_with=self.engine)

                                chunk_dicts = df.to_dict(orient='records')
                                self.__insert_in_batches(connection, table_sql, chunk_dicts, lote=linhas_por_lote, table_name=table_name)

                        self.tables_finished.append(table_name)

                except SQLAlchemyError as e: 
                    self.dbLoader._except_logs(self.tables_finished, table["name_table"], e, "__insert_data_into_tables_not_relational")

        except Exception as e:
            logger.error(e)
            logger.error("\033[91m❌ Unknown error when trying to insert data into tables that do not contain foreign keys.\033[0m")
            self.dbLoader._except_logs(self.tables_finished, table_name, e, "__insert_data_into_tables_not_relational")


    def __insert_in_batches(self, connection, table_sql, valores, lote=1000, table_name=None):
        """
            Inserts records into the database in batches to optimize performance.

            Parameters:
            - connection: active database connection.
            - table_sql: SQLAlchemy Table object representing the target table.
            - valores: list of dictionaries containing records to be inserted.
            - lote: batch size for each insertion (default 1000).
            - table_name: name of the table for logging purposes (optional).

            For each batch of records, executes the insert and logs the progress including how many rows were inserted.

            In case of database error, calls the logging method for error handling.
        """
        try:
            total_batches = (len(valores) + lote - 1) // lote
            for i in range(0, len(valores), lote):
                lote_valores = valores[i:i + lote]
                stmt = insert(table_sql).values(lote_valores)
                result = connection.execute(stmt)

                if table_name:
                    logger.info(
                        f"✅ Table '{table_name}': Batch {i // lote + 1} of {total_batches} inserted successfully "
                        f"({result.rowcount} rows)."
                    )

        except SQLAlchemyError as e:
            self.dbLoader._except_logs(self.tables_finished, table_name, e, "__insert_in_batches")


    def estimate_max_row_size_and_chunk(self, table_name):
        """
            Estimates the maximum number of rows that can be inserted per batch and per chunk, considering the maximum row size and memory constraints.

            Parameters:
            - table_name: name of the table for which the estimation is made.

            Returns:
            - rows_per_batch: maximum number of rows per insert batch.
            - rows_per_chunk: maximum number of rows per chunk for reading and processing.

            The method considers:
            - estimated maximum row size in the table,
            - maximum insert size limit defined by the database,
            - and 60% of available RAM for chunk calculation.

            In case of error, logs the exception.
        """
        try:
            max_bytes_per_row = self.calculate_max_row_size(table_name)    
            max_bytes_insert = self.get_max_insert_size()
            mem = psutil.virtual_memory()
            free_memory_bytes = mem.available
            seventy_percent_bytes = free_memory_bytes * 0.60

            rows_per_batch = max(1, int((max_bytes_insert * 0.80) // max_bytes_per_row))
            rows_per_chunk = max(1, int((seventy_percent_bytes * 0.30) // max_bytes_per_row))

            return rows_per_batch, rows_per_chunk
        
        except Exception as e:
            self.dbLoader._except_logs(self.tables_finished, table_name, e, "estimate_max_row_size_and_chunk")
    
    
    def calculate_max_row_size(self, table_name):
        """
            Calculates the estimated maximum size in bytes of a row in the specified table.

            Parameters:
            - table_name: name of the table to calculate the row size for.

            Returns:
            - total_bytes: estimated size in bytes for a row in the table.

            The calculation considers the data type and length of each column based on a specific mapping for the DBMS, plus an estimated overhead per row.

            In case of error, logs the exception.
        """
        try:
            insp = inspect(self.engine)
            columns = insp.get_columns(table_name)
            total_bytes = 0

            size_map = self.MAP_LENGTH_TYPE.get(self.sgbd.lower())
            if not size_map:
                raise ValueError(f"DBMS '{self.sgbd}' not supported.")

            for col in columns:
                col_type = str(col['type']).lower()

                if any(t in col_type for t in ['int', 'bigint', 'smallint', 'tinyint', 'float', 'double', 'real', 'number']):
                    length = 0
                else:
                    m = re.search(r'\((\d+)', col_type)
                    length = int(m.group(1)) if m else getattr(col['type'], 'length', None) or 0

                size = None
                for type_key, value in size_map.items():
                    if type_key in col_type:
                        if callable(value):
                            size = value(length)
                        else:
                            size = value
                        break

                if size is None:
                    size = 8

                total_bytes += size
            total_bytes += 20
            return total_bytes
        
        except Exception as e:
            self.dbLoader._except_logs(self.tables_finished, table_name, e, "calculate_max_row_size")

    
    
    def set_max_allowed_packet(self, size_bytes= 128 * 1024 * 1024):
        """
            Attempt to set the MySQL 'max_allowed_packet' system variable to the specified size in bytes.
            Default is 512 MB.

            This operation requires the user to have sufficient privileges to execute 'SET GLOBAL'.
            It only applies when the database system is MySQL.

            After setting the variable, the database connection is re-established to ensure the new
            setting is recognized in the current session.

            Parameters:
            size_bytes (int): The desired 'max_allowed_packet' size in bytes.

            Logs:
            - Success or failure message about the attempt to set the variable.
        """
        if self.sgbd.lower() != "mysql":
            return

        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"SET GLOBAL max_allowed_packet = {size_bytes}"))
                self.engine, self.session = self.__db_conect(self.json_config)
        except Exception as e:
            logger.warning(f"⚠️ Could not set max_allowed_packet to {size_bytes} bytes.")
        

    def get_max_insert_size(self):
        """
            Retrieves the maximum allowed packet size for database insert operations.

            - For MySQL, it queries the current 'max_allowed_packet' system variable.
            - For PostgreSQL and Oracle, it returns a fixed value of 128 MB.
            - Raises an error if the DBMS is unsupported.
            - Logs and handles exceptions appropriately.
        """
        try:
            with self.engine.connect() as conn:
                if self.sgbd.lower() == "mysql":
                    result = conn.execute(text("SHOW VARIABLES LIKE 'max_allowed_packet'")).fetchone()
                    if result:
                        logger.info(f"max_allowed_packet is currently set to {int(result[1]) // (1024*1024)}MB.")
                        return int(result[1]) if int(result[1]) <= 129*1024*1024 else 128*1024*1024
                    else:
                        return None

                elif self.sgbd.lower() in ["postgresql", "postgres"]:
                    return 128 * 1024 * 1024  # 128 MB

                elif self.sgbd.lower() == "oracle":
                    return 128 * 1024 * 1024  # 128 MB

                else:
                    raise ValueError(f"SGBD '{self.sgbd}' not supported.")

        except Exception as e:
            self.dbLoader._except_logs(self.tables_finished, "Insert", e, "get_max_insert_size")


    def _insertDate(self, json): 
        """
            Main method that orchestrates the entire data insertion process.

            - Validates the input dictionary structure.
            - Adjusts MySQL's max_allowed_packet parameter.
            - Extracts the list of table names to be processed.
            - Loads the log of tables already completed from the database.
            - Validates all tables before insertion.
            - Adds the 'id_old_insert' column to assist in maintaining relationships.
            - Identifies tables with foreign keys and inserts data into non-relational tables first.
            - Performs insertion into relational tables respecting foreign key dependencies.
            - Removes the 'id_old_insert' column after insertion is complete.
            - Closes the database session and deletes the execution log from the database.
            - Logs success messages at the end of the process.
        """
        self.validation._validation_structure_dict_insert()
        self.set_max_allowed_packet()

        teble_names = self.__extract_tables_name()
        self.total_tables = len(self.json_tables)
        
        self._load_completed_tables_log_from_db()
        self.validation._validate_all_before_insert(teble_names)

        self.__add_old_id_column_to_tables()
        
        colunas_com_forengKey = self.__extract_foreign_keys()
        not_forengKey_tables = list(set(teble_names) - set(colunas_com_forengKey))
        self.__insert_data_into_tables_not_relational(not_forengKey_tables)

        self.__insert_data_into_tables_relational()
        
        self.dbLoader._remove_old_insert_id_column()

        self.session.close()
        self.dbLoader._delete_log_table_from_db()
        logger.info("\033[92m==================================================\033[0m")
        logger.info("\033[92m==================================================\033[0m")
        logger.info("\033[92m============= SUCCESSFULL INSERTION ==============\033[0m")
        logger.info("\033[92m==================================================\033[0m")
        logger.info("\033[92m==================================================\033[0m")
    
    #==========Atividades==============
    # corrigir o codigo para poder inserir somente uma tabela
    # adicionar o sistema de leitura em beach json e parquet
    # adicionar o sistema de leitura em beach para validação de valores unique
    # adicionar o sistema de leitura em beach na validação json e parquet
    # validar um sistema para mensurar o tamanho ideal para a chunk do arquivo
    
    # Esta com erro no if da função de inserção do que tem relacionamento, isso 
    # está acontecendo pq estou tentando incluir uma forma de inserir uma unica 
    # tabela mesmo que as outras tabelas que ela precisa da chave estrangeira não tenham sido inseridas
    
    # vou inserir um sistema de verificação do tamanho que cada tupla tem, com isso eu vou verificar quanto 
    # de memoria tem no PC e calcular o tamanho que cada chunk vai ter e cada lot de inserção também
    # vou buscar no banco o maximo de bites que pode ter uma query e sempre utilizar o maximo possivel
    # logica: lê o arquvo utilizando o read_file do validadion, pega o retorno e utiliza para calcular, e retorna o valor
    # linhas_por_lote, linhas_por_chunk para os métodos de insert, para cada arquivo.
    # adicionar tipo de dados texte que ocupam mais espaço
    
    #buscar no banco os tipos de dados e verificar quando de espaço cada linha ocupa
    
    # não está conseguindo ler o arquivo de transactions e se eu leio com muitos registros gera erro
    
    # traduzir tudo para o inglês
    # Resumir logs
    # remover métodos e codigo que não esta em uso ou que esta comentado.
    # quando estourar um erro no inserter mostrar o inicio do erro não o log completo do insert