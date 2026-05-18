# This file stores th econfiguration variables

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("URL")
SUPABASE_KEY = os.getenv("KEY")