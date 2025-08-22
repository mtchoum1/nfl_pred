from flask import Flask, jsonify, render_template
import csv
import requests
import json
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json, Team
from collections import defaultdict

app = Flask(__name__)

# --- Load Historical and Base Data ---
prediction_history = []
latest_season_stats = {}

try:
    with open('prediction_history.csv', mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            prediction_history.append(row)
    print("Prediction history loaded successfully.")
except FileNotFoundError:
    print("WARNING: 'prediction_history.csv' not found. Historical data will be unavailable.")

try:
    latest_season_stats = load_teams_from_csv('final_team_stats.csv')
    print("Base stats for live predictions loaded successfully from 'final_team_stats.csv'.")
except FileNotFoundError:
    print("WARNING: 'final_team_stats.csv' not found. Live predictions may not work.")
    print("Please run 'history_generator.py' to create the necessary files.")

# --- NEW: Helper to load team mappings ---
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


def predict_future_week(year, seasontype, week):
    """
    Generates predictions for a future week on-the-fly.
    """
    print(f"Generating live predictions for {year}, Season Type {seasontype}, Week {week}...")
    
    old_teams = latest_season_stats
    new_teams = load_teams_from_csv('team_abv.csv') # Base stats for a new season

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

            # For live predictions, we assume it's late in the season, so we can use a high week number
            prediction_week = week if seasontype == 2 else 18 + week

            predicted_winner, team1_prob, team2_prob = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams, prediction_week, home_team_abv)

            game_info = {
                "id": game_id, "date": game.get('date'), "name": game.get('name'),
                "status": game.get('status', {}).get('type', {}).get('detail'),
                "home_team": {
                    "abbreviation": home_team_abv, "logo": home_team_data.get('team', {}).get('logo'),
                    "score": '0', "win_probability": team1_prob
                },
                "away_team": {
                    "abbreviation": away_team_abv, "logo": away_team_data.get('team', {}).get('logo'),
                    "score": '0', "win_probability": team2_prob
                },
                "predicted_winner": predicted_winner, "actual_winner": None, "is_correct": None
            }
            predictions_list.append(game_info)

        return {"games": predictions_list, "accuracy": {"correct": 0, "total": 0, "percentage": 0}}, 200

    except requests.RequestException as e:
        return {"error": f"Could not fetch live schedule: {e}"}, 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/predict/<int:year>/<int:seasontype>/<int:week>')
def get_predictions(year, seasontype, week):
    # Check if the requested week is in our history
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
                "is_correct": game['is_correct'] == 'True' if game['is_correct'] else None
            }
            if game['actual_winner']:
                total += 1
                if game['is_correct'] == 'True': correct += 1
            predictions_list.append(game_info)
        
        return jsonify({
            "games": predictions_list,
            "accuracy": {"correct": correct, "total": total, "percentage": (correct / total * 100) if total > 0 else 0}
        })
    else:
        result, status_code = predict_future_week(year, seasontype, week)
        return jsonify(result), status_code

# --- NEW: Standings Page Route ---
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


if __name__ == '__main__':
    app.run(debug=True)