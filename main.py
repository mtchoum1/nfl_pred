import requests
import json
from data_loader import load_teams_from_json
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
teams_from_json = load_teams_from_json(json.dumps(response.json()))

print("\n--- Predicting Winner with JSON Data ---")
predict_winner("BAL", "BUF", teams_from_json, teams_from_json)
predict_winner("PHI", "DAL", teams_from_json, teams_from_json)
predict_winner("SF", "MIN", teams_from_json, teams_from_json)