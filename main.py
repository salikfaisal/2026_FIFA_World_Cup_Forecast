import pandas as pd
from get_adjusted_elo_ratings import ratings_df
import statistics
import random
from pathlib import Path

# reads Dataframe of world cup matches
wc_matches_df = pd.read_csv("Match Results.csv")

# Reads Dataframe of third place teams combinations
third_place_combinations_df = pd.read_csv("Group Winners vs Third Placed Teams Combinations.csv")

# updates names of teams when they need to be changed
name_fixes = {
    "Turkey": "Türkiye",
    "Ivory Coast": "Côte d'Ivoire",
    "Curacao": "Curaçao",
    "Czech Republic": "Czechia",
    "Korea Republic": "South Korea",
    "Congo DR": "DR Congo",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Cape Verde": "Cabo Verde",
    "Republic of Ireland": "Ireland"
}

wc_matches_df["Home Team"] = wc_matches_df["Home Team"].replace(name_fixes)
wc_matches_df["Away Team"] = wc_matches_df["Away Team"].replace(name_fixes)

# gets each team's elo rating in a dictionary
team_ratings_dict = dict(
    zip(
        ratings_df["Team"],
        ratings_df["Adjusted Elo Rating"]
    )
)

# this function returns a simulation of the results of a game given the elo ratings of the two teams
def match_result(team_1_elo, team_2_elo):
    # uses the elo formula to get the two-outcome win probability
    team_1_wl = 1 / (10 ** ((team_2_elo - team_1_elo) / 400) + 1)
    # gets the average goal difference expected between the two sides
    # if two sides have an equal rating the probabilities are: 35% Team 1 win, 30% draw, 35% Team 2 win
    team_1_margin_mean = statistics.NormalDist(0, 1.3).inv_cdf(team_1_wl)
    # the goal difference as a result of a random simulation
    team_1_margin = round(statistics.NormalDist(team_1_margin_mean, 1.3).inv_cdf(random.random()))
    # the goal probability distribution from 1826 matches in the 2020-21 season in Europe's top 5 leagues
    goal_prob = [0.25985761226725085, 0.3417305585980285, 0.22343921139101863, 0.1119934282584885, 0.0443592552026287,
                 0.014786418400876232, 0.0024644030668127055, 0.0008214676889375684, 0.0002738225629791895,
                 0.0002738225629791895]
    gp_list = []
    if abs(team_1_margin) > 9:
        winning_goal_count = abs(team_1_margin)
        losing_goal_count = 0
    else:
        gp_list = goal_prob[abs(team_1_margin):]
        total = sum(gp_list)
        cum = 0
        for goal_count, goal_probability in enumerate(gp_list):
            gp_list[goal_count] = goal_probability / total
        goal_result = random.random()
        for gc, gp in enumerate(gp_list):
            cum += gp
            if goal_result < cum:
                winning_goal_count = gc + abs(team_1_margin)
                winning_goal_count = gc + abs(team_1_margin)
                losing_goal_count = winning_goal_count - abs(team_1_margin)
                break
    if team_1_margin >= 0:
        home_goals = winning_goal_count
        away_goals = home_goals - team_1_margin
    else:
        away_goals = winning_goal_count
        home_goals = away_goals + team_1_margin
    return [home_goals, away_goals]

def build_third_place_combinations_lookup(third_place_combinations_df):
    # Converts the third-place combinations CSV into a dictionary.
    # Key:
    #     tuple of advancing third-place groups, sorted alphabetically
    #
    #     Example:
    #     ("D", "E", "F", "G", "H", "I", "J", "K")
    #
    # Value:
    #     dictionary showing which third-place team each group winner plays
    #
    #     Example:
    #     {
    #         "1A": "3E",
    #         "1B": "3G",
    #         "1D": "3I",
    #         "1E": "3D",
    #         "1G": "3H",
    #         "1I": "3F",
    #         "1K": "3L",
    #         "1L": "3K",
    #     }

    group_columns = list("ABCDEFGHIJKL")
    winner_columns = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]

    combinations_lookup = {}

    for _, row in third_place_combinations_df.iterrows():
        advancing_groups = []

        # Find which third-place groups advanced in this row.
        for group in group_columns:
            if pd.notna(row[group]):
                advancing_groups.append(group)

        # Sort so the key works no matter what order we pass the groups in later.
        advancing_groups_key = tuple(sorted(advancing_groups))

        # Store the matchup assignment for this combination.
        assignment = {}

        for winner_column in winner_columns:
            assignment[winner_column] = row[winner_column]

        combinations_lookup[advancing_groups_key] = assignment

    return combinations_lookup

