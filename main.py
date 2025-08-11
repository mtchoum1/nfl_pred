import json
import requests
import csv # Keeping csv import as it was in the original code, though not used in the new function
from math import pow # pow is in math module

class team:
    """
    Represents an NFL team's average statistics for various categories.
    """
    def __init__(self, pyds_for, pyds_agst, ryds_for, ryds_agst, takeaways, giveaways, points_for, points_agst, games):
        """
        Initializes a team object with total stats and calculates average per game.
        Args:
            pyds_for (float): Total passing yards for.
            pyds_agst (float): Total passing yards against.
            ryds_for (float): Total rushing yards for.
            ryds_agst (float): Total rushing yards against.
            takeaways (float): Total takeaways (interceptions + fumble recoveries).
            giveaways (float): Total giveaways (interceptions + fumbles lost).
            points_for (float): Total points scored.
            points_agst (float): Total points allowed.
            games (float): Total games played. Ensures division by at least 1.
        """
        # Ensure games is at least 1 to prevent ZeroDivisionError
        valid_games = max(games, 1)

        self.avg_pyds_for = pyds_for / valid_games
        self.avg_pyds_agst = pyds_agst / valid_games
        self.avg_ryds_for = ryds_for / valid_games
        self.avg_ryds_agst = ryds_agst / valid_games
        self.avg_takeaways = takeaways / valid_games
        self.avg_giveaways = giveaways / valid_games
        self.avg_points_for = points_for / valid_games
        self.avg_points_agst = points_agst / valid_games

def pyth_win(stat_for, stat_agst):
    """
    Calculates the Pythagorean win expectation for a given statistical category.
    Args:
        stat_for (float): The "stat for" a team (e.g., points scored, yards gained).
        stat_agst (float): The "stat against" a team (e.g., points allowed, yards allowed by opponent).
    Returns:
        float: The Pythagorean win expectation (a value between 0 and 1).
    """
    # Ensure denominator is not zero. If both are zero, return 0.5 (even chance).
    denominator = pow(stat_for, 2.37) + pow(stat_agst, 2.37)
    if denominator == 0:
        return 0.5
    return pow(stat_for, 2.37) / denominator

def expect_stat(stat_for, stat_agst):
    """
    Calculates the expected value of a stat when two teams face each other.
    This is a simple average of one team's "for" stat and the opponent's "against" stat.
    Args:
        stat_for (float): The stat "for" the primary team.
        stat_agst (float): The stat "against" the opponent team.
    Returns:
        float: The expected stat value for the primary team in the matchup.
    """
    return (stat_for + stat_agst) / 2

def get_weighted_stat(old_stat, new_stat, old_weight=0.2, new_weight=0.8):
    """
    Calculates a weighted average of a stat from two different periods.
    Args:
        old_stat (float): The statistic from an older period.
        new_stat (float): The statistic from a newer period.
        old_weight (float): The weight assigned to the old statistic (default: 0.2).
        new_weight (float): The weight assigned to the new statistic (default: 0.8).
    Returns:
        float: The weighted average of the stat.
    """
    return (old_stat * old_weight) + (new_stat * new_weight)

