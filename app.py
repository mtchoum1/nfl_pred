# app.py
from flask import Flask, jsonify, render_template
import requests
import json
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json, Team

app = Flask(__name__)

# --- Caching ---
# In a real-world app, you'd use a more robust caching solution like Redis or Flask-Caching.
# For this example, we'll use a simple dictionary to cache the initial team data.
cache = {
    "teams_2022": None
}

def get_2022_team_data():
    """
    Fetches and caches the team data from the 2022 season.
    This prevents re-fetching and processing this data on every request.
    """
    if cache["teams_2022"] is None:
        print("Fetching and processing 2022 data for the first time...")
        teams_2022 = load_teams_from_csv('team_abv.csv')
        schedule_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2022"
        boxscore_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="

        try:
            schedule_response = requests.get(schedule_url)
            schedule_response.raise_for_status()
            schedule_data = schedule_response.json()
            events = schedule_data.get('events', [])

            for game in events:
                game_id = game.get('id')
                season_type = game.get('season', {}).get('type')
                if game_id and season_type in [2, 3]:  # Regular Season & Postseason
                    boxscore_url = f"{boxscore_base_url}{game_id}"
                    try:
                        boxscore_response = requests.get(boxscore_url)
                        boxscore_response.raise_for_status()
                        boxscore_data = boxscore_response.json()
                        parse_game_json(boxscore_data, teams_2022)
                    except requests.exceptions.RequestException as e:
                        print(f"Could not fetch boxscore for game {game_id}: {e}")
            cache["teams_2022"] = teams_2022
            print("Finished processing 2022 data.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching 2022 schedule data: {e}")
            return None
    return cache["teams_2022"]


@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')


@app.route('/api/predict/<int:year>/<int:week>')
def get_predictions(year, week):
    """
    API endpoint to get the schedule and predictions for a given year and week.
    """
    old_teams = get_2022_team_data()
    if old_teams is None:
        return jsonify({"error": "Could not load historical team data."}), 500

    new_teams = load_teams_from_csv('team_abv.csv') # Fresh stats for the current year
    weekly_schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}&week={week}"
    boxscore_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="

    predictions_list = []
    correct_predictions = 0
    total_games = 0

    try:
        weekly_response = requests.get(weekly_schedule_url)
        weekly_response.raise_for_status()
        weekly_data = weekly_response.json()
        events = weekly_data.get('events', [])

        for game in events:
            game_id = game.get('id')
            competition = game['competitions'][0]
            competitors = competition['competitors']
            
            home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})

            if not home_team_data or not away_team_data:
                continue

            home_team_abv = home_team_data.get('team', {}).get('abbreviation')
            away_team_abv = away_team_data.get('team', {}).get('abbreviation')

            # Make prediction
            predicted_winner_abv, team1_win_prob, team2_win_prob = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams)

            game_info = {
                "id": game_id,
                "date": game.get('date'),
                "name": game.get('name'),
                "status": game.get('status', {}).get('type', {}).get('detail'),
                "home_team": {
                    "abbreviation": home_team_abv,
                    "logo": home_team_data.get('team', {}).get('logo'),
                    "score": home_team_data.get('score', '0'),
                    "win_probability": team1_win_prob if home_team_abv == home_team_abv else team2_win_prob
                },
                "away_team": {
                    "abbreviation": away_team_abv,
                    "logo": away_team_data.get('team', {}).get('logo'),
                    "score": away_team_data.get('score', '0'),
                    "win_probability": team1_win_prob if away_team_abv == home_team_abv else team2_win_prob
                },
                "predicted_winner": predicted_winner_abv,
                "actual_winner": None,
                "is_correct": None
            }
            
            # If game is over, determine actual winner and check prediction
            if game.get('status', {}).get('type', {}).get('completed', False):
                total_games += 1
                home_score = int(home_team_data.get('score', 0))
                away_score = int(away_team_data.get('score', 0))
                
                actual_winner = None
                if home_score > away_score:
                    actual_winner = home_team_abv
                elif away_score > home_score:
                    actual_winner = away_team_abv
                
                game_info["actual_winner"] = actual_winner
                if predicted_winner_abv == actual_winner:
                    game_info["is_correct"] = True
                    correct_predictions += 1
                else:
                    game_info["is_correct"] = False


            predictions_list.append(game_info)

        return jsonify({
            "games": predictions_list,
            "accuracy": {
                "correct": correct_predictions,
                "total": total_games,
                "percentage": (correct_predictions / total_games * 100) if total_games > 0 else 0
            }
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching weekly schedule for week {week}: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    # To run this:
    # 1. Make sure you have Flask installed: pip install Flask
    # 2. Create a folder named 'templates' and put 'index.html' inside it.
    # 3. Make sure 'team_abv.csv', 'data_loader.py', 'predict.py', and 'team.py' are in the same directory.
    # 4. Run this script: python app.py
    # 5. Open your web browser to http://127.0.0.1:5000
    app.run(debug=True)