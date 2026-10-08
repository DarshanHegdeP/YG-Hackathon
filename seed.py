import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.db.seed import seed_database

if __name__ == "__main__":
    seed_database()
