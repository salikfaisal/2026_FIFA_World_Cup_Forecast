from playwright.sync_api import sync_playwright
import pandas as pd


# Website we are scraping
SOFIFA_URL = "https://sofifa.com/teams?type=national"


# JavaScript code that runs inside the browser page.
# It looks at each table row and extracts the team ratings.
EXTRACT_TEAM_ROWS_JS = """
rows => rows.map(row => {
    // Helper function:
    // Find an element inside the row and return its visible text.
    const getText = selector => {
        const el = row.querySelector(selector);
        return el ? el.innerText.trim() : null;
    };

    // Helper function:
    // Some SoFIFA rating numbers are inside <em title="86">86</em>.
    // This gets the title value first, or falls back to visible text.
    const getTitleOrText = selector => {
        const el = row.querySelector(selector);
        if (!el) return null;
        return el.getAttribute("title") || el.innerText.trim();
    };

    // Return one clean object for each national team row.
    return {
        team: getText("td.s20 a[href^='/team/']"),
        overall: getTitleOrText("td[data-col='oa'] em"),
        attack: getTitleOrText("td[data-col='at'] em"),
        midfield: getTitleOrText("td[data-col='md'] em"),
        defense: getTitleOrText("td[data-col='df'] em"),
        players: getText("td[data-col='ps']"),
        starting_xi_average_age: getText("td[data-col='sa']")
    };
})
"""


def get_sofifa_national_team_ratings():

    with sync_playwright() as p:
        # headless=False lets you see the browser while testing.
        # Later you can change this to headless=True.
        browser = p.chromium.launch(headless=False)

        # Open a fresh browser page.
        page = browser.new_page()

        # Load the page.
        # Do NOT use wait_until="networkidle" here because SoFIFA can keep
        # background requests running and cause a timeout.
        page.goto(SOFIFA_URL, wait_until="domcontentloaded", timeout=60000)

        # Wait until the team table rows exist.
        # This is better than waiting for the entire page to fully stop loading.
        page.wait_for_selector("article table tbody tr", timeout=60000)

        # Select all table rows and run the JavaScript extraction code on them.
        rows = page.locator("article table tbody tr").evaluate_all(
            EXTRACT_TEAM_ROWS_JS
        )

        # Close the browser once we have the data.
        browser.close()

    # Convert the list of dictionaries into a DataFrame.
    df = pd.DataFrame(rows)

    # Remove rows that did not contain a team name.
    df = df.dropna(subset=["team"])

    # Convert number-looking columns from strings to numeric values.
    numeric_columns = [
        "overall",
        "attack",
        "midfield",
        "defense",
        "players",
        "starting_xi_average_age",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


if __name__ == "__main__":
    # Run the scraper.
    sofifa_df = get_sofifa_national_team_ratings()

    # Preview the results.
    print(sofifa_df.head(60))
    print(f"\nTotal teams scraped: {len(sofifa_df)}")

    # Save results to CSV.
    sofifa_df.to_csv(
        "sofifa_national_team_ratings.csv",
        index=False,
        encoding="utf-8-sig"
    )