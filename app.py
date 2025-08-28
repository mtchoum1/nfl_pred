# app.py
from flask import Flask, jsonify, render_template
import csv
import json
import os
import datetime
from collections import defaultdict

# Refactored imports
from data_loader import load_teams_from_csv, save_teams_to_csv
from predict import predict_winner
from team import parse_game_json
from firebase_config import initialize_firebase
import espn_api

from firebase_admin import db, auth

# Initialize services
initialize_firebase()
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Firebase Configuration for Frontend ---
# This remains for client-side JS
firebase_config_string = os.environ.get('FIREBASE_CONFIG', None)
if firebase_config_string:
    firebase_config = json.loads(firebase_config_string)
else:
    print("WARNING: 'FIREBASE_CONFIG' environment variable not set. Attempting to load from config.json.")
    try:
        with open('firebase_config.json', 'r') as f:
            firebase_config = json.load(f)
        print("Successfully loaded Firebase config from firebase_config.json.")
    except FileNotFoundError:
        print("ERROR: config.json not found. Firebase client-side features will not work.")
        firebase_config = {}
# --- Constants and Globals ---
HISTORY_FILE = 'prediction_history.csv'
CURRENT_SEASON_STATS_FILE = 'current_season_stats.csv'
FIELDNAMES = [
    'year', 'seasontype', 'week', 'game_id', 'home_team', 'away_team',
    'predicted_winner', 'actual_winner', 'home_win_prob', 'away_win_prob', 'is_correct'
]
prediction_history = []
latest_season_stats = {}
current_season_stats = {}
teams_map = {}
team_logos = {}
divisions_map = []
PLACEHOLDER_LOGO = 'https://placehold.co/40x40/cccccc/ffffff?text=?'

# --- Data Loading ---
def load_all_data():
    """Loads all necessary data when the application starts."""
    global prediction_history, latest_season_stats, teams_map, current_season_stats, divisions_map

    try:
        with open(HISTORY_FILE, mode='r') as infile:
            prediction_history = list(csv.DictReader(infile))
        print("Prediction history loaded successfully.")
    except FileNotFoundError:
        print(f"WARNING: '{HISTORY_FILE}' not found.")

    try:
        latest_season_stats = load_teams_from_csv('./final_team_stats.csv')
        print("Base stats for live predictions loaded.")
    except FileNotFoundError:
        print("WARNING: 'final_team_stats.csv' not found.")

    try:
        with open('team_abv.csv', mode='r') as infile:
            teams_map = {row['Team_Abv']: row['Team'] for row in csv.DictReader(infile)}
        print("Team abbreviations map loaded.")
    except FileNotFoundError:
        print("WARNING: 'team_abv.csv' not found.")
    
    try:
        with open('nfl_divisions.csv', mode='r') as infile:
            divisions_map = list(csv.DictReader(infile))
        print("NFL divisions map loaded.")
    except FileNotFoundError:
        print("WARNING: 'nfl_divisions.csv' not found.")

    # Load data using the new API module
    data, error = espn_api.get_all_teams_data()
    if data:
        for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
            team_data = team.get('team', {})
            abbreviation = team_data.get('abbreviation')
            logo_url = next((logo.get('href') for logo in team_data.get('logos', [])), None)
            if abbreviation and logo_url:
                team_logos[abbreviation] = logo_url
        print("Team logos loaded from ESPN API.")
    else:
        print(f"Could not fetch team logos: {error}")

    try:
        current_season_stats = load_teams_from_csv(CURRENT_SEASON_STATS_FILE)
        print(f"Loaded in-progress season stats from '{CURRENT_SEASON_STATS_FILE}'.")
    except FileNotFoundError:
        print(f"'{CURRENT_SEASON_STATS_FILE}' not found. Initializing empty stats.")
        current_season_stats = load_teams_from_csv('team_abv.csv')

