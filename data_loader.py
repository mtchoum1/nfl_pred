import csv
import json
from team import Team

def load_teams_from_csv(filepath):
    teams = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Team_Abv']
            t = Team(0, 0, 0, 0, 0, 0, 0, 0, 1)
            teams[name] = t
    return teams

def load_teams_from_json(json_string, games_played=17):
    teams = {}
    data = json.loads(json_string)
    for team_data in data["body"]:
        team_abv = team_data["teamAbv"]
        stats = team_data["teamStats"]
        pyds_for = float(stats["Passing"]["passYds"])
        ryds_for = float(stats["Rushing"]["rushYds"])
        points_for = (
            float(stats["Passing"]["passTD"]) * 6 +
            float(stats["Rushing"]["rushTD"]) * 6 +
            float(stats["Kicking"]["fgMade"]) * 3 +
            float(stats["Kicking"]["xpMade"]) * 1 +
            float(stats["Passing"].get("passingTwoPointConversion", 0)) * 2 +
            float(stats["Rushing"].get("rushingTwoPointConversion", 0)) * 2
        )
        pyds_agst = float(stats["Defense"]["passingYardsAllowed"])
        ryds_agst = float(stats["Defense"]["rushingYardsAllowed"])
        points_agst = (
            float(stats["Defense"]["passingTDAllowed"]) * 6 +
            float(stats["Defense"]["rushingTDAllowed"]) * 6
        )
        takeaways = float(stats["Defense"]["defensiveInterceptions"]) + float(stats["Defense"]["fumblesRecovered"])
        giveaways = float(stats["Passing"]["int"]) + float(stats["Defense"]["fumblesLost"])
        teams[team_abv] = Team(
            pyds_for, pyds_agst, ryds_for, ryds_agst,
            takeaways, giveaways, points_for, points_agst, float(games_played)
        )
    return teams