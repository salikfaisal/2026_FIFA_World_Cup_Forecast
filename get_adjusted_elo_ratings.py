import pandas as pd
from get_xg_elo_ratings import xg_elo_dict

# Import Elo and SOFIFA data
elo_df = pd.read_csv("elo_ratings.csv")

# Use utf-8-sig so names with accents, like Türkiye and Côte d'Ivoire,
# are read correctly.
sofifa_df = pd.read_csv("sofifa_national_team_ratings.csv", encoding="utf-8-sig")

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

# Apply the same dictionary to both dataframes.
# If a team is not in the dictionary, it stays exactly the same.
elo_df["team"] = elo_df["team"].replace(name_fixes)
sofifa_df["team"] = sofifa_df["team"].replace(name_fixes)

# merge SOFIFA onto Elo
ratings_df = elo_df.merge(sofifa_df, on="team",how="left")

# If "overall" exists, that team matched with SoFIFA.
ratings_df["has_sofifa"] = ratings_df["overall"].notna()

matched = ratings_df["has_sofifa"]

sofifa_mean = ratings_df.loc[matched, "overall"].mean()
sofifa_sd = ratings_df.loc[matched, "overall"].std(ddof=0)

elo_mean = ratings_df.loc[matched, "elo"].mean()
elo_sd = ratings_df.loc[matched, "elo"].std(ddof=0)

# Formula:
# 1. Convert SoFIFA overall into a z-score.
# 2. Put that z-score onto the Elo scale.
ratings_df.loc[matched, "sofifa_elo"] = (elo_mean + ((ratings_df.loc[matched, "overall"] - sofifa_mean) / sofifa_sd)
                                         * elo_sd)

# So for missing teams, their SoFIFA-based Elo equals their normal Elo.
ratings_df.loc[~matched, "sofifa_elo"] = ratings_df.loc[~matched, "elo"]

ratings_df["sofifa_elo"] = ratings_df["sofifa_elo"]

# Creates a new column for xG Elo Ratings
ratings_df["xG Elo Rating"] = ratings_df["team"].map(xg_elo_dict)

# Renames columns
ratings_df.rename(columns={"team": "Team", "elo": "Elo Rating", "sofifa_elo": "FC Elo Rating"}, inplace=True)

# gets the Adjusted Elo Ratings
ratings_df["Adjusted Elo Rating"] = (ratings_df["Elo Rating"]  * 0.25 + ratings_df["FC Elo Rating"] * 0.4 +
                                     ratings_df["xG Elo Rating"] * 0.35)

# Sorts by Adjusted Elo Ratings and Ranks them
ratings_df = ratings_df.sort_values(
    by="Adjusted Elo Rating",
    ascending=False
).reset_index(drop=True)

ratings_df["Rank"] = ratings_df.index + 1

# Re-orders the dataframe's columns and exports as a csv
ratings_df = ratings_df[["Rank", "Team",  "Adjusted Elo Rating", "Elo Rating", "FC Elo Rating", "xG Elo Rating"]]

ratings_df = ratings_df.head(48)
ratings_df.to_csv("Adjusted Elo Ratings.csv", index=False, encoding="utf-8-sig")