third_place_combinations_lookup = build_third_place_combinations_lookup(third_place_combinations_df)

groups = {"A": ["Mexico", "South Africa", "South Korea", "Czechia"],
          "B": ["Canada", "Bosnia & Herzegovina", "Qatar", "Switzerland"],
          "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
          "D": ["United States", "Paraguay", "Australia", "Türkiye"],
          "E": ["Germany", "Curaçao", "Côte d'Ivoire", "Ecuador"],
          "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
          "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
          "H": ["Spain", "Cabo Verde", "Saudi Arabia", "Uruguay"],
          "I": ["France", "Senegal", "Iraq", "Norway"],
          "J": ["Argentina", "Algeria", "Austria", "Jordan"],
          "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
          "L": ["England", "Croatia", "Ghana", "Panama"]}


group_fixtures = {}

for group_letter in groups:
    group_matches_df = wc_matches_df[wc_matches_df["Group/Stage"] == group_letter]

    fixtures = []

    for _, match in group_matches_df.iterrows():
        fixtures.append({
            "home_team": match["Home Team"],
            "away_team": match["Away Team"],
            "home_goals": match["Home Goals"],
            "away_goals": match["Away Goals"],
        })

    group_fixtures[group_letter] = fixtures


def update_group_table(table, home_team, away_team, home_goals, away_goals):
    # Updates the Group Table after One Match
    # Format: "France": {"points": 0, "gf": 0, "ga": 0, "gd": 0}

    # Award points
    if home_goals > away_goals:
        table[home_team]["points"] += 3
    elif home_goals < away_goals:
        table[away_team]["points"] += 3
    else:
        table[home_team]["points"] += 1
        table[away_team]["points"] += 1

    # Goals for
    table[home_team]["gf"] += home_goals
    table[away_team]["gf"] += away_goals

    # Goals against
    table[home_team]["ga"] += away_goals
    table[away_team]["ga"] += home_goals

    # Goal difference
    table[home_team]["gd"] = table[home_team]["gf"] - table[home_team]["ga"]
    table[away_team]["gd"] = table[away_team]["gf"] - table[away_team]["ga"]


def split_teams_by_sort_key(teams, key_function):
    # Groups teams by the same sorting key
    # Example: If France and Senegal have the same key, they stay together
    #     and need another tiebreaker.

    groups_by_key = {}

    for team in teams:
        key = key_function(team)

        if key not in groups_by_key:
            groups_by_key[key] = []

        groups_by_key[key].append(team)

    # Sort keys from best to worst.
    sorted_keys = sorted(groups_by_key.keys(), reverse=True)

    return [groups_by_key[key] for key in sorted_keys]


def get_head_to_head_stats(tied_teams, match_results):
    # Gets the Mini-Table Stats among the tied teams.
    # tied_teams
    # example:
    # ["Mexico", "South Korea", "Czechia"]
    #
    # match_results
    # format:
    # [
    #     ("Mexico", "South Korea", 1, 0),
    #     ("Czechia", "Mexico", 2, 2),
    # ]

    h2h_table = {}

    for team in tied_teams:
        h2h_table[team] = {
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
        }

    tied_team_set = set(tied_teams)

    for home_team, away_team, home_goals, away_goals in match_results:
        # Only use matches where BOTH teams are in the tied group.
        if home_team in tied_team_set and away_team in tied_team_set:
            update_group_table(
                h2h_table,
                home_team,
                away_team,
                home_goals,
                away_goals
            )

    return h2h_table


