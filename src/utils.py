from datetime import datetime


def log_with_timestamp(message):
    """Log message with timestamp prefix"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")