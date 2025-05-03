"""
Utility functions for LinkedIn Job Scraper
"""
import os
import time
import logging
import csv
import json
from typing import List, Dict, Any, Callable
from functools import wraps
import random


def setup_logging(level=logging.INFO):
    """Set up logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def retry_with_backoff(func):
    """
    Decorator to retry a function with exponential backoff
    
    Args:
        func: Function to retry
        
    Returns:
        Wrapped function with retry logic
    """
    from config import RETRY_COUNT, RETRY_BACKOFF, RETRY_MAX_BACKOFF
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        max_retries = RETRY_COUNT
        retry_count = 0
        backoff = RETRY_BACKOFF
        
        while retry_count <= max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retry_count += 1
                
                if retry_count > max_retries:
                    logger.error(f"Maximum retries ({max_retries}) exceeded: {str(e)}")
                    raise
                
                # Calculate backoff with jitter
                jitter = random.uniform(0.8, 1.2)
                sleep_time = min(backoff * (2 ** (retry_count - 1)) * jitter, RETRY_MAX_BACKOFF)
                
                logger.warning(
                    f"Retry {retry_count}/{max_retries} after error: {str(e)}. "
                    f"Retrying in {sleep_time:.2f} seconds..."
                )
                
                time.sleep(sleep_time)
                
    return wrapper


def export_to_csv(jobs: List[Dict[str, Any]], filename: str) -> str:
    """
    Export job listings to CSV file
    
    Args:
        jobs: List of job dictionaries
        filename: Output filename (without extension)
        
    Returns:
        Path to the saved file
    """
    logger = logging.getLogger(__name__)
    
    if not jobs:
        logger.warning("No jobs to export")
        return ""
    
    # Ensure filename has .csv extension
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            # Get all possible fields from all jobs
            fieldnames = set()
            for job in jobs:
                fieldnames.update(job.keys())
            
            # Sort fieldnames to ensure consistent output
            fieldnames = sorted(fieldnames)
            
            # Move important fields to the beginning
            for field in ['id', 'title', 'company', 'location', 'url', 'description']:
                if field in fieldnames:
                    fieldnames.remove(field)
                    fieldnames.insert(0, field)
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)
            
        logger.info(f"Exported {len(jobs)} jobs to {filename}")
        return filename
    
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise


def export_to_json(jobs: List[Dict[str, Any]], filename: str) -> str:
    """
    Export job listings to JSON file
    
    Args:
        jobs: List of job dictionaries
        filename: Output filename (without extension)
        
    Returns:
        Path to the saved file
    """
    logger = logging.getLogger(__name__)
    
    if not jobs:
        logger.warning("No jobs to export")
        return ""
    
    # Ensure filename has .json extension
    if not filename.endswith(".json"):
        filename = f"{filename}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "count": len(jobs),
                "jobs": jobs
            }, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported {len(jobs)} jobs to {filename}")
        return filename
    
    except Exception as e:
        logger.error(f"Error exporting to JSON: {str(e)}")
        raise