def break_points_tie(tied_teams, full_table, match_results):
    # Applies FIFA-style tiebreakers for teams tied on points.
    #
    # Order:
    # 1. Head-to-head points among tied teams
    # 2. Head-to-head goal difference among tied teams
    # 3. Head-to-head goals scored among tied teams
    # 4. Reapply head-to-head to teams still tied
    # 5. Overall group goal difference
    # 6. Overall group goals scored
    # 7. Random if still perfectly tied

    if len(tied_teams) == 1:
        return tied_teams

    # Build mini-table among only the tied teams.
    h2h_table = get_head_to_head_stats(tied_teams, match_results)

    # First apply head-to-head points, head-to-head GD, head-to-head GF.
    h2h_groups = split_teams_by_sort_key(
        tied_teams,
        lambda team: (
            h2h_table[team]["points"],
            h2h_table[team]["gd"],
            h2h_table[team]["gf"],
        )
    )

    ordered_teams = []

    for h2h_group in h2h_groups:
        # If this subgroup has one team, it is decided.
        if len(h2h_group) == 1:
            ordered_teams.extend(h2h_group)

        # If head-to-head split the larger tied group into smaller tied groups,
        # reapply head-to-head criteria only within the still-tied subgroup.
        elif len(h2h_group) < len(tied_teams):
            ordered_teams.extend(
                break_points_tie(h2h_group, full_table, match_results)
            )

        # If head-to-head did not separate this group at all,
        # move to overall group GD and goals scored.
        else:
            overall_groups = split_teams_by_sort_key(
                h2h_group,
                lambda team: (
                    full_table[team]["gd"],
                    full_table[team]["gf"],
                )
            )

            for overall_group in overall_groups:
                if len(overall_group) == 1:
                    ordered_teams.extend(overall_group)
                else:
                    # FIFA would continue to fair play / drawing lots.
                    # For a Monte Carlo model, random is a reasonable fallback.
                    random.shuffle(overall_group)
                    ordered_teams.extend(overall_group)

    return ordered_teams


def sort_group_table(table, match_results):
    # Sorts the group using FIFA-style tiebreakers.
    # Returns: [["France", points, gd, gf, ga],...]

    teams = list(table.keys())

    # First split teams by total group points.
    points_groups = split_teams_by_sort_key(
        teams,
        lambda team: (table[team]["points"],)
    )

    ordered_teams = []

    for points_group in points_groups:
        if len(points_group) == 1:
            ordered_teams.extend(points_group)
        else:
            ordered_teams.extend(
                break_points_tie(points_group, table, match_results)
            )

    standings = []

    for team in ordered_teams:
        standings.append([
            team,
            table[team]["points"],
            table[team]["gd"],
            table[team]["gf"],
            table[team]["ga"],
        ])

    return standings


def simulate_group(group_letter):
    # Simulates one World Cup group.
    # Returns a sorted group table in this format: [[team, points, goal_difference, goals_for, goals_against],...]

    teams = groups[group_letter]

    # Create empty group table.
    table = {}

    for team in teams:
        table[team] = {
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
        }

    # Get this group's six matches from the match CSV.
    group_matches_df = wc_matches_df[
        wc_matches_df["Group/Stage"] == group_letter
    ].copy()

    # Store every match result in this group.
    # This is needed for head-to-head tiebreakers.
    match_results = []

    for _, match in group_matches_df.iterrows():
        home_team = match["Home Team"]
        away_team = match["Away Team"]

        # If the match has already been played, use the real score.
        if pd.notna(match["Home Goals"]) and pd.notna(match["Away Goals"]):
            home_goals = int(match["Home Goals"])
            away_goals = int(match["Away Goals"])

        # Otherwise, simulate the match.
        else:
            home_elo = team_ratings_dict[home_team]
            away_elo = team_ratings_dict[away_team]
            if home_team in ["Mexico", "Canada", "United States"]:
                home_elo += 100
            elif away_team in ["Mexico", "Canada", "United States"]:
                away_elo += 100
            home_goals, away_goals = match_result(home_elo, away_elo)
        # Save result for head-to-head tiebreakers.
        match_results.append((home_team, away_team, home_goals, away_goals)
        )
        # Update group table.
        update_group_table(
            table,
            home_team,
            away_team,
            home_goals,
            away_goals
        )

    # Sort table using points first, then FIFA-style tiebreakers.
    standings = sort_group_table(table, match_results)

    return standings