def calculate_expected_stats(team1_data_old, team1_data_new, team2_data_old, team2_data_new):
    """
    Calculates expected stats for two teams across various categories using weighted averages.
    Returns a dictionary of expected stats for team1 and team2.
    Args:
        team1_data_old (team): Team 1's older statistical data.
        team1_data_new (team): Team 1's newer statistical data.
        team2_data_old (team): Team 2's older statistical data.
        team2_data_new (team): Team 2's newer statistical data.
    Returns:
        dict: A dictionary containing expected stats for 'team1' and 'team2'.
    """
    expected_stats = {
        "team1": {},
        "team2": {}
    }

    # Calculate weighted average stats for Team 1
    team1_pyds_for_weighted = get_weighted_stat(team1_data_old.avg_pyds_for, team1_data_new.avg_pyds_for)
    team1_pyds_agst_weighted = get_weighted_stat(team1_data_old.avg_pyds_agst, team1_data_new.avg_pyds_agst)
    team1_ryds_for_weighted = get_weighted_stat(team1_data_old.avg_ryds_for, team1_data_new.avg_ryds_for)
    team1_ryds_agst_weighted = get_weighted_stat(team1_data_old.avg_ryds_agst, team1_data_new.avg_ryds_agst)
    team1_takeaways_weighted = get_weighted_stat(team1_data_old.avg_takeaways, team1_data_new.avg_takeaways)
    team1_giveaways_weighted = get_weighted_stat(team1_data_old.avg_giveaways, team1_data_new.avg_giveaways)
    team1_points_for_weighted = get_weighted_stat(team1_data_old.avg_points_for, team1_data_new.avg_points_for)
    team1_points_agst_weighted = get_weighted_stat(team1_data_old.avg_points_agst, team1_data_new.avg_points_agst)

    # Calculate weighted average stats for Team 2
    team2_pyds_for_weighted = get_weighted_stat(team2_data_old.avg_pyds_for, team2_data_new.avg_pyds_for)
    team2_pyds_agst_weighted = get_weighted_stat(team2_data_old.avg_pyds_agst, team2_data_new.avg_pyds_agst)
    team2_ryds_for_weighted = get_weighted_stat(team2_data_old.avg_ryds_for, team2_data_new.avg_ryds_for)
    team2_ryds_agst_weighted = get_weighted_stat(team2_data_old.avg_ryds_agst, team2_data_new.avg_ryds_agst)
    team2_takeaways_weighted = get_weighted_stat(team2_data_old.avg_takeaways, team2_data_new.avg_takeaways)
    team2_giveaways_weighted = get_weighted_stat(team2_data_old.avg_giveaways, team2_data_new.avg_giveaways)
    team2_points_for_weighted = get_weighted_stat(team2_data_old.avg_points_for, team2_data_new.avg_points_for)
    team2_points_agst_weighted = get_weighted_stat(team2_data_old.avg_points_agst, team2_data_new.avg_points_agst)

    # Passing Yards Expectation for the matchup
    expected_stats["team1"]["pyds"] = expect_stat(team1_pyds_for_weighted, team2_pyds_agst_weighted)
    expected_stats["team2"]["pyds"] = expect_stat(team2_pyds_for_weighted, team1_pyds_agst_weighted)

    # Rushing Yards Expectation for the matchup
    expected_stats["team1"]["ryds"] = expect_stat(team1_ryds_for_weighted, team2_ryds_agst_weighted)
    expected_stats["team2"]["ryds"] = expect_stat(team2_ryds_for_weighted, team1_ryds_agst_weighted)

    # Turnovers (Takeaways vs Giveaways) Expectation for the matchup
    expected_stats["team1"]["takeaways"] = expect_stat(team1_takeaways_weighted, team2_giveaways_weighted)
    expected_stats["team2"]["takeaways"] = expect_stat(team2_takeaways_weighted, team1_giveaways_weighted)

    # Points Expectation for the matchup
    expected_stats["team1"]["points"] = expect_stat(team1_points_for_weighted, team2_points_agst_weighted)
    expected_stats["team2"]["points"] = expect_stat(team2_points_for_weighted, team1_points_agst_weighted)

    return expected_stats

def calculate_pythagorean_wins(expected_stats_team1, expected_stats_team2):
    """
    Calculates the Pythagorean win expectation for a team based on expected stats
    across multiple categories.
    Args:
        expected_stats_team1 (dict): Dictionary of expected stats for the first team.
        expected_stats_team2 (dict): Dictionary of expected stats for the second team (opponent).
    Returns:
        float: The average Pythagorean win expectation across all categories.
    """
    total_pyth_win = 0
    categories = ["pyds", "ryds", "takeaways", "points"]
    for category in categories:
        # Handle cases where expected stat might be zero for both, preventing division by zero
        # The pyth_win function already handles this by returning 0.5.
        total_pyth_win += pyth_win(expected_stats_team1[category], expected_stats_team2[category])
    return total_pyth_win / len(categories)

def load_teams_from_csv(filepath):
    """
    Reads a CSV file and returns a dictionary of team name to team object.
    The CSV should have columns: Team, Team_Abv, Total_GamesPlayed, Total_PassingYardsFor, Total_PassingYardsAgainst,
    Total_RushingYardsFor, Total_RushingYardsAgainst, Total_Takeaways, Total_Giveaways, Total_PointsFor, Total_PointsAgainst
    """
    teams = {}
    try:
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row['Team_Abv']
                # Ensure all values are converted to float, providing defaults if missing
                t = team(
                    float(row.get('Total_PassingYardsFor', 0)),
                    float(row.get('Total_PassingYardsAgainst', 0)),
                    float(row.get('Total_RushingYardsFor', 0)),
                    float(row.get('Total_RushingYardsAgainst', 0)),
                    float(row.get('Total_Takeaways', 0)),
                    float(row.get('Total_Giveaways', 0)),
                    float(row.get('Total_PointsFor', 0)),
                    float(row.get('Total_PointsAgainst', 0)),
                    float(row.get('Total_GamesPlayed', 1)) # Default to 1 game if not found
                )
                teams[name] = t
    except FileNotFoundError:
        print(f"Error: CSV file not found at {filepath}")
    except Exception as e:
        print(f"An error occurred while loading CSV: {e}")
    return teams


