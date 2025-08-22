import csv
from team import Team

def load_teams_from_csv(filepath):
    teams = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Team_Abv']
            t = Team(
                pyds_for=float(row.get('Total_PassingYardsFor', 0)),
                pyds_agst=float(row.get('Total_PassingYardsAgainst', 0)),
                ryds_for=float(row.get('Total_RushingYardsFor', 0)),
                ryds_agst=float(row.get('Total_RushingYardsAgainst', 0)),
                takeaways=float(row.get('Total_Takeaways', 0)),
                giveaways=float(row.get('Total_Giveaways', 0)),
                points_for=float(row.get('Total_PointsFor', 0)),
                points_agst=float(row.get('Total_PointsAgainst', 0)),
                pass_attempts=float(row.get('Total_PassAttempts', 0)),
                rush_attempts=float(row.get('Total_RushAttempts', 0)),
                games=float(row.get('Total_GamesPlayed', 0))
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
        'Total_PointsFor', 'Total_PointsAgainst', 'Total_PassAttempts', 'Total_RushAttempts'
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
                'Total_PassAttempts': team.pass_attempts,
                'Total_RushAttempts': team.rush_attempts
            }
            writer.writerow(row)