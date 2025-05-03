# LinkedIn Job Scraper

A Python-based web application and command-line tool for scraping job listings from LinkedIn with search parameters and structured data output.

## Features

- Web-based interface for easy job searching and results viewing
- Command-line interface for automation and scripting
- Scrape job listings from LinkedIn based on keywords and location
- Extract detailed job information (title, company, location, description, etc.)
- Handle pagination to retrieve multiple pages of results
- Export data in CSV or JSON format
- Implement rate limiting and user agent rotation to avoid being blocked
- Proper error handling and retry mechanisms
- Real-time status updates during scraping process

## Screenshots

### Web Interface
- **Home Page**: Search form for job keywords, location, and pagination options
- **Results Page**: Real-time scraping status and job listings in a sortable table
- **CLI Usage**: Documentation for command-line usage

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Web Scraping**: Selenium, BeautifulSoup4
- **Data Export**: CSV, JSON

## Requirements

- Python 3.6+
- Selenium
- BeautifulSoup4
- Requests
- Flask
- Chromium or Chrome Browser

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Ensure you have Chrome or Chromium browser installed

## Usage

### Web Interface

1. Start the web server:

```bash
python main.py
```

2. Open your browser and navigate to `http://localhost:5000`
3. Enter job search keywords, location (optional), and number of pages to scrape
4. Click "Start Scraping" to begin the process
5. View results in real-time and export to CSV or JSON when complete

### Command Line

For command-line usage:

```bash
python main.py --keywords "python developer" --location "remote" --pages 2 --format json
```

Available options:
- `--keywords`: Job search keywords (required)
- `--location`: Job location (optional)
- `--pages`: Number of pages to scrape (default: 1)
- `--format`: Output format (csv or json, default: csv)
- `--output`: Output filename without extension (default: auto-generated)
- `--verbose`: Enable verbose logging

## Disclaimer

This tool is for educational purposes only. Please respect LinkedIn's terms of service and use responsibly. Excessive scraping may result in IP blocking.
   