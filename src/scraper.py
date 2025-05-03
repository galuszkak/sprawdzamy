import time
import json
import random # Import random module
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import config

# Configuration
TARGET_URL = config.TARGET_URL
PROJECT_ARTICLE_SELECTOR = ".ideas article.idea"
PROJECT_NAME_SELECTOR = "h2 a" # Used for name and URL
VOTE_SELECTOR = "strong" # For votes on the main listing page
VOTE_SELECTOR_IN_PROJECT = "aside.digger strong" # Selector for votes *on the project page* - ADJUST IF NEEDED

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
            main_votes = main_votes_text.split()[0] # Assuming format "123 Głosów"

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
        try:
            page.goto(data["project_url"])
            page.wait_for_load_state('networkidle') # Wait for project page to load

            # Scrape votes from the project page using the specific selector
            project_vote_element = page.locator(VOTE_SELECTOR_IN_PROJECT).first # Assume first match is the one
            project_votes_text = project_vote_element.text_content().strip() if project_vote_element.count() > 0 else "0"
            project_votes = project_votes_text.split()[0] # Assuming format "123 Głosów"
            result = {
                "project_name": data["project_name"],
                "main_votes": data["main_votes"],
                "project_votes": project_votes, # Add the project page votes
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            results.append(result)
            print(result)

        except Exception as e:
            print(f"Error visiting or scraping project page {data['project_url']}: {e}")
            # Append partial data or skip
            results.append({
                "project_name": data["project_name"],
                "main_votes": data["main_votes"],
                "project_votes": "Error", # Indicate error
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        finally:
             # Add random delay only if it's not the last project
            if idx < len(initial_data) - 1:
                delay = random.uniform(5, 25)
                print(f"Waiting for {delay:.2f} seconds before next project...")
                time.sleep(delay)

    return results

def main():
    with sync_playwright() as p:
        browser, page = setup_browser(p)

        try:
            scraped_data = scrape_votes(page)
            processed_data = []
            for data in scraped_data:
                try:
                    # Ensure votes are integers before printing
                    main_votes_int = int(data["main_votes"]) if isinstance(data["main_votes"], str) and data["main_votes"].isdigit() else 0
                    project_votes_int = int(data["project_votes"]) if isinstance(data["project_votes"], str) and data["project_votes"].isdigit() else 0 # Handle potential "Error" string

                    processed_data.append({
                        "project_name": data["project_name"],
                        "main_votes": main_votes_int,
                        "project_votes": project_votes_int, # Add project votes
                        "timestamp": data["timestamp"]
                    })
                except ValueError as ve:
                     print(f"Could not convert votes to int for {data.get('project_name', 'N/A')}: main='{data.get('main_votes', 'N/A')}', project='{data.get('project_votes', 'N/A')}'. Error: {ve}")
                except Exception as e:
                    print(f"Error processing data row: {data}. Error: {e}")

            # Print the final processed data
            print("\n--- Scraped Data ---")
            if processed_data:
                print(json.dumps(processed_data, indent=2, ensure_ascii=False))
            else:
                print("No data scraped or processed.")
            print("--- End of Scraped Data ---")

        finally:
            browser.close()

if __name__ == "__main__":
    main()