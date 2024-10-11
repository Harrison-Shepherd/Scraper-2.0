import re
import os
import pandas as pd
import requests
from Utils.sanitize_filename import sanitize_filename  

class League:
    league_info = {}
    
    @classmethod
    def fetch_leagues(cls):
        url = 'http://mc.championdata.com/data/competitions.json'
        response = requests.get(url)
    
        if response.status_code == 200:
            leagues = response.json()
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return pd.DataFrame(), pd.DataFrame()
        
        leagues_df = pd.json_normalize(leagues['competitionDetails']['competition'])
        
        leagues_df['cleaned_name'] = leagues_df['name'].apply(lambda x: sanitize_filename(re.sub(r'\b\d{4}\b', '', x).strip()))
        leagues_df['league_season'] = leagues_df['cleaned_name'] + ' (' + leagues_df['season'].astype(str) + ')'
        
        cls.league_info = leagues_df.set_index('id')['league_season'].to_dict()
    
        return leagues_df, leagues_df[['id', 'league_season', 'season']].drop_duplicates()
    
    @classmethod
    def get_league_name_and_season(cls, league_id):
        return cls.league_info.get(league_id, 'Unknown League')

