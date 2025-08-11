import requests
import json
from data_loader import load_teams_from_json, load_teams_from_csv
from predict import predict_winner

url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLTeams"
querystring = {
    "sortBy": "standings",
    "rosters": "false",
    "schedules": "false",
    "topPerformers": "false",
    "teamStats": "true",
    "teamStatsSeason": "2023"
}
headers = {
    "x-rapidapi-key": "8052fdc050msh22dab4831663d70p1d8b78jsna0a4c17fee52",
    "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
old_teams = load_teams_from_json(json.dumps(response.json()))
new_teams = load_teams_from_csv("team_abv.csv")

# Get weekly schedule
schedule_url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLGamesForWeek"
schedule_querystring = {"week": "1", "seasonType": "reg", "season": "2024"}

schedule_response = requests.get(schedule_url, headers=headers, params=schedule_querystring)
schedule_data = schedule_response.json()

print("Predictions for Week 1, 2024:\n")
games_with_ids = []
predictions = {}

for game in schedule_data.get("body", []):
    home = game.get("home")
    away = game.get("away")
    game_id = game.get("gameID")
    if home and away and game_id:
        print(f"{away} at {home} (GameID: {game_id}):")
        # Predict winner and store prediction
        winner = predict_winner(away, home, old_teams, new_teams)
        predictions[game_id] = winner  # Store predicted winner
        print("-" * 30)
        games_with_ids.append({
            "gameID": game_id,
            "home": home,
            "away": away
        })

# Now check results using the box score API
boxscore_url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLBoxScore"
correct = 0
total = 0

for game in games_with_ids:
    game_id = game["gameID"]
    home = game["home"]
    away = game["away"]
    querystring = {"gameID": game_id}
    boxscore_response = requests.get(boxscore_url, headers=headers, params=querystring)
    boxscore_data = boxscore_response.json()
    try:
        # Updated for new JSON structure
        body = boxscore_data["body"]
        home_pts = int(body["homePts"])
        away_pts = int(body["awayPts"])
        actual_winner = home if home_pts > away_pts else away
        predicted_winner = predictions.get(game_id)
        print(f"Game {game_id}: Predicted {predicted_winner}, Actual {actual_winner}")
        if predicted_winner == actual_winner:
            correct += 1
        total += 1
    except Exception as e:
        print(f"Could not get result for {game_id}: {e}")

print(f"\nPrediction accuracy: {correct}/{total} correct")