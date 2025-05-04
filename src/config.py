import os
# Configuration settings for the web scraper

TARGET_URL = "https://sprawdzamy.com/zgloszone-pomysly/"
HEADLESS_BROWSER = True  # Set to True to run the browser in headless mode
SCRAPE_INTERVAL_MINUTES = 15  # Interval for scraping in minutes

# --- Google Cloud Storage --- #
GCS_BUCKET_NAME = os.environ.get("BUCKET", "your-bucket")  # <<< CHANGE THIS to your actual GCS bucket name
SCREENSHOT_TEMP_DIR = "/tmp/screenshots" # Local temporary directory for screenshots