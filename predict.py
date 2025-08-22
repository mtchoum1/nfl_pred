import random
from team import pyth_win, expect_stat, get_weighted_stat

def calculate_expected_stats(team1_data_old, team1_data_new, team2_data_old, team2_data_new, week, home_team_abv, team1_abv):
    expected_stats = {"team1": {}, "team2": {}}
    
    # --- Define Thresholds and Constants ---
    PASS_HEAVY_THRESHOLD = 0.55
    RUN_HEAVY_THRESHOLD = 0.45
    BAD_PASS_DEF_THRESHOLD = 235
    BAD_RUSH_DEF_THRESHOLD = 125
    HOME_FIELD_ADVANTAGE_POINTS = 2.5 # Average point advantage for home teams

    # --- Get Weighted Averages using Dynamic Weighting ---
    t1_pyds_for = get_weighted_stat(team1_data_old.avg_pyds_for, team1_data_new.avg_pyds_for, week)
    t1_pyds_agst = get_weighted_stat(team1_data_old.avg_pyds_agst, team1_data_new.avg_pyds_agst, week)
    t1_ryds_for = get_weighted_stat(team1_data_old.avg_ryds_for, team1_data_new.avg_ryds_for, week)
    t1_ryds_agst = get_weighted_stat(team1_data_old.avg_ryds_agst, team1_data_new.avg_ryds_agst, week)

    t2_pyds_for = get_weighted_stat(team2_data_old.avg_pyds_for, team2_data_new.avg_pyds_for, week)
    t2_pyds_agst = get_weighted_stat(team2_data_old.avg_pyds_agst, team2_data_new.avg_pyds_agst, week)
    t2_ryds_for = get_weighted_stat(team2_data_old.avg_ryds_for, team2_data_new.avg_ryds_for, week)
    t2_ryds_agst = get_weighted_stat(team2_data_old.avg_ryds_agst, team2_data_new.avg_ryds_agst, week)

    # --- Calculate Tendencies ---
    t1_total_plays = team1_data_new.avg_pass_attempts + team1_data_new.avg_rush_attempts
    t1_pass_tendency = team1_data_new.avg_pass_attempts / t1_total_plays if t1_total_plays > 0 else 0.5
    t2_total_plays = team2_data_new.avg_pass_attempts + team2_data_new.avg_rush_attempts
    t2_pass_tendency = team2_data_new.avg_pass_attempts / t2_total_plays if t2_total_plays > 0 else 0.5
    
    # --- Apply Boosts for Favorable Matchups ---
    t1_pyds_boost = 1.05 if t1_pass_tendency > PASS_HEAVY_THRESHOLD and t2_pyds_agst > BAD_PASS_DEF_THRESHOLD else 1.0
    t1_ryds_boost = 1.05 if (1 - t1_pass_tendency) > RUN_HEAVY_THRESHOLD and t2_ryds_agst > BAD_RUSH_DEF_THRESHOLD else 1.0
    t2_pyds_boost = 1.05 if t2_pass_tendency > PASS_HEAVY_THRESHOLD and t1_pyds_agst > BAD_PASS_DEF_THRESHOLD else 1.0
    t2_ryds_boost = 1.05 if (1 - t2_pass_tendency) > RUN_HEAVY_THRESHOLD and t1_ryds_agst > BAD_RUSH_DEF_THRESHOLD else 1.0

    # --- Calculate Final Expected Stats ---
    expected_stats["team1"]["pyds"] = expect_stat(t1_pyds_for * t1_pyds_boost, t2_pyds_agst)
    expected_stats["team2"]["pyds"] = expect_stat(t2_pyds_for * t2_pyds_boost, t1_pyds_agst)
    expected_stats["team1"]["ryds"] = expect_stat(t1_ryds_for * t1_ryds_boost, t2_ryds_agst)
    expected_stats["team2"]["ryds"] = expect_stat(t2_ryds_for * t2_ryds_boost, t1_ryds_agst)
    expected_stats["team1"]["takeaways"] = expect_stat(get_weighted_stat(team1_data_old.avg_takeaways, team1_data_new.avg_takeaways, week), get_weighted_stat(team2_data_old.avg_giveaways, team2_data_new.avg_giveaways, week))
    expected_stats["team2"]["takeaways"] = expect_stat(get_weighted_stat(team2_data_old.avg_takeaways, team2_data_new.avg_takeaways, week), get_weighted_stat(team1_data_old.avg_giveaways, team1_data_new.avg_giveaways, week))
    expected_stats["team1"]["points"] = expect_stat(get_weighted_stat(team1_data_old.avg_points_for, team1_data_new.avg_points_for, week), get_weighted_stat(team2_data_old.avg_points_agst, team2_data_new.avg_points_agst, week))
    expected_stats["team2"]["points"] = expect_stat(get_weighted_stat(team2_data_old.avg_points_for, team2_data_new.avg_points_for, week), get_weighted_stat(team1_data_old.avg_points_agst, team1_data_new.avg_points_agst, week))

    # --- Apply Home-Field Advantage ---
    if team1_abv == home_team_abv:
        expected_stats["team1"]["points"] += HOME_FIELD_ADVANTAGE_POINTS
    else:
        expected_stats["team2"]["points"] += HOME_FIELD_ADVANTAGE_POINTS
        
    return expected_stats

def calculate_pythagorean_wins(expected_stats_team1, expected_stats_team2):
    total_pyth_win = 0
    categories = ["pyds", "ryds", "takeaways", "points"]
    for category in categories:
        total_pyth_win += pyth_win(expected_stats_team1[category], expected_stats_team2[category])
    return total_pyth_win / len(categories)

def predict_winner(team1_abv, team2_abv, teamsold_dict, teamsnew_dict, week, home_team_abv):
    if team1_abv not in teamsold_dict or team2_abv not in teamsold_dict:
        return None, 0, 0
        
    expected_stats = calculate_expected_stats(
        teamsold_dict[team1_abv], teamsnew_dict[team1_abv],
        teamsold_dict[team2_abv], teamsnew_dict[team2_abv],
        week, home_team_abv, team1_abv
    )
    
    team1_score = calculate_pythagorean_wins(expected_stats["team1"], expected_stats["team2"])
    team2_score = 1 - team1_score

    print(f"{team1_abv} (Home: {team1_abv == home_team_abv}): {team1_score * 100:.2f}% | {team2_abv}: {team2_score * 100:.2f}%")
    
    winner = team1_abv if team1_score > team2_score else team2_abv
    if team1_score == team2_score:
        winner = random.choice([team1_abv, team2_abv])

    return winner, team1_score, team2_score
