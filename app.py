from flask import Flask, jsonify, render_template
import csv
import requests
import json
import os
from collections import defaultdict
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json, Team

app = Flask(__name__)

# --- Constants and Globals ---
HISTORY_FILE = 'prediction_history.csv'
FIELDNAMES = [
    'year', 'seasontype', 'week', 'game_id', 'home_team', 'away_team',
    'predicted_winner', 'actual_winner', 'home_win_prob', 'away_win_prob', 'is_correct'
]
prediction_history = []
latest_season_stats = {}

# --- Load Historical and Base Data ---
try:
    with open(HISTORY_FILE, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            prediction_history.append(row)
    print("Prediction history loaded successfully.")
except FileNotFoundError:
    print(f"WARNING: '{HISTORY_FILE}' not found. It will be created when the first game goes final.")

try:
    latest_season_stats = load_teams_from_csv('final_team_stats.csv')
    print("Base stats for live predictions loaded successfully from 'final_team_stats.csv'.")
except FileNotFoundError:
    print("WARNING: 'final_team_stats.csv' not found. Live predictions may not work.")
    print("Please run 'history_generator.py' to create the necessary files.")

teams_map = {}
try:
    with open('team_abv.csv', mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            teams_map[row['Team_Abv']] = row['Team']
    print("Team abbreviations map loaded.")
except FileNotFoundError:
    print("WARNING: 'team_abv.csv' not found. Full team names will be unavailable for standings.")

team_logos = {}
def load_team_logos():
    global team_logos
    if not team_logos:
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                team_data = team.get('team', {})
                abbreviation = team_data.get('abbreviation')
                logo_url = next((logo.get('href') for logo in team_data.get('logos', []) if logo.get('width') == 40), None)
                if abbreviation and logo_url:
                    team_logos[abbreviation] = logo_url
            print("Team logos loaded from ESPN API.")
        except requests.RequestException as e:
            print(f"Could not fetch team logos from ESPN API: {e}")

load_team_logos()

# --- NEW: Function to write completed games to CSV ---
def append_to_history(game_data):
    """Appends a single game record to the history CSV and in-memory list."""
    if any(str(g['game_id']) == str(game_data['game_id']) for g in prediction_history):
        print(f"Game {game_data['game_id']} already in history. Skipping append.")
        return

    try:
        file_exists = os.path.isfile(HISTORY_FILE)
        with open(HISTORY_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(game_data)
        
        prediction_history.append(game_data)
        print(f"Successfully appended game {game_data['game_id']} to prediction history.")
    except Exception as e:
        print(f"Error appending to history file: {e}")

def predict_future_week(year, seasontype, week):
    """
    Generates predictions for a future week and saves them to history if they are final.
    """
    print(f"Generating live predictions for {year}, Season Type {seasontype}, Week {week}...")
    
    old_teams = latest_season_stats
    new_teams = load_teams_from_csv('team_abv.csv') 

    if not old_teams:
        return {"error": "Missing base data from last season. Cannot make live predictions."}, 500

    predictions_list = []
    try:
        weekly_schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&seasontype={seasontype}&dates={year}&week={week}"
        response = requests.get(weekly_schedule_url)
        response.raise_for_status()
        events = response.json().get('events', [])

        for game in events:
            game_id = game.get('id')
            competition = game['competitions'][0]
            competitors = competition['competitors']
            home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})
            if not home_team_data or not away_team_data: continue
            
            home_team_abv = home_team_data.get('team', {}).get('abbreviation')
            away_team_abv = away_team_data.get('team', {}).get('abbreviation')

            prediction_week = week if seasontype == 2 else 18 + week
            predicted_winner, team1_prob, team2_prob = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams, prediction_week, home_team_abv)

            game_info = {
                "id": game_id, "date": game.get('date'), "name": game.get('name'),
                "status": game.get('status', {}).get('type', {}).get('detail'),
                "home_team": {"abbreviation": home_team_abv, "logo": home_team_data.get('team', {}).get('logo'), "score": home_team_data.get('score', '0'), "win_probability": team1_prob},
                "away_team": {"abbreviation": away_team_abv, "logo": away_team_data.get('team', {}).get('logo'), "score": away_team_data.get('score', '0'), "win_probability": team2_prob},
                "predicted_winner": predicted_winner, "actual_winner": None, "is_correct": None
            }
            
            # UPDATED: Check if game is final and save to history
            is_final = game.get('status', {}).get('type', {}).get('name') == 'STATUS_FINAL'
            if is_final:
                actual_winner_data = next((c for c in competitors if c.get('winner') is True), None)
                actual_winner = actual_winner_data['team']['abbreviation'] if actual_winner_data else None

                if actual_winner:
                    is_correct = (predicted_winner == actual_winner)
                    game_info.update({"actual_winner": actual_winner, "is_correct": is_correct})
                    
                    history_row = {
                        'year': year, 'seasontype': seasontype, 'week': week, 'game_id': game_id,
                        'home_team': home_team_abv, 'away_team': away_team_abv,
                        'predicted_winner': predicted_winner, 'actual_winner': actual_winner,
                        'home_win_prob': team1_prob, 'away_win_prob': team2_prob, 'is_correct': is_correct
                    }
                    append_to_history(history_row)

            predictions_list.append(game_info)

        return {"games": predictions_list, "accuracy": {"correct": 0, "total": 0, "percentage": 0}}, 200

    except requests.RequestException as e:
        return {"error": f"Could not fetch live schedule: {e}"}, 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/predict/<int:year>/<int:seasontype>/<int:week>')
