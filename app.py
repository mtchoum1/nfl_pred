from flask import Flask, jsonify, render_template
import csv
import requests
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json, Team

app = Flask(__name__)

# --- Load Prediction History ---
# Load the pre-generated history file into memory on startup.
prediction_history = []
try:
    with open('prediction_history.csv', mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            prediction_history.append(row)
    print("Prediction history loaded successfully.")
except FileNotFoundError:
    print("WARNING: 'prediction_history.csv' not found.")
    print("Please run 'history_generator.py' to create the history file.")
    prediction_history = []


@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')


@app.route('/api/predict/<int:year>/<int:week>')
def get_predictions(year, week):
    """
    API endpoint to get the schedule and predictions for a given year and week
    by reading from the pre-generated history file.
    """
    
    # Filter the loaded history for the requested year and week
    games_for_week = [
        game for game in prediction_history 
        if int(game['year']) == year and int(game['week']) == week
    ]

    if not games_for_week:
        return jsonify({"error": f"No historical data found for {year}, Week {week}. The schedule may not be available for future dates."}), 404

    # We still need to fetch live data to get logos, game status, and current scores
    live_data = {}
    try:
        weekly_schedule_url = f"[https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=){year}&week={week}"
        response = requests.get(weekly_schedule_url)
        response.raise_for_status()
        for event in response.json().get('events', []):
            live_data[event['id']] = event
    except requests.RequestException as e:
        print(f"Could not fetch live data for {year}, Week {week}: {e}")
        # We can still proceed with the historical data, but it might be less complete
    
    
    predictions_list = []
    correct_predictions = 0
    total_games = 0

    for game in games_for_week:
        live_game_data = live_data.get(game['game_id'], {})
        
        # Default to historical data, but override with live data if available
        status = live_game_data.get('status', {}).get('type', {}).get('detail', 'Status Unavailable')
        game_date = live_game_data.get('date', '')
        game_name = live_game_data.get('name', f"{game['away_team']} at {game['home_team']}")

        home_team_live = {}
        away_team_live = {}
        if 'competitions' in live_game_data:
            competitors = live_game_data['competitions'][0]['competitors']
            home_team_live = next((c.get('team', {}) for c in competitors if c.get('homeAway') == 'home'), {})
            away_team_live = next((c.get('team', {}) for c in competitors if c.get('homeAway') == 'away'), {})


        game_info = {
            "id": game['game_id'],
            "date": game_date,
            "name": game_name,
            "status": status,
            "home_team": {
                "abbreviation": game['home_team'],
                "logo": home_team_live.get('logo'),
                "score": next((c.get('score', '0') for c in live_game_data.get('competitions', [{}])[0].get('competitors', []) if c.get('homeAway') == 'home'), '0'),
                "win_probability": float(game['home_win_prob']) if game['home_win_prob'] else 0
            },
            "away_team": {
                "abbreviation": game['away_team'],
                "logo": away_team_live.get('logo'),
                "score": next((c.get('score', '0') for c in live_game_data.get('competitions', [{}])[0].get('competitors', []) if c.get('homeAway') == 'away'), '0'),
                "win_probability": float(game['away_win_prob']) if game['away_win_prob'] else 0
            },
            "predicted_winner": game['predicted_winner'],
            "actual_winner": game['actual_winner'],
            "is_correct": game['is_correct'] == 'True' if game['is_correct'] else None
        }
        
        if game['actual_winner']:
            total_games += 1
            if game['is_correct'] == 'True':
                correct_predictions += 1

        predictions_list.append(game_info)

    return jsonify({
        "games": predictions_list,
        "accuracy": {
            "correct": correct_predictions,
            "total": total_games,
            "percentage": (correct_predictions / total_games * 100) if total_games > 0 else 0
        }
    })


if __name__ == '__main__':
    app.run(debug=True)
