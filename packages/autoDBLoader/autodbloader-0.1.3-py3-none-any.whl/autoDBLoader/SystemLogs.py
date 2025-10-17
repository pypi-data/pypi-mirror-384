from sqlalchemy import Table, Integer, Column, Text, text, MetaData
import logging
import json
import sys

logger = logging.getLogger("AutoDBLoader")

logger.setLevel(logging.DEBUG)

if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class AutoDBLoaderLogs:
    
    def __init__(self, total_tables, engine, json_tables):
        
        self.total_tables = total_tables
        self.json_tables = json_tables
        
        self.metadata = MetaData()
        self.engine = engine
        
        self.log_table = Table(
            "log_AutoDBLoader",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("log", Text, nullable=False)
        )
        self.metadata.create_all(self.engine)
        

    def _save_completed_tables_log_to_db(self, tables_finished):
        """
            Saves the list of completed tables to the database log table.

            - Creates the log table if it does not exist.
            - Clears any existing log entries.
            - Inserts the current list of finished tables as a JSON string into the log table.
        """
        logger.info(f"save {tables_finished}")
        if len(tables_finished) > 0:
            self.metadata.create_all(self.engine)
            with self.engine.begin() as conn:
                conn.execute(self.log_table.delete())
                json_data = json.dumps(tables_finished)
                conn.execute(self.log_table.insert().values(log=json_data))


    def _delete_log_table_from_db(self):
        """
            Deletes the log table from the database if it exists.
            Logs a confirmation message upon successful deletion.
        """
        self.log_table.drop(self.engine, checkfirst=True)
        logger.info("\033[92m🗑️ Log table deleted successfully from the database.\033[0m")
 

    def _remove_old_insert_id_column(self):
        """
            Removes the 'id_old_insert' column from the tables.

            This column stores the reference to the primary key from the old database.

            Logs an error if the table is not found, or info if the column does not exist.
            Logs a success message when the column is removed successfully.
        """
        self.metadata.reflect(bind=self.engine)
        for table in self.json_tables:
            table_name = table["name_table"]
            if table_name not in self.metadata.tables:
                logger.error(f"🚫 Table '{table_name}' not found.")
                return

            table = self.metadata.tables[table_name]

            if 'id_old_insert' in table.columns:
                with self.engine.connect() as conn:
                    conn.execute(text(f'ALTER TABLE {table_name} DROP COLUMN id_old_insert'))

        logger.info(f"\033[92m✅ Columns 'id_old_insert' successfully removed.\033[0m")



    def _except_logs(self, tables_finished, table_name, error, func):
        """
            Handles error logging during data insertion.

            - Logs a summarized version of the error message (first and last 5000 characters if too long).
            - Saves the current insertion progress (list of finished tables) into the database log table.
            - Logs information about the completed tables and total tables.
            - Exits the program with status 1.

            Args:
                tables_finished (list): List of table names already successfully inserted.
                table_name (str or None): Name of the table where the error occurred.
                error (Exception): The caught exception.
                func (str): Name of the function where the error occurred.
        """
        error_str = str(error)
        max_len = 5000
        if len(error_str) > max_len * 2:
            error_summary = error_str[:max_len] + "\n... [truncated] ...\n" + error_str[-max_len:]
        else:
            error_summary = error_str
        
        logger.error(f"\033[91mError inserting data into table '{table_name}': {error_summary}\033[0m")
        self._save_completed_tables_log_to_db(tables_finished)
        
        logger.info(f"\033[92mList of completed tables: {tables_finished}\033[0m")
        logger.info(f"\033[92mTotal number of tables: {self.total_tables}\033[0m")
        logger.info(f"\033[92mTotal completed: {len(tables_finished)}\033[0m")

        sys.exit(1)