summary_dict = {}
# In the Form of {Team: [Points, Goal Difference, 1st, 2nd, 3rd, 4th, R32, R16, QF, SF, F, C]
for group, teams in groups.items():
    for team in teams:
        summary_dict.update({team: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})


num_of_simulations = 100
for simulation in range(num_of_simulations):
    first_place_teams = []
    second_place_teams = []
    third_place_teams_stats = []
    for group in groups:
        group_results = simulate_group(group)
        for group_rank, team_stats in enumerate(group_results):
            team = team_stats[0]
            summary_stats = summary_dict[team]
            summary_stats[0] += team_stats[1]
            summary_stats[1] += team_stats[2]
            summary_stats[2 + group_rank] += 1

        first_place_teams.append(group_results[0][0])
        second_place_teams.append(group_results[1][0])

        third_place_team = group_results[2]

        third_place_teams_stats.append([
            third_place_team[0],  # team
            group,  # group
            third_place_team[1],  # points
            third_place_team[2],  # goal difference
            third_place_team[3],  # goals scored
            third_place_team[4],  # goals against
        ])

    # Rank third-place teams.
    # Tiebreakers:
    # 1. Points
    # 2. Goal difference
    # 3. Goals scored
    # 4. Random fallback if still tied
    random.shuffle(third_place_teams_stats)

    third_place_teams_stats = sorted(third_place_teams_stats, key=lambda team: (team[2],  # points
            team[3],  # goal difference
            team[4],  # goals scored
        ),
        reverse=True
    )

    # Top 8 third-place teams advance.
    third_place_advancing_stats = third_place_teams_stats[:8]
    third_place_eliminated_stats = third_place_teams_stats[8:]

    third_place_advancing_teams_dict = {}
    # In the form of {Group Letter: Team}
    for team_stats in third_place_advancing_stats:
        third_place_advancing_teams_dict.update({team_stats[1]: team_stats[0]})

    # Overwrite the original variable name
    third_place_advancing_teams_dict = dict(sorted(third_place_advancing_teams_dict.items()))

    third_place_combinations_dict_without_team_name = third_place_combinations_lookup[tuple(third_place_advancing_teams_dict.keys())]
    third_place_combinations_dict = {}
    for group_winner, third_placed_team in third_place_combinations_dict_without_team_name.items():
        # 1. Extract the group letter from the original value tuple/list
        group_of_third_placed_team = third_placed_team[1]

        # 2. Look up the actual country name from your second dictionary
        # print(group_winner, third_placed_team, group_of_third_placed_team)
        actual_team_name = third_place_advancing_teams_dict[group_of_third_placed_team]

        third_place_combinations_dict.update({group_winner: actual_team_name})

    round_of_32_matchups = [
        [first_place_teams[4], third_place_combinations_dict["1E"]],  # Match 1: Winner Group E vs 3rd
        [first_place_teams[8], third_place_combinations_dict["1I"]],  # Match 2: Winner Group I vs 3rd
        [second_place_teams[0], second_place_teams[1]],  # Match 3: Runner-up Group A vs Runner-up Group B
        [first_place_teams[5], second_place_teams[2]],  # Match 4: Winner Group F vs Runner-up Group C
        [second_place_teams[10], second_place_teams[11]],  # Match 5: Runner-up Group K vs Runner-up Group L
        [first_place_teams[7], second_place_teams[9]],  # Match 6: Winner Group H vs Runner-up Group J
        [first_place_teams[3], third_place_combinations_dict["1D"]],  # Match 7: Winner Group D vs 3rd
        [first_place_teams[6], third_place_combinations_dict["1G"]],  # Match 8: Winner Group G vs 3rd
        [first_place_teams[2], second_place_teams[5]],  # Match 9: Winner Group C vs Runner-up Group F
        [second_place_teams[4], second_place_teams[8]],  # Match 10: Runner-up Group E vs Runner-up Group I
        [first_place_teams[0], third_place_combinations_dict["1A"]],  # Match 11: Winner Group A vs 3rd
        [first_place_teams[11], third_place_combinations_dict["1L"]],  # Match 12: Winner Group L vs 3rd
        [first_place_teams[9], second_place_teams[7]],  # Match 13: Winner Group J vs Runner-up Group H
        [second_place_teams[3], second_place_teams[6]],  # Match 14: Runner-up Group D vs Runner-up Group G
        [first_place_teams[1], third_place_combinations_dict["1B"]],  # Match 15: Winner Group B vs 3rd
        [first_place_teams[10], third_place_combinations_dict["1K"]]  # Match 16: Winner Group K vs 3rd
    ]

    octofinalists = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for matchup_number, matchup in enumerate(round_of_32_matchups):
        home_team = matchup[0]
        away_team = matchup[1]
        summary_dict[home_team][6] += 1
        summary_dict[away_team][6] += 1
        if (home_team in octofinalists) or (away_team in octofinalists):
            continue
        else:
            # simulates the match
            home_team_elo = team_ratings_dict[home_team]
            away_team_elo = team_ratings_dict[away_team]
            if home_team in ["Mexico", "United States"]:
                home_team_elo += 100
            home_goals, away_goals = match_result(home_team_elo, away_team_elo)
            # advances the winning team
            if home_goals > away_goals:
                octofinalists[matchup_number] = home_team
            elif home_goals < away_goals:
                octofinalists[matchup_number] = away_team
            else:
                octofinalists[matchup_number] = random.choice(matchup)

    round_of_16_matchups = []
    matchup = []
    for team_number, team in enumerate(octofinalists):
        matchup.append(team)
        if len(matchup) == 2:
            round_of_16_matchups.append(matchup)
            matchup = []

    # Round of 16
    quarterfinalists = [0, 1, 2, 3, 4, 5, 6, 7]
    for matchup_number, matchup in enumerate(round_of_16_matchups):
        home_team = matchup[0]
        away_team = matchup[1]
        summary_dict[home_team][7] += 1
        summary_dict[away_team][7] += 1
        if (home_team in quarterfinalists) or (away_team in quarterfinalists):
            continue
        else:
            # simulates the match
            home_team_elo = team_ratings_dict[home_team]
            away_team_elo = team_ratings_dict[away_team]
            if home_team in ["Mexico", "United States"]:
                home_team_elo += 100
            home_goals, away_goals = match_result(home_team_elo, away_team_elo)
            # advances the winning team
            if home_goals > away_goals:
                quarterfinalists[matchup_number] = home_team
            elif home_goals < away_goals:
                quarterfinalists[matchup_number] = away_team
            else:
                quarterfinalists[matchup_number] = random.choice(matchup)

    quarterfinal_matchups = []
    matchup = []
    for team_number, team in enumerate(quarterfinalists):
        matchup.append(team)
        if len(matchup) == 2:
            quarterfinal_matchups.append(matchup)
            matchup = []

    # Quarterfinals
    semifinalists = [0, 1, 2, 3]
    for matchup_number, matchup in enumerate(quarterfinal_matchups):
        home_team = matchup[0]
        away_team = matchup[1]
        summary_dict[home_team][8] += 1
        summary_dict[away_team][8] += 1
        if (home_team in semifinalists) or (away_team in semifinalists):
            continue
        else:
            # simulates the match
            home_team_elo = team_ratings_dict[home_team]
            away_team_elo = team_ratings_dict[away_team]
            if home_team == "United States":
                home_team_elo += 100
            elif away_team == "United States":
                away_team_elo += 100
            home_goals, away_goals = match_result(home_team_elo, away_team_elo)
            # advances the winning team
            if home_goals > away_goals:
                semifinalists[matchup_number] = home_team
            elif home_goals < away_goals:
                semifinalists[matchup_number] = away_team
            else:
                semifinalists[matchup_number] = random.choice(matchup)

    semifinal_matchups = []
    matchup = []
    for team_number, team in enumerate(semifinalists):
        matchup.append(team)
        if len(matchup) == 2:
            semifinal_matchups.append(matchup)
            matchup = []

    # Semifinals
    finalists = [0, 1]
    for matchup_number, matchup in enumerate(semifinal_matchups):
        home_team = matchup[0]
        away_team = matchup[1]
        summary_dict[home_team][9] += 1
        summary_dict[away_team][9] += 1
        if (home_team in finalists) or (away_team in finalists):
            continue
        else:
            # simulates the match
            home_team_elo = team_ratings_dict[home_team]
            away_team_elo = team_ratings_dict[away_team]
            if home_team == "United States":
                home_team_elo += 100
            elif away_team == "United States":
                away_team_elo += 100
            home_goals, away_goals = match_result(home_team_elo, away_team_elo)
            # advances the winning team
            if home_goals > away_goals:
                finalists[matchup_number] = home_team
            elif home_goals < away_goals:
                finalists[matchup_number] = away_team
            else:
                finalists[matchup_number] = random.choice(matchup)

    # Final
    home_team = finalists[0]
    away_team = finalists[1]
    summary_dict[home_team][10] += 1
    summary_dict[away_team][10] += 1
    # simulates the match
    home_team_elo = team_ratings_dict[home_team]
    away_team_elo = team_ratings_dict[away_team]
    if home_team == "United States":
        home_team_elo += 100
    elif away_team == "United States":
        away_team_elo += 100
    home_goals, away_goals = match_result(home_team_elo, away_team_elo)
    # advances the winning team
    if home_goals > away_goals:
        champion = home_team
    elif home_goals < away_goals:
        champion = away_team
    else:
        champion = random.choice(finalists)
    summary_dict[champion][11] += 1

