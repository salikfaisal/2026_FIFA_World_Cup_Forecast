# 2026_FIFA_World_Cup_Forecast
2026_FIFA_World_Cup_Forecast utilizes Expected Goals (xG) data and squad quality ratings within an Elo-based Monte Carlo model to simulate the 2026 FIFA World Cup. These projections are generated through 10,000 simulations for each competition.

## Overview

These simulations are calculated using a combination of actual league results and simulated matches based on [Elo ratings](https://github.com/salikfaisal/2026_FIFA_World_Cup_Forecast/blob/main/Adjusted%20Elo%20Ratings.csv). Elo Ratings are weighted based on three different metrics, as shown in the following table:

| Weight | Short Description         | Long Description                                                                                                                   |
| ------ | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 40%    | Squad Quality             | Squad Quality Metrics are determined by the FC Ratings of all 26 players for each National Team and the likely Playing XI from [sofifa](https://sofifa.com/teams?type=national). They are then converted into an Elo rating. This rating is combined with other metrics to assess a team's overall strength on paper, considering the quality of players it has. |
| 35%    | Expected Goals            | Expected Goals (xG) ratings utilize a Poisson Distribution model to predict the points exchanged in a match between two teams. These statistics focus on the quality of scoring chances created during a match and do not consider the actual match results. The Expected Goals data is sourced from [Opta Analayst](https://theanalyst.com/). |
| 25%    | [World Elo Ratings](https://www.eloratings.net/) | Club Elo ratings are derived from real match results using the formula provided by [World Elo Ratings](https://www.eloratings.net/about).        |

Expect regular updates, typically after every match day!
