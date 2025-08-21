import csv
import json
from team import Team

def load_teams_from_csv(filepath):
    teams = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Team_Abv']
            t = Team(
                float(row.get('Total_PassingYardsFor', 0)),
                float(row.get('Total_PassingYardsAgainst', 0)),
                float(row.get('Total_RushingYardsFor', 0)),
                float(row.get('Total_RushingYardsAgainst', 0)),
                float(row.get('Total_Takeaways', 0)),
                float(row.get('Total_Giveaways', 0)),
                float(row.get('Total_PointsFor', 0)),
                float(row.get('Total_PointsAgainst', 0)),
                float(row.get('Total_GamesPlayed', 1))
            )
            teams[name] = t
    return teams