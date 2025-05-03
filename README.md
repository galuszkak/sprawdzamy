# Web Scraper for Ideas and Votes

This project is a web scraper designed to extract voting information for ideas and projects from the specified website. It collects data on the number of votes from the main site and prints the results to the console.

## Project Structure

```
web-scraper-gcp
├── src
│   ├── scraper.py          # Main logic for the web scraper using Playwright
│   ├── config.py          # Configuration settings for the scraper
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
└── README.md               # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd web-scraper-gcp
   ```

2. **Install dependencies:**
   Ensure you have Python 3.7 or higher installed. Then, install the required packages using pip:
   ```
   pip install -r requirements.txt
   ```
   Install Playwright browsers:
   ```
   playwright install
   ```

3. **Configure the scraper:**
   Edit `src/config.py` to set the target URL and any other necessary parameters (like headless mode).

4. **Run the scraper:**
   You can run the scraper directly using:
   ```
   python src/scraper.py
   ```

## Usage

The scraper will run once when executed. It extracts project names, votes from the main site, and the timestamp of the scrape. The data is printed to the console at the end of the execution.

## Docker

To build and run the scraper in a Docker container, use the following commands:

1. **Build the Docker image:**
   ```
   docker build -t web-scraper-gcp .
   ```

2. **Run the Docker container:**
   ```
   docker run --rm web-scraper-gcp
   ```
   *(Using `--rm` automatically removes the container when it exits)*

## Notes

- The scraper uses Playwright with Chromium by default.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.