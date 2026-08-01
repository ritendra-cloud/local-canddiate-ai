#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings
from app.models.database import init_database
init_database(settings.database_file); print('Local SQLite database initialized.')
