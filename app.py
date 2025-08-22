from flask import Flask, jsonify, render_template
import csv
import requests
import json
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json, Team

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
    with open('latest_season_stats.json', 'r') as f:
        # When loading, convert the dicts back into Team objects
        deserialized_stats = json.load(f)
        for name, stats in deserialized_stats.items():
            latest_season_stats[name] = Team(**stats)
    print("Base stats for live predictions loaded successfully.")
except FileNotFoundError:
    print("WARNING: 'latest_season_stats.json' not found. Live predictions may not work.")
    print("Please run 'history_generator.py' to create the necessary files.")


def predict_future_week(year, week):
    """
    Generates predictions for a future week on-the-fly.
    """
    print(f"Generating live predictions for {year}, Week {week}...")
    
    # For future predictions, 'old_teams' is the last fully completed season.
    old_teams = latest_season_stats
    # 'new_teams' starts fresh for the new season.
    # In a more advanced version, you would update this with the current season's completed games.
    new_teams = load_teams_from_csv('team_abv.csv')

    if not old_teams:
        return {"error": "Missing base data from last season. Cannot make live predictions."}, 500

    predictions_list = []
    try:
        weekly_schedule_url = f"[https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=){year}&week={week}"
        response = requests.get(weekly_schedule_url)
        response.raise_for_status()
        events = response.json().get('events', [])

        for game in events:
            # ... (logic to extract teams and run prediction)
            game_id = game.get('id')
            competition = game['competitions'][0]
            competitors = competition['competitors']
            home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})
            if not home_team_data or not away_team_data: continue
            
            home_team_abv = home_team_data.get('team', {}).get('abbreviation')
            away_team_abv = away_team_data.get('team', {}).get('abbreviation')

            predicted_winner, team1_prob, team2_prob = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams)

            game_info = {
                "id": game_id,
                "date": game.get('date'),
                "name": game.get('name'),
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


@app.route('/api/predict/<int:year>/<int:week>')
def get_predictions(year, week):
    # Check if the requested week is in our history
    games_for_week = [g for g in prediction_history if int(g['year']) == year and int(g['week']) == week]

    if games_for_week:
        # If it is, serve the historical data
        print(f"Serving historical data for {year}, Week {week}.")
        # (The rest of the historical data processing logic remains the same)
        live_data = {}
        try:
            weekly_schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}&week={week}"
            response = requests.get(weekly_schedule_url)
            response.raise_for_status()
            for event in response.json().get('events', []):
                live_data[event['id']] = event
        except requests.RequestException as e:
            print(f"Could not fetch live data for {year}, Week {week}: {e}")
        
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
        # If not in history, it's a future week, so predict it live
        result, status_code = predict_future_week(year, week)
        return jsonify(result), status_code

if __name__ == '__main__':
    app.run(debug=True)
