import csv
import json
from team import Team

def load_teams_from_csv(filepath):
    teams = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Team_Abv']
            teams[name] = Team()
    return teams