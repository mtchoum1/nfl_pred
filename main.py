import requests
import json
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json

old_teams = load_teams_from_csv('team_abv.csv')

schedule_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2022"
boxscore_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="

try:
    schedule_response = requests.get(schedule_url)
    schedule_response.raise_for_status()
    schedule_data = schedule_response.json()

    # The new JSON format has a top-level 'events' key
    events = schedule_data.get('events', [])
    
    for game in events:
        game_id = game.get('id')
        season_type = game.get('season', {}).get('type')

        # The API uses integers for season types: 2 for Regular Season, 3 for Postseason
        # We will skip preseason games which are type 1
        if game_id and season_type in [2, 3]:
            print(f"Processing game ID: {game_id}")
            boxscore_url = f"{boxscore_base_url}{game_id}"
            try:
                boxscore_response = requests.get(boxscore_url)
                boxscore_response.raise_for_status()
                boxscore_data = boxscore_response.json()
                
                # Assuming parse_game_json takes the boxscore data and updates teams
                parse_game_json(boxscore_data, old_teams)
            except requests.exceptions.RequestException as e:
                print(f"Could not fetch boxscore for game {game_id}: {e}")
            except Exception as e:
                print(f"Could not parse game data for {game_id}: {e}")
        else:
            print(f"Skipping game {game_id} (Preseason or invalid).")

except requests.exceptions.RequestException as e:
    print(f"Error fetching schedule data: {e}")
except json.JSONDecodeError:
    print("Error decoding JSON from schedule response.")

print(f"\nFinal teams object:\n{old_teams}")