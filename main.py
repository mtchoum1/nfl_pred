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

new_teams = load_teams_from_csv('team_abv.csv')

weekly_schedule_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023&week="

for week in range(1, 19):  # Assuming 18 weeks in the season
    games_with_ids = []
    predictions = {}

    try:
        weekly_response = requests.get(f"{weekly_schedule_url}{week}")
        weekly_response.raise_for_status()
        weekly_data = weekly_response.json()
        events = weekly_data.get('events', [])

        for game in events:
            game_id = game.get('id')
            home_team_abv = game['competitions'][0]['competitors'][0]['team']['abbreviation']
            away_team_abv = game['competitions'][0]['competitors'][1]['team']['abbreviation']
            print(f"Predicting winner for {home_team_abv} vs {away_team_abv}")
            winner = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams)
            predictions[game_id] = winner
            print("-" * 40)
            games_with_ids.append({
                "gameID": game_id,
                "home": home_team_abv,
                "away": away_team_abv,
                "seasonType": game.get('season', {}).get('type')
            })
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weekly schedule for week {week}: {e}")

    correct = 0
    total = 0

    for game in games_with_ids:
        game_id = game["gameID"]
        home = game["home"]
        away = game["away"]
        season_type = game["seasonType"]
        if game_id and season_type in [2, 3]:
            boxscore_url = f"{boxscore_base_url}{game_id}"
            boxscore_response = requests.get(boxscore_url)
            boxscore_data = boxscore_response.json()
            try:

                parse_game_json(boxscore_data, new_teams)
                # Access the competitions list from the 'header' key
                competitions = boxscore_data.get('header', {}).get('competitions', [])
                if not competitions:
                    print(f"Error: No competition data found for game {game_id}.")
                    continue

                competitors = competitions[0].get('competitors', [])
                
                # Extract home and away scores and determine the winner
                home_score = 0
                away_score = 0
                for competitor in competitors:
                    if competitor.get('homeAway') == 'home':
                        home_score = int(competitor.get('score', 0))
                    elif competitor.get('homeAway') == 'away':
                        away_score = int(competitor.get('score', 0))

                actual_winner = None
                if home_score > away_score:
                    actual_winner = home
                elif away_score > home_score:
                    actual_winner = away
                else:
                    actual_winner = "Tie"

                predicted_winner = predictions.get(game_id)
                print(f"Game {game_id}: Predicted {predicted_winner}, Actual {actual_winner}")
                
                if predicted_winner == actual_winner:
                    correct += 1
                total += 1

            except Exception as e:
                print(f"Could not get result for {game_id}: {e}")

        print(f"\nPrediction accuracy: {correct}/{total} correct")