# --- Prediction and History Logic ---
def append_to_history(game_data):
    """Appends a single game record to the history CSV and in-memory list."""
    if any(str(g.get('game_id')) == str(game_data.get('game_id')) for g in prediction_history):
        return

    try:
        file_exists = os.path.isfile(HISTORY_FILE)
        with open(HISTORY_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(game_data)
        prediction_history.append(game_data)
    except IOError as e:
        print(f"Error appending to history file: {e}")

def predict_future_week(year, seasontype, week):
    """Generates predictions for a future week."""
    if not latest_season_stats:
        return {"error": "Missing base data for predictions."}, 500

    data, error = espn_api.get_weekly_schedule(year, seasontype, week)
    if error:
        return {"error": f"Could not fetch live schedule: {error}"}, 500

    predictions_list = []
    stats_were_updated = False
    
    for game in data.get('events', []):
        game_id = game.get('id')
        home_team_data, away_team_data = espn_api.parse_competitors(game)
        if not home_team_data or not away_team_data: continue
        
        home_team_abv = home_team_data.get('team', {}).get('abbreviation')
        away_team_abv = away_team_data.get('team', {}).get('abbreviation')

        prediction_week = week if int(seasontype) == 2 else 18 + week
        predicted_winner, home_prob, away_prob = predict_winner(
            home_team_abv, away_team_abv, latest_season_stats, 
            current_season_stats, prediction_week, home_team_abv
        )

        game_info = {
            "id": game_id, "date": game.get('date'), "name": game.get('name'),
            "status": game.get('status', {}).get('type', {}).get('detail'),
            "home_team": {"abbreviation": home_team_abv, "logo": team_logos.get(home_team_abv, PLACEHOLDER_LOGO), "score": home_team_data.get('score', '0'), "win_probability": home_prob},
            "away_team": {"abbreviation": away_team_abv, "logo": team_logos.get(away_team_abv, PLACEHOLDER_LOGO), "score": away_team_data.get('score', '0'), "win_probability": away_prob},
            "predicted_winner": predicted_winner, "actual_winner": None, "is_correct": None
        }
        
        is_final = game.get('status', {}).get('type', {}).get('name') == 'STATUS_FINAL'
        game_in_history = next((g for g in prediction_history if str(g.get('game_id')) == str(game_id)), None)

        if is_final and not game_in_history:
            actual_winner = home_team_abv if home_team_data.get('winner') else (away_team_abv if away_team_data.get('winner') else None)
            is_correct = (predicted_winner == actual_winner) if actual_winner else None
            
            game_info.update({"actual_winner": actual_winner, "is_correct": is_correct})
            
            history_row = {
                'year': year, 'seasontype': seasontype, 'week': week, 'game_id': game_id,
                'home_team': home_team_abv, 'away_team': away_team_abv, 'predicted_winner': predicted_winner,
                'actual_winner': actual_winner, 'home_win_prob': home_prob, 'away_win_prob': away_prob, 'is_correct': is_correct
            }
            append_to_history(history_row)

            box_data, _ = espn_api.get_boxscore(game_id)
            if box_data:
                parse_game_json(box_data, current_season_stats)
                stats_were_updated = True
        elif game_in_history:
            game_info.update({"actual_winner": game_in_history.get('actual_winner'), "is_correct": game_in_history.get('is_correct') == 'True'})

        predictions_list.append(game_info)

    if stats_were_updated:
        print(f"Saving updated season stats to '{CURRENT_SEASON_STATS_FILE}'...")
        save_teams_to_csv(current_season_stats, CURRENT_SEASON_STATS_FILE)

    return {"games": predictions_list, "accuracy": {"correct": 0, "total": 0, "percentage": 0}}, 200

def calculate_leaderboard():
    """Calculates total wins and current streak for all players."""
    try:
        year = datetime.date.today().year
        leaderboard = []
        uid_to_email = {user.uid: user.email for user in auth.list_users().iterate_all()}
        
        lms_ref = db.reference(f'last_man_standing/{year}')
        all_players_data = lms_ref.get()
        if not all_players_data: return []

        for uid, data in all_players_data.items():
            if not isinstance(data, dict): continue

            picks = data.get('picks', {})
            total_wins, current_streak = 0, 0
            
            for week in range(1, len(picks)):
                pick_info = picks[week]
                if isinstance(pick_info, dict) and pick_info.get('result') == 'correct':
                    total_wins += 1
                
            for week in range(len(picks) - 1, 0, -1):
                pick_info = picks[week]
                if isinstance(pick_info, dict) and pick_info.get('result') == 'correct':
                    current_streak += 1
                elif isinstance(pick_info, dict) and pick_info.get('result') == 'unknown':
                    continue
                else:
                    break 

            leaderboard.append({
                'email': uid_to_email.get(uid, 'Unknown User'),
                'wins': total_wins,
                'streak': current_streak,
                'status': data.get('status', 'active')
            })

        return sorted(leaderboard, key=lambda x: (x['wins'], x['streak']), reverse=True)
        
    except Exception as e:
        print(f"An error occurred while calculating the leaderboard: {e}")
        return []

# --- Flask Routes (Largely unchanged, but API routes are now cleaner) ---

@app.route('/')
def index():
    return render_template('index.html', firebase_config=firebase_config)

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html', leaderboard=calculate_leaderboard(), firebase_config=firebase_config)

# ... (other HTML routes like /login, /last_man_standing, /standings are unchanged) ...
@app.route('/login')
def login():
    return render_template('login.html', firebase_config=firebase_config)

@app.route('/last_man_standing')
def last_man_standing():
    return render_template('last_man_standing.html', firebase_config=firebase_config)

@app.route('/standings/<int:year>/<int:seasontype>')
def standings(year, seasontype):
    standings_data = defaultdict(lambda: {'actual_wins': 0, 'actual_losses': 0, 'actual_ties': 0, 'predicted_wins': 0, 'predicted_losses': 0})
    games_for_year = [
        g for g in prediction_history
        if g.get('year') and g.get('seasontype') and
           int(g['year']) == year and int(g['seasontype']) == seasontype and
           g.get('actual_winner') is not None and g.get('actual_winner') != ''
    ]
    all_teams = set(g['home_team'] for g in games_for_year) | set(g['away_team'] for g in games_for_year)
    for team_abv in all_teams:
        standings_data[team_abv]['team_name'] = teams_map.get(team_abv, team_abv)
        standings_data[team_abv]['team_logo'] = team_logos.get(team_abv, PLACEHOLDER_LOGO)
        home_games = [g for g in games_for_year if g['home_team'] == team_abv]
        away_games = [g for g in games_for_year if g['away_team'] == team_abv]
        for game in home_games + away_games:
            is_home_team = (game['home_team'] == team_abv)
            opponent = game['away_team'] if is_home_team else game['home_team']
            if game['actual_winner'] == team_abv: standings_data[team_abv]['actual_wins'] += 1
            elif game['actual_winner'] == opponent: standings_data[team_abv]['actual_losses'] += 1
            else: standings_data[team_abv]['actual_ties'] += 1
            if game.get('predicted_winner') == team_abv: standings_data[team_abv]['predicted_wins'] += 1
            elif game.get('predicted_winner') == opponent: standings_data[team_abv]['predicted_losses'] += 1
    for team, data in standings_data.items():
        data['difference'] = data['actual_wins'] - data['predicted_wins']
        data['actual_record'] = f"{data['actual_wins']}-{data['actual_losses']}" + (f"-{data['actual_ties']}" if data['actual_ties'] > 0 else "")
        data['predicted_record'] = f"{data['predicted_wins']}-{data['predicted_losses']}"
    sorted_standings = dict(sorted(standings_data.items(), key=lambda item: item[1]['actual_wins'], reverse=True))
    return render_template('standings.html', standings=sorted_standings, selected_year=year, selected_seasontype=seasontype, firebase_config=firebase_config)

# --- API Routes ---
@app.route('/api/predict/<int:year>/<int:seasontype>/<int:week>')
def get_predictions(year, seasontype, week):
    games_for_week = [
        g for g in prediction_history
        if g.get('year') and g.get('seasontype') and g.get('week') and
           int(g['year']) == year and int(g['seasontype']) == seasontype and int(g['week']) == week
    ]

    if games_for_week:
        # Serve historical data, enriched with live scores for display
        print(f"Serving historical data for {year}, ST {seasontype}, Wk {week}.")
        live_data, _ = espn_api.get_weekly_schedule(year, seasontype, week)
        live_events = {event['id']: event for event in live_data.get('events', [])} if live_data else {}
        
        predictions_list, correct, total = [], 0, 0
        for game in games_for_week:
            live_game = live_events.get(game['game_id'], {})
            home_comp, away_comp = espn_api.parse_competitors(live_game)

            game_info = {
                "id": game['game_id'], "date": live_game.get('date', ''), "name": live_game.get('name', ''), 
                "status": live_game.get('status', {}).get('type', {}).get('detail', 'Unavailable'),
                "home_team": {"abbreviation": game['home_team'], "logo": team_logos.get(game['home_team'], PLACEHOLDER_LOGO), "score": home_comp.get('score', '0'), "win_probability": float(game.get('home_win_prob') or 0)},
                "away_team": {"abbreviation": game['away_team'], "logo": team_logos.get(game['away_team'], PLACEHOLDER_LOGO), "score": away_comp.get('score', '0'), "win_probability": float(game.get('away_win_prob') or 0)},
                "predicted_winner": game.get('predicted_winner'), "actual_winner": game.get('actual_winner'),
                "is_correct": game.get('is_correct') == 'True'
            }
            if game.get('actual_winner'):
                total += 1
                if game.get('is_correct') == 'True': correct += 1
            predictions_list.append(game_info)
        
        accuracy = {"correct": correct, "total": total, "percentage": (correct / total * 100) if total > 0 else 0}
        return jsonify({"games": predictions_list, "accuracy": accuracy})
    else:
        # Predict a future week
        result, status_code = predict_future_week(year, seasontype, week)
        return jsonify(result), status_code

@app.route('/api/lms_schedule/<int:year>/<int:week>')
def get_lms_schedule(year, week):
    """
    Provides game schedule, including game start times, for the Last Man Standing game.
    """
    data, error = espn_api.get_weekly_schedule(year, 2, week)
    if error:
        return jsonify({"games": [], "error": error}), 500

    schedule_list = []
    for game in data.get('events', []):
        competitors = game.get('competitions', [{}])[0].get('competitors', [])
        home_team_data = next((c.get('team', {}) for c in competitors if c.get('homeAway') == 'home'), {})
        away_team_data = next((c.get('team', {}) for c in competitors if c.get('homeAway') == 'away'), {})
        
        home_team_abv = home_team_data.get('abbreviation')
        away_team_abv = away_team_data.get('abbreviation')
        
        # --- NEW: Include the game's start time (in ISO 8601 format) ---
        game_date = game.get('date')

        if home_team_abv and away_team_abv:
            schedule_list.append({
                "date": game_date, 
                "home_team": {"abbreviation": home_team_abv, "logo": team_logos.get(home_team_abv, PLACEHOLDER_LOGO)},
                "away_team": {"abbreviation": away_team_abv, "logo": team_logos.get(away_team_abv, PLACEHOLDER_LOGO)}
            })
    return jsonify({"games": schedule_list})

def find_season_start_date(year):
    """
    Finds the date of the first Thursday in September for a given year.
    """
    # Start with September 1st of the given year
    d = datetime.date(year, 9, 1)
    # Find the offset to the first Thursday (weekday() is 0=Mon, 3=Thu)
    offset = (3 - d.weekday() + 7) % 7
    return d + datetime.timedelta(days=offset)

# --- UPDATED API ROUTE ---
@app.route('/api/nfl_week')
def get_nfl_week():
    """Calculates the current week of the NFL season dynamically."""
    today = datetime.date.today()
    year = today.year

    season_start_date = find_season_start_date(year)
    
    # If it's before this year's season starts, check if we're still in last year's season (e.g., January playoffs)
    if today < season_start_date:
        # Check last year's season start
        last_year_start = find_season_start_date(year - 1)
        days_since_start = (today - last_year_start).days
        # Assuming a season lasts about 22 weeks (18 regular + 4 postseason)
        if 0 <= days_since_start < (22 * 7):
             current_week = (days_since_start // 7) + 1
             # Cap regular season at 18
             return jsonify({"year": year - 1, "week": min(current_week, 18)})
        else:
            # It's the offseason, so default to Week 1 of the upcoming season
            return jsonify({"year": year, "week": 1})

    # If we are in the current season
    days_since_start = (today - season_start_date).days
    current_week = (days_since_start // 7) + 1
    
    # Cap the regular season week at 18
    week = min(current_week, 18)
    
    return jsonify({"year": year, "week": week})

@app.route('/api/nfl_divisions')
def get_nfl_divisions():
    return jsonify(divisions_map)

# --- App Startup ---
load_all_data()

if __name__ == '__main__':
    app.run(debug=True)