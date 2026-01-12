import os

# load environment variables from a .env file if it exists
from dotenv import load_dotenv

load_dotenv()

my_username = os.getenv("WIKI_USERNAME", "")
mdwiki_pass = os.getenv("WIKI_PASSWORD", "")