for team, original_summary_stats in summary_dict.items():
    # This replaces your empty list, inner loop, and append statements
    summary_dict[team] = [stat / num_of_simulations for stat in original_summary_stats]


# Define your column headers in the exact order of your list indices
column_names = [
    "Average Points",
    "Average Goal Difference",
    "1st",
    "2nd",
    "3rd",
    "4th",
    "Round of 32",
    "Round of 16",
    "Quarterfinals",
    "Semifinals",
    "Final",
    "Champion",
]


# Load the dictionary with teams as rows
df = pd.DataFrame.from_dict(summary_dict,orient="index", columns=column_names)

# Move team names from index into a real column
df = df.reset_index()
df = df.rename(columns={"index": "Team"})

# Add group column safely
team_to_group = {}

for group, group_teams in groups.items():
    for team in group_teams:
        team_to_group[team] = group

df.insert(0, "Group", df["Team"].map(team_to_group))

# Stage columns are counts across all simulations,
stage_columns = [
    "1st",
    "2nd",
    "3rd",
    "4th",
    "Round of 32",
    "Round of 16",
    "Quarterfinals",
    "Semifinals",
    "Final",
    "Champion",
]

# Sort the final results
# This sorts by best World Cup winning chance first.

df = df.sort_values(by=["Champion", "Final", "Semifinals", "Quarterfinals"], ascending=False).reset_index(drop=True)

