import os
import sys
from pathlib import Path

from dotenv import load_dotenv

new_var = Path(__file__).parents[3]

# load environment variables from a .env file if it exists
load_dotenv(new_var / ".env")

my_username = os.getenv("MDWIKI_USERNAME", "")
mdwiki_pass = os.getenv("MDWIKI_PASSWORD", "")
MAIN_PATH = os.getenv("MAIN_PATH", "")

if not my_username:
    raise ValueError("Please set MDWIKI_USERNAME environment variable")

main_dump_path = Path(MAIN_PATH) if MAIN_PATH else new_var / "dumps_all_agents"

json_titles_path = main_dump_path / "titles"
views_by_year_path = main_dump_path / "views_by_year"

main_dump_path.mkdir(exist_ok=True)
json_titles_path.mkdir(exist_ok=True)
views_by_year_path.mkdir(exist_ok=True)

parallelism = 10

for arg in sys.argv:
    key, _, val = arg.partition(":")
    if key == "-para":
        parallelism = int(val) or parallelism
