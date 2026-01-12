# Medical Pageviews Analysis

This project collects and analyzes pageview data for medical articles across various Wikimedia projects.

## Prerequisites

- Python 3.9+
- Database access to Wikimedia's labsdb (for SQL queries)
- Environment variables configured (see `.env` or `example.env`)

## Installation

```bash
pip install -r requirements.txt
```

## Workflow and Execution Steps

The data collection and processing should be performed in the following order:

### 1. Collect Article Titles
First, fetch the list of medical article titles for each language from the Wikimedia database.

```bash
python3 start_titles.py
```
- **What it does:** Retrieves medicine-related titles using SQL queries and saves them as JSON files in the configured titles directory.

### 2. Collect Pageview Data
Next, fetch the historical pageview data for the collected titles.

```bash
python3 start_views.py
```
- **What it does:** Iterates through the titles and uses the Wikimedia Pageviews API to fetch views.
- **Parameters:**
  - `-max:<number>`: Maximum number of titles to process per language.
  - `-min:<number>`: Minimum number of titles required to process a language.

### 3. Generate Reports and Upload
Finally, aggregate the data and generate a summary report to be uploaded to MDWiki.

```bash
python3 start.py
```
- **What it does:** Aggregates views by language, generates a formatted wikitable, and saves/updates the summary page on MDWiki.
- **Parameters:**
  - `year:<year>`: The year for which to generate stats (default: 2024).
  - `limit:<number>`: Limit the number of languages processed.

## Testing

Run the test suite using `pytest`:

```bash
python -m pytest
```

## Project Structure

- `src/`: Core logic, including API clients and utility functions.
- `tests/`: Automated tests mirroring the source structure.
- `start_titles.py`: Entry point for title collection.
- `start_views.py`: Entry point for view collection.
- `start.py`: Entry point for report generation.