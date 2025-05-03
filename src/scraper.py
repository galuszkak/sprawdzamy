import time
import random
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from google.cloud import bigquery # Import BigQuery library
import config

# Configuration
TARGET_URL = config.TARGET_URL
PROJECT_ARTICLE_SELECTOR = ".ideas article.idea"
PROJECT_NAME_SELECTOR = "h2 a" # Used for name and URL
VOTE_SELECTOR = "strong" # For votes on the main listing page
VOTE_SELECTOR_IN_PROJECT = "aside.digger strong" # Selector for votes *on the project page* - ADJUST IF NEEDED
BIGQUERY_TABLE_ID = "sprawdzamy.votes" # Define BigQuery table ID

def setup_browser(p):
    browser = p.chromium.launch(headless=config.HEADLESS_BROWSER)
    page = browser.new_page()
    return browser, page

def scrape_votes(page):
    page.goto(TARGET_URL)
    page.wait_for_load_state('networkidle')

    project_articles = page.locator(PROJECT_ARTICLE_SELECTOR)
    initial_data = []
    count = project_articles.count()
    print(f"Found {count} project articles on the main page.")

    # --- Step 1: Scrape initial data from the main listing page ---
    for i in range(count):
        article = project_articles.nth(i)
        try:
            name_element = article.locator(PROJECT_NAME_SELECTOR)
            project_name = name_element.text_content().strip() if name_element.count() > 0 else "Name not found"
            project_url = name_element.get_attribute("href") if name_element.count() > 0 else None

            vote_element = article.locator(VOTE_SELECTOR)
            main_votes_text = vote_element.text_content().strip() if vote_element.count() > 0 else "0"
            main_votes = main_votes_text.split()[0]

            if project_url:
                # Ensure the URL is absolute
                if not project_url.startswith(('http://', 'https://')):
                    base_url = '/'.join(TARGET_URL.split('/')[:3]) # Get base URL like https://sprawdzamy.com
                    project_url = base_url + project_url if project_url.startswith('/') else base_url + '/' + project_url

                initial_data.append({
                    "project_name": project_name,
                    "main_votes": main_votes,
                    "project_url": project_url,
                })
            else:
                 print(f"Skipping article {i} due to missing URL.")

        except Exception as e:
            print(f"Error processing article {i} on main page: {e}")
            # print(f"Article HTML: {article.inner_html()}")

    # --- Step 2: Visit each project page and scrape project-specific votes ---
    results = []
    print(f"\nVisiting {len(initial_data)} project pages...")
    for idx, data in enumerate(initial_data):
        print(f"Processing project {idx+1}/{len(initial_data)}: {data['project_name']}")
        project_votes_int = None # Default to None for nullable field
        main_votes_int = 0 # Default to 0 for required field

        try:
            # Convert main_votes from initial scrape (already string)
            main_votes_str = data["main_votes"]
            main_votes_int = int(main_votes_str) if main_votes_str.isdigit() else 0

            page.goto(data["project_url"])
            page.wait_for_load_state('networkidle') # Wait for project page to load

            # Scrape votes from the project page using the specific selector
            project_vote_element = page.locator(VOTE_SELECTOR_IN_PROJECT).first # Assume first match is the one
            project_votes_text = project_vote_element.text_content().strip() if project_vote_element.count() > 0 else None
            if project_votes_text:
                project_votes_str = project_votes_text.split()[0] 
                project_votes_int = int(project_votes_str) if project_votes_str.isdigit() else None # Convert to int or None

            result = {
                "project_name": data["project_name"],
                "main_page_votes": main_votes_int, # Use converted int
                "project_page_votes": project_votes_int, # Use converted int or None
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            results.append(result)
            print(result) # Optional: print the processed result

        except Exception as e:
            print(f"Error visiting or scraping project page {data['project_url']}: {e}")
            # Append partial data with default/error values if needed, ensuring types are correct
            results.append({
                "project_name": data["project_name"],
                "main_page_votes": main_votes_int, # Use already converted or default int
                "project_page_votes": None, # Default to None on error for nullable field
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        finally:
             # Add random delay only if it's not the last project
            if idx < len(initial_data) - 1:
                delay = random.uniform(3, 8)
                print(f"Waiting for {delay:.2f} seconds before next project...")
                time.sleep(delay)

    return results

def main():
    with sync_playwright() as p:
        browser, page = setup_browser(p)

        try:
            scraped_data = scrape_votes(page)
            if scraped_data:
                print(f"\nAttempting to insert {len(scraped_data)} rows into BigQuery table {BIGQUERY_TABLE_ID}...")
                try:
                    # Directly use scraped_data as it contains the correctly formatted rows
                    bq_client = bigquery.Client()
                    errors = bq_client.insert_rows_json(BIGQUERY_TABLE_ID, scraped_data)
                    if not errors:
                        print(f"Successfully inserted {len(scraped_data)} rows into {BIGQUERY_TABLE_ID}.")
                    else:
                        print("Encountered errors while inserting rows into BigQuery:")
                        for error in errors:
                            print(error)
                except Exception as e:
                    print(f"Error inserting data into BigQuery: {e}")
            else:
                print("No data scraped to insert into BigQuery.")

        finally:
            browser.close()

if __name__ == "__main__":
    main()