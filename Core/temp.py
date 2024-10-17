import logging
import json
import os
import pandas as pd
import re
import traceback
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
        self.connection.autocommit = False  # Turn off auto-commit
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
        print(f"Fetched {len(leagues_df)} leagues.")

        for _, league in leagues_df.iterrows():
            league_id = league['id']
            league_name = league['league_season']
            regulation_periods = league['regulationPeriods']
            fixture_id = league['id']

            fixture = Fixture(league_id, fixture_id, regulation_periods)
            fixture.fetch_data()
            print(f"Fetched {len(fixture.data)} fixtures for league {league_id}.")
            if fixture.data.empty:
                continue

            # Extract squad_ids from fixture data
            squad_ids = pd.unique(
                fixture.data[['homeSquadId', 'awaySquadId']].values.ravel()
            ).tolist()
            print(f"Extracted squad IDs: {squad_ids}")

            # Use the determine_sport_category function to filter the sport category and ID
            sport_category, sport_id = determine_sport_category(
                regulation_periods,
                squad_ids,
                league_name,
                league_id
            )

            # Start the transaction
            try:
                # Process sport info
                sport_info_data = {
                    'sportId': str(sport_id),
                    'sportName': sport_category,
                    'fixtureId': str(fixture_id),
                    'fixtureTitle': league_name,
                    'fixtureYear': None  # Will be set below
                }

                # Generate unique sport ID
                uniqueSportId = f"{sport_id}-{fixture_id}" if sport_id and fixture_id else 'Unknown'

                # Add uniqueSportId to sport_info_data dictionary
                sport_info_data['uniqueSportId'] = uniqueSportId

                # Extract fixture year from league_name
                match_year = re.search(r'\b(20\d{2})\b', league_name)
                if match_year:
                    sport_info_data['fixtureYear'] = match_year.group(1)
                    fixture_title = league_name.replace(match_year.group(1), '').strip()
                    fixture_title = re.sub(r'\(\)$', '', fixture_title).strip()
                    sport_info_data['fixtureTitle'] = fixture_title
                else:
                    sport_info_data['fixtureYear'] = None

                # Insert sport info data
                print(f"Inserting sport info data: {sport_info_data}")
                self.db_helper.insert_data_dynamically('sport_info', sport_info_data, self.sport_fields)

                # Collect data for batch insertion
                squad_info_list = []
                fixture_data_list = []
                player_info_list = []
                match_data_list = []
                period_data_list = []
                score_flow_data_list = []

                # For table names
                table_prefix = sport_category.lower().replace(' ', '_')
                fixture_table = f"{table_prefix}_fixture"
                match_table = f"{table_prefix}_match"
                period_table = f"{table_prefix}_period"
                score_flow_table = f"{table_prefix}_score_flow"

                for index, match_row in fixture.data.iterrows():
                    if match_row['matchStatus'] in ['scheduled', 'incomplete']:
                        continue

                    match_id = match_row['matchId'] or 'Unknown'
                    fixture.data.at[index, 'sportId'] = sport_id

                    # Ensure fixture_id and match_id are not null for generating uniqueFixtureId
                    uniqueFixtureId = f"{fixture_id}-{match_id}"
                    print(f"Unique fixture ID: {uniqueFixtureId}")

                    # Ensure matchName is populated (fallback if it's None)
                    match_name = match_row.get('matchName', 'Unknown Match')

                    # Generate unique squad IDs for home and away squads
                    home_squad_id = str(match_row.get('homeSquadId', 'Unknown'))
                    away_squad_id = str(match_row.get('awaySquadId', 'Unknown'))
                    home_squad_name = match_row.get('homeSquadName', 'Unknown Squad')
                    away_squad_name = match_row.get('awaySquadName', 'Unknown Squad')
                    
                    uniqueHomeSquadId = f"{home_squad_id}-{home_squad_name}"
                    uniqueAwaySquadId = f"{away_squad_id}-{away_squad_name}"

                    # Collect fixture data
                    fixture_data = {
                        **match_row,
                        'fixtureId': fixture_id,
                        'sportId': sport_id,
                        'matchId': match_id,
                        'uniqueFixtureId': uniqueFixtureId,
                        'matchName': match_name,  # Ensure matchName is included
                        'uniqueHomeSquadId': uniqueHomeSquadId,  # Home squad unique ID
                        'uniqueAwaySquadId': uniqueAwaySquadId,   # Away squad unique ID
                        'uniqueSportId': uniqueSportId  # Add uniqueSportId to fixture data
                    }
                    fixture_data_list.append(fixture_data)

                    # Collect squad info for both home and away
                    for squad_side in ['home', 'away']:
                        squad_id = str(match_row.get(f'{squad_side}SquadId', 'Unknown'))
                        squad_name = match_row.get(f'{squad_side}SquadName', 'Unknown Squad')
                        uniqueSquadId = f"{squad_id}-{squad_name}"
                        squad_info_data = {
                            'squadId': squad_id,
                            'squadName': squad_name,
                            'uniqueSquadId': uniqueSquadId,
                            'fixtureTitle': sport_info_data['fixtureTitle'],
                            'fixtureYear': sport_info_data['fixtureYear']
                        }
                        squad_info_list.append(squad_info_data)

                    # Fetch match data
                    match = Match(league_id, match_id, fixture_id, sport_id)
                    match.fetch_data()

                    if match.data.empty:
                        logging.warning(f"Match data is empty for matchId: {match_id}, leagueId: {league_id}.")
                    else:
                        print(f"Fetched {len(match.data)} match records for match {match_id}.")

                    # Process and collect match data, defaulting to 'Unknown' for missing player or squad info
                    for _, row in match.data.iterrows():
                        player_id = str(row.get('playerId', 'Unknown'))
                        squad_id = str(row.get('squadId', 'Unknown'))

                        row['matchId'] = str(match_id)
                        row['playerId'] = player_id
                        row['squadId'] = squad_id

                        # Generate unique player ID and match ID
                        uniquePlayerId = f"{player_id}-{squad_id}"
                        uniqueMatchId = f"{match_id}-{player_id}"
                        uniqueSquadId = f"{squad_id}-{squad_name}"
                        uniqueSportId = f"{sport_id}-{fixture_id}"


                        
                        row['uniquePlayerId'] = uniquePlayerId
                        row['uniqueMatchId'] = uniqueMatchId
                        row['uniqueSquadId'] = uniqueSquadId
                        row['uniqueSportId'] = uniqueSportId

                        match_data_list.append(row.to_dict())

                    print(f"Collected {len(match_data_list)} match entries for league {league_id}.")

                    # Fetch period data
                    period_data = PeriodData(league_id, match_id)
                    period_data.fetch_data()
                    print(f"Fetched {len(period_data.data)} period records for match {match_id}.")
                    if not period_data.data.empty:
                        period_data.data['matchId'] = str(match_id)
                        for idx, row in period_data.data.iterrows():
                            period_num = str(row.get('period', 'Unknown'))
                            period_id = f"{match_id}_{period_num}"
                            row['periodId'] = period_id

                            player_id = str(row.get('playerId', 'Unknown'))
                            row['playerId'] = player_id
                            row['uniquePlayerId'] = f"{player_id}-{row.get('squadId', 'Unknown')}"

                            period_data_list.append(row.to_dict())

                    # Fetch score flow data
                    score_flow = ScoreFlow(league_id, match_id)
                    score_flow.fetch_data()
                    print(f"Fetched {len(score_flow.data)} score flow records for match {match_id}.")
                    if not score_flow.data.empty:
                        score_flow_counter = 1
                        for idx, row in score_flow.data.iterrows():
                            score_flow_id = f"{match_id}_flow_{score_flow_counter}"
                            score_flow.data.at[idx, 'scoreFlowId'] = score_flow_id
                            score_flow_counter += 1

                            row['uniqueMatchId'] = f"{match_id}-{row.get('playerId', 'Unknown')}"
                            row['uniquePlayerId'] = f"{row.get('playerId', 'Unknown')}-{row.get('squadId', 'Unknown')}"

                            score_flow_data_list.append(row.to_dict())

                print(f"Collected {len(squad_info_list)} squad info entries.")
                print(f"Collected {len(fixture_data_list)} fixture entries.")
                print(f"Collected {len(player_info_list)} player info entries.")
                print(f"Collected {len(match_data_list)} match entries.")
                print(f"Collected {len(period_data_list)} period data entries.")
                print(f"Collected {len(score_flow_data_list)} score flow entries.")

                # Insert squad_info data
                unique_squad_info_dict = {squad['squadId']: squad for squad in squad_info_list}
                unique_squad_info = unique_squad_info_dict.values()

                for squad_info_data in unique_squad_info:
                    print(f"Inserting squad info: {squad_info_data}")
                    self.db_helper.insert_data_dynamically('squad_info', squad_info_data, self.squad_fields)

                # Insert player_info data
                unique_player_info = {(player['playerId'], player['squadId']): player for player in player_info_list}.values()
                for player_info_data in unique_player_info:
                    print(f"Inserting player info: {player_info_data}")
                    self.db_helper.insert_data_dynamically('player_info', player_info_data, self.player_fields)

                # Insert fixture data
                for fixture_data in fixture_data_list:
                    print(f"Inserting fixture data: {fixture_data}")
                    self.db_helper.insert_data_dynamically(fixture_table, fixture_data, self.fixture_fields)

                # Insert match data
                for match_data in match_data_list:
                    print(f"Inserting match data: {match_data}")
                    self.db_helper.insert_data_dynamically(match_table, match_data, self.match_fields)

                # Insert period data
                for period_row in period_data_list:
                    print(f"Inserting period data: {period_row}")
                    self.db_helper.insert_data_dynamically(period_table, period_row, self.period_fields)

                # Insert score flow data
                for score_flow_row in score_flow_data_list:
                    print(f"Inserting score flow data: {score_flow_row}")
                    self.db_helper.insert_data_dynamically(score_flow_table, score_flow_row, self.score_flow_fields)

                # Commit the transaction after successful batch insertion
                self.connection.commit()
                print(f"Transaction committed successfully for fixtureId: {fixture_id}")

            except Exception as e:
                logging.error(f"Error during transaction for fixtureId: {fixture_id}, leagueId: {league_id}. Error: {e}")
                logging.error(f"Traceback: {traceback.format_exc()}")
                self.connection.rollback()  # Rollback the transaction on error
                logging.error(f"Transaction rolled back for fixtureId: {fixture_id}")
                raise  # Re-raise the error after rollback
