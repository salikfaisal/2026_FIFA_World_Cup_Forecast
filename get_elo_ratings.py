from playwright.sync_api import sync_playwright
import pandas as pd

url = "https://www.eloratings.net/"

js_code = """
rows => rows.map(row => {
    const getText = selector => {
        const el = row.querySelector(selector);
        return el ? el.innerText.trim() : null;
    };

    return {
        rank: getText(".l0"),
        team: getText(".team-cell a") || getText(".l1"),
        elo: getText(".l2"),
        one_year_rank_change: getText(".l3"),
        one_year_rating_change: getText(".l4")
    };
})
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")

    rows = page.locator("#maintable_World .slick-row").evaluate_all(js_code)

    browser.close()

elo_df = pd.DataFrame(rows)

elo_df["rank"] = pd.to_numeric(elo_df["rank"])
elo_df["elo"] = pd.to_numeric(elo_df["elo"])

elo_df.to_csv("elo_ratings.csv", index=False)