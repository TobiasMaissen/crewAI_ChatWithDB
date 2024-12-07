from datetime import datetime, timedelta
import os

def is_file_outdated(file_path: str, days_threshold: int = 30) -> bool:
    """Check if the file is older than the given threshold in days"""
    if not os.path.exists(file_path):
        return True # Treat missing file as outdated
    
    last_modified = os.path.getmtime(file_path)
    last_modified_date = datetime.fromtimestamp(last_modified)
    # True/False based on the calculation result
    return (datetime.now() - last_modified_date) > timedelta(days=days_threshold)