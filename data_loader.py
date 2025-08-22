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

def save_teams_to_csv(teams, filename):
    """
    Save the teams dictionary to a CSV file with the correct columns.
    """
    fieldnames = [
        'Team_Abv', 'Total_GamesPlayed', 'Total_PassingYardsFor', 'Total_PassingYardsAgainst',
        'Total_RushingYardsFor', 'Total_RushingYardsAgainst', 'Total_Takeaways', 'Total_Giveaways',
        'Total_PointsFor', 'Total_PointsAgainst'
    ]
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for abv, team in teams.items():
            row = {
                'Team_Abv': abv,
                'Total_GamesPlayed': team.games,
                'Total_PassingYardsFor': team.pyds_for,
                'Total_PassingYardsAgainst': team.pyds_agst,
                'Total_RushingYardsFor': team.ryds_for,
                'Total_RushingYardsAgainst': team.ryds_agst,
                'Total_Takeaways': team.takeaways,
                'Total_Giveaways': team.giveaways,
                'Total_PointsFor': team.points_for,
                'Total_PointsAgainst': team.points_agst,
            }
            writer.writerow(row)