import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# load environment variables from a .env file if it exists
load_dotenv()

my_username = os.getenv("MDWIKI_USERNAME", "")
mdwiki_pass = os.getenv("MDWIKI_PASSWORD", "")

main_dump_path = Path(__file__).parent.parent / "dumps"

json_titles_path = main_dump_path / "titles"
views_new_path = main_dump_path / "views_new"
views_by_year_path = main_dump_path / "views_by_year"
total_sites_by_year_path = main_dump_path / "total_sites_by_year"

main_dump_path.mkdir(parents=True, exist_ok=True)
json_titles_path.mkdir(parents=True, exist_ok=True)
views_new_path.mkdir(parents=True, exist_ok=True)
views_by_year_path.mkdir(parents=True, exist_ok=True)
total_sites_by_year_path.mkdir(parents=True, exist_ok=True)

parallelism = 10

for arg in sys.argv:
    key, _, val = arg.partition(":")
    if key == "-para":
        parallelism = int(val) or parallelism
