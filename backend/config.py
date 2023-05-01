"""config.py"""
import os

# Get the Flask app's root directory
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Specify the path to key resources
DATABASE_PATH = os.path.join(APP_ROOT, '..', 'database', 'database.sqlite')
PROMPT_PATH = os.path.join(APP_ROOT, '..', 'database', 'prompt.txt')
PROMPT_PATH_LINK = os.path.join(APP_ROOT, '..', 'database', 'prompt_link.txt')
# Make sure to include API_KEYS from OpenAI
API_KEYS = []
MAX_TRIALS = len(API_KEYS)
