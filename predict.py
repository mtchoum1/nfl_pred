from team import pyth_win, expect_stat, get_weighted_stat

def calculate_expected_stats(team1_data_old, team1_data_new, team2_data_old, team2_data_new):
    expected_stats = {"team1": {}, "team2": {}}
    # Team 1
    team1_pyds_for_weighted = get_weighted_stat(team1_data_old.avg_pyds_for, team1_data_new.avg_pyds_for)
    team1_pyds_agst_weighted = get_weighted_stat(team1_data_old.avg_pyds_agst, team1_data_new.avg_pyds_agst)
    team1_ryds_for_weighted = get_weighted_stat(team1_data_old.avg_ryds_for, team1_data_new.avg_ryds_for)
    team1_ryds_agst_weighted = get_weighted_stat(team1_data_old.avg_ryds_agst, team1_data_new.avg_ryds_agst)
    team1_takeaways_weighted = get_weighted_stat(team1_data_old.avg_takeaways, team1_data_new.avg_takeaways)
    team1_giveaways_weighted = get_weighted_stat(team1_data_old.avg_giveaways, team1_data_new.avg_giveaways)
    team1_points_for_weighted = get_weighted_stat(team1_data_old.avg_points_for, team1_data_new.avg_points_for)
    team1_points_agst_weighted = get_weighted_stat(team1_data_old.avg_points_agst, team1_data_new.avg_points_agst)
    # Team 2
    team2_pyds_for_weighted = get_weighted_stat(team2_data_old.avg_pyds_for, team2_data_new.avg_pyds_for)
    team2_pyds_agst_weighted = get_weighted_stat(team2_data_old.avg_pyds_agst, team2_data_new.avg_pyds_agst)
    team2_ryds_for_weighted = get_weighted_stat(team2_data_old.avg_ryds_for, team2_data_new.avg_ryds_for)
    team2_ryds_agst_weighted = get_weighted_stat(team2_data_old.avg_ryds_agst, team2_data_new.avg_ryds_agst)
    team2_takeaways_weighted = get_weighted_stat(team2_data_old.avg_takeaways, team2_data_new.avg_takeaways)
    team2_giveaways_weighted = get_weighted_stat(team2_data_old.avg_giveaways, team2_data_new.avg_giveaways)
    team2_points_for_weighted = get_weighted_stat(team2_data_old.avg_points_for, team2_data_new.avg_points_for)
    team2_points_agst_weighted = get_weighted_stat(team2_data_old.avg_points_agst, team2_data_new.avg_points_agst)
    # Expectations
    expected_stats["team1"]["pyds"] = expect_stat(team1_pyds_for_weighted, team2_pyds_agst_weighted)
    expected_stats["team2"]["pyds"] = expect_stat(team2_pyds_for_weighted, team1_pyds_agst_weighted)
    expected_stats["team1"]["ryds"] = expect_stat(team1_ryds_for_weighted, team2_ryds_agst_weighted)
    expected_stats["team2"]["ryds"] = expect_stat(team2_ryds_for_weighted, team1_ryds_agst_weighted)
    expected_stats["team1"]["takeaways"] = expect_stat(team1_takeaways_weighted, team2_giveaways_weighted)
    expected_stats["team2"]["takeaways"] = expect_stat(team2_takeaways_weighted, team1_giveaways_weighted)
    expected_stats["team1"]["points"] = expect_stat(team1_points_for_weighted, team2_points_agst_weighted)
    expected_stats["team2"]["points"] = expect_stat(team2_points_for_weighted, team1_points_agst_weighted)
    return expected_stats

def calculate_pythagorean_wins(expected_stats_team1, expected_stats_team2):
    total_pyth_win = 0
    categories = ["pyds", "ryds", "takeaways", "points"]
    for category in categories:
        total_pyth_win += pyth_win(expected_stats_team1[category], expected_stats_team2[category])
    return total_pyth_win / len(categories)

def predict_winner(team1_abv, team2_abv, teamsold_dict, teamsnew_dict):
    if team1_abv not in teamsold_dict or team1_abv not in teamsnew_dict:
        print(f"Error: Team abbreviation '{team1_abv}' not found in data.")
        return
    if team2_abv not in teamsold_dict or team2_abv not in teamsnew_dict:
        print(f"Error: Team abbreviation '{team2_abv}' not found in data.")
        return
    expected_stats = calculate_expected_stats(
        teamsold_dict[team1_abv], teamsnew_dict[team1_abv],
        teamsold_dict[team2_abv], teamsnew_dict[team2_abv]
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
