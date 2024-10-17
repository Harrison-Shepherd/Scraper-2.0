import shelve
import logging
import json
import os
import sys

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the logger setup function from Utils.logger
from Utils.logger import setup_logging

from DatabaseUtils.SqlConnector import connect
from DatabaseUtils.database_helper import DatabaseHelper


class DataInserterWithSQL:
    def __init__(self):
        # Setup logging: Log file will only capture ERROR and above
        log_filename = "data_insertion.log"  # Define log filename
        log_path = setup_logging(log_filename)  # Call the logging setup function from Utils.logger

        # Create a logger and clear any default handlers
        logger = logging.getLogger()
        logger.handlers = []  # Clear any existing handlers to avoid duplicates

        # Create a file handler that logs only ERROR and above to the log file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.ERROR)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Create a console handler that logs INFO and above to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        logger.setLevel(logging.DEBUG)  # Set the base level to DEBUG to ensure all levels are captured by appropriate handlers

        logging.info("Starting the data inserter.")
        self.connection = connect()
        if self.connection is None:
            logging.error("Failed to connect to the database.")
            raise ConnectionError("Database connection failed.")
        self.db_helper = DatabaseHelper(self.connection)

        # Load existing progress from shelve
        self.shelve_filename = "scraping_progress.db"
        self.load_shelve_data()

        # Load SQL insert query paths
        self.load_sql_insert_queries()

    def load_shelve_data(self):
        """
        Load the progress and data from the shelve file.
        """
        try:
            with shelve.open(self.shelve_filename) as db:
                self.all_squad_info = db.get('all_squad_info', [])
                self.all_sport_info = db.get('all_sport_info', [])
                self.all_player_info = db.get('all_player_info', [])
            logging.info(f"Loaded data from shelve file: {self.shelve_filename}")
        except Exception as e:
            logging.error(f"Error loading shelve data: {e}")
            raise

    def load_sql_insert_queries(self):
        """
        Load the paths to the SQL insert queries from the JSON file.
        """
        json_file_path = os.path.join('Assets', 'Jsons', 'sql_insert_queries_file_paths.json')
        try:
            with open(json_file_path, 'r') as file:
                self.sql_insert_queries = json.load(file)
            logging.info(f"Loaded SQL insert query paths from: {json_file_path}")
        except Exception as e:
            logging.error(f"Error loading SQL insert query paths: {e}")
            raise

    def execute_sql_insert_query(self, sql_file_path, data):
        """
        Execute the SQL insert query from a file, binding the data dynamically.
        Suppress duplicate entry errors (Error code: 1062), but log all other errors.
        """
        try:
            # Read the SQL query
            with open(sql_file_path, 'r') as sql_file:
                query = sql_file.read()

            # Replace with INSERT IGNORE if desired, but we're handling duplicates differently here
            # query = query.replace("INSERT INTO", "INSERT IGNORE INTO")

            # Log the query and data for debugging
            logging.info(f"Executing query: {query}")
            logging.info(f"With data: {data}")

            cursor = self.connection.cursor()
            cursor.execute(query, data)
            self.connection.commit()
            cursor.close()

            logging.info(f"Executed insert query from {sql_file_path} successfully.")
        except Exception as e:
            # Check if it's a duplicate entry error (Error code 1062)
            if e.args[0] == 1062:
                logging.info(f"Duplicate entry detected, skipping: {e}")
            else:
                logging.error(f"Error executing query from {sql_file_path}: {e}")
                raise

    def insert_squad_info(self):
        """
        Insert squad_info data using the predefined SQL query from the file.
        """
        sql_file_path = self.sql_insert_queries['Squads']['info']
        for entry in self.all_squad_info:
            try:
                squad_data = {
                    'squadId': entry['squadId'],
                    'squadName': entry['squadName']
                }
                logging.info(f"Inserting squad info: {squad_data}")
                self.execute_sql_insert_query(sql_file_path, (squad_data['squadId'], squad_data['squadName']))
            except Exception as e:
                logging.error(f"Error inserting squad info data: {e}")

    def insert_player_info(self):
        """
        Insert player_info data using the predefined SQL query from the file.
        Checks for missing or invalid squadName and squadId, and ensures they match with squad_info.
        """
        sql_file_path = self.sql_insert_queries['Players']['info']
        for entry in self.all_player_info:
            try:
                # Check for valid squadName and squadId
                if not entry['squadId']:
                    logging.error(f"Missing squadId for playerId: {entry['playerId']}. Skipping player insertion.")
                    continue

                if not entry['squadName']:
                    logging.error(f"Missing squadName for playerId: {entry['playerId']}. Skipping player insertion.")
                    continue

                # Log the player data being inserted for debugging
                player_data = {
                    'playerId': entry['playerId'],
                    'firstname': entry.get('firstname', None),
                    'surname': entry.get('surname', None),
                    'displayName': entry.get('displayName', None),
                    'shortDisplayName': entry.get('shortDisplayName', None),
                    'squadName': entry['squadName'],
                    'squadId': entry['squadId'],
                    'sportId': entry.get('sportId', None)
                }
                logging.info(f"Inserting player info: {player_data}")

                # Execute the SQL insert query for player_info
                self.execute_sql_insert_query(sql_file_path, (
                    player_data['playerId'],
                    player_data['firstname'],
                    player_data['surname'],
                    player_data['displayName'],
                    player_data['shortDisplayName'],
                    player_data['squadName'],
                    player_data['squadId'],
                    player_data['sportId']
                ))

            except Exception as e:
                logging.error(f"Error inserting player info data: {e}")

    def insert_sport_info(self):
        """
        Insert sport_info data using the predefined SQL query from the file.
        """
        sql_file_path = self.sql_insert_queries['Sports']['info']
        for entry in self.all_sport_info:
            try:
                sport_data = {
                    'sportId': entry['sportId'],
                    'sportName': entry.get('sportName', None),
                    'fixtureId': entry['fixtureId'],
                    'fixtureTitle': entry.get('fixtureTitle', None),
                    'fixtureYear': entry.get('fixtureYear', None)
                }
                logging.info(f"Inserting sport info: {sport_data}")
                self.execute_sql_insert_query(sql_file_path, (
                    sport_data['sportId'],
                    sport_data['sportName'],
                    sport_data['fixtureId'],
                    sport_data['fixtureTitle'],
                    sport_data['fixtureYear']
                ))
            except Exception as e:
                logging.error(f"Error inserting sport info data: {e}")

    def insert_all_data(self):
        """
        Insert all the loaded data into the SQL database for squad_info, sport_info, and player_info.
        """
        try:
            logging.info("Inserting squad_info data.")
            self.insert_squad_info()

            logging.info("Inserting sport_info data.")
            self.insert_sport_info()

            logging.info("Inserting player_info data.")
            self.insert_player_info()

        except Exception as e:
            logging.error(f"Error during data insertion: {e}")
            raise

if __name__ == "__main__":
    try:
        inserter = DataInserterWithSQL()
        inserter.insert_all_data()
    except Exception as e:
        logging.critical(f"Critical error in data insertion: {e}")