def get_predictions(year, seasontype, week):
    games_for_week = [g for g in prediction_history if g.get('year') and g.get('seasontype') and g.get('week') and int(g['year']) == year and int(g['seasontype']) == seasontype and int(g['week']) == week]

    if games_for_week:
        print(f"Serving historical data for {year}, Season Type {seasontype}, Week {week}.")
        live_data = {}
        try:
            weekly_schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&seasontype={seasontype}&dates={year}&week={week}"
            response = requests.get(weekly_schedule_url)
            response.raise_for_status()
            for event in response.json().get('events', []):
                live_data[event['id']] = event
        except requests.RequestException as e:
            print(f"Could not fetch live data: {e}")
        
        predictions_list = []
        correct, total = 0, 0
        for game in games_for_week:
            live_game = live_data.get(game['game_id'], {})
            status = live_game.get('status', {}).get('type', {}).get('detail', 'Unavailable')
            home_team_live = next((c.get('team', {}) for c in live_game.get('competitions', [{}])[0].get('competitors', []) if c.get('homeAway') == 'home'), {})
            away_team_live = next((c.get('team', {}) for c in live_game.get('competitions', [{}])[0].get('competitors', []) if c.get('homeAway') == 'away'), {})
            
            game_info = {
                "id": game['game_id'], "date": live_game.get('date', ''), "name": live_game.get('name', ''), "status": status,
                "home_team": {
                    "abbreviation": game['home_team'], "logo": home_team_live.get('logo'),
                    "score": next((c.get('score', '0') for c in live_game.get('competitions', [{}])[0].get('competitors', []) if c.get('homeAway') == 'home'), '0'),
                    "win_probability": float(game['home_win_prob'] or 0)
                },
                "away_team": {
                    "abbreviation": game['away_team'], "logo": away_team_live.get('logo'),
                    "score": next((c.get('score', '0') for c in live_game.get('competitions', [{}])[0].get('competitors', []) if c.get('homeAway') == 'away'), '0'),
                    "win_probability": float(game['away_win_prob'] or 0)
                },
                "predicted_winner": game['predicted_winner'], "actual_winner": game['actual_winner'],
                "is_correct": game['is_correct'] == 'True' if game['is_correct'] else (False if game['is_correct'] == 'False' else None)
            }
            if game.get('actual_winner'):
                total += 1
                if game.get('is_correct') == 'True': correct += 1
            predictions_list.append(game_info)
        
        return jsonify({
            "games": predictions_list,
            "accuracy": {"correct": correct, "total": total, "percentage": (correct / total * 100) if total > 0 else 0}
        })
    else:
        result, status_code = predict_future_week(year, seasontype, week)
        return jsonify(result), status_code

@app.route('/standings/<int:year>/<int:seasontype>')
def standings(year, seasontype):
    standings_data = defaultdict(lambda: {
        'actual_wins': 0, 'actual_losses': 0, 'actual_ties': 0,
        'predicted_wins': 0, 'predicted_losses': 0,
        'team_name': '', 'team_logo': ''
    })

    games_for_year = [
        g for g in prediction_history
        if g.get('year') and g.get('seasontype') and 
           int(g['year']) == year and int(g['seasontype']) == seasontype and
           g.get('actual_winner') is not None and g.get('actual_winner') != '' and
           g.get('predicted_winner') is not None and g.get('predicted_winner') != ''
    ]

    all_teams = set(g['home_team'] for g in games_for_year) | set(g['away_team'] for g in games_for_year)

    for team_abv in all_teams:
        standings_data[team_abv]['team_name'] = teams_map.get(team_abv, team_abv)
        standings_data[team_abv]['team_logo'] = team_logos.get(team_abv, 'https://placehold.co/40x40/cccccc/ffffff?text=?')

    for game in games_for_year:
        home = game['home_team']
        away = game['away_team']
        actual_winner = game['actual_winner']
        predicted_winner = game['predicted_winner']

        is_tie = not (actual_winner == home or actual_winner == away)
        
        if is_tie:
            standings_data[home]['actual_ties'] += 1
            standings_data[away]['actual_ties'] += 1
        else:
            actual_loser = away if actual_winner == home else home
            standings_data[actual_winner]['actual_wins'] += 1
            standings_data[actual_loser]['actual_losses'] += 1
            
        predicted_loser = away if predicted_winner == home else home
        standings_data[predicted_winner]['predicted_wins'] += 1
        standings_data[predicted_loser]['predicted_losses'] += 1

    for team, data in standings_data.items():
        data['difference'] = data['actual_wins'] - data['predicted_wins']
        data['actual_record'] = f"{data['actual_wins']}-{data['actual_losses']}"
        if data['actual_ties'] > 0:
            data['actual_record'] += f"-{data['actual_ties']}"
        data['predicted_record'] = f"{data['predicted_wins']}-{data['predicted_losses']}"

    sorted_standings = dict(sorted(standings_data.items(), key=lambda item: item[1]['actual_wins'], reverse=True))

    return render_template('standings.html', standings=sorted_standings, selected_year=year, selected_seasontype=seasontype)


# if __name__ == '__main__':
#     app.run(debug=True)