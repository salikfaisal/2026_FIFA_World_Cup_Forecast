import pandas as pd
import statistics
import math
from scipy.stats import poisson


xg_elo_df = pd.read_csv("Tournament Starting Elo Ratings.csv")
match_results_df = pd.read_csv("Match Results.csv")

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

xg_elo_df['Team'] = xg_elo_df['Team'].replace(name_fixes)
match_results_df['Home Team'] = match_results_df['Home Team'].replace(name_fixes)
match_results_df['Away Team'] = match_results_df['Away Team'].replace(name_fixes)

# Convert to a dictionary with Team as keys and Rating as values
xg_elo_dict = xg_elo_df.set_index('Team')['Starting Elo'].to_dict()


for idx, match in match_results_df.iterrows():
    # gets information regarding the match
    home_team = match['Home Team']
    away_team = match['Away Team']
    home_xg = match['Home xG']
    away_xg = match['Away xG']
    country_of_venue = match['Country of Venue']
    # breaks the loop when there's matches yet to be played
    if pd.isna(home_xg):
        break
    # gets the elo rating of each team from the dictionary
    home_elo = xg_elo_dict[home_team]
    away_elo = xg_elo_dict[away_team]
    # adds 100 rating if a team is the host
    if home_team == country_of_venue:
        home_elo += 100
    elif away_team == country_of_venue:
        away_elo += 100
    # calculates the home team's win expectancy based on both teams' elo ratings
    home_we = 1 / (10 ** ((away_elo - home_elo) / 400) + 1)
    # calculates the mean expected goal difference based on the home team's win expectancy
    home_mean_gd = statistics.NormalDist(0, 1.3).inv_cdf(home_we)
    # gets the pre-match win and loss probabilities for the home team
    z_loss_mark = (-0.5 - home_mean_gd) / 1.3
    z_win_mark = (0.5 - home_mean_gd) / 1.3
    home_pre_match_win_prob =  1 - statistics.NormalDist().cdf(z_win_mark)
    home_pre_match_loss_prob = statistics.NormalDist().cdf(z_loss_mark)
    # gets a list based on a Poisson distribution of Expected Goals in a Match for both teams
    home_gps = []
    away_gps = []
    for goal_count in range(11):
        home_goal_prob = poisson.pmf(k=goal_count, mu=home_xg)
        away_goal_prob = poisson.pmf(k=goal_count, mu=away_xg)
        home_gps.append(home_goal_prob)
        away_gps.append(away_goal_prob)
    # gets a dictionary of goal differences and the probabilities based on the expected goals
    gd_probabilities = {}
    for gd in range(-10, 11):
        z_lower = (gd - 0.5 - home_mean_gd) / 1.3
        z_upper = (gd + 0.5 - home_mean_gd) / 1.3
        # Approximate the probabilities using the standard normal distribution
        probability_lower = statistics.NormalDist().cdf(z_upper)
        probability_upper = statistics.NormalDist().cdf(z_lower)
        # gets the pre-match probability for a particular Goal Difference Margin
        pre_match_gd_prob = probability_lower - probability_upper
        gd_probabilities.update({gd: 0})
    # estimates the probability of each goal difference based on the expected goals statistic
    for home_gc, home_gp in enumerate(home_gps):
        for away_gc, away_gp, in enumerate(away_gps):
            gd = home_gc - away_gc
            prob = home_gp * away_gp
            gd_probabilities[gd] += prob
    # calculates the change in elo rating based on the probabilities from the expected goal statistic
    change_in_elo = 0
    for gd, prob in gd_probabilities.items():
        if gd < -3:
            change_in_elo += (0 - home_we) * 60 * (1.75 + (gd - 3) / 8) * prob
        elif gd == -3:
            change_in_elo += (0 - home_we) * 60 * 1.75 * prob
        elif gd == -2:
            change_in_elo += (0 - home_we) * 60 * 1.5 * prob
        elif gd == -1:
            change_in_elo += (0 - home_we) * 60 * prob
        elif gd == 0:
            change_in_elo += (0.5 - home_we) * 60 * prob
        elif gd == 1:
            change_in_elo += (1 - home_we) * 60 * prob
        elif gd == 2:
            change_in_elo += (1 - home_we) * 60 * 1.5 * prob
        elif gd == 3:
            change_in_elo += (1 - home_we) * 60 * 1.75 * prob
        elif gd > 3:
            change_in_elo += (1 - home_we) * 60 * (1.75 + (gd - 3) / 8) * prob
    # updates the dictionary based on the xG result
    xg_elo_dict[home_team] += change_in_elo
    xg_elo_dict[away_team] -= change_in_elo