# Create group-stage results DataFrame

group_stage_df = df[
    [
        "Group",
        "Team",
        "Average Points",
        "Average Goal Difference",
        "1st",
        "2nd",
        "3rd",
        "4th",
        "Round of 32",
    ]
].copy()

group_stage_df = group_stage_df.sort_values(by=["Group", "Average Points", "Average Goal Difference", "1st"],
    ascending=[True, False, False, False]).reset_index(drop=True)

group_stage_df.insert(1,"Group Rank",group_stage_df.groupby("Group").cumcount() + 1)


# Create knockout-stage results DataFrame

knockout_stage_df = df[
    [
        "Team",
        "Round of 32",
        "Round of 16",
        "Quarterfinals",
        "Semifinals",
        "Final",
        "Champion",
    ]
].copy()

knockout_stage_df = knockout_stage_df.sort_values(by=["Champion", "Final", "Semifinals", "Quarterfinals"],
                                                  ascending=False).reset_index(drop=True)

knockout_stage_df.insert(0, "Rank", knockout_stage_df.index + 1)

# Save final results to CSV
group_stage_df.to_csv("Group Stage Simulation Results.csv", index=False, encoding="utf-8-sig")

knockout_stage_df.to_csv("Knockout Stage Simulation Results.csv", index=False, encoding="utf-8-sig")

