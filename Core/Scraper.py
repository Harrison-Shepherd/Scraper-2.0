import logging
import json
import os
import pandas as pd
import re
from DatabaseUtils.SqlConnector import connect
from DatabaseUtils.database_helper import DatabaseHelper
from Utils.logger import setup_logging
from Core.League import League
from Core.Fixture import Fixture
from Core.Match import Match
from Core.PeriodData import PeriodData
from Core.ScoreFlow import ScoreFlow
from Utils.sport_category import determine_sport_category

class Scraper:
    def __init__(self):
        setup_logging('full_scrape.log')
        logging.getLogger().setLevel(logging.ERROR)
        self.connection = connect()
        if self.connection is None:
            logging.error("Failed to connect to the database.")
            raise ConnectionError("Database connection failed.")
        self.db_helper = DatabaseHelper(self.connection)
        self.load_json_fields()
    
    def load_json_fields(self):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        json_dir = os.path.join(base_dir, '..', 'Assets', 'jsons', 'unique fields')
        try:
            with open(os.path.join(json_dir, 'fixtureFields.json'), 'r') as file:
                data = json.load(file)
                self.fixture_fields = data.get('fixture_fields', {})
            
            with open(os.path.join(json_dir, 'matchFields.json'), 'r') as file:
                data = json.load(file)
                self.match_fields = data.get('match_fields', {})
            
            with open(os.path.join(json_dir, 'periodFields.json'), 'r') as file:
                data = json.load(file)
                self.period_fields = data.get('period_fields', {})
            
            with open(os.path.join(json_dir, 'scoreFlowFields.json'), 'r') as file:
                data = json.load(file)
                self.score_flow_fields = data.get('score_flow_fields', {})

            # Load player fields
            with open(os.path.join(json_dir, 'playerFields.json'), 'r') as file:
                data = json.load(file)
                self.player_fields = data.get('player_fields', {})
    
            # Load squad fields
            with open(os.path.join(json_dir, 'squadFields.json'), 'r') as file:
                data = json.load(file)
                self.squad_fields = data.get('squad_fields', {})
    
            # Load sport fields
            with open(os.path.join(json_dir, 'sportFields.json'), 'r') as file:
                data = json.load(file)
                self.sport_fields = data.get('sport_fields', {})
    
            logging.info("JSON field mappings loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading JSON fields: {e}")
            raise

    def scrape_entire_database(self):
        # Fetch leagues
        leagues_df, _ = League.fetch_leagues()

        for _, league in leagues_df.iterrows():
            league_id = league['id']
            league_name = league['league_season']
            regulation_periods = league['regulationPeriods']
            fixture_id = league['id']

            fixture = Fixture(league_id, fixture_id, regulation_periods)
            fixture.fetch_data()
            if fixture.data.empty:
                continue

            # Extract squad_ids from fixture data
            squad_ids = pd.unique(
                fixture.data[['homeSquadId', 'awaySquadId']].values.ravel()
            ).tolist()

            # Determine sportId and sportName
            sport_category, sport_id = determine_sport_category(
                regulation_periods,
                squad_ids,  # Pass the actual squad IDs
                league_name,
                league_id
            )

            # Process sport info
            sport_info_data = {
                'sportId': str(sport_id),
                'sportName': sport_category,
                'fixtureId': str(fixture_id),
                'fixtureTitle': league_name,
                'fixtureYear': None  # Will be set below
            }

            # Extract fixture year from league_name
            match_year = re.search(r'\b(20\d{2})\b', league_name)
            if match_year:
                sport_info_data['fixtureYear'] = match_year.group(1)
                # Remove the year and any trailing '()' or whitespace
                fixture_title = league_name.replace(match_year.group(1), '').strip()
                # Remove trailing '()' if present
                fixture_title = re.sub(r'\(\)$', '', fixture_title).strip()
                sport_info_data['fixtureTitle'] = fixture_title
            else:
                sport_info_data['fixtureYear'] = None  # Or set a default value

            # Insert sport info data
            try:
                self.db_helper.insert_data_dynamically('sport_info', sport_info_data, self.sport_fields)
            except Exception as e:
                logging.error(f"Error inserting sport info data: {e}")

            for index, match_row in fixture.data.iterrows():
                if match_row['matchStatus'] in ['scheduled', 'incomplete']:
                    continue

                match_id = match_row['matchId']
                # Assign sport_id to the fixture row
                fixture.data.at[index, 'sportId'] = sport_id

                # Determine table names
                table_prefix = sport_category.lower().replace(' ', '_')
                fixture_table = f"{table_prefix}_fixture"
                match_table = f"{table_prefix}_match"
                period_table = f"{table_prefix}_period"
                score_flow_table = f"{table_prefix}_score_flow"

                # Insert fixture data
                fixture_data = {
                    **match_row,
                    'fixtureId': fixture_id,
                    'sportId': sport_id,
                    'matchId': match_id
                }
                try:
                    self.db_helper.insert_data_dynamically(fixture_table, fixture_data, self.fixture_fields)
                except Exception as e:
                    logging.error(f"Error inserting fixture data into {fixture_table}: {e}")
                    continue  # Skip to the next match if insertion fails

                # Process squad info
                for squad_side in ['home', 'away']:
                    squad_id = str(match_row[f'{squad_side}SquadId'])
                    squad_name = match_row.get(f'{squad_side}SquadName', '')
                    squad_info_data = {
                        'squadId': squad_id,
                        'squadName': squad_name,
                        'fixtureTitle': sport_info_data['fixtureTitle'],
                        'fixtureYear': sport_info_data['fixtureYear']
                    }

                    try:
                        self.db_helper.insert_data_dynamically('squad_info', squad_info_data, self.squad_fields)
                    except Exception as e:
                        logging.error(f"Error inserting squad info data for squad {squad_id}: {e}")

                # Fetch and insert match data
                match = Match(league_id, match_id, fixture_id, sport_id)
                match.fetch_data()
                if not match.data.empty:
                    for _, row in match.data.iterrows():
                        if not row.get('playerId'):
                            continue
                        # Ensure IDs are strings
                        row['matchId'] = str(match_id)
                        row['playerId'] = str(row['playerId'])
                        row['squadId'] = str(row.get('squadId', ''))

                        # Process player info
                        player_info_data = {
                            'playerId': row['playerId'],
                            'surname': row.get('surname', ''),
                            'shortDisplayName': row.get('shortDisplayName', ''),
                            'firstname': row.get('firstname', ''),
                            'displayName': row.get('displayName', ''),
                            'squadId': row['squadId'],
                            'sportId': sport_info_data['sportId']
                        }

                        try:
                            self.db_helper.insert_data_dynamically('player_info', player_info_data, self.player_fields)
                        except Exception as e:
                            logging.error(f"Error inserting player info data for player {row['playerId']}: {e}")

                        # Insert match data
                        try:
                            self.db_helper.insert_data_dynamically(match_table, row.to_dict(), self.match_fields)
                        except Exception as e:
                            logging.error(f"Error inserting match data into {match_table}: {e}")

                # Fetch and insert period data
                period_data = PeriodData(league_id, match_id)
                period_data.fetch_data()
                if not period_data.data.empty:
                    period_data.data['matchId'] = str(match_id)
                    for idx, row in period_data.data.iterrows():
                        period_num = row.get('period', None)
                        if pd.isnull(period_num):
                            logging.warning(f"Missing 'period' for row {idx} in match {match_id}. Skipping this row.")
                            continue  # Skip rows with missing 'period'

                        match_id_str = str(match_id)
                        period_num_str = str(int(period_num))

                        period_id = f"{match_id_str}_{period_num_str}"
                        period_data.data.at[idx, 'periodId'] = period_id

                        
                        if 'playerId' in row and pd.notnull(row['playerId']):
                            row['playerId'] = str(row['playerId'])
                        else:
                            logging.warning(f"Missing 'playerId' for row {idx} in match {match_id}. Skipping this row.")
                            continue  # Skip rows with missing 'playerId'

                        row['matchId'] = match_id_str
                        row['period'] = int(period_num)
                        row['periodId'] = period_id

                        try:
                            self.db_helper.insert_data_dynamically(period_table, row.to_dict(), self.period_fields)
                        except Exception as e:
                            logging.error(f"Error inserting period data into {period_table}: {e}")

                # Fetch and insert score flow data
                score_flow = ScoreFlow(league_id, match_id)
                score_flow.fetch_data()
                if not score_flow.data.empty:
                    score_flow.data['matchId'] = str(match_id)
                    # Generate unique scoreFlowId
                    score_flow_counter = 1
                    for idx, row in score_flow.data.iterrows():
                        score_flow_id = f"{match_id}_flow_{score_flow_counter}"
                        score_flow.data.at[idx, 'scoreFlowId'] = score_flow_id
                        score_flow_counter += 1

                        
                        row['matchId'] = str(match_id)
                        row['scoreFlowId'] = score_flow_id

                        try:
                            self.db_helper.insert_data_dynamically(score_flow_table, row.to_dict(), self.score_flow_fields)
                        except Exception as e:
                            logging.error(f"Error inserting score flow data into {score_flow_table}: {e}")
