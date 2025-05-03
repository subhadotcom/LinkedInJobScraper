#!/usr/bin/env python3
"""
LinkedIn Job Scraper - Web Application
"""
import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, flash, redirect, url_for
import threading
import time

from linkedin_scraper import LinkedInJobScraper
from utils import setup_logging, export_to_csv, export_to_json

# Set up Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SESSION_SECRET", "linkedin-job-scraper-secret")

# Set up logging
setup_logging(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global variables to store scraping state
scraping_status = {
    "is_scraping": False,
    "total_jobs": 0,
    "jobs_scraped": 0,
    "current_page": 0,
    "total_pages": 0,
    "start_time": None,
    "end_time": None,
    "status": "idle",  # idle, running, completed, error
    "error": None,
    "jobs": []
}

def run_scraper(keywords, location, pages):
    """Run scraper in a background thread"""
    global scraping_status
    
    try:
        scraping_status["is_scraping"] = True
        scraping_status["status"] = "running"
        scraping_status["start_time"] = datetime.now()
        scraping_status["total_pages"] = pages
        scraping_status["jobs"] = []
        scraping_status["error"] = None
        
        # Log scraping parameters
        logger.info(f"Starting LinkedIn Job Scraper with parameters:")
        logger.info(f"Keywords: {keywords}")
        logger.info(f"Location: {location}")
        logger.info(f"Pages to scrape: {pages}")
        
        try:
            # Initialize scraper
            scraper = LinkedInJobScraper()
            
            # Execute scraping
            scraping_status["jobs"] = scraper.scrape_jobs(
                keywords=keywords,
                location=location,
                pages=pages,
                status_callback=update_scraping_status
            )
            
            # Update scraping status
            scraping_status["status"] = "completed"
            scraping_status["total_jobs"] = len(scraping_status["jobs"])
            logger.info(f"Scraping completed. Found {scraping_status['total_jobs']} jobs.")
            
        except Exception as e:
            logger.error(f"Error during scraping process: {str(e)}")
            
            # Check for specific Selenium errors
            error_message = str(e)
            if "chromedriver" in error_message.lower() and "127" in error_message:
                error_message = "Could not start Selenium WebDriver. The system may be missing Chrome/Chromium dependencies."
            elif "webdriver" in error_message.lower():
                error_message = "Selenium WebDriver error. Please make sure Chrome/Chromium is installed."
            
            scraping_status["error"] = error_message
            
            # Create mock data for UI testing if no jobs were found yet
            if not scraping_status["jobs"] and os.environ.get("ALLOW_MOCK_DATA") == "1":
                logger.warning("Creating mock data for testing purposes")
                scraping_status["jobs"] = [{
                    "id": f"mock{i}",
                    "title": f"Sample Job {i}",
                    "company": "Demo Company",
                    "location": location or "Remote",
                    "url": "https://linkedin.com/jobs",
                    "description": "This is a mock job listing for testing purposes.",
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                    "job_type": "Full-time",
                    "seniority_level": "Entry level",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_mock": True
                } for i in range(1, 4)]
                scraping_status["status"] = "partial_error"
                scraping_status["total_jobs"] = len(scraping_status["jobs"])
            else:
                scraping_status["status"] = "error"
            
    except Exception as e:
        logger.error(f"Error in scraper thread: {str(e)}")
        scraping_status["status"] = "error"
        scraping_status["error"] = f"General error: {str(e)}"
    
    finally:
        scraping_status["is_scraping"] = False
        scraping_status["end_time"] = datetime.now()

def update_scraping_status(page, jobs_count):
    """Update scraping status"""
    global scraping_status
    scraping_status["current_page"] = page
    scraping_status["jobs_scraped"] = jobs_count


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Start scraping process"""
    global scraping_status
    
    # Check if scraping is already in progress
    if scraping_status["is_scraping"]:
        flash("A scraping task is already in progress", "warning")
        return redirect(url_for('index'))
    
    # Get form data
    keywords = request.form.get('keywords')
    location = request.form.get('location', '')
    pages = int(request.form.get('pages', 1))
    
    # Validate input
    if not keywords:
        flash("Keywords are required", "danger")
        return redirect(url_for('index'))
    
    if pages < 1 or pages > 10:
        flash("Pages must be between 1 and 10", "danger")
        return redirect(url_for('index'))
    
    # Start scraping in a background thread
    scraper_thread = threading.Thread(
        target=run_scraper,
        args=(keywords, location, pages)
    )
    scraper_thread.daemon = True
    scraper_thread.start()
    
    flash("Scraping started. This may take some time.", "info")
    return redirect(url_for('results'))

@app.route('/status')
def status():
    """Get current scraping status"""
    return jsonify(scraping_status)

@app.route('/results')
def results():
    """Show scraping results"""
    return render_template('results.html')

@app.route('/export', methods=['POST'])
def export():
    """Export job data to file"""
    global scraping_status
    
    # Check if there are jobs to export
    if not scraping_status["jobs"]:
        flash("No jobs to export", "warning")
        return redirect(url_for('results'))
    
    # Get export format
    export_format = request.form.get('format', 'csv')
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = f"linkedin_jobs_{timestamp}"
    
    try:
        # Export data
        if export_format == 'csv':
            file_path = export_to_csv(scraping_status["jobs"], output_name)
            mime_type = 'text/csv'
        else:
            file_path = export_to_json(scraping_status["jobs"], output_name)
            mime_type = 'application/json'
        
        # Send file to user
        return send_file(
            file_path, 
            mimetype=mime_type, 
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        flash(f"Error exporting data: {str(e)}", "danger")
        return redirect(url_for('results'))

@app.route('/clear', methods=['POST'])
def clear():
    """Clear scraping results"""
    global scraping_status
    
    # Reset scraping status
    scraping_status = {
        "is_scraping": False,
        "total_jobs": 0,
        "jobs_scraped": 0,
        "current_page": 0,
        "total_pages": 0,
        "start_time": None,
        "end_time": None,
        "status": "idle",
        "error": None,
        "jobs": []
    }
    
    flash("Results cleared", "info")
    return redirect(url_for('index'))

@app.route('/cli', methods=['GET'])
def cli_info():
    """Show CLI usage information"""
    return render_template('cli.html')

# For command line usage
def main():
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    main()
