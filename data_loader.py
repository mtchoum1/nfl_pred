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
        'Team', 'Team_Abv', 'Total_GamesPlayed', 'Total_PassingYardsFor', 'Total_PassingYardsAgainst',
        'Total_RushingYardsFor', 'Total_RushingYardsAgainst', 'Total_Takeaways', 'Total_Giveaways',
        'Total_PointsFor', 'Total_PointsAgainst'
    ]
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for abv, team in teams.items():
            # Assume team object has attributes matching the columns
            row = {
                'Team_Abv': abv,
                'Total_GamesPlayed': getattr(team, 'games_played', 0),
                'Total_PassingYardsFor': getattr(team, 'total_passing_yards_for', 0),
                'Total_PassingYardsAgainst': getattr(team, 'total_passing_yards_against', 0),
                'Total_RushingYardsFor': getattr(team, 'total_rushing_yards_for', 0),
                'Total_RushingYardsAgainst': getattr(team, 'total_rushing_yards_against', 0),
                'Total_Takeaways': getattr(team, 'total_takeaways', 0),
                'Total_Giveaways': getattr(team, 'total_giveaways', 0),
                'Total_PointsFor': getattr(team, 'total_points_for', 0),
                'Total_PointsAgainst': getattr(team, 'total_points_against', 0),
            }
            writer.writerow(row)