import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app")
API_BASE_URL = os.getenv("API_BASE_URL", "https://qae-assignment-tau.vercel.app/api")
USER_ID = os.getenv("USER_ID", "")

IMPLICIT_WAIT = 10
EXPLICIT_WAIT = 15
PAGE_LOAD_TIMEOUT = 30
