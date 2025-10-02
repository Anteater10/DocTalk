import os, sys

# Add the api/ directory to the import path so `from app.main import app` works
CURRENT_DIR = os.path.dirname(__file__)
API_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)
