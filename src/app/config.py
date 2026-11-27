import os
from pathlib import Path

from dotenv import load_dotenv

home = Path.home()

# load environment variables from a .env file if it exists
load_dotenv(Path(__file__).parents[3] / ".env")

my_username = os.getenv("MDWIKI_USERNAME", "Mr. Ibrahem")
mdwiki_pass = os.getenv("MDWIKI_HIMO_PASSWORD", "")
VIEWS_DUMP_PATH = os.getenv("VIEWS_DUMP_PATH", "")

if not mdwiki_pass:
    raise ValueError("Please set MDWIKI_HIMO_PASSWORD environment variable")

main_dump_path = Path(VIEWS_DUMP_PATH) if VIEWS_DUMP_PATH else home / "data/views_dumps"

json_titles_path = main_dump_path / "titles"
views_by_year_path = main_dump_path / "views_by_year"

main_dump_path.mkdir(exist_ok=True)
json_titles_path.mkdir(exist_ok=True)
views_by_year_path.mkdir(exist_ok=True)

parallelism = 10