team_flags = {
    "Mexico": "🇲🇽",
    "South Africa": "🇿🇦",
    "South Korea": "🇰🇷",
    "Czechia": "🇨🇿",

    "Canada": "🇨🇦",
    "Bosnia & Herzegovina": "🇧🇦",
    "Qatar": "🇶🇦",
    "Switzerland": "🇨🇭",

    "Brazil": "🇧🇷",
    "Morocco": "🇲🇦",
    "Haiti": "🇭🇹",
    "Scotland": "🏴",

    "United States": "🇺🇸",
    "Paraguay": "🇵🇾",
    "Australia": "🇦🇺",
    "Türkiye": "🇹🇷",

    "Germany": "🇩🇪",
    "Curaçao": "🇨🇼",
    "Côte d'Ivoire": "🇨🇮",
    "Ecuador": "🇪🇨",

    "Netherlands": "🇳🇱",
    "Japan": "🇯🇵",
    "Sweden": "🇸🇪",
    "Tunisia": "🇹🇳",

    "Belgium": "🇧🇪",
    "Egypt": "🇪🇬",
    "Iran": "🇮🇷",
    "New Zealand": "🇳🇿",

    "Spain": "🇪🇸",
    "Cabo Verde": "🇨🇻",
    "Saudi Arabia": "🇸🇦",
    "Uruguay": "🇺🇾",

    "France": "🇫🇷",
    "Senegal": "🇸🇳",
    "Iraq": "🇮🇶",
    "Norway": "🇳🇴",

    "Argentina": "🇦🇷",
    "Algeria": "🇩🇿",
    "Austria": "🇦🇹",
    "Jordan": "🇯🇴",

    "Portugal": "🇵🇹",
    "DR Congo": "🇨🇩",
    "Uzbekistan": "🇺🇿",
    "Colombia": "🇨🇴",

    "England": "🏴",
    "Croatia": "🇭🇷",
    "Ghana": "🇬🇭",
    "Panama": "🇵🇦",
}

def add_flags_to_team_column(display_df):
    display_df = display_df.copy()

    display_df["Team"] = display_df["Team"].apply(
        lambda team: f"{team_flags.get(team, '')} {team}"
    )

    return display_df

def format_display_df(display_df):
    display_df = display_df.copy()

    if "Average Points" in display_df.columns:
        display_df["Average Points"] = display_df["Average Points"].apply(
            lambda value: f"{value:.2f}"
        )

    if "Average Goal Difference" in display_df.columns:
        display_df["Average Goal Difference"] = display_df["Average Goal Difference"].apply(
            lambda value: f"{value:.2f}"
        )

    percentage_columns = [
        "1st",
        "2nd",
        "3rd",
        "4th",
        "Round of 32",
        "Round of 16",
        "Quarterfinals",
        "Semifinals",
        "Final",
        "Champion",
    ]

    for column in percentage_columns:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(
                lambda value: f"{value * 100:.1f}%"
            )

    return display_df


DOCS_FOLDER = Path("docs")
DOCS_FOLDER.mkdir(exist_ok=True)


