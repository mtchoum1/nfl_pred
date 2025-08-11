import requests
import json
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json

old_teams = load_teams_from_csv('team_abv.csv')

url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLGamesForWeek"
boxscore_url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLBoxScore"

querystring = {"week":"all","seasonType":"all","season":"2022"}

headers = {
	"x-rapidapi-key": "8052fdc050msh22dab4831663d70p1d8b78jsna0a4c17fee52",
	"x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
schedule_data = response.json()

for game in schedule_data.get("body", []):
    game_id = game.get("gameID")
    seasontype = game.get("seasonType")
    if game_id and seasontype in ["Regular Season", "Postseason"]:
        bquerystring = {"gameID": game_id}
        boxscore_response = requests.get(boxscore_url, headers=headers, params=bquerystring)
        boxscore_data = boxscore_response.json()
        try:
            parse_game_json(boxscore_data, old_teams)
        except Exception as e:
            print(f"Could not get result for {game_id}: {e}")

print(f"{old_teams}")