def load_teams_from_json(json_string, games_played=17):
    """
    Converts a JSON string containing NFL team data into a dictionary of team objects.
    Args:
        json_string (str): The JSON data as a string.
        games_played (int): The number of games to use for calculating average stats,
                            as the provided JSON 'wins', 'loss', 'tie' are all '0'.
    Returns:
        dict: A dictionary where keys are team abbreviations (str) and values are team objects.
    """
    teams = {}
    data = json.loads(json_string) # Parse the JSON string
    
    for team_data in data["body"]:
        team_abv = team_data["teamAbv"]
        stats = team_data["teamStats"]

        # Extracting Offensive Stats
        pyds_for = float(stats["Passing"]["passYds"])
        ryds_for = float(stats["Rushing"]["rushYds"])

        # Calculating Points For
        # Assuming touchdowns are 6 points, field goals are 3, extra points are 1, 2-point conversions are 2
        points_for = (
            float(stats["Passing"]["passTD"]) * 6 +
            float(stats["Rushing"]["rushTD"]) * 6 +
            float(stats["Kicking"]["fgMade"]) * 3 +
            float(stats["Kicking"]["xpMade"]) * 1 +
            float(stats["Passing"].get("passingTwoPointConversion", 0)) * 2 +
            float(stats["Rushing"].get("rushingTwoPointConversion", 0)) * 2 +
            float(stats["Receiving"].get("receivingTwoPointConversion", 0)) * 2
        )

        # Extracting Defensive Stats (as "against" for opponent)
        pyds_agst = float(stats["Defense"]["passingYardsAllowed"])
        ryds_agst = float(stats["Defense"]["rushingYardsAllowed"])

        # Calculating Points Against (from opponent's perspective, so using TDs allowed)
        points_agst = (
            float(stats["Defense"]["passingTDAllowed"]) * 6 +
            float(stats["Defense"]["rushingTDAllowed"]) * 6
            # Kicking points allowed by opponent are not directly in this JSON structure
        )

        # Turnovers: Takeaways and Giveaways
        takeaways = float(stats["Defense"]["defensiveInterceptions"]) + float(stats["Defense"]["fumblesRecovered"])
        giveaways = float(stats["Passing"]["int"]) + float(stats["Defense"]["fumblesLost"]) # fumblesLost is offensive fumbles lost

        # Create a team object and add to the dictionary
        teams[team_abv] = team(
            pyds_for,
            pyds_agst,
            ryds_for,
            ryds_agst,
            takeaways,
            giveaways,
            points_for,
            points_agst,
            float(games_played)
        )
    return teams

def predict_winner(team1_abv, team2_abv, teams_dict):
    """
    Given two team abbreviations and a teams dictionary, calculates Pythagorean win averages
    and prints which team is favored.
    Args:
        team1_abv (str): Abbreviation for the first team.
        team2_abv (str): Abbreviation for the second team.
        teams_dict (dict): A dictionary mapping team abbreviations to team objects.
    """
    if team1_abv not in teams_dict:
        print(f"Error: Team abbreviation '{team1_abv}' not found in data.")
        return
    if team2_abv not in teams_dict:
        print(f"Error: Team abbreviation '{team2_abv}' not found in data.")
        return

    # In this scenario, we only have one set of "current" data from the JSON,
    # so we use the same team object for both 'old' and 'new' parameters.
    # This effectively means get_weighted_stat will return the exact value
    # from the team object without weighting.
    expected_stats = calculate_expected_stats(
        teams_dict[team1_abv], teams_dict[team1_abv],
        teams_dict[team2_abv], teams_dict[team2_abv]
    )
    team1_score = calculate_pythagorean_wins(expected_stats["team1"], expected_stats["team2"])
    team2_score = calculate_pythagorean_wins(expected_stats["team2"], expected_stats["team1"])
    print(f"{team1_abv}: {team1_score * 100:.2f}% | {team2_abv}: {team2_score * 100:.2f}%")
    if team1_score > team2_score:
        print(f"{team1_abv} is favored to win.")
    elif team2_score > team1_score:
        print(f"{team2_abv} is favored to win.")
    else:
        print("It's a tie!")

url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLTeams"

querystring = {"sortBy":"standings","rosters":"false","schedules":"false","topPerformers":"false","teamStats":"true","teamStatsSeason":"2023"}

headers = {
	"x-rapidapi-key": "8052fdc050msh22dab4831663d70p1d8b78jsna0a4c17fee52",
	"x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

# Load team data from the JSON string
teams_from_json = load_teams_from_json(json.dumps(response.json()))

# Example Usage: Predict a winner using the loaded JSON data
print("\n--- Predicting Winner with JSON Data ---")
predict_winner("BAL", "BUF", teams_from_json)
predict_winner("PHI", "DAL", teams_from_json)
predict_winner("SF", "MIN", teams_from_json)