def create_html_page(title, subtitle, table_html):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>
    <main>
        <h1>{title}</h1>

        <nav>
            <a href="index.html">Home</a>
            <a href="group-stage.html">Group Stage</a>
            <a href="knockout-stage.html">Knockout Stage</a>
        </nav>

        <p class="subtitle">{subtitle}</p>

        <section>
            {table_html}
        </section>
    </main>
</body>
</html>
"""


# Group-stage page

group_display_df = add_flags_to_team_column(group_stage_df)
group_display_df = format_display_df(group_display_df)

group_table_html = group_display_df.to_html(
    index=False,
    classes="results-table",
    border=0
)

group_stage_html = create_html_page(
    title="2026 FIFA World Cup Group Stage Forecast",
    subtitle=f"Group-stage averages and advancement chances from {num_of_simulations:,} simulations.",
    table_html=group_table_html
)

with open(DOCS_FOLDER / "group-stage.html", "w", encoding="utf-8") as file:
    file.write(group_stage_html)


# Knockout-stage page

knockout_display_df = add_flags_to_team_column(knockout_stage_df)
knockout_display_df = format_display_df(knockout_display_df)

knockout_table_html = knockout_display_df.to_html(
    index=False,
    classes="results-table",
    border=0
)

knockout_stage_html = create_html_page(
    title="2026 FIFA World Cup Knockout Stage Forecast",
    subtitle=f"Chances of reaching each knockout round from {num_of_simulations:,} simulations.",
    table_html=knockout_table_html
)

with open(DOCS_FOLDER / "knockout-stage.html", "w", encoding="utf-8") as file:
    file.write(knockout_stage_html)

index_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>2026 FIFA World Cup Forecast</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>
    <main>
        <h1>2026 FIFA World Cup Forecast</h1>

        <nav>
            <a href="index.html">Home</a>
            <a href="group-stage.html">Group Stage</a>
            <a href="knockout-stage.html">Knockout Stage</a>
        </nav>

        <p class="subtitle">
            Monte Carlo simulation forecast based on adjusted Elo ratings.
            The tournament was simulated {num_of_simulations:,} times.
        </p>

        <section class="cards">
            <a class="card" href="group-stage.html">
                <h2>Group Stage Forecast</h2>
                <p>Average points, goal difference, group finish probabilities, and Round of 32 chances.</p>
            </a>

            <a class="card" href="knockout-stage.html">
                <h2>Knockout Stage Forecast</h2>
                <p>Chances of reaching the Round of 32, Round of 16, quarterfinals, semifinals, final, and winning the World Cup.</p>
            </a>
        </section>
    </main>
</body>
</html>
"""

with open(DOCS_FOLDER / "index.html", "w", encoding="utf-8") as file:
    file.write(index_html)

css = """
body {
    font-family: Arial, sans-serif;
    margin: 0;
    background: #f5f5f5;
    color: #222;
}

main {
    max-width: 1400px;
    margin: 40px auto;
    padding: 28px;
    background: white;
}

h1 {
    margin-bottom: 12px;
}

nav {
    margin-bottom: 28px;
}

nav a {
    display: inline-block;
    margin-right: 16px;
    color: #0645ad;
    text-decoration: none;
    font-weight: bold;
}

nav a:hover {
    text-decoration: underline;
}

.subtitle {
    color: #555;
    margin-bottom: 32px;
}

.results-table {
    border-collapse: collapse;
    width: 100%;
    font-size: 14px;
}

.results-table th {
    background: #222;
    color: white;
    padding: 10px;
    text-align: left;
    position: sticky;
    top: 0;
}

.results-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #ddd;
}

.results-table tr:nth-child(even) {
    background: #f2f2f2;
}

.results-table tr:hover {
    background: #e8e8e8;
}

.cards {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
}

.card {
    display: block;
    padding: 22px;
    background: #f7f7f7;
    border: 1px solid #ddd;
    text-decoration: none;
    color: #222;
}

.card:hover {
    background: #eeeeee;
}

.card h2 {
    margin-top: 0;
}
"""

with open(DOCS_FOLDER / "style.css", "w", encoding="utf-8") as file:
    file.write